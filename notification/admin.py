from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django import forms
from django.contrib import messages
from .models import Notification


class NotificationAdminForm(forms.ModelForm):
    """Custom form for creating notifications"""
    class Meta:
        model = Notification
        fields = '__all__'
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make action_url optional
        self.fields['action_url'].required = False
        self.fields['data'].required = False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    form = NotificationAdminForm
    list_display = ('title', 'user_email', 'notification_type', 'is_read_badge', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'read_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    actions = ['mark_as_read', 'mark_as_unread', 'send_general_notification']

    fieldsets = (
        ('Recipient', {
            'fields': ('user',),
            'description': 'Select a user to send this notification to. Leave empty when creating a template for general notifications.'
        }),
        ('Notification Content', {
            'fields': ('title', 'message', 'notification_type', 'action_url')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('Metadata', {
            'fields': ('data',),
            'classes': ('collapse',),
            'description': 'Optional JSON data for additional notification metadata.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_email(self, obj):
        return obj.user.email if obj.user else 'N/A'
    user_email.short_description = 'User'

    def is_read_badge(self, obj):
        if obj.is_read:
            return format_html(
                '<span style="padding: 3px 10px; border-radius: 3px; background-color: green; color: white;">Read</span>'
            )
        return format_html(
            '<span style="padding: 3px 10px; border-radius: 3px; background-color: orange; color: white;">Unread</span>'
        )
    is_read_badge.short_description = 'Status'

    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read"""
        updated = queryset.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        self.message_user(request, f'{updated} notification(s) marked as read.')
    mark_as_read.short_description = 'Mark selected as read'

    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread"""
        updated = queryset.filter(is_read=True).update(
            is_read=False,
            read_at=None
        )
        self.message_user(request, f'{updated} notification(s) marked as unread.')
    mark_as_unread.short_description = 'Mark selected as unread'

    def send_general_notification(self, request, queryset):
        """Send a general notification to all users (creates individual notifications)"""
        from account.models import UserModel
        
        # Get notification details from first selected notification
        if queryset.count() != 1:
            self.message_user(request, 'Please select exactly one notification to use as template.', level=messages.ERROR)
            return
        
        template_notification = queryset.first()
        
        # Get all active users
        users = UserModel.objects.filter(is_active=True)
        count = users.count()
        
        if count == 0:
            self.message_user(request, 'No active users found.', level=messages.ERROR)
            return
        
        # Create notifications for all users
        notifications = []
        for user in users:
            notifications.append(
                Notification(
                    user=user,
                    title=template_notification.title,
                    message=template_notification.message,
                    notification_type=template_notification.notification_type,
                    action_url=template_notification.action_url,
                    data=template_notification.data or {}
                )
            )
        
        # Bulk create
        Notification.objects.bulk_create(notifications)
        self.message_user(request, f'General notification sent to {count} user(s).')
    send_general_notification.short_description = 'Send as general notification to all users'
