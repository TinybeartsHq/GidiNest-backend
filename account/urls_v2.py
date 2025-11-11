# account/urls_v2.py
"""
V2 URLs for Mobile App - Profile & Settings
Enhanced profile management with bank accounts, sessions, and avatar upload
"""

from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Placeholder view (to be replaced with actual implementation)
class PlaceholderView(APIView):
    """Temporary placeholder for v2 endpoints during URL setup"""
    def get(self, request, *args, **kwargs):
        return Response({
            "success": True,
            "message": "V2 endpoint - Implementation pending",
            "endpoint": request.path
        }, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        return Response({
            "success": True,
            "message": "V2 endpoint - Implementation pending",
            "endpoint": request.path,
            "method": "POST"
        }, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        return Response({
            "success": True,
            "message": "V2 endpoint - Implementation pending",
            "endpoint": request.path,
            "method": "PUT"
        }, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        return Response({
            "success": True,
            "message": "V2 endpoint - Implementation pending",
            "endpoint": request.path,
            "method": "DELETE"
        }, status=status.HTTP_200_OK)

urlpatterns = [
    # ==========================================
    # PROFILE MANAGEMENT
    # ==========================================
    path('', PlaceholderView.as_view(), name='v2-profile'),  # GET, PUT
    path('avatar', PlaceholderView.as_view(), name='v2-profile-avatar'),  # POST

    # ==========================================
    # BANK ACCOUNTS
    # ==========================================
    path('bank-accounts', PlaceholderView.as_view(), name='v2-bank-accounts-list'),  # GET, POST
    path('bank-accounts/<uuid:account_id>', PlaceholderView.as_view(), name='v2-bank-account-detail'),  # DELETE
    path('bank-accounts/<uuid:account_id>/default', PlaceholderView.as_view(), name='v2-bank-account-default'),  # PUT

    # ==========================================
    # SESSIONS
    # ==========================================
    path('sessions', PlaceholderView.as_view(), name='v2-sessions-list'),  # GET
    path('sessions/<uuid:session_id>', PlaceholderView.as_view(), name='v2-session-detail'),  # DELETE
    path('sessions/all', PlaceholderView.as_view(), name='v2-sessions-end-all'),  # DELETE
]
