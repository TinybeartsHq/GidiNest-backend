from django.db import models
from django.utils import timezone


class ServerLog(models.Model):
    """
    Model to store server logs for monitoring and debugging.
    """
    LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]

    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, db_index=True)
    logger_name = models.CharField(max_length=255, db_index=True, help_text="Name of the logger (e.g., 'django.request')")
    message = models.TextField(help_text="Log message")
    pathname = models.CharField(max_length=500, blank=True, null=True, help_text="File path where log originated")
    function_name = models.CharField(max_length=255, blank=True, null=True, help_text="Function name where log originated")
    line_number = models.IntegerField(blank=True, null=True, help_text="Line number where log originated")
    exception = models.TextField(blank=True, null=True, help_text="Exception traceback if available")
    request_path = models.CharField(max_length=500, blank=True, null=True, db_index=True, help_text="HTTP request path if available")
    request_method = models.CharField(max_length=10, blank=True, null=True, help_text="HTTP request method (GET, POST, etc.)")
    user_email = models.EmailField(blank=True, null=True, db_index=True, help_text="User email if authenticated")
    ip_address = models.GenericIPAddressField(blank=True, null=True, help_text="Client IP address")
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Server Log'
        verbose_name_plural = 'Server Logs'
        indexes = [
            models.Index(fields=['-timestamp', 'level']),
            models.Index(fields=['logger_name', '-timestamp']),
        ]

    def __str__(self):
        return f"[{self.level}] {self.logger_name} - {self.message[:50]}"

    def get_short_message(self):
        """Return truncated message for display"""
        return self.message[:100] + '...' if len(self.message) > 100 else self.message
