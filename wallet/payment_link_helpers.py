# wallet/payment_link_helpers.py
import logging
from decimal import Decimal
from django.db import transaction
from wallet.models import PaymentLink, PaymentLinkContribution, WalletTransaction
from savings.models import SavingsGoalTransaction

logger = logging.getLogger(__name__)


def process_payment_link_contribution(reference, wallet_transaction, sender_name=None):
    """
    Check if a transaction is linked to a payment link and process accordingly.

    Args:
        reference: Payment reference from webhook
        wallet_transaction: The WalletTransaction object created
        sender_name: Name of the sender (contributor)

    Returns:
        tuple: (is_payment_link, payment_link_object or None)
    """
    # Payment links use a custom reference format: "PL-{token}-{timestamp}"
    # Check if reference starts with "PL-"
    if not reference or not reference.startswith('PL-'):
        return (False, None)

    try:
        # Extract token from reference
        # Format: PL-{token}-{optional_timestamp}
        parts = reference.split('-')
        if len(parts) < 2:
            logger.warning(f"Invalid payment link reference format: {reference}")
            return (False, None)

        token = parts[1]  # Token is the second part

        # Find payment link by token
        try:
            payment_link = PaymentLink.objects.select_related('savings_goal', 'user__wallet').get(token=token)
        except PaymentLink.DoesNotExist:
            logger.warning(f"Payment link not found for token: {token}")
            return (False, None)

        # Check if link is still active
        if not payment_link.is_active:
            logger.error(f"Payment link {token} is not active")
            return (False, None)

        # Check if link has expired
        from django.utils import timezone
        if payment_link.expires_at and timezone.now() > payment_link.expires_at:
            logger.error(f"Payment link {token} has expired")
            return (False, None)

        # Check one-time use
        if payment_link.one_time_use and payment_link.used:
            logger.error(f"Payment link {token} has already been used")
            return (False, None)

        # Process the contribution
        with transaction.atomic():
            # Create contribution record
            contribution = PaymentLinkContribution.objects.create(
                payment_link=payment_link,
                amount=wallet_transaction.amount,
                status='completed',
                wallet_transaction=wallet_transaction,
                contributor_name=sender_name,
                external_reference=reference
            )

            # If payment link is for a savings goal, credit the goal
            if payment_link.link_type == 'savings_goal' and payment_link.savings_goal:
                goal = payment_link.savings_goal

                # Add to goal's amount
                goal.amount += wallet_transaction.amount
                goal.save(update_fields=['amount', 'updated_at'])

                # Create savings goal transaction
                SavingsGoalTransaction.objects.create(
                    goal=goal,
                    transaction_type='contribution',
                    amount=wallet_transaction.amount,
                    description=f"Contribution from {sender_name or 'Anonymous'} via payment link",
                    goal_current_amount=goal.amount
                )

                # Debit from wallet (money goes to goal)
                wallet = payment_link.user.wallet
                wallet.withdraw(wallet_transaction.amount)

                logger.info(f"Credited {wallet_transaction.amount} to savings goal {goal.name}")

            elif payment_link.link_type == 'event' and payment_link.savings_goal:
                # Event link with linked goal
                goal = payment_link.savings_goal

                goal.amount += wallet_transaction.amount
                goal.save(update_fields=['amount', 'updated_at'])

                SavingsGoalTransaction.objects.create(
                    goal=goal,
                    transaction_type='contribution',
                    amount=wallet_transaction.amount,
                    description=f"Contribution for {payment_link.event_name} from {sender_name or 'Anonymous'}",
                    goal_current_amount=goal.amount
                )

                wallet = payment_link.user.wallet
                wallet.withdraw(wallet_transaction.amount)

                logger.info(f"Credited {wallet_transaction.amount} to event goal {goal.name}")

            else:
                # Wallet funding or event without goal - money stays in wallet
                logger.info(f"Payment link contribution stays in wallet: {wallet_transaction.amount}")

            # Mark as used if one-time use
            if payment_link.one_time_use:
                payment_link.used = True
                payment_link.save(update_fields=['used'])

            # Send notifications
            try:
                _send_payment_link_notifications(payment_link, contribution, wallet_transaction)
            except Exception as e:
                logger.error(f"Failed to send payment link notifications: {str(e)}")

        logger.info(f"Successfully processed payment link contribution: {reference}")
        return (True, payment_link)

    except Exception as e:
        logger.error(f"Error processing payment link contribution: {str(e)}", exc_info=True)
        return (False, None)


def _send_payment_link_notifications(payment_link, contribution, wallet_transaction):
    """
    Send notifications for payment link contributions.
    """
    from notification.helper.email import MailClient
    from providers.helpers.cuoral import CuoralAPI

    # Optional push notification import
    try:
        from notification.helper.push import send_push_notification_to_user
        PUSH_NOTIFICATIONS_AVAILABLE = True
    except (ImportError, FileNotFoundError, Exception):
        PUSH_NOTIFICATIONS_AVAILABLE = False

    user = payment_link.user
    contributor_name = contribution.contributor_name or "Someone"
    amount = wallet_transaction.amount
    currency = user.wallet.currency if hasattr(user, 'wallet') else 'NGN'

    # Determine context based on link type
    if payment_link.link_type == 'savings_goal' and payment_link.savings_goal:
        context_name = payment_link.savings_goal.name
        notification_text = f"{contributor_name} contributed {currency} {amount} to your savings goal '{context_name}'"
    elif payment_link.link_type == 'event' and payment_link.event_name:
        context_name = payment_link.event_name
        notification_text = f"{contributor_name} contributed {currency} {amount} for your event '{context_name}'"
    else:
        context_name = "your wallet"
        notification_text = f"{contributor_name} contributed {currency} {amount} to {context_name}"

    # Send SMS
    try:
        cuoral_client = CuoralAPI()
        cuoral_client.send_sms(user.phone, notification_text)
        logger.info(f"Payment link SMS notification sent to {user.phone}")
    except Exception as e:
        logger.error(f"Failed to send payment link SMS: {str(e)}")

    # Send Email
    try:
        emailclient = MailClient()
        emailclient.send_email(
            to_email=user.email,
            subject="New Contribution Received!",
            template_name="emails/payment_link_contribution.html",
            context={
                "contributor_name": contributor_name,
                "amount": f"{currency} {amount}",
                "context_name": context_name,
                "link_type": payment_link.get_link_type_display(),
                "total_raised": str(payment_link.get_total_raised()),
                "target_amount": str(payment_link.target_amount) if payment_link.target_amount else "No target set",
            },
            to_name=user.first_name
        )
        logger.info(f"Payment link email notification sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send payment link email: {str(e)}")

    # Send Push Notification
    try:
        if PUSH_NOTIFICATIONS_AVAILABLE:
            send_push_notification_to_user(
                user=user,
                title="New Contribution!",
                message=notification_text
            )
            logger.info(f"Payment link push notification sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send payment link push notification: {str(e)}")


def generate_payment_reference(payment_link):
    """
    Generate a unique payment reference for a payment link.
    Format: PL-{token}-{timestamp}
    """
    import time
    timestamp = int(time.time())
    return f"PL-{payment_link.token}-{timestamp}"
