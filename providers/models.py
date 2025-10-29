from django.db import models
from django.utils import timezone

class ProviderRequestLog(models.Model):
    provider_name = models.CharField(max_length=100)
    http_method = models.CharField(max_length=10)
    endpoint = models.CharField(max_length=255)
    request_payload = models.JSONField(null=True, blank=True)
    response_body = models.JSONField(null=True, blank=True)
    response_status = models.PositiveSmallIntegerField(null=True, blank=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"[{self.provider_name}] {self.http_method} {self.endpoint} ({self.response_status})"
