# wallet/urls.py
from django.urls import path
from .views import (
    WalletBalanceAPIView,
    InitiateWithdrawalAPIView,
    ResolveBankAccountAPIView,
    EmbedlyWebhookView,
    PayoutWebhookView,
    WalletTransactionHistoryAPIView,
    GetBanksAPIView,
    CheckWithdrawalStatusAPIView
)

urlpatterns = [
    path('balance', WalletBalanceAPIView.as_view(), name='wallet_balance'),

    path('history', WalletTransactionHistoryAPIView.as_view(), name='wallet_history'),

    path('withdraw/request', InitiateWithdrawalAPIView.as_view(), name='wallet_withdraw_request'),

    path('withdraw/status/<int:withdrawal_id>', CheckWithdrawalStatusAPIView.as_view(), name='check_withdrawal_status'),

    path('banks', GetBanksAPIView.as_view(), name='get-banks'),

    path('resolve-bank-account', ResolveBankAccountAPIView.as_view(), name='resolve-bank-account'),

    path('embedly/webhook/secure', EmbedlyWebhookView.as_view(), name='embedly-webhook'),

    path('payout/webhook', PayoutWebhookView.as_view(), name='payout-webhook'),

]

