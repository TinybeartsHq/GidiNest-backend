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


class OnboardingProfile(BaseModel):
    """
    V2 Mobile - Rich onboarding profile for personalized mobile experience.
    This model is OPTIONAL and only created for mobile users who complete the onboarding flow.
    Web users can exist without this profile.
    """

    JOURNEY_CHOICES = [
        ('pregnant', 'Pregnant'),
        ('trying', 'Trying to Conceive'),
        ('new_mom', 'New Mom'),
    ]

    HOSPITAL_PLAN_CHOICES = [
        ('basic', 'Basic/Public Hospital'),
        ('private', 'Private Hospital'),
        ('premium', 'Premium/International Hospital'),
    ]

    BABY_ESSENTIALS_CHOICES = [
        ('minimalist', 'Minimalist - Just the Basics'),
        ('comfort', 'Comfort - Quality Essentials'),
        ('deluxe', 'Deluxe - Premium Everything'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='onboarding_profile',
        help_text="User who completed this onboarding"
    )

    # Journey Information
    journey_type = models.CharField(
        max_length=20,
        choices=JOURNEY_CHOICES,
        null=True,
        blank=True,
        help_text="User's pregnancy/motherhood journey stage"
    )

    # Date Information
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expected due date (for pregnant users)"
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        help_text="Baby's birth date (for new moms)"
    )
    conception_date = models.DateField(
        null=True,
        blank=True,
        help_text="Target conception date (for trying to conceive)"
    )

    # Calculated Fields
    pregnancy_weeks = models.IntegerField(
        null=True,
        blank=True,
        help_text="Current pregnancy week (calculated from due date)"
    )

    # Planning Preferences
    hospital_plan = models.CharField(
        max_length=20,
        choices=HOSPITAL_PLAN_CHOICES,
        null=True,
        blank=True,
        help_text="Preferred hospital delivery plan"
    )
    location = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="User's location (city/state) for cost calculations"
    )
    baby_essentials_preference = models.CharField(
        max_length=20,
        choices=BABY_ESSENTIALS_CHOICES,
        null=True,
        blank=True,
        help_text="Preference level for baby essentials"
    )

    # Onboarding Metadata
    onboarding_completed = models.BooleanField(
        default=False,
        help_text="Whether user completed the full onboarding flow"
    )
    onboarding_source = models.CharField(
        max_length=20,
        choices=[('web', 'Web'), ('mobile', 'Mobile')],
        default='mobile',
        help_text="Platform where onboarding was completed"
    )
    onboarding_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when onboarding was completed"
    )

    # Partner/Support
    partner_invited = models.BooleanField(
        default=False,
        help_text="Whether user invited a partner during onboarding"
    )
    partner_email = models.EmailField(
        null=True,
        blank=True,
        help_text="Partner's email if invited"
    )
    partner_phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Partner's phone if invited"
    )

    class Meta:
        db_table = 'onboarding_profiles'
        verbose_name = "Onboarding Profile"
        verbose_name_plural = "Onboarding Profiles"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.journey_type or 'No Journey'}"

    def calculate_pregnancy_weeks(self):
        """Calculate current pregnancy week from due date"""
        if self.due_date and self.journey_type == 'pregnant':
            from datetime import date
            # Pregnancy is 40 weeks, so calculate backwards
            conception_estimate = self.due_date - timezone.timedelta(weeks=40)
            weeks_elapsed = (timezone.now().date() - conception_estimate).days // 7
            return max(0, min(42, weeks_elapsed))  # Cap between 0 and 42 weeks
        return None

    def save(self, *args, **kwargs):
        """Auto-calculate pregnancy weeks on save"""
        if self.due_date and self.journey_type == 'pregnant':
            self.pregnancy_weeks = self.calculate_pregnancy_weeks()

        if self.onboarding_completed and not self.onboarding_completed_at:
            self.onboarding_completed_at = timezone.now()

        super().save(*args, **kwargs)


class UserDevice(BaseModel):
    """
    Track user devices and platforms for analytics and platform-specific features.
    """
    PLATFORM_CHOICES = [
        ('web', 'Web'),
        ('mobile_ios', 'Mobile - iOS'),
        ('mobile_android', 'Mobile - Android'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='devices',
        help_text="User who owns this device"
    )

    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        help_text="Platform/device type"
    )

    device_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Unique device identifier (for push notifications)"
    )

    device_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Device name/model (e.g., 'iPhone 14 Pro')"
    )

    app_version = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="App version running on this device"
    )

    last_login_at = models.DateTimeField(
        auto_now=True,
        help_text="Last time user logged in from this device"
    )

    created_via = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        help_text="Platform where user first registered"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Whether this device is currently active"
    )

    class Meta:
        db_table = 'user_devices'
        verbose_name = "User Device"
        verbose_name_plural = "User Devices"
        ordering = ['-last_login_at']
        unique_together = ['user', 'device_id']

    def __str__(self):
        return f"{self.user.email} - {self.get_platform_display()} - {self.device_name or 'Unknown Device'}"
    