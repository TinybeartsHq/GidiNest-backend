# wallet/payment_link_helpers.py
import re
import logging
from decimal import Decimal
from django.db import transaction
from wallet.models import PaymentLink, PaymentLinkContribution, WalletTransaction
from savings.models import SavingsGoalTransaction

logger = logging.getLogger(__name__)


def _extract_pl_identifier(reference, narration=None):
    """
    Find a PL-{token}-{timestamp} identifier in the narration or reference.
    Returns the identifier string or None.
    Priority: narration (user-typed) > reference (system-generated).
    """
    # Check narration first — this is what the contributor types
    if narration:
        for segment in narration.split():
            if segment.startswith('PL-'):
                return segment
    # Fall back to reference (system-generated, less likely to contain PL-)
    if reference and reference.startswith('PL-'):
        return reference
    return None


def _extract_token_from_identifier(pl_identifier):
    """
    Extract the PaymentLink token from a PL-{token}-{timestamp} identifier.
    Handles tokens that may contain dashes (from secrets.token_urlsafe).
    """
    stripped = pl_identifier[3:]  # Remove "PL-" prefix
    # Timestamp is a trailing segment of 8+ digits after the last dash
    match = re.match(r'^(.+)-(\d{8,})$', stripped)
    if match:
        return match.group(1)
    # No timestamp suffix — treat entire remainder as token
    return stripped if stripped else None


