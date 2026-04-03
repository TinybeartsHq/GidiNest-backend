# gifting/admin.py
from django.contrib import admin
from gifting.models import BabyFund, Gift


@admin.register(BabyFund)
class BabyFundAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'user_email', 'balance_display', 'gift_count_display',
        'target_amount', 'status', 'is_active', 'created_at',
    ]
    list_filter = ['status', 'is_active', 'created_at']
    search_fields = ['name', 'token', 'user__email', 'user__first_name']
    readonly_fields = ['id', 'token', 'balance', 'created_at', 'updated_at']
    raw_id_fields = ['user']

    fieldsets = (
        ('Fund Info', {
            'fields': ('id', 'user', 'token', 'name', 'description'),
        }),
        ('Financials', {
            'fields': ('balance', 'target_amount'),
        }),
        ('Settings', {
            'fields': ('due_date', 'thank_you_message', 'show_contributors', 'status', 'is_active'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Owner'

    def balance_display(self, obj):
        return f"NGN {obj.balance:,.2f}"
    balance_display.short_description = 'Balance'

    def gift_count_display(self, obj):
        return obj.get_gift_count()
    gift_count_display.short_description = 'Gifts'


@admin.register(Gift)
class GiftAdmin(admin.ModelAdmin):
    list_display = [
        'contributor_name', 'amount_display', 'fee_display', 'net_display',
        'fund_name', 'status', 'created_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = [
        'contributor_name', 'contributor_email', 'paystack_reference',
        'baby_fund__name', 'baby_fund__token',
    ]
    readonly_fields = [
        'id', 'paystack_reference', 'paystack_access_code',
        'fee_amount', 'net_amount', 'created_at', 'updated_at',
    ]
    raw_id_fields = ['baby_fund']

    fieldsets = (
        ('Gift Info', {
            'fields': ('id', 'baby_fund', 'status'),
        }),
        ('Financials', {
            'fields': ('amount', 'fee_amount', 'net_amount'),
        }),
        ('Contributor', {
            'fields': ('contributor_name', 'contributor_email', 'contributor_phone', 'message'),
        }),
        ('Paystack', {
            'fields': ('paystack_reference', 'paystack_access_code'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def amount_display(self, obj):
        return f"NGN {obj.amount:,.2f}"
    amount_display.short_description = 'Amount'

    def fee_display(self, obj):
        return f"NGN {obj.fee_amount:,.2f}"
    fee_display.short_description = 'Fee'

    def net_display(self, obj):
        return f"NGN {obj.net_amount:,.2f}" if obj.net_amount else '-'
    net_display.short_description = 'Net'

    def fund_name(self, obj):
        return obj.baby_fund.name
    fund_name.short_description = 'Fund'
