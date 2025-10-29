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
