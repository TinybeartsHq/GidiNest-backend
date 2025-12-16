# account/urls_v2_kyc.py
"""
V2 URLs for Mobile App - KYC Verification
Two-step BVN and NIN verification flow with Prembly integration
"""

from django.urls import path
from account.views_v2_kyc import (
    V2BVNVerifyView,
    V2BVNConfirmView,
    V2NINVerifyView,
    V2NINConfirmView,
    V2WalletRetryView,
    V2WalletSyncView
)

urlpatterns = [
    # ==========================================
    # BVN VERIFICATION (Two-Step - Prembly)
    # ==========================================
    # Step 1: Verify BVN with Prembly and return details for review
    path('bvn/verify', V2BVNVerifyView.as_view(), name='v2-kyc-bvn-verify'),

    # Step 2: Confirm BVN details and save to database
    path('bvn/confirm', V2BVNConfirmView.as_view(), name='v2-kyc-bvn-confirm'),

    # ==========================================
    # NIN VERIFICATION (Two-Step - Prembly)
    # ==========================================
    # Step 1: Verify NIN with Prembly and return details for review
    path('nin/verify', V2NINVerifyView.as_view(), name='v2-kyc-nin-verify'),

    # Step 2: Confirm NIN details and save to database
    path('nin/confirm', V2NINConfirmView.as_view(), name='v2-kyc-nin-confirm'),

    # ==========================================
    # WALLET MANAGEMENT
    # ==========================================
    # Sync wallet details manually (for when wallet exists in 9PSB but not in database)
    path('wallet/sync', V2WalletSyncView.as_view(), name='v2-kyc-wallet-sync'),

    # Retry wallet creation if BVN verified but wallet creation failed
    path('wallet/retry', V2WalletRetryView.as_view(), name='v2-kyc-wallet-retry'),
]
