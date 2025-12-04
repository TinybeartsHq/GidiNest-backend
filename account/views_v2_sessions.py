"""
V2 Session Management Views
Handle user session listing, deletion, and remote logout functionality for mobile app.
"""
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db.models import Q
from account.models.sessions import UserSession
from account.serializers import UserSessionSerializer
from core.helpers.response import success_response, error_response


class SessionListView(APIView):
    """
    API endpoint to list all active sessions for the authenticated user.
    GET: Retrieve all active sessions with device details.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V2 - Profile & Settings'],
        summary='List Active Sessions',
        description='Get all active sessions for the authenticated user. Shows device information, location, and last active timestamp.',
        responses={
            200: {
                'description': 'Sessions retrieved successfully',
                'content': {
                    'application/json': {
                        'example': {
                            'success': True,
                            'message': 'Sessions retrieved successfully',
                            'data': {
                                'sessions': [
                                    {
                                        'id': 'uuid',
                                        'device_name': 'iPhone 14 Pro',
                                        'device_type': 'ios',
                                        'device_id': 'device-uuid',
                                        'ip_address': '192.168.1.1',
                                        'location': 'Lagos, Nigeria',
                                        'is_active': True,
                                        'is_current': True,
                                        'is_expired': False,
                                        'created_at': '2025-01-01T00:00:00Z',
                                        'last_active_at': '2025-01-22T12:00:00Z',
                                        'expires_at': '2025-02-01T00:00:00Z'
                                    }
                                ],
                                'total_sessions': 1,
                                'active_sessions': 1
                            }
                        }
                    }
                }
            },
            401: {'description': 'Unauthorized'},
        }
    )
    def get(self, request):
        """
        List all active sessions for the authenticated user.
        """
        user = request.user

        # Get all sessions for this user (both active and inactive for transparency)
        sessions = UserSession.objects.filter(user=user).order_by('-last_active_at')

        # Serialize sessions
        serializer = UserSessionSerializer(
            sessions,
            many=True,
            context={'request': request}
        )

        # Count active vs total
        active_count = sessions.filter(is_active=True).count()
        total_count = sessions.count()

        response_data = {
            'sessions': serializer.data,
            'total_sessions': total_count,
            'active_sessions': active_count
        }

        return success_response(
            message="Sessions retrieved successfully",
            data=response_data
        )


class SessionDetailView(APIView):
    """
    API endpoint to manage a specific session.
    DELETE: Terminate a specific session (remote logout).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V2 - Profile & Settings'],
        summary='Delete Specific Session',
        description='Terminate a specific session by ID. This will log out the device associated with this session.',
        parameters=[
            OpenApiParameter(
                name='session_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Session ID to terminate',
                required=True,
            ),
        ],
        responses={
            200: {
                'description': 'Session terminated successfully',
                'content': {
                    'application/json': {
                        'example': {
                            'success': True,
                            'message': 'Session terminated successfully'
                        }
                    }
                }
            },
            400: {'description': 'Cannot delete current session'},
            404: {'description': 'Session not found'},
            401: {'description': 'Unauthorized'},
        }
    )
    def delete(self, request, session_id):
        """
        Terminate a specific session for the authenticated user.
        Users cannot delete their current session (must use logout for that).
        """
        user = request.user

        try:
            session = UserSession.objects.get(id=session_id, user=user)
        except UserSession.DoesNotExist:
            return error_response(
                "Session not found or does not belong to you.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Prevent users from deleting their current session
        # They should use the logout endpoint for that
        current_token_hash = self.request.META.get('HTTP_X_REFRESH_TOKEN_HASH')
        if current_token_hash and session.refresh_token_hash == current_token_hash:
            return error_response(
                "Cannot delete current session. Please use logout endpoint.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Invalidate the session
        session.invalidate()

        return success_response(
            message=f"Session for {session.device_name} terminated successfully"
        )


class EndAllSessionsView(APIView):
    """
    API endpoint to terminate all sessions except the current one.
    DELETE: End all other sessions (useful for security purposes).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V2 - Profile & Settings'],
        summary='End All Other Sessions',
        description='Terminate all sessions except the current one. Useful for security when you suspect unauthorized access.',
        responses={
            200: {
                'description': 'All other sessions terminated successfully',
                'content': {
                    'application/json': {
                        'example': {
                            'success': True,
                            'message': '3 sessions terminated successfully',
                            'data': {
                                'sessions_terminated': 3,
                                'remaining_sessions': 1
                            }
                        }
                    }
                }
            },
            401: {'description': 'Unauthorized'},
        }
    )
    def delete(self, request):
        """
        Terminate all sessions except the current one for the authenticated user.
        """
        user = request.user

        # Get current session's token hash (if available)
        current_token_hash = self.request.META.get('HTTP_X_REFRESH_TOKEN_HASH')

        # Get all active sessions for this user
        all_sessions = UserSession.objects.filter(user=user, is_active=True)

        if current_token_hash:
            # Exclude current session from termination
            other_sessions = all_sessions.exclude(refresh_token_hash=current_token_hash)
        else:
            # If we can't identify current session, terminate all but the most recent
            # This is a fallback - ideally the token hash should always be available
            most_recent = all_sessions.order_by('-last_active_at').first()
            if most_recent:
                other_sessions = all_sessions.exclude(id=most_recent.id)
            else:
                other_sessions = all_sessions

        # Count before terminating
        sessions_count = other_sessions.count()

        # Terminate all other sessions
        other_sessions.update(is_active=False)

        # Count remaining active sessions
        remaining_count = UserSession.objects.filter(user=user, is_active=True).count()

        response_data = {
            'sessions_terminated': sessions_count,
            'remaining_sessions': remaining_count
        }

        return success_response(
            message=f"{sessions_count} session(s) terminated successfully",
            data=response_data
        )
