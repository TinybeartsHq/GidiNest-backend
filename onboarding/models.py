from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model
import uuid

from core.helpers.model import BaseModel

User = get_user_model()

class PasswordResetOTP(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def has_expired(self):
        # OTP expires in 10 minutes
        return (timezone.now() - self.created_at).total_seconds() > 600
    



class RegisterTempData(BaseModel):
    """
    Model to store temporary user data during OAuth2 authentication.
    """
    email = models.EmailField()
    phone = models.CharField(max_length=255,null=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    oauth_provider = models.CharField(max_length=50,null=True)  # e.g., 'google', 'apple'
    created_at = models.DateTimeField(auto_now_add=True)
    otp = models.CharField(max_length=255)
    is_oauth = models.BooleanField(default=False)
    auth_id = models.CharField(max_length=255,null=True)
    otp_verified = models.BooleanField(default=False)


    class Meta:
        verbose_name = "Registration Session"
        verbose_name_plural = "Registration Sessions"
        ordering = ['-created_at']



    def __str__(self):
        return f"{self.email} - {self.oauth_provider} - {self.id}"
    