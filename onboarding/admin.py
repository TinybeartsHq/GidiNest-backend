from django.contrib import admin
from django.utils import timezone
from .models import RegisterTempData, PasswordResetOTP


@admin.register(RegisterTempData)
class RegisterTempDataAdmin(admin.ModelAdmin):
    list_display = (
        'email',
        'phone',
        'first_name',
        'last_name',
        'oauth_provider',
        'is_oauth',
        'otp_verified',
        'created_at',
    )
    list_filter = ('oauth_provider', 'is_oauth', 'otp_verified', 'created_at')
    search_fields = ('email', 'phone', 'first_name', 'last_name', 'auth_id')
    readonly_fields = ('created_at', 'otp')

    ordering = ('-created_at',)


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user_email',
        'otp',
        'is_used',
        'is_expired',
        'created_at',
    )
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'otp')
    readonly_fields = ('created_at', 'otp', 'user')

    ordering = ('-created_at',)

    def user_email(self, obj):
        """Display the user's email in the list view"""
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'

    def is_expired(self, obj):
        """Display whether the OTP has expired"""
        return obj.has_expired()
    is_expired.short_description = 'Expired'
    is_expired.boolean = True

    def has_add_permission(self, request):
        """Prevent manual creation of OTPs in admin"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion of OTPs for cleanup"""
        return True

    def get_readonly_fields(self, request, obj=None):
        """Make all fields readonly except is_used"""
        if obj:
            return self.readonly_fields + ('is_used',)
        return self.readonly_fields
