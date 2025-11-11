# account/urls_v2_kyc.py
"""
V2 URLs for Mobile App - KYC Verification
Two-step BVN and NIN verification flow
"""

from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Placeholder view (to be replaced with actual implementation)
class PlaceholderView(APIView):
    """Temporary placeholder for v2 endpoints during URL setup"""
    def post(self, request, *args, **kwargs):
        return Response({
            "success": True,
            "message": "V2 KYC endpoint - Implementation pending",
            "endpoint": request.path,
            "method": "POST"
        }, status=status.HTTP_200_OK)

urlpatterns = [
    # ==========================================
    # BVN VERIFICATION (Two-Step)
    # ==========================================
    path('bvn/verify', PlaceholderView.as_view(), name='v2-kyc-bvn-verify'),
    path('bvn/confirm', PlaceholderView.as_view(), name='v2-kyc-bvn-confirm'),

    # ==========================================
    # NIN VERIFICATION (Two-Step)
    # ==========================================
    path('nin/verify', PlaceholderView.as_view(), name='v2-kyc-nin-verify'),
    path('nin/confirm', PlaceholderView.as_view(), name='v2-kyc-nin-confirm'),
]
