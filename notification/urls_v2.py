# notification/urls_v2.py
"""
V2 URLs for Mobile App - Notifications
Comprehensive notification management system
"""

from django.urls import path
from .views import (
    NotificationListAPIView,
    NotificationDetailAPIView,
    MarkNotificationReadAPIView,
    MarkAllNotificationsReadAPIView,
    UnreadNotificationCountAPIView,
)

urlpatterns = [
    # ==========================================
    # NOTIFICATION MANAGEMENT
    # ==========================================
    path('', NotificationListAPIView.as_view(), name='v2-notifications-list'),  # GET
    path('unread-count', UnreadNotificationCountAPIView.as_view(), name='v2-notifications-unread-count'),  # GET
    path('read-all', MarkAllNotificationsReadAPIView.as_view(), name='v2-notifications-read-all'),  # PUT
    path('<uuid:notification_id>', NotificationDetailAPIView.as_view(), name='v2-notification-detail'),  # GET, DELETE
    path('<uuid:notification_id>/read', MarkNotificationReadAPIView.as_view(), name='v2-notification-read'),  # PUT
]
