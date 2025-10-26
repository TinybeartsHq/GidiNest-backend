from django.contrib import admin
from .models import Wallet, WalletTransaction, WithdrawalRequest


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = (
        'user_email',
        'balance',
        'currency',
        'account_number',
        'bank',
        'account_name',
        'created_at',
        'updated_at',
    )
    search_fields = ('user__email', 'account_number', 'account_name', 'bank')
    list_filter = ('currency', 'bank', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'balance')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = (
        'user_email',
        'amount',
        'bank_name',
        'account_number',
        'status',
        'created_at',
        'updated_at',
    )
    search_fields = ('user__email', 'bank_name', 'account_number')
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at', 'updated_at')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'



@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'wallet_account_number',
        'transaction_type',
        'amount',
        'description',
        'sender_name',
        'sender_account',
        'created_at',
    )
    search_fields = ('wallet__account_number', 'sender_name', 'sender_account')
    list_filter = ('transaction_type', 'created_at')
    readonly_fields = ('created_at',)

    def wallet_account_number(self, obj):
        return obj.wallet.account_number
    wallet_account_number.short_description = 'Wallet Account Number'