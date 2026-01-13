from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, Q
from django import forms
from datetime import timedelta
from .models.users import UserModel
from .models import UserDevices, UserSession, UserBankAccount, CustomerNote, AdminAuditLog


class WalletIssueFilter(admin.SimpleListFilter):
    """Filter to find users with wallet flag issues"""
    title = 'wallet flag issue'
    parameter_name = 'wallet_flag_issue'

    def lookups(self, request, model_admin):
        return (
            ('has_issue', 'Has wallet but flag not set'),
            ('no_issue', 'Flag correctly set'),
        )

    def queryset(self, request, queryset):
        from wallet.models import Wallet

        if self.value() == 'has_issue':
            # Users who have wallet with account number but has_virtual_wallet=False
            return queryset.filter(
                has_virtual_wallet=False,
                wallet__account_number__isnull=False
            )
        elif self.value() == 'no_issue':
            # Users where flag is correctly set
            return queryset.filter(
                Q(has_virtual_wallet=True) | Q(wallet__account_number__isnull=True)
            )


class UserChangeForm(forms.ModelForm):
    """
    Custom form for editing users that makes all fields optional except email.
    This allows staff users to be saved without filling customer-specific fields.
    """
    class Meta:
        model = UserModel
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional except email
        for field_name, field in self.fields.items():
            if field_name != 'email':
                field.required = False


