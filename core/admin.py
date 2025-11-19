from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import ServerLog


# Update admin site branding
admin.site.site_header = _("GidiNest Internal Admin")
admin.site.site_title = _("GidiNest Admin")
admin.site.index_title = _("Welcome to GidiNest Internal Admin")


@admin.register(ServerLog)
class ServerLogAdmin(admin.ModelAdmin):
    """
    Admin interface for viewing server logs with filtering and search.
    """
    list_display = (
        'timestamp',
        'level_colored',
        'logger_name',
        'short_message',
        'request_info',
        'user_email',
        'location_info'
    )
    list_filter = (
        'level',
        'logger_name',
        ('timestamp', admin.DateFieldListFilter),
        'request_method',
    )
    search_fields = (
        'message',
        'logger_name',
        'user_email',
        'request_path',
        'exception',
        'ip_address'
    )
    readonly_fields = (
        'level',
        'logger_name',
        'message',
        'pathname',
        'function_name',
        'line_number',
        'exception_display',
        'request_path',
        'request_method',
        'user_email',
        'ip_address',
        'timestamp'
    )
    ordering = ('-timestamp',)
    list_per_page = 50
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Log Information', {
            'fields': ('timestamp', 'level', 'logger_name', 'message')
        }),
        ('Source Location', {
            'fields': ('pathname', 'function_name', 'line_number'),
            'classes': ('collapse',)
        }),
        ('Request Information', {
            'fields': ('request_path', 'request_method', 'user_email', 'ip_address'),
            'classes': ('collapse',)
        }),
        ('Exception Details', {
            'fields': ('exception_display',),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual log creation through admin"""
        return False

    def has_change_permission(self, request, obj=None):
        """Make logs read-only"""
        return False

    def level_colored(self, obj):
        """Display log level with color coding"""
        colors = {
            'DEBUG': 'gray',
            'INFO': 'blue',
            'WARNING': 'orange',
            'ERROR': 'red',
            'CRITICAL': 'darkred',
        }
        color = colors.get(obj.level, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.level
        )
    level_colored.short_description = 'Level'

    def short_message(self, obj):
        """Display truncated message"""
        return obj.get_short_message()
    short_message.short_description = 'Message'

    def request_info(self, obj):
        """Display request method and path"""
        if obj.request_path:
            return format_html(
                '<span style="font-family: monospace;">{} {}</span>',
                obj.request_method or '',
                obj.request_path
            )
        return '-'
    request_info.short_description = 'Request'

    def location_info(self, obj):
        """Display source location"""
        if obj.function_name:
            return format_html(
                '<span style="font-family: monospace;">{}:{}</span>',
                obj.function_name,
                obj.line_number or '?'
            )
        return '-'
    location_info.short_description = 'Location'

    def exception_display(self, obj):
        """Display exception with formatting"""
        if obj.exception:
            return format_html(
                '<pre style="background: #f5f5f5; padding: 10px; overflow: auto;">{}</pre>',
                obj.exception
            )
        return 'No exception'
    exception_display.short_description = 'Exception Traceback'

    def changelist_view(self, request, extra_context=None):
        """Add statistics to the change list view"""
        extra_context = extra_context or {}

        # Calculate time ranges
        now = timezone.now()
        last_hour = now - timedelta(hours=1)
        last_24h = now - timedelta(hours=24)

        # Get statistics
        total_logs = ServerLog.objects.count()
        logs_last_hour = ServerLog.objects.filter(timestamp__gte=last_hour).count()
        logs_last_24h = ServerLog.objects.filter(timestamp__gte=last_24h).count()

        # Count by level (last 24h)
        level_counts = ServerLog.objects.filter(
            timestamp__gte=last_24h
        ).values('level').annotate(count=Count('id')).order_by('level')

        # Recent errors
        recent_errors = ServerLog.objects.filter(
            level__in=['ERROR', 'CRITICAL'],
            timestamp__gte=last_24h
        ).count()

        extra_context['log_stats'] = {
            'total_logs': total_logs,
            'logs_last_hour': logs_last_hour,
            'logs_last_24h': logs_last_24h,
            'recent_errors': recent_errors,
            'level_counts': {item['level']: item['count'] for item in level_counts},
        }

        return super().changelist_view(request, extra_context=extra_context)