def process_payment_link_contribution(reference, wallet_transaction, sender_name=None, narration=None):
    """
    Check if a transaction is linked to a payment link and process accordingly.

    Args:
        reference: Payment reference from webhook (system-generated)
        wallet_transaction: The WalletTransaction object created
        sender_name: Name of the sender (contributor)
        narration: Transfer narration/remark from webhook (user-typed, may contain PL- code)

    Returns:
        tuple: (is_payment_link, payment_link_object or None)
    """
    # Look for a PL- identifier in narration or reference
    pl_identifier = _extract_pl_identifier(reference, narration)
    if not pl_identifier:
        return (False, None)

    try:
        # Extract token from PL-{token}-{timestamp} format
        token = _extract_token_from_identifier(pl_identifier)
        if not token:
            logger.warning(f"Could not extract token from payment link identifier: {pl_identifier}")
            return (False, None)

        # Find payment link by token
        try:
            payment_link = PaymentLink.objects.select_related('savings_goal', 'user__wallet').get(token=token)
        except PaymentLink.DoesNotExist:
            logger.warning(f"Payment link not found for token: {token}")
            return (False, None)

        # Verify the payment link belongs to the wallet owner
        if payment_link.user_id != wallet_transaction.wallet.user_id:
            logger.warning(
                f"Payment link token {token} belongs to user {payment_link.user_id} "
                f"but transaction is for wallet user {wallet_transaction.wallet.user_id}. Skipping."
            )
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
        # Use net_amount (after fees) for goal crediting
        credited_amount = wallet_transaction.net_amount or wallet_transaction.amount

        with transaction.atomic():
            # Create contribution record with fee data from wallet transaction
            contribution = PaymentLinkContribution.objects.create(
                payment_link=payment_link,
                amount=wallet_transaction.amount,
                commission_amount=wallet_transaction.commission_amount,
                vat_amount=wallet_transaction.vat_amount,
                total_fee=wallet_transaction.total_fee,
                net_amount=credited_amount,
                status='completed',
                wallet_transaction=wallet_transaction,
                contributor_name=sender_name,
                external_reference=reference or pl_identifier
            )

            # If payment link is for a savings goal, credit the goal with net amount
            if payment_link.link_type == 'savings_goal' and payment_link.savings_goal:
                goal = payment_link.savings_goal

                goal.amount += credited_amount
                goal.save(update_fields=['amount', 'updated_at'])

                SavingsGoalTransaction.objects.create(
                    goal=goal,
                    transaction_type='contribution',
                    amount=credited_amount,
                    description=f"Contribution from {sender_name or 'Anonymous'} via payment link",
                    goal_current_amount=goal.amount
                )

                # Debit from wallet (money goes to goal)
                wallet = payment_link.user.wallet
                wallet.withdraw(credited_amount)

                logger.info(f"Credited {credited_amount} to savings goal {goal.name} (gross {wallet_transaction.amount}, fees {wallet_transaction.total_fee})")

            elif payment_link.link_type == 'event' and payment_link.savings_goal:
                # Event link with linked goal
                goal = payment_link.savings_goal

                goal.amount += credited_amount
                goal.save(update_fields=['amount', 'updated_at'])

                SavingsGoalTransaction.objects.create(
                    goal=goal,
                    transaction_type='contribution',
                    amount=credited_amount,
                    description=f"Contribution for {payment_link.event_name} from {sender_name or 'Anonymous'}",
                    goal_current_amount=goal.amount
                )

                wallet = payment_link.user.wallet
                wallet.withdraw(credited_amount)

                logger.info(f"Credited {credited_amount} to event goal {goal.name} (gross {wallet_transaction.amount}, fees {wallet_transaction.total_fee})")

            else:
                # Wallet funding or event without goal - net amount stays in wallet
                logger.info(f"Payment link contribution stays in wallet: {credited_amount} (gross {wallet_transaction.amount}, fees {wallet_transaction.total_fee})")

            # Mark as used if one-time use
            if payment_link.one_time_use:
                payment_link.used = True
                payment_link.save(update_fields=['used'])

            # Send notifications
            try:
                _send_payment_link_notifications(payment_link, contribution, wallet_transaction)
            except Exception as e:
                logger.error(f"Failed to send payment link notifications: {str(e)}")

        logger.info(f"Successfully processed payment link contribution: {pl_identifier} (ref: {reference})")
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

    # Send confirmation email to contributor (if email available)
    if contribution.contributor_email:
        try:
            from django.conf import settings
            emailclient = MailClient()

            # Get goal/event name for display
            if payment_link.link_type == 'savings_goal' and payment_link.savings_goal:
                goal_or_event_name = payment_link.savings_goal.name
            elif payment_link.link_type == 'event' and payment_link.event_name:
                goal_or_event_name = payment_link.event_name
            else:
                goal_or_event_name = "General Wallet Funding"

            emailclient.send_email(
                to_email=contribution.contributor_email,
                subject="Payment Confirmed - Thank You!",
                template_name="emails/payment_link_contributor_confirmation.html",
                context={
                    "goal_or_event_name": goal_or_event_name,
                    "amount": f"{currency} {amount}",
                    "payment_reference": contribution.external_reference,
                    "custom_message": payment_link.custom_message,
                    "token": payment_link.token,
                },
                to_name=contributor_name
            )
            logger.info(f"Contributor confirmation email sent to {contribution.contributor_email}")
        except Exception as e:
            logger.error(f"Failed to send contributor confirmation email: {str(e)}")


def generate_payment_reference(payment_link):
    """
    Generate a unique payment reference for a payment link.
    Format: PL-{token}-{timestamp}
    """
    import time
    timestamp = int(time.time())
    return f"PL-{payment_link.token}-{timestamp}"


