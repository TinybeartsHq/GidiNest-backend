from django.contrib import admin
from .models import Wallet, WalletTransaction, WithdrawalRequest, PaymentLink, PaymentLinkContribution, FeeConfiguration, PlatformWallet


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
        'total_fee',
        'net_amount',
        'status',
        'reference',
        'external_reference',
        'description',
        'created_at',
    )
    search_fields = ('wallet__account_number', 'sender_name', 'sender_account', 'reference', 'external_reference')
    list_filter = ('transaction_type', 'status', 'created_at')
    readonly_fields = ('created_at',)

    def wallet_account_number(self, obj):
        return obj.wallet.account_number
    wallet_account_number.short_description = 'Wallet Account Number'


@admin.register(PaymentLink)
class PaymentLinkAdmin(admin.ModelAdmin):
    list_display = (
        'token_preview',
        'user_email',
        'link_type',
        'goal_or_event_name',
        'total_raised_display',
        'contributor_count_display',
        'is_active',
        'created_at',
    )
    search_fields = ('token', 'user__email', 'event_name', 'savings_goal__name')
    list_filter = ('link_type', 'is_active', 'show_contributors', 'created_at')
    readonly_fields = ('id', 'token', 'created_at', 'updated_at', 'total_raised_display', 'contributor_count_display')

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'token', 'link_type', 'is_active')
        }),
        ('Link Configuration', {
            'fields': ('savings_goal', 'event_name', 'event_date', 'event_description')
        }),
        ('Settings', {
            'fields': ('target_amount', 'allow_custom_amount', 'fixed_amount', 'show_contributors')
        }),
        ('Messaging', {
            'fields': ('description', 'custom_message')
        }),
        ('Advanced', {
            'fields': ('expires_at', 'one_time_use', 'used')
        }),
        ('Statistics', {
            'fields': ('total_raised_display', 'contributor_count_display', 'created_at', 'updated_at')
        }),
    )

    def token_preview(self, obj):
        return f"{obj.token[:20]}..." if len(obj.token) > 20 else obj.token
    token_preview.short_description = 'Token'

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'

    def goal_or_event_name(self, obj):
        if obj.link_type == 'savings_goal' and obj.savings_goal:
            return obj.savings_goal.name
        elif obj.link_type == 'event' and obj.event_name:
            return obj.event_name
        return '-'
    goal_or_event_name.short_description = 'Goal/Event'

    def total_raised_display(self, obj):
        return f"₦{obj.get_total_raised():,.2f}"
    total_raised_display.short_description = 'Total Raised'

    def contributor_count_display(self, obj):
        return obj.get_contributor_count()
    contributor_count_display.short_description = 'Contributors'


@admin.register(PaymentLinkContribution)
class PaymentLinkContributionAdmin(admin.ModelAdmin):
    list_display = (
        'payment_link_preview',
        'contributor_name',
        'amount',
        'status',
        'created_at',
    )
    search_fields = ('payment_link__token', 'contributor_name', 'contributor_email', 'external_reference')
    list_filter = ('status', 'created_at')
    readonly_fields = ('id', 'created_at', 'updated_at')

    def payment_link_preview(self, obj):
        return str(obj.payment_link)
    payment_link_preview.short_description = 'Payment Link'


@admin.register(FeeConfiguration)
class FeeConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'is_active',
        'transfer_fee_tier1_amount',
        'transfer_fee_tier2_amount',
        'transfer_fee_tier3_amount',
        'vat_rate_display',
        'emtl_amount',
        'pl_commission_display',
        'created_at',
    )
    list_filter = ('is_active', 'created_at')
    readonly_fields = ('id', 'created_at', 'updated_at')

    fieldsets = (
        ('Configuration Identity', {
            'fields': ('id', 'name', 'is_active', 'notes')
        }),
        ('Transfer Fee Tiers', {
            'fields': (
                'transfer_fee_tier1_max', 'transfer_fee_tier1_amount',
                'transfer_fee_tier2_max', 'transfer_fee_tier2_amount',
                'transfer_fee_tier3_amount',
            ),
            'description': 'Tiered fees applied to transfers, withdrawals, and deposits.'
        }),
        ('VAT', {
            'fields': ('vat_rate',),
            'description': 'VAT is applied to the transfer fee or commission, NOT the principal amount.'
        }),
        ('EMTL / Stamp Duty', {
            'fields': ('emtl_threshold', 'emtl_amount'),
            'description': 'Fixed charge applied when transaction amount >= threshold.'
        }),
        ('Payment Link Commission', {
            'fields': ('payment_link_commission_rate',),
            'description': 'Percentage commission charged on payment link contributions. VAT is applied on top.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def vat_rate_display(self, obj):
        return f"{obj.vat_rate * 100:.2f}%"
    vat_rate_display.short_description = 'VAT Rate'

    def pl_commission_display(self, obj):
        return f"{obj.payment_link_commission_rate * 100:.2f}%"
    pl_commission_display.short_description = 'PL Commission'


@admin.register(PlatformWallet)
class PlatformWalletAdmin(admin.ModelAdmin):
    list_display = (
        'wallet_type',
        'balance_display',
        'transfer_fees_display',
        'vat_display',
        'emtl_display',
        'commission_display',
        'updated_at',
    )
    readonly_fields = (
        'id', 'wallet_type', 'balance', 'total_transfer_fees',
        'total_vat', 'total_emtl', 'total_commission',
        'created_at', 'updated_at',
    )

    fieldsets = (
        ('Revenue Summary', {
            'fields': ('id', 'wallet_type', 'balance'),
        }),
        ('Fee Breakdown (Lifetime)', {
            'fields': (
                'total_transfer_fees', 'total_vat',
                'total_emtl', 'total_commission',
            ),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def has_add_permission(self, request):
        return not PlatformWallet.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def balance_display(self, obj):
        return f"₦{obj.balance:,.2f}"
    balance_display.short_description = 'Balance'

    def transfer_fees_display(self, obj):
        return f"₦{obj.total_transfer_fees:,.2f}"
    transfer_fees_display.short_description = 'Transfer Fees'

    def vat_display(self, obj):
        return f"₦{obj.total_vat:,.2f}"
    vat_display.short_description = 'VAT'

    def emtl_display(self, obj):
        return f"₦{obj.total_emtl:,.2f}"
    emtl_display.short_description = 'EMTL'

    def commission_display(self, obj):
        return f"₦{obj.total_commission:,.2f}"
    commission_display.short_description = 'Commission'