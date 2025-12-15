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
    CheckWithdrawalStatusAPIView,
    SetTransactionPinAPIView,
    VerifyTransactionPinAPIView,
    TransactionPinStatusAPIView
)
from .views_v2 import PSB9WebhookView

urlpatterns = [
    path('balance', WalletBalanceAPIView.as_view(), name='wallet_balance'),

    path('history', WalletTransactionHistoryAPIView.as_view(), name='wallet_history'),

    path('withdraw/request', InitiateWithdrawalAPIView.as_view(), name='wallet_withdraw_request'),

    path('withdraw/status/<int:withdrawal_id>', CheckWithdrawalStatusAPIView.as_view(), name='check_withdrawal_status'),

    path('banks', GetBanksAPIView.as_view(), name='get-banks'),

    path('resolve-bank-account', ResolveBankAccountAPIView.as_view(), name='resolve-bank-account'),

    path('transaction-pin/set', SetTransactionPinAPIView.as_view(), name='set_transaction_pin'),

    path('transaction-pin/verify', VerifyTransactionPinAPIView.as_view(), name='verify_transaction_pin'),

    path('transaction-pin/status', TransactionPinStatusAPIView.as_view(), name='transaction_pin_status'),

    path('embedly/webhook/secure', EmbedlyWebhookView.as_view(), name='embedly-webhook'),

    path('payout/webhook', PayoutWebhookView.as_view(), name='payout-webhook'),

    # V2 Webhooks - 9PSB (9 Payment Service Bank)
    path('9psb/webhook', PSB9WebhookView.as_view(), name='9psb-webhook'),

]