def _complete_contribution(contribution, wallet_transaction):
    """
    Complete a pending contribution: link it to the wallet transaction,
    route money to savings goal if applicable, and send notifications.
    """
    payment_link = contribution.payment_link
    sender_name = contribution.contributor_name
    credited_amount = wallet_transaction.net_amount or wallet_transaction.amount

    with transaction.atomic():
        contribution.status = 'completed'
        contribution.wallet_transaction = wallet_transaction
        contribution.commission_amount = wallet_transaction.commission_amount
        contribution.vat_amount = wallet_transaction.vat_amount
        contribution.total_fee = wallet_transaction.total_fee
        contribution.net_amount = credited_amount
        contribution.save(update_fields=[
            'status', 'wallet_transaction', 'commission_amount',
            'vat_amount', 'total_fee', 'net_amount', 'updated_at'
        ])

        # Route money to savings goal if applicable (use net amount)
        if payment_link.link_type == 'savings_goal' and payment_link.savings_goal:
            goal = payment_link.savings_goal
            goal.amount += credited_amount
            goal.save(update_fields=['amount', 'updated_at'])

            SavingsGoalTransaction.objects.create(
                goal=goal,
                transaction_type='contribution',
                amount=credited_amount,
                description=f"Contribution from {sender_name or 'Anonymous'} via payment link",
                goal_current_amount=goal.amount
            )

            wallet = payment_link.user.wallet
            wallet.withdraw(credited_amount)
            logger.info(f"Credited {credited_amount} to savings goal {goal.name}")

        elif payment_link.link_type == 'event' and payment_link.savings_goal:
            goal = payment_link.savings_goal
            goal.amount += credited_amount
            goal.save(update_fields=['amount', 'updated_at'])

            SavingsGoalTransaction.objects.create(
                goal=goal,
                transaction_type='contribution',
                amount=credited_amount,
                description=f"Contribution for {payment_link.event_name} from {sender_name or 'Anonymous'}",
                goal_current_amount=goal.amount
            )

            wallet = payment_link.user.wallet
            wallet.withdraw(credited_amount)
            logger.info(f"Credited {credited_amount} to event goal {goal.name}")

        else:
            logger.info(f"Payment link contribution stays in wallet: {credited_amount}")

        # Mark as used if one-time use
        if payment_link.one_time_use:
            payment_link.used = True
            payment_link.save(update_fields=['used'])

    # Send notifications (outside atomic block — non-critical)
    try:
        _send_payment_link_notifications(payment_link, contribution, wallet_transaction)
    except Exception as e:
        logger.error(f"Failed to send payment link notifications: {str(e)}")


def try_match_deposit_to_pending_contribution(wallet_transaction):
    """
    Called from webhooks when a deposit has no PL- reference.
    Looks for a pending PaymentLinkContribution that matches by amount
    and belongs to the wallet owner's active payment links.

    Returns:
        tuple: (matched, payment_link or None)
    """
    from datetime import timedelta
    from django.utils import timezone

    try:
        wallet_user = wallet_transaction.wallet.user
        amount = wallet_transaction.amount
        # Only match contributions created in the last 2 hours
        cutoff = timezone.now() - timedelta(hours=2)

        pending = PaymentLinkContribution.objects.filter(
            payment_link__user=wallet_user,
            payment_link__is_active=True,
            status='pending',
            amount=amount,
            created_at__gte=cutoff,
        ).select_related('payment_link', 'payment_link__savings_goal', 'payment_link__user__wallet')

        if pending.count() == 1:
            contribution = pending.first()
            _complete_contribution(contribution, wallet_transaction)
            logger.info(
                f"Auto-matched deposit {wallet_transaction.external_reference} "
                f"to pending contribution {contribution.id}"
            )
            return (True, contribution.payment_link)
        elif pending.count() > 1:
            logger.info(
                f"Multiple pending contributions match deposit amount {amount} "
                f"for user {wallet_user.email}. Skipping auto-match."
            )
        return (False, None)

    except Exception as e:
        logger.error(f"Error in try_match_deposit_to_pending_contribution: {str(e)}", exc_info=True)
        return (False, None)


def try_match_contribution_to_deposit(contribution):
    """
    Called when a contributor confirms payment. Looks for a recent
    unmatched deposit to the link owner's wallet with the same amount.

    Returns:
        WalletTransaction or None
    """
    from datetime import timedelta
    from django.utils import timezone

    try:
        payment_link = contribution.payment_link
        wallet = payment_link.user.wallet
        amount = contribution.amount
        # Look for deposits in the last 2 hours
        cutoff = timezone.now() - timedelta(hours=2)

        # Find credit transactions to this wallet that aren't already
        # linked to a completed contribution
        candidates = WalletTransaction.objects.filter(
            wallet=wallet,
            transaction_type='credit',
            amount=amount,
            created_at__gte=cutoff,
        ).exclude(
            payment_link_contributions__status='completed'
        ).order_by('-created_at')

        if candidates.count() == 1:
            return candidates.first()
        # If multiple matches, don't auto-match (ambiguous)
        return None

    except Exception as e:
        logger.error(f"Error in try_match_contribution_to_deposit: {str(e)}", exc_info=True)
        return None
