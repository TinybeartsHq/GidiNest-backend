# notification/serializers.py
"""
Serializers for notification system
"""
from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model
    """
    notification_type_display = serializers.CharField(
        source='get_notification_type_display',
        read_only=True
    )
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'message',
            'notification_type',
            'notification_type_display',
            'is_read',
            'read_at',
            'data',
            'action_url',
            'created_at',
            'updated_at',
            'time_ago',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'notification_type_display',
            'time_ago',
        ]

    def get_time_ago(self, obj):
        """
        Calculate human-readable time ago
        """
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        diff = now - obj.created_at

        if diff < timedelta(minutes=1):
            return "just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff < timedelta(days=30):
            days = diff.days
            return f"{days} day{'s' if days != 1 else ''} ago"
        elif diff < timedelta(days=365):
            months = int(diff.days / 30)
            return f"{months} month{'s' if months != 1 else ''} ago"
        else:
            years = int(diff.days / 365)
            return f"{years} year{'s' if years != 1 else ''} ago"


class NotificationListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for notification lists
    """
    notification_type_display = serializers.CharField(
        source='get_notification_type_display',
        read_only=True
    )

    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'message',
            'notification_type',
            'notification_type_display',
            'is_read',
            'created_at',
        ]
