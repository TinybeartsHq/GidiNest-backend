# notification/views.py
"""
V2 Mobile - Notification System Views
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from core.helpers.response import success_response, error_response
from .models import Notification
from .serializers import NotificationSerializer, NotificationListSerializer


class NotificationListAPIView(APIView):
    """
    V2 Mobile - List Notifications

    GET: List all notifications for the authenticated user
    Supports pagination and filtering by read/unread status
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V2 - Notifications'],
        summary='List Notifications',
        description='Get paginated list of user notifications with optional filtering',
        parameters=[
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Page number (default: 1)',
                required=False,
            ),
            OpenApiParameter(
                name='page_size',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Number of items per page (default: 20, max: 100)',
                required=False,
            ),
            OpenApiParameter(
                name='is_read',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by read status (true/false)',
                required=False,
            ),
        ],
        responses={200: NotificationListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        """
        List all notifications for the authenticated user
        """
        # Get query parameters
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 100)
        is_read_filter = request.query_params.get('is_read')

        # Base queryset
        notifications = Notification.objects.filter(user=request.user)

        # Apply filters
        if is_read_filter is not None:
            is_read = is_read_filter.lower() in ['true', '1', 'yes']
            notifications = notifications.filter(is_read=is_read)

        # Get counts
        total_count = notifications.count()
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

        # Paginate
        paginator = Paginator(notifications, page_size)
        page_obj = paginator.get_page(page)

        # Serialize
        serializer = NotificationListSerializer(page_obj.object_list, many=True)

        response_data = {
            'notifications': serializer.data,
            'pagination': {
                'current_page': page,
                'total_pages': paginator.num_pages,
                'page_size': page_size,
                'total_count': total_count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            },
            'unread_count': unread_count,
        }

        return success_response(
            data=response_data,
            message="Notifications retrieved successfully"
        )


class NotificationDetailAPIView(APIView):
    """
    V2 Mobile - Notification Detail

    GET: Get notification details
    DELETE: Delete a notification
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, notification_id, user):
        """Helper method to get notification and check ownership"""
        try:
            return Notification.objects.get(id=notification_id, user=user)
        except Notification.DoesNotExist:
            return None

    @extend_schema(
        tags=['V2 - Notifications'],
        summary='Get Notification Details',
        description='Retrieve details of a specific notification',
        responses={
            200: NotificationSerializer,
            404: OpenApiTypes.OBJECT
        }
    )
    def get(self, request, notification_id, *args, **kwargs):
        """
        Get notification details
        """
        notification = self.get_object(notification_id, request.user)
        if not notification:
            return error_response(
                message="Notification not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Mark as read if not already
        if not notification.is_read:
            notification.mark_as_read()

        serializer = NotificationSerializer(notification)
        return success_response(
            data=serializer.data,
            message="Notification retrieved successfully"
        )

    @extend_schema(
        tags=['V2 - Notifications'],
        summary='Delete Notification',
        description='Delete a specific notification',
        responses={
            200: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        }
    )
    def delete(self, request, notification_id, *args, **kwargs):
        """
        Delete a notification
        """
        notification = self.get_object(notification_id, request.user)
        if not notification:
            return error_response(
                message="Notification not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        notification.delete()
        return success_response(
            message="Notification deleted successfully"
        )


class MarkNotificationReadAPIView(APIView):
    """
    V2 Mobile - Mark Notification as Read

    PUT: Mark a notification as read
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V2 - Notifications'],
        summary='Mark Notification as Read',
        description='Mark a specific notification as read',
        responses={
            200: NotificationSerializer,
            404: OpenApiTypes.OBJECT
        }
    )
    def put(self, request, notification_id, *args, **kwargs):
        """
        Mark notification as read
        """
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
        except Notification.DoesNotExist:
            return error_response(
                message="Notification not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Mark as read
        notification.mark_as_read()

        serializer = NotificationSerializer(notification)
        return success_response(
            data=serializer.data,
            message="Notification marked as read"
        )


class MarkAllNotificationsReadAPIView(APIView):
    """
    V2 Mobile - Mark All Notifications as Read

    PUT: Mark all notifications as read for the authenticated user
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V2 - Notifications'],
        summary='Mark All Notifications as Read',
        description='Mark all notifications as read for the authenticated user',
        responses={200: OpenApiTypes.OBJECT}
    )
    def put(self, request, *args, **kwargs):
        """
        Mark all notifications as read
        """
        # Get all unread notifications
        unread_notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        )

        # Count before updating
        count = unread_notifications.count()

        # Mark all as read
        now = timezone.now()
        unread_notifications.update(is_read=True, read_at=now)

        return success_response(
            data={'marked_read_count': count},
            message=f"{count} notification(s) marked as read"
        )


class UnreadNotificationCountAPIView(APIView):
    """
    V2 Mobile - Get Unread Notification Count

    GET: Get count of unread notifications
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V2 - Notifications'],
        summary='Get Unread Count',
        description='Get count of unread notifications for the authenticated user',
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request, *args, **kwargs):
        """
        Get unread notification count
        """
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

        return success_response(
            data={'unread_count': unread_count},
            message="Unread count retrieved successfully"
        )
