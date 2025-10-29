from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models.users import UserModel
from .models import UserDevices
from django.db.models import Count


@admin.register(UserModel)
class UserAdmin(BaseUserAdmin):
    model = UserModel
    list_display = (
        'email','phone', 'first_name', 'last_name', 'is_verified', 'is_staff', 'is_active', 'account_tier'
    )
    list_filter = ('is_active', 'is_staff', 'is_verified', 'account_tier')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-created_at',)
    readonly_fields = ('last_login', 'created_at', 'updated_at')

    fieldsets = (
        (_('Account Info'), {
            'fields': ('email', 'password')
        }),
        (_('Personal Info'), {
            'fields': (
                'first_name', 'last_name', 'phone', 'address', 'country', 'state', 'dob', 'image',
                'account_tier', 'currency'
            )
        }),
        (_('BVN Info'), {
            'fields': (
                'bvn', 'bvn_first_name', 'bvn_last_name', 'bvn_phone', 'bvn_dob',
                'bvn_gender', 'bvn_marital_status', 'bvn_nationality',
                'bvn_residential_address', 'bvn_state_of_residence',
                'bvn_watch_listed', 'bvn_enrollment_bank', 'has_bvn'
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_verified', 'is_staff', 'is_superuser', 'email_verified'
            )
        }),
        (_('Wallet Info'), {
            'fields': ('has_virtual_wallet', 'embedly_customer_id', 'embedly_wallet_id')
        }),
        (_('Important Dates'), {
            'fields': ('last_login', 'created_at', 'updated_at')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_active', 'is_staff'),
        }),
    )


    # 👇 Add this
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        # 🧮 Basic stats
        extra_context['stats'] = {
            'total_users': UserModel.objects.count(),
            'verified_users': UserModel.objects.filter(is_verified=True).count(),
            'unverified_users': UserModel.objects.filter(is_verified=False).count(),
            'active_users': UserModel.objects.filter(is_active=True).count(),
            'inactive_users': UserModel.objects.filter(is_active=False).count(),
            'tiers': UserModel.objects.values('account_tier').annotate(count=Count('id')),
        }
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(UserDevices)
class UserDevicesAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_id', 'device_os', 'active')
    list_filter = ('active', 'device_os')
    search_fields = ('user__email', 'device_id', 'device_info', 'fcm_token')
    ordering = ('-created_at',)
