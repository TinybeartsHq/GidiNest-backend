# wallet/urls_v2.py
"""
V2 URLs for Mobile App - Wallet Management
Enhanced wallet APIs with limits enforcement and deposit initiation
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
            "message": "V2 Wallet endpoint - Implementation pending",
            "endpoint": request.path
        }, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        return Response({
            "success": True,
            "message": "V2 Wallet endpoint - Implementation pending",
            "endpoint": request.path,
            "method": "POST"
        }, status=status.HTTP_200_OK)

urlpatterns = [
    # ==========================================
    # WALLET OPERATIONS
    # ==========================================
    path('', PlaceholderView.as_view(), name='v2-wallet-detail'),  # GET
    path('deposit', PlaceholderView.as_view(), name='v2-wallet-deposit'),  # POST
    path('withdraw', PlaceholderView.as_view(), name='v2-wallet-withdraw'),  # POST

    # Note: Webhooks remain in v1 as they're shared
    # Note: Banks list, account resolution, PIN management can be shared from v1
]
