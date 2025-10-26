from django.contrib import admin
from .models import RegisterTempData


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
