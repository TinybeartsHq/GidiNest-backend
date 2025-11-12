# wallet/urls_v2.py
"""
V2 URLs for Mobile App - Wallet Management
Enhanced wallet APIs with limits enforcement and deposit initiation
"""

from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from wallet.payment_link_views import (
    CreateGoalPaymentLinkAPIView,
    CreateEventPaymentLinkAPIView,
    CreateWalletPaymentLinkAPIView,
    ViewPaymentLinkPublicAPIView,
    PaymentLinkAnalyticsAPIView,
    ListUserPaymentLinksAPIView,
    UpdatePaymentLinkAPIView,
    DeletePaymentLinkAPIView,
)

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

    # ==========================================
    # PAYMENT LINKS
    # ==========================================
    # Create payment links
    path('payment-links/create-goal-link', CreateGoalPaymentLinkAPIView.as_view(), name='v2-create-goal-payment-link'),
    path('payment-links/create-event-link', CreateEventPaymentLinkAPIView.as_view(), name='v2-create-event-payment-link'),
    path('payment-links/create-wallet-link', CreateWalletPaymentLinkAPIView.as_view(), name='v2-create-wallet-payment-link'),

    # List user's payment links
    path('payment-links/my-links', ListUserPaymentLinksAPIView.as_view(), name='v2-list-payment-links'),

    # Public view (anyone with token can access)
    path('payment-links/<str:token>/', ViewPaymentLinkPublicAPIView.as_view(), name='v2-view-payment-link'),

    # Owner-only operations
    path('payment-links/<str:token>/analytics', PaymentLinkAnalyticsAPIView.as_view(), name='v2-payment-link-analytics'),
    path('payment-links/<str:token>/update', UpdatePaymentLinkAPIView.as_view(), name='v2-update-payment-link'),
    path('payment-links/<str:token>/delete', DeletePaymentLinkAPIView.as_view(), name='v2-delete-payment-link'),

    # Note: Webhooks remain in v1 as they're shared
    # Note: Banks list, account resolution, PIN management can be shared from v1
]