@admin.register(UserModel)
class UserAdmin(BaseUserAdmin):
    model = UserModel
    form = UserChangeForm  # Use custom form that makes fields optional
    list_display = (
        'email', 'phone', 'first_name', 'last_name', 'is_verified', 'is_staff', 'is_active',
        'account_tier', 'support_notes_count'
    )
    list_filter = ('is_active', 'is_staff', 'is_verified', 'account_tier', 'has_bvn', 'has_nin', WalletIssueFilter)
    search_fields = ('email', 'first_name', 'last_name', 'phone', 'bvn', 'nin')
    ordering = ('-created_at',)
    readonly_fields = (
        'last_login', 'created_at', 'updated_at', 'wallet_link',
        'sessions_link', 'bank_accounts_link', 'support_notes_link'
    )

    # Custom actions for support staff
    actions = [
        'verify_users',
        'unverify_users',
        'activate_users',
        'deactivate_users',
        'reset_transaction_pins',
        'reset_passcodes',
        'apply_24hr_restriction',
        'fix_wallet_flags',
        'retry_wallet_creation',
        'create_embedly_wallets',
    ]

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
            ),
            'classes': ('collapse',)
        }),
        (_('NIN Info'), {
            'fields': (
                'nin', 'nin_first_name', 'nin_last_name', 'nin_phone', 'nin_dob',
                'nin_gender', 'nin_marital_status', 'nin_nationality',
                'nin_residential_address', 'nin_state_of_residence', 'has_nin'
            ),
            'classes': ('collapse',)
        }),
        (_('Security'), {
            'fields': (
                'passcode_set', 'transaction_pin_set', 'biometric_enabled',
                'daily_limit', 'per_transaction_limit', 'monthly_limit',
                'limit_restricted_until', 'restricted_limit'
            ),
            'classes': ('collapse',)
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_verified', 'is_staff', 'is_superuser', 'email_verified',
                'groups', 'user_permissions'
            )
        }),
        (_('Wallet Info'), {
            'fields': ('has_virtual_wallet', 'embedly_customer_id', 'embedly_wallet_id')
        }),
        (_('Related Data'), {
            'fields': ('wallet_link', 'sessions_link', 'bank_accounts_link', 'support_notes_link')
        }),
        (_('Important Dates'), {
            'fields': ('last_login', 'created_at', 'updated_at')
        }),
    )

    add_fieldsets = (
        (_('Login Credentials'), {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
            'description': 'Required fields for login'
        }),
        (_('Personal Information'), {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name'),
            'description': 'Optional but recommended for staff identification'
        }),
        (_('Permissions & Access'), {
            'classes': ('wide',),
            'fields': ('is_active', 'is_staff', 'is_superuser'),
            'description': 'Check "Staff status" to grant admin panel access. Check "Superuser" for full admin rights.'
        }),
    )

    # Custom display methods
    def support_notes_count(self, obj):
        count = obj.support_notes.count()
        if count > 0:
            url = reverse('admin:account_customernote_changelist') + f'?user__id__exact={obj.id}'
            return format_html('<a href="{}">{} notes</a>', url, count)
        return '0 notes'
    support_notes_count.short_description = 'Support Notes'

    def wallet_link(self, obj):
        if hasattr(obj, 'wallet'):
            url = reverse('admin:wallet_wallet_change', args=[obj.wallet.id])
            return format_html('<a href="{}">View Wallet</a>', url)
        return 'No wallet'
    wallet_link.short_description = 'Wallet'

    def sessions_link(self, obj):
        count = obj.sessions.filter(is_active=True).count()
        url = reverse('admin:account_usersession_changelist') + f'?user__id__exact={obj.id}'
        return format_html('<a href="{}">{} active sessions</a>', url, count)
    sessions_link.short_description = 'Sessions'

    def bank_accounts_link(self, obj):
        count = obj.bank_accounts.count()
        url = reverse('admin:account_userbankaccount_changelist') + f'?user__id__exact={obj.id}'
        return format_html('<a href="{}">{} bank accounts</a>', url, count)
    bank_accounts_link.short_description = 'Bank Accounts'

    def support_notes_link(self, obj):
        count = obj.support_notes.count()
        url = reverse('admin:account_customernote_changelist') + f'?user__id__exact={obj.id}'
        return format_html('<a href="{}">View {} notes</a>', url, count)
    support_notes_link.short_description = 'Support Notes'

    # Custom actions
    @admin.action(description='✅ Verify selected users')
    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True, verification_status='verified')
        self.message_user(request, f'{updated} users marked as verified.', messages.SUCCESS)

    @admin.action(description='❌ Unverify selected users')
    def unverify_users(self, request, queryset):
        updated = queryset.update(is_verified=False, verification_status='pending')
        self.message_user(request, f'{updated} users marked as unverified.', messages.WARNING)

    @admin.action(description='🟢 Activate selected users')
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated.', messages.SUCCESS)

    @admin.action(description='🔴 Deactivate selected users')
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated.', messages.WARNING)

    @admin.action(description='🔑 Reset transaction PINs')
    def reset_transaction_pins(self, request, queryset):
        count = 0
        for user in queryset:
            user.transaction_pin = None
            user.transaction_pin_set = False
            user.save()
            count += 1
        self.message_user(request, f'{count} transaction PINs reset. Users will need to set new PINs.', messages.SUCCESS)

    @admin.action(description='🔐 Reset passcodes')
    def reset_passcodes(self, request, queryset):
        count = 0
        for user in queryset:
            user.passcode_hash = None
            user.passcode_set = False
            user.save()
            count += 1
        self.message_user(request, f'{count} passcodes reset. Users will need to set new passcodes.', messages.SUCCESS)

    @admin.action(description='⏰ Apply 24-hour restriction')
    def apply_24hr_restriction(self, request, queryset):
        count = 0
        for user in queryset:
            user.apply_24hr_restriction()
            count += 1
        self.message_user(request, f'{count} users now have 24-hour transaction restrictions.', messages.WARNING)

    @admin.action(description='💰 Fix wallet flags for users with wallets')
    def fix_wallet_flags(self, request, queryset):
        """
        Fix has_virtual_wallet flag for users who have wallet data but flag is not set
        """
        from wallet.models import Wallet

        count = 0
        skipped = 0
        for user in queryset:
            try:
                wallet = user.wallet
                # Check if wallet has account number but flag not set
                if wallet.account_number and not user.has_virtual_wallet:
                    user.has_virtual_wallet = True
                    user.save()
                    count += 1
                else:
                    skipped += 1
            except Wallet.DoesNotExist:
                skipped += 1

        if count > 0:
            self.message_user(
                request,
                f'✅ Fixed wallet flag for {count} user(s). {skipped} skipped (no wallet or already fixed).',
                messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                f'No users needed fixing. {skipped} user(s) either have no wallet or flag already set.',
                messages.INFO
            )

    @admin.action(description='🔄 Retry wallet creation (for users with BVN)')
    def retry_wallet_creation(self, request, queryset):
        """
        Retry wallet creation for users who have verified BVN but wallet creation failed
        """
        from wallet.models import Wallet
        from providers.helpers.psb9 import PSB9Client
        from datetime import datetime
        import uuid

        psb9_client = PSB9Client()
        success_count = 0
        failed_count = 0
        skipped_count = 0
        errors = []

        for user in queryset:
            # Check if user has BVN
            if not user.has_bvn or not user.bvn:
                skipped_count += 1
                errors.append(f"{user.email}: No BVN verified")
                continue

            # Check if wallet already has account number
            try:
                wallet = user.wallet
                if wallet.psb9_account_number:
                    skipped_count += 1
                    errors.append(f"{user.email}: Wallet already exists")
                    continue
            except Wallet.DoesNotExist:
                # Create wallet record
                wallet = Wallet.objects.create(user=user)

            # Prepare customer data for 9PSB wallet creation
            try:
                # Gender conversion
                gender_int = 1  # Default to Male
                if user.bvn_gender:
                    gender_str = str(user.bvn_gender).strip().upper()
                    if gender_str in ["FEMALE", "F", "2"]:
                        gender_int = 2
                    elif gender_str in ["MALE", "M", "1"]:
                        gender_int = 1

                # Date formatting
                dob = user.bvn_dob if user.bvn_dob else user.dob
                if isinstance(dob, str):
                    try:
                        from dateutil import parser
                        dob_obj = parser.parse(dob)
                        formatted_dob = dob_obj.strftime('%d/%m/%Y')
                    except:
                        try:
                            dob_obj = datetime.strptime(dob, '%Y-%m-%d')
                            formatted_dob = dob_obj.strftime('%d/%m/%Y')
                        except:
                            formatted_dob = dob
                elif hasattr(dob, 'strftime'):
                    formatted_dob = dob.strftime('%d/%m/%Y')
                else:
                    formatted_dob = str(dob) if dob else ""

                # Names
                first_name = user.bvn_first_name or user.first_name or ""
                middle_name = getattr(user, 'bvn_middle_name', '') or getattr(user, 'middle_name', '') or ""
                other_names_parts = [name.strip() for name in [first_name, middle_name] if name and name.strip()]
                other_names = " ".join(other_names_parts) if other_names_parts else " "

                tracking_ref = f"GIDINEST_ADMIN_RETRY_{user.id}_{uuid.uuid4().hex[:8].upper()}"

                customer_data = {
                    "firstName": first_name,
                    "lastName": user.bvn_last_name or user.last_name,
                    "otherNames": other_names,
                    "phoneNo": user.bvn_phone or user.phone,
                    "email": user.email,
                    "bvn": user.bvn,
                    "gender": gender_int,
                    "dateOfBirth": formatted_dob,
                    "address": user.bvn_residential_address or user.address or "Not Provided",
                    "transactionTrackingRef": tracking_ref
                }

                # Create wallet with 9PSB
                result = psb9_client.open_wallet(customer_data)

                if result.get("status") == "success":
                    wallet_data = result.get("data", {})

                    # Update wallet
                    wallet.provider_version = "v2"
                    wallet.psb9_customer_id = wallet_data.get("customerID") or wallet_data.get("customerId")
                    wallet.psb9_account_number = wallet_data.get("accountNumber")
                    wallet.psb9_wallet_id = wallet_data.get("orderRef") or wallet_data.get("walletId")
                    wallet.account_number = wallet_data.get("accountNumber")
                    wallet.account_name = wallet_data.get("fullName") or wallet_data.get("accountName")
                    wallet.bank = "9PSB"
                    wallet.bank_code = "120001"
                    wallet.save()

                    # Update user flag
                    user.has_virtual_wallet = True
                    user.save()

                    success_count += 1
                else:
                    error_msg = result.get("message", "Unknown error")
                    failed_count += 1
                    errors.append(f"{user.email}: {error_msg}")

            except Exception as e:
                failed_count += 1
                errors.append(f"{user.email}: {str(e)}")

        # Build result message
        message_parts = []
        if success_count > 0:
            message_parts.append(f"✅ {success_count} wallet(s) created successfully")
        if failed_count > 0:
            message_parts.append(f"❌ {failed_count} failed")
        if skipped_count > 0:
            message_parts.append(f"⏭️ {skipped_count} skipped")

        result_message = ". ".join(message_parts)

        if errors:
            result_message += f"\n\nDetails:\n" + "\n".join(errors[:10])  # Show first 10 errors
            if len(errors) > 10:
                result_message += f"\n... and {len(errors) - 10} more"

        if success_count > 0:
            self.message_user(request, result_message, messages.SUCCESS)
        elif failed_count > 0:
            self.message_user(request, result_message, messages.ERROR)
        else:
            self.message_user(request, result_message, messages.INFO)

    @admin.action(description='💳 Create Embedly wallets (for Prembly verified users)')
    def create_embedly_wallets(self, request, queryset):
        """
        Create Embedly wallets for users who have completed Prembly BVN/NIN verification.
        This is for temporary use until 9PSB goes live.
        """
        from wallet.models import Wallet
        from providers.helpers.embedly import EmbedlyClient
        from datetime import datetime

        embedly_client = EmbedlyClient()
        success_count = 0
        failed_count = 0
        skipped_count = 0
        errors = []

        for user in queryset:
            # Check if user has completed Prembly verification (BVN or NIN)
            if not user.has_bvn and not user.has_nin:
                skipped_count += 1
                errors.append(f"{user.email}: No Prembly verification (BVN/NIN required)")
                continue

            # Check if wallet already has Embedly account
            try:
                wallet = user.wallet
                if wallet.embedly_wallet_id and wallet.account_number:
                    skipped_count += 1
                    errors.append(f"{user.email}: Embedly wallet already exists ({wallet.account_number})")
                    continue
            except Wallet.DoesNotExist:
                # Create wallet record
                wallet = Wallet.objects.create(user=user)

            # Create Embedly customer and wallet
            try:
                # Get required user fields
                first_name = user.bvn_first_name or user.first_name or ""
                last_name = user.bvn_last_name or user.last_name or ""
                phone = user.bvn_phone or user.phone or ""

                # Validate required fields
                if not first_name or not last_name:
                    failed_count += 1
                    errors.append(f"{user.email}: Missing first name or last name (required by Embedly)")
                    continue

                if not phone:
                    failed_count += 1
                    errors.append(f"{user.email}: Missing phone number (required by Embedly)")
                    continue

                # Step 1: Get or create Embedly customer
                if user.embedly_customer_id:
                    # User already has Embedly customer, use existing ID
                    customer_id = user.embedly_customer_id
                else:
                    # Create new Embedly customer
                    customer_payload = {
                        "firstName": first_name,
                        "lastName": last_name,
                        "emailAddress": user.email,
                        "mobileNumber": phone,
                    }

                    # Add optional fields if available
                    if user.dob:
                        customer_payload["dob"] = str(user.dob) if hasattr(user.dob, 'strftime') else user.dob

                    if user.address:
                        customer_payload["address"] = user.address

                    if user.state:
                        customer_payload["city"] = user.state

                    if user.country:
                        customer_payload["country"] = user.country

                    # Create customer (pass dict directly, not as named parameter)
                    customer_result = embedly_client.create_customer(customer_payload)

                    if not customer_result.get("success"):
                        error_msg = customer_result.get("message", "Failed to create customer")

                        # Check if customer already exists
                        if "already exist" in error_msg.lower():
                            skipped_count += 1
                            errors.append(f"{user.email}: Embedly customer already exists but customer_id not in database. Please manually retrieve customer_id from Embedly and update user.embedly_customer_id")
                            continue

                        failed_count += 1
                        errors.append(f"{user.email}: {error_msg}")
                        continue

                    customer_id = customer_result["data"]["id"]

                    # Save customer_id to user
                    user.embedly_customer_id = customer_id
                    user.save(update_fields=['embedly_customer_id'])

                # Step 2: Upgrade KYC with BVN (if available)
                if user.bvn:
                    kyc_result = embedly_client.upgrade_kyc(customer_id=customer_id, bvn=user.bvn)
                    if not kyc_result.get("success"):
                        # KYC upgrade failed, but we can still create wallet
                        errors.append(f"{user.email}: Warning - KYC upgrade failed but continuing with wallet creation")

                # Step 3: Create wallet
                wallet_name = f"{first_name} {last_name}".strip() or user.email
                wallet_result = embedly_client.create_wallet(
                    customer_id=customer_id,
                    name=wallet_name,
                    phone=phone
                )

                if not wallet_result.get("success"):
                    error_msg = wallet_result.get("message", "Failed to create wallet")
                    failed_count += 1
                    errors.append(f"{user.email}: {error_msg}")
                    continue

                wallet_data = wallet_result["data"]

                # Step 4: Update wallet record
                wallet.provider_version = "v1"  # Embedly is v1
                wallet.embedly_customer_id = customer_id
                wallet.embedly_wallet_id = wallet_data.get("id")
                wallet.account_number = wallet_data.get("accountNumber")
                wallet.account_name = wallet_data.get("name")
                wallet.bank = wallet_data.get("bankName", "Embedly")
                wallet.bank_code = wallet_data.get("bankCode", "")
                wallet.save()

                # Update user flags
                user.embedly_customer_id = customer_id
                user.embedly_wallet_id = wallet_data.get("id")
                user.has_virtual_wallet = True
                user.save()

                success_count += 1

            except Exception as e:
                failed_count += 1
                errors.append(f"{user.email}: {str(e)}")

        # Build result message
        message_parts = []
        if success_count > 0:
            message_parts.append(f"✅ {success_count} Embedly wallet(s) created successfully")
        if failed_count > 0:
            message_parts.append(f"❌ {failed_count} failed")
        if skipped_count > 0:
            message_parts.append(f"⏭️ {skipped_count} skipped")

        result_message = ". ".join(message_parts)

        if errors:
            result_message += f"\n\nDetails:\n" + "\n".join(errors[:10])
            if len(errors) > 10:
                result_message += f"\n... and {len(errors) - 10} more"

        if success_count > 0:
            self.message_user(request, result_message, messages.SUCCESS)
        elif failed_count > 0:
            self.message_user(request, result_message, messages.ERROR)
        else:
            self.message_user(request, result_message, messages.INFO)

    def save_model(self, request, obj, form, change):
        """
        Override save to handle staff user creation properly.
        Staff users don't need all customer fields filled.
        """
        # If this is a new user (not editing existing)
        if not change:
            # Set defaults for staff users
            if obj.is_staff:
                obj.is_verified = True
                obj.email_verified = True
                obj.account_tier = 'Staff'

                # Set optional fields to prevent null issues
                if not obj.phone:
                    obj.phone = ''
                if not obj.username:
                    obj.username = obj.email.split('@')[0]
                if not obj.first_name:
                    obj.first_name = ''
                if not obj.last_name:
                    obj.last_name = ''

        super().save_model(request, obj, form, change)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        # Basic stats
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
    list_display = ('user', 'device_id', 'device_os', 'active', 'created_at')
    list_filter = ('active', 'device_os')
    search_fields = ('user__email', 'device_id', 'device_info', 'fcm_token')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    def has_add_permission(self, request):
        # Devices are created by the app, not manually
        return False


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = (
        'user_email', 'device_name', 'device_type', 'ip_address',
        'location_display', 'is_active', 'last_active_at', 'created_at'
    )
    list_filter = ('is_active', 'device_type', 'created_at')
    search_fields = ('user__email', 'device_name', 'device_id', 'ip_address', 'location')
    ordering = ('-last_active_at',)
    readonly_fields = ('created_at', 'updated_at', 'last_active_at', 'refresh_token_hash')
    actions = ['deactivate_sessions', 'activate_sessions']

    fieldsets = (
        ('User Info', {
            'fields': ('user',)
        }),
        ('Device Info', {
            'fields': ('device_name', 'device_type', 'device_id')
        }),
        ('Location Info', {
            'fields': ('ip_address', 'location')
        }),
        ('Session Status', {
            'fields': ('is_active', 'expires_at', 'last_active_at', 'refresh_token_hash')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def location_display(self, obj):
        return obj.location[:50] if obj.location else '-'
    location_display.short_description = 'Location'

    @admin.action(description='🔴 Deactivate selected sessions (logout)')
    def deactivate_sessions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} sessions deactivated. Users will be logged out.', messages.SUCCESS)

    @admin.action(description='🟢 Activate selected sessions')
    def activate_sessions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} sessions activated.', messages.SUCCESS)

    def has_add_permission(self, request):
        # Sessions are created by the app during login
        return False


@admin.register(UserBankAccount)
class UserBankAccountAdmin(admin.ModelAdmin):
    list_display = (
        'user_email', 'bank_name', 'account_number', 'account_name',
        'is_verified', 'is_default', 'created_at'
    )
    list_filter = ('is_verified', 'is_default', 'created_at')
    search_fields = ('user__email', 'account_number', 'account_name', 'bank_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    actions = ['verify_accounts', 'unverify_accounts', 'set_as_default']

    fieldsets = (
        ('User Info', {
            'fields': ('user',)
        }),
        ('Bank Details', {
            'fields': ('bank_name', 'bank_code', 'account_number', 'account_name')
        }),
        ('Status', {
            'fields': ('is_verified', 'is_default')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    @admin.action(description='✅ Verify selected bank accounts')
    def verify_accounts(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} bank accounts verified.', messages.SUCCESS)

    @admin.action(description='❌ Unverify selected bank accounts')
    def unverify_accounts(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} bank accounts unverified.', messages.WARNING)

    @admin.action(description='⭐ Set as default account')
    def set_as_default(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, 'Please select only one account to set as default.', messages.ERROR)
            return

        account = queryset.first()
        # Unset all other default accounts for this user
        UserBankAccount.objects.filter(user=account.user).update(is_default=False)
        # Set this one as default
        account.is_default = True
        account.save()
        self.message_user(request, f'Bank account set as default for {account.user.email}.', messages.SUCCESS)


@admin.register(CustomerNote)
class CustomerNoteAdmin(admin.ModelAdmin):
    list_display = (
        'user_email', 'subject', 'category', 'priority', 'status',
        'created_by_email', 'flagged', 'created_at'
    )
    list_filter = ('status', 'priority', 'category', 'flagged', 'internal_only', 'created_at')
    search_fields = ('user__email', 'subject', 'note', 'created_by__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'resolved_at')
    actions = ['mark_as_resolved', 'mark_as_closed', 'flag_notes', 'unflag_notes']

    fieldsets = (
        ('User & Staff', {
            'fields': ('user', 'created_by')
        }),
        ('Note Details', {
            'fields': ('category', 'priority', 'status', 'subject', 'note')
        }),
        ('Resolution', {
            'fields': ('resolution', 'resolved_by', 'resolved_at'),
            'classes': ('collapse',)
        }),
        ('Options', {
            'fields': ('internal_only', 'flagged')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def user_email(self, obj):
        url = reverse('admin:account_usermodel_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_email.short_description = 'Customer'
    user_email.admin_order_field = 'user__email'

    def created_by_email(self, obj):
        if obj.created_by:
            return obj.created_by.email
        return '-'
    created_by_email.short_description = 'Created By'
    created_by_email.admin_order_field = 'created_by__email'

    @admin.action(description='✅ Mark as Resolved')
    def mark_as_resolved(self, request, queryset):
        for note in queryset:
            note.status = 'resolved'
            note.resolved_by = request.user
            note.resolved_at = timezone.now()
            note.save()
        count = queryset.count()
        self.message_user(request, f'{count} notes marked as resolved.', messages.SUCCESS)

    @admin.action(description='🔒 Mark as Closed')
    def mark_as_closed(self, request, queryset):
        for note in queryset:
            note.status = 'closed'
            if not note.resolved_by:
                note.resolved_by = request.user
            if not note.resolved_at:
                note.resolved_at = timezone.now()
            note.save()
        count = queryset.count()
        self.message_user(request, f'{count} notes marked as closed.', messages.SUCCESS)

    @admin.action(description='🚩 Flag notes for attention')
    def flag_notes(self, request, queryset):
        updated = queryset.update(flagged=True)
        self.message_user(request, f'{updated} notes flagged.', messages.WARNING)

    @admin.action(description='Remove flag')
    def unflag_notes(self, request, queryset):
        updated = queryset.update(flagged=False)
        self.message_user(request, f'{updated} notes unflagged.', messages.SUCCESS)

    def save_model(self, request, obj, form, change):
        # Auto-set created_by if creating new note
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

        # Log the action
        action = 'update' if change else 'create'
        AdminAuditLog.log_action(
            user=request.user,
            action=action,
            obj=obj,
            description=f"{'Updated' if change else 'Created'} customer note for {obj.user.email}",
            request=request
        )


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    list_display = (
        'timestamp', 'user_email', 'action_colored', 'action_description',
        'object_repr', 'ip_address'
    )
    list_filter = ('action', 'timestamp', 'content_type')
    search_fields = ('user__email', 'action_description', 'object_repr', 'ip_address')
    ordering = ('-timestamp',)
    readonly_fields = (
        'user', 'action', 'action_description', 'content_type', 'object_id',
        'object_repr', 'changes', 'ip_address', 'user_agent', 'timestamp',
        'changes_display'
    )
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Action Details', {
            'fields': ('timestamp', 'user', 'action', 'action_description')
        }),
        ('Object Information', {
            'fields': ('content_type', 'object_id', 'object_repr')
        }),
        ('Changes', {
            'fields': ('changes_display',),
            'classes': ('collapse',)
        }),
        ('Request Metadata', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )

    def user_email(self, obj):
        if obj.user:
            url = reverse('admin:account_usermodel_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return 'System'
    user_email.short_description = 'Admin User'
    user_email.admin_order_field = 'user__email'

    def action_colored(self, obj):
        colors = {
            'create': 'green',
            'update': 'blue',
            'delete': 'red',
            'view': 'gray',
            'custom': 'orange',
        }
        color = colors.get(obj.action, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_action_display()
        )
    action_colored.short_description = 'Action'
    action_colored.admin_order_field = 'action'

    def changes_display(self, obj):
        if obj.changes:
            import json
            try:
                formatted = json.dumps(obj.changes, indent=2)
                return format_html(
                    '<pre style="background: #f5f5f5; padding: 10px; overflow: auto;">{}</pre>',
                    formatted
                )
            except (TypeError, ValueError) as e:
                return format_html(
                    '<span style="color: red;">Error displaying changes: {}</span>',
                    str(e)
                )
        return 'No changes recorded'
    changes_display.short_description = 'Field Changes'

    def has_add_permission(self, request):
        # Audit logs are created automatically, not manually
        return False

    def has_change_permission(self, request, obj=None):
        # Audit logs are read-only
        return False

    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete audit logs (for cleanup)
        return request.user.is_superuser

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        # Statistics
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)

        total_logs = AdminAuditLog.objects.count()
        logs_24h = AdminAuditLog.objects.filter(timestamp__gte=last_24h).count()
        logs_7d = AdminAuditLog.objects.filter(timestamp__gte=last_7d).count()

        # Action breakdown
        action_counts = AdminAuditLog.objects.filter(
            timestamp__gte=last_7d
        ).values('action').annotate(count=Count('id')).order_by('action')

        # Most active admins
        active_admins = AdminAuditLog.objects.filter(
            timestamp__gte=last_7d
        ).values('user__email').annotate(count=Count('id')).order_by('-count')[:5]

        extra_context['audit_stats'] = {
            'total_logs': total_logs,
            'logs_24h': logs_24h,
            'logs_7d': logs_7d,
            'action_counts': {item['action']: item['count'] for item in action_counts},
            'active_admins': active_admins,
        }

        return super().changelist_view(request, extra_context=extra_context)
