from django.contrib import admin
from providers.models import ProviderRequestLog

@admin.register(ProviderRequestLog)
class ProviderRequestLogAdmin(admin.ModelAdmin):
    list_display = ("provider_name", "http_method", "endpoint", "response_status", "success", "created_at")
    list_filter = ("provider_name", "success", "response_status")
    search_fields = ("endpoint", "error_message")