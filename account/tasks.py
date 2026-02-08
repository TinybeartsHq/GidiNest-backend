"""
Celery tasks for account app.
"""
from celery import shared_task
from account.services.sync_embedly import EmbedlySyncService
import logging

logger = logging.getLogger(__name__)


@shared_task(name='account.tasks.sync_embedly_verifications_task')
def sync_embedly_verifications_task(limit=None):
    """
    Periodic task to sync user verification status from Embedly.

    Args:
        limit (int, optional): Limit the number of users to sync

    Returns:
        dict: Summary of sync results
    """
    logger.info("Starting scheduled Embedly verification sync task")

    sync_service = EmbedlySyncService()
    results = sync_service.sync_all_users(limit=limit)

    logger.info(
        f"Embedly sync task completed. "
        f"Total: {results['total_users']}, "
        f"Successful: {results['successful']}, "
        f"Failed: {results['failed']}, "
        f"Updated: {results['updated']}"
    )

    return results


@shared_task(name='account.tasks.sync_single_user_task')
def sync_single_user_task(user_id):
    """
    Task to sync a single user's verification status.

    Args:
        user_id (int): The user ID to sync

    Returns:
        dict: Sync result
    """
    from account.models.users import UserModel

    try:
        user = UserModel.objects.get(id=user_id)
        sync_service = EmbedlySyncService()
        result = sync_service.sync_user_verification(user)

        logger.info(f"Single user sync completed for {user.email}: {result}")
        return result

    except UserModel.DoesNotExist:
        error_msg = f"User with ID {user_id} not found"
        logger.error(error_msg)
        return {"success": False, "message": error_msg}


@shared_task(name='account.tasks.sync_users_by_emails_task')
def sync_users_by_emails_task(emails):
    """
    Task to sync multiple users by email addresses.

    Args:
        emails (list): List of email addresses

    Returns:
        dict: Summary of sync results
    """
    logger.info(f"Starting sync for {len(emails)} users by email")

    sync_service = EmbedlySyncService()
    results = sync_service.sync_users_by_email(emails)

    logger.info(
        f"Email-based sync completed. "
        f"Found: {results['found_users']}, "
        f"Successful: {results['successful']}, "
        f"Failed: {results['failed']}"
    )

    return results


@shared_task(name='account.tasks.nudge_users_without_wallet')
def nudge_users_without_wallet():
    """
    Find users who signed up ~24 hours ago but still have no wallet.
    Send them a friendly email + in-app notification to complete KYC.

    Runs hourly via Celery beat. The 24-25 hour window ensures each user
    is only caught once, and the nudge_wallet_setup_sent flag prevents duplicates.
    """
    from datetime import timedelta
    from django.utils import timezone
    from account.models.users import UserModel
    from wallet.models import Wallet
    from notification.helper.notifications import notify_wallet_setup_nudge
    from notification.helper.email import MailClient

    now = timezone.now()
    window_start = now - timedelta(hours=25)
    window_end = now - timedelta(hours=24)

    # Users who signed up 24-25 hours ago, haven't been nudged, and have no wallet
    users = (
        UserModel.objects
        .filter(
            created_at__gte=window_start,
            created_at__lte=window_end,
            nudge_wallet_setup_sent=False,
            is_active=True,
        )
        .exclude(
            id__in=Wallet.objects.values_list('user_id', flat=True)
        )
    )

    nudged_count = 0
    failed_count = 0
    mail_client = MailClient()

    for user in users:
        try:
            first_name = user.first_name or "there"

            # Send email
            mail_client.send_email(
                to_email=user.email,
                subject="Your Gidinest wallet is waiting for you!",
                template_name='emails/wallet_setup_nudge.html',
                context={
                    'first_name': first_name,
                    'year': now.year,
                },
                to_name=user.get_full_name() or user.email,
            )

            # Create in-app notification
            notify_wallet_setup_nudge(user)

            # Mark as nudged
            user.nudge_wallet_setup_sent = True
            user.save(update_fields=['nudge_wallet_setup_sent'])

            nudged_count += 1
        except Exception:
            failed_count += 1
            logger.exception(f"Failed to send wallet setup nudge to {user.email}")

    logger.info(
        f"Wallet setup nudge task completed. "
        f"Nudged: {nudged_count}, Failed: {failed_count}"
    )

    return {'nudged': nudged_count, 'failed': failed_count}
