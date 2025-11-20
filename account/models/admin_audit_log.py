from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class AdminAuditLog(models.Model):
    """
    Tracks all admin actions for security and compliance.
    Records who did what, when, and to which object.
    """

    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('view', 'Viewed'),
        ('custom', 'Custom Action'),
    ]

    # Who performed the action
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='admin_actions',
        help_text='Staff member who performed this action'
    )

    # What action was performed
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        db_index=True
    )
    action_description = models.CharField(
        max_length=255,
        help_text='Human-readable description of the action'
    )

    # Which object was affected (using generic foreign key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # Object representation (in case object is deleted)
    object_repr = models.CharField(
        max_length=255,
        help_text='String representation of the object'
    )

    # Additional context
    changes = models.JSONField(
        null=True,
        blank=True,
        help_text='JSON of fields that were changed (before/after values)'
    )

    # Request metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the admin user'
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text='Browser user agent string'
    )

    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'admin_audit_log'
        ordering = ['-timestamp']
        verbose_name = 'Admin Audit Log'
        verbose_name_plural = 'Admin Audit Logs'
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['action', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.user.email if self.user else 'Unknown'} - {self.action} - {self.object_repr} - {self.timestamp}"

    @classmethod
    def log_action(cls, user, action, obj, description=None, changes=None, request=None):
        """
        Helper method to create an audit log entry.

        Args:
            user: The User who performed the action
            action: One of the ACTION_CHOICES
            obj: The object being acted upon
            description: Optional custom description
            changes: Optional dict of field changes
            request: Optional HttpRequest object for metadata
        """
        ip_address = None
        user_agent = None

        if request:
            # Get IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')

            # Get user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Generate description if not provided
        if not description:
            action_verbs = {
                'create': 'created',
                'update': 'updated',
                'delete': 'deleted',
                'view': 'viewed',
                'custom': 'performed action on',
            }
            verb = action_verbs.get(action, 'performed action on')
            description = f"{verb} {obj}"

        return cls.objects.create(
            user=user,
            action=action,
            content_type=ContentType.objects.get_for_model(obj) if obj else None,
            object_id=obj.pk if obj else None,
            object_repr=str(obj),
            action_description=description,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
        )
