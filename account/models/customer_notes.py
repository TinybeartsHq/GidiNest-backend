from django.db import models
from django.conf import settings


class CustomerNote(models.Model):
    """
    Model for tracking customer support interactions and notes.
    Allows support staff to document conversations, issues, and resolutions.
    """

    CATEGORY_CHOICES = [
        ('general', 'General Inquiry'),
        ('account', 'Account Issue'),
        ('wallet', 'Wallet/Transaction Issue'),
        ('withdrawal', 'Withdrawal Issue'),
        ('savings', 'Savings Goal Issue'),
        ('verification', 'Verification/KYC Issue'),
        ('security', 'Security Concern'),
        ('technical', 'Technical Issue'),
        ('complaint', 'Complaint'),
        ('feedback', 'Feedback'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    # Core fields
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='support_notes',
        help_text='The customer this note is about'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_notes',
        help_text='Support staff member who created this note'
    )

    # Note details
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='general',
        db_index=True
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        db_index=True
    )

    subject = models.CharField(
        max_length=200,
        help_text='Brief subject/title for this note'
    )
    note = models.TextField(
        help_text='Detailed note about the interaction or issue'
    )

    # Resolution
    resolution = models.TextField(
        blank=True,
        null=True,
        help_text='How the issue was resolved'
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_notes',
        help_text='Support staff member who resolved this issue'
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the issue was resolved'
    )

    # Metadata
    internal_only = models.BooleanField(
        default=False,
        help_text='If true, this note is for internal use only and should not be shared with customer'
    )
    flagged = models.BooleanField(
        default=False,
        help_text='Flag for escalation or special attention'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customer_notes'
        ordering = ['-created_at']
        verbose_name = 'Customer Note'
        verbose_name_plural = 'Customer Notes'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['category', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.subject} ({self.status})"

    def save(self, *args, **kwargs):
        # Auto-set resolved_at when status changes to resolved/closed
        if self.status in ['resolved', 'closed'] and not self.resolved_at:
            from django.utils import timezone
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)
