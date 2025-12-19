# wallet/urls_v2_9psb.py
"""
9PSB Wallet Operations URLs
All 17 test case endpoints for production launch
"""
from django.urls import path
from .views_v2_9psb import (
    WalletEnquiryAPIView,
    DebitWalletAPIView,
    CreditWalletAPIView,
    GetBanksAPIView,
    OtherBanksAccountEnquiryAPIView,
    OtherBanksTransferAPIView,
    WalletTransactionHistoryAPIView,
    WalletTransactionRequeryAPIView,
    WalletStatusAPIView,
    ChangeWalletStatusAPIView,
    WalletOpeningAPIView,
    WalletUpgradeAPIView,
    UpgradeStatusAPIView,
    NotificationRequeryAPIView,
    GetWalletByBVNAPIView,
    WalletUpgradeFileAPIView,
)

urlpatterns = [
    # Test Case 1: Wallet Opening
    path('open', WalletOpeningAPIView.as_view(), name='wallet-opening'),

    # Test Case 3: Wallet Enquiry (Get Balance)
    path('enquiry', WalletEnquiryAPIView.as_view(), name='wallet-enquiry'),

    # Test Case 4: Debit Wallet
    path('debit', DebitWalletAPIView.as_view(), name='wallet-debit'),

    # Test Case 5: Credit Wallet (Admin)
    path('credit', CreditWalletAPIView.as_view(), name='wallet-credit'),

    # Test Case 14: Get Banks
    path('banks', GetBanksAPIView.as_view(), name='get-banks'),

    # Test Case 6: Other Banks Account Enquiry
    path('banks/enquiry', OtherBanksAccountEnquiryAPIView.as_view(), name='other-banks-enquiry'),

    # Test Case 7: Other Banks Transfer
    path('transfer/banks', OtherBanksTransferAPIView.as_view(), name='other-banks-transfer'),

    # Test Case 8: Transaction History
    path('transactions', WalletTransactionHistoryAPIView.as_view(), name='transaction-history'),

    # Test Case 11: Transaction Requery
    path('transactions/requery', WalletTransactionRequeryAPIView.as_view(), name='transaction-requery'),

    # Test Case 9: Wallet Status
    path('status', WalletStatusAPIView.as_view(), name='wallet-status'),

    # Test Case 10: Change Wallet Status (Admin)
    path('status/change', ChangeWalletStatusAPIView.as_view(), name='change-wallet-status'),

    # Test Case 12: Wallet Upgrade
    path('upgrade', WalletUpgradeAPIView.as_view(), name='wallet-upgrade'),

    # Test Case 13: Upgrade Status
    path('upgrade/status', UpgradeStatusAPIView.as_view(), name='upgrade-status'),

    # Test Case 15: Notification Requery
    path('notification/requery', NotificationRequeryAPIView.as_view(), name='notification-requery'),

    # Test Case 16: Get Wallet by BVN (Admin)
    path('wallet/bvn', GetWalletByBVNAPIView.as_view(), name='get-wallet-by-bvn'),

    # Test Case 17: Wallet Upgrade with File Upload
    path('upgrade/file', WalletUpgradeFileAPIView.as_view(), name='wallet-upgrade-file'),
]
