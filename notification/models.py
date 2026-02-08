# notification/models.py
"""
In-app notification system for user notifications
"""
import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    In-app notification model for storing user notifications
    """

    NOTIFICATION_TYPES = [
        # Wallet related
        ('wallet_deposit', 'Wallet Deposit'),
        ('wallet_withdrawal_requested', 'Withdrawal Requested'),
        ('wallet_withdrawal_approved', 'Withdrawal Approved'),
        ('wallet_withdrawal_failed', 'Withdrawal Failed'),

        # Savings related
        ('goal_created', 'Goal Created'),
        ('goal_funded', 'Goal Funded'),
        ('goal_withdrawn', 'Goal Withdrawn'),
        ('goal_milestone', 'Goal Milestone'),
        ('goal_completed', 'Goal Completed'),
        ('goal_unlocked', 'Goal Unlocked'),

        # Community related
        ('post_liked', 'Post Liked'),
        ('post_commented', 'Post Commented'),
        ('comment_replied', 'Comment Replied'),
        ('challenge_joined', 'Challenge Joined'),
        ('challenge_completed', 'Challenge Completed'),
        ('group_joined', 'Group Joined'),

        # System related
        ('verification_completed', 'Verification Completed'),
        ('account_upgraded', 'Account Upgraded'),
        ('security_alert', 'Security Alert'),
        ('system_announcement', 'System Announcement'),
        ('wallet_setup_nudge', 'Wallet Setup Nudge'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    # Notification content
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)

    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # Optional metadata (JSON for flexibility)
    data = models.JSONField(default=dict, blank=True)

    # Optional link to navigate to
    action_url = models.CharField(max_length=500, blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
