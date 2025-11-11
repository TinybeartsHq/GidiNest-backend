from django.db import models
from django.contrib.auth import get_user_model
from core.helpers.model import BaseModel

User = get_user_model()


class UserSession(BaseModel):
    """
    Track user login sessions for mobile app
    Enables features like:
    - View active sessions
    - Remote logout
    - Security monitoring
    """

    class Meta:
        db_table = 'user_sessions'
        verbose_name = "User Session"
        verbose_name_plural = "User Sessions"
        ordering = ['-last_active_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['refresh_token_hash']),
            models.Index(fields=['device_id']),
        ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions',
        help_text="User who owns this session"
    )

    device_name = models.CharField(
        max_length=255,
        help_text="Device name (e.g., 'iPhone 14 Pro')"
    )

    device_type = models.CharField(
        max_length=50,
        choices=[
            ('ios', 'iOS'),
            ('android', 'Android'),
            ('web', 'Web'),
            ('unknown', 'Unknown')
        ],
        default='unknown',
        help_text="Device platform"
    )

    device_id = models.CharField(
        max_length=255,
        help_text="Unique device identifier"
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the session"
    )

    location = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Approximate location (e.g., 'Lagos, Nigeria')"
    )

    refresh_token_hash = models.CharField(
        max_length=255,
        unique=True,
        help_text="Hashed refresh token for invalidation"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Whether session is still valid"
    )

    expires_at = models.DateTimeField(
        help_text="When the refresh token expires"
    )

    last_active_at = models.DateTimeField(
        auto_now=True,
        help_text="Last time this session was used"
    )

    def __str__(self):
        return f"{self.user.email} - {self.device_name} ({self.device_type})"

    def invalidate(self):
        """Invalidate this session (logout)"""
        self.is_active = False
        self.save(update_fields=['is_active'])

    def is_expired(self):
        """Check if session has expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def update_activity(self):
        """Update last active timestamp"""
        self.save(update_fields=['last_active_at'])
