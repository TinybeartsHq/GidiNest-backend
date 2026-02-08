# notification/helper/notifications.py
"""
Helper functions for creating and sending notifications
"""
import logging
from typing import Dict, Optional
from django.conf import settings
from notification.models import Notification

logger = logging.getLogger(__name__)

# Optional push notification import
try:
    from notification.helper.push import send_push_notification_to_user
    PUSH_AVAILABLE = True
except (ImportError, Exception):
    PUSH_AVAILABLE = False
    def send_push_notification_to_user(*args, **kwargs):
        pass


def create_notification(
    user,
    title: str,
    message: str,
    notification_type: str,
    data: Optional[Dict] = None,
    action_url: Optional[str] = None,
    send_push: bool = True
) -> Notification:
    """
    Create an in-app notification and optionally send push notification

    Args:
        user: User object
        title: Notification title
        message: Notification message
        notification_type: Type of notification (from Notification.NOTIFICATION_TYPES)
        data: Optional metadata dict
        action_url: Optional deep link URL
        send_push: Whether to send push notification (default: True)

    Returns:
        Notification object
    """
    # Create in-app notification
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        data=data or {},
        action_url=action_url
    )

    # Send push notification if enabled
    if send_push and PUSH_AVAILABLE:
        try:
            send_push_notification_to_user(
                user=user,
                title=title,
                message=message,
                data={'notification_id': str(notification.id), 'type': notification_type}
            )
        except Exception as e:
            # Don't fail if push notification fails
            logger.error(f"Failed to send push notification: {e}")

    return notification


# Wallet Notification Helpers
def notify_wallet_deposit(user, amount, reference=None):
    """Notify user about wallet deposit"""
    return create_notification(
        user=user,
        title="Wallet Funded",
        message=f"Your wallet has been credited with ₦{amount:,.2f}",
        notification_type='wallet_deposit',
        data={'amount': str(amount), 'reference': reference},
        action_url='/wallet'
    )


def notify_withdrawal_requested(user, amount, withdrawal_id):
    """Notify user about withdrawal request"""
    return create_notification(
        user=user,
        title="Withdrawal Request Received",
        message=f"Your withdrawal request of ₦{amount:,.2f} is being processed",
        notification_type='wallet_withdrawal_requested',
        data={'amount': str(amount), 'withdrawal_id': str(withdrawal_id)},
        action_url=f'/wallet/withdrawals/{withdrawal_id}'
    )


def notify_withdrawal_approved(user, amount, withdrawal_id):
    """Notify user about withdrawal approval"""
    return create_notification(
        user=user,
        title="Withdrawal Successful",
        message=f"₦{amount:,.2f} has been transferred to your bank account",
        notification_type='wallet_withdrawal_approved',
        data={'amount': str(amount), 'withdrawal_id': str(withdrawal_id)},
        action_url=f'/wallet/withdrawals/{withdrawal_id}'
    )


def notify_withdrawal_failed(user, amount, withdrawal_id, reason=None):
    """Notify user about withdrawal failure"""
    message = f"Your withdrawal request of ₦{amount:,.2f} failed"
    if reason:
        message += f": {reason}"

    return create_notification(
        user=user,
        title="Withdrawal Failed",
        message=message,
        notification_type='wallet_withdrawal_failed',
        data={'amount': str(amount), 'withdrawal_id': str(withdrawal_id), 'reason': reason},
        action_url=f'/wallet/withdrawals/{withdrawal_id}'
    )


# Savings Goal Notification Helpers
def notify_goal_created(user, goal_name, goal_id):
    """Notify user about goal creation"""
    return create_notification(
        user=user,
        title="Savings Goal Created",
        message=f"Your savings goal '{goal_name}' has been created",
        notification_type='goal_created',
        data={'goal_name': goal_name, 'goal_id': str(goal_id)},
        action_url=f'/savings/goals/{goal_id}',
        send_push=False  # Don't send push for goal creation
    )


def notify_goal_funded(user, goal_name, amount, goal_id, new_balance):
    """Notify user about goal funding"""
    return create_notification(
        user=user,
        title=f"Goal Funded: {goal_name}",
        message=f"You added ₦{amount:,.2f} to {goal_name}. New balance: ₦{new_balance:,.2f}",
        notification_type='goal_funded',
        data={
            'goal_name': goal_name,
            'amount': str(amount),
            'goal_id': str(goal_id),
            'new_balance': str(new_balance)
        },
        action_url=f'/savings/goals/{goal_id}'
    )


