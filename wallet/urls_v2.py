# wallet/urls_v2.py
"""
V2 URLs for Mobile App - Wallet Management
Enhanced wallet APIs with limits enforcement and deposit initiation
"""

from django.urls import path
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
from wallet.views_v2 import (
    WalletDetailAPIView,
    WalletDepositAPIView,
    WalletWithdrawAPIView,
)

urlpatterns = [
    # ==========================================
    # WALLET OPERATIONS
    # ==========================================
    path('', WalletDetailAPIView.as_view(), name='v2-wallet-detail'),  # GET
    path('deposit', WalletDepositAPIView.as_view(), name='v2-wallet-deposit'),  # POST
    path('withdraw', WalletWithdrawAPIView.as_view(), name='v2-wallet-withdraw'),  # POST

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
