# wallet/urls.py
from django.urls import path
from .views import (
    WalletBalanceAPIView,
    InitiateWithdrawalAPIView,
    ResolveBankAccountAPIView,
    EmbedlyWebhookView,
    PayoutWebhookView,
    WalletTransactionHistoryAPIView,
    GetBanksAPIView
)

urlpatterns = [
    path('balance', WalletBalanceAPIView.as_view(), name='wallet_balance'),

    path('history', WalletTransactionHistoryAPIView.as_view(), name='wallet_history'),

    path('withdraw/request', InitiateWithdrawalAPIView.as_view(), name='wallet_withdraw_request'),

    path('banks', GetBanksAPIView.as_view(), name='get-banks'),

    path('resolve-bank-account', ResolveBankAccountAPIView.as_view(), name='resolve-bank-account'),

    path('embedly/webhook/secure', EmbedlyWebhookView.as_view(), name='embedly-webhook'),

    path('payout/webhook', PayoutWebhookView.as_view(), name='payout-webhook'),

]