def notify_goal_withdrawn(user, goal_name, amount, goal_id):
    """Notify user about goal withdrawal"""
    return create_notification(
        user=user,
        title=f"Withdrawal from {goal_name}",
        message=f"You withdrew ₦{amount:,.2f} from {goal_name}",
        notification_type='goal_withdrawn',
        data={'goal_name': goal_name, 'amount': str(amount), 'goal_id': str(goal_id)},
        action_url=f'/savings/goals/{goal_id}'
    )


def notify_goal_milestone(user, goal_name, goal_id, percentage):
    """Notify user about goal milestone (25%, 50%, 75%, 100%)"""
    return create_notification(
        user=user,
        title=f"Milestone Reached: {goal_name}",
        message=f"Congratulations! You've reached {percentage}% of your {goal_name} goal",
        notification_type='goal_milestone',
        data={'goal_name': goal_name, 'goal_id': str(goal_id), 'percentage': percentage},
        action_url=f'/savings/goals/{goal_id}'
    )


def notify_goal_completed(user, goal_name, goal_id, amount):
    """Notify user about goal completion"""
    return create_notification(
        user=user,
        title=f"Goal Achieved: {goal_name}!",
        message=f"Congratulations! You've reached your ₦{amount:,.2f} savings goal",
        notification_type='goal_completed',
        data={'goal_name': goal_name, 'goal_id': str(goal_id), 'amount': str(amount)},
        action_url=f'/savings/goals/{goal_id}'
    )


def notify_goal_unlocked(user, goal_name, goal_id):
    """Notify user about goal unlock after maturity"""
    return create_notification(
        user=user,
        title=f"Goal Unlocked: {goal_name}",
        message=f"Your savings goal '{goal_name}' has matured and is now available for withdrawal",
        notification_type='goal_unlocked',
        data={'goal_name': goal_name, 'goal_id': str(goal_id)},
        action_url=f'/savings/goals/{goal_id}'
    )


# Community Notification Helpers
def notify_post_liked(user, liker_name, post_id):
    """Notify user about post like"""
    return create_notification(
        user=user,
        title="Post Liked",
        message=f"{liker_name} liked your post",
        notification_type='post_liked',
        data={'liker_name': liker_name, 'post_id': str(post_id)},
        action_url=f'/community/posts/{post_id}',
        send_push=False  # Don't send push for likes
    )


def notify_post_commented(user, commenter_name, post_id, comment_preview):
    """Notify user about post comment"""
    return create_notification(
        user=user,
        title="New Comment",
        message=f"{commenter_name} commented: {comment_preview[:50]}...",
        notification_type='post_commented',
        data={'commenter_name': commenter_name, 'post_id': str(post_id)},
        action_url=f'/community/posts/{post_id}'
    )


def notify_challenge_completed(user, challenge_name, challenge_id):
    """Notify user about challenge completion"""
    return create_notification(
        user=user,
        title="Challenge Completed!",
        message=f"Congratulations! You've completed the '{challenge_name}' challenge",
        notification_type='challenge_completed',
        data={'challenge_name': challenge_name, 'challenge_id': str(challenge_id)},
        action_url=f'/community/challenges/{challenge_id}'
    )


# System Notification Helpers
def notify_verification_completed(user, verification_type):
    """Notify user about verification completion"""
    return create_notification(
        user=user,
        title="Verification Complete",
        message=f"Your {verification_type} verification has been completed successfully",
        notification_type='verification_completed',
        data={'verification_type': verification_type},
        action_url='/profile'
    )


def notify_security_alert(user, alert_message):
    """Notify user about security alert"""
    return create_notification(
        user=user,
        title="Security Alert",
        message=alert_message,
        notification_type='security_alert',
        data={},
        action_url='/profile/security'
    )


# Onboarding Nudge Helpers
def notify_wallet_setup_nudge(user):
    """Nudge user who signed up but hasn't created a wallet yet"""
    first_name = user.first_name or "there"
    return create_notification(
        user=user,
        title="Complete Your Wallet Setup",
        message=f"Hey {first_name}, you're almost there! Complete your verification to unlock your wallet and start building your nest.",
        notification_type='wallet_setup_nudge',
        action_url='/kyc',
        send_push=False,
    )
