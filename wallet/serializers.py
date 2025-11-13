from rest_framework import serializers
from django.utils import timezone
from wallet.models import Wallet, WalletTransaction, PaymentLink, PaymentLinkContribution


class WalletBalanceSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying the wallet balance.
    """
    class Meta:
        model = Wallet
        fields = ['balance', 'currency','account_number','bank','bank_code','account_name']
        read_only_fields = ['balance', 'currency','account_number','bank','bank_code','account_name']


class WalletTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for WalletTransaction model.
    """

    wallet_account_number = serializers.CharField(source='wallet.account_number')

    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'wallet_account_number', 'transaction_type', 'amount', 'description',
            'sender_name', 'sender_account', 'created_at', 'updated_at'
        ]


class PaymentLinkContributionSerializer(serializers.ModelSerializer):
    """
    Serializer for PaymentLinkContribution - for displaying contributor information.
    """
    class Meta:
        model = PaymentLinkContribution
        fields = [
            'id', 'amount', 'contributor_name', 'contributor_email',
            'message', 'status', 'created_at'
        ]
        read_only_fields = fields


class PaymentLinkSerializer(serializers.ModelSerializer):
    """
    Serializer for PaymentLink model - for creating and managing payment links.
    """
    # Computed fields
    total_raised = serializers.SerializerMethodField()
    contributor_count = serializers.SerializerMethodField()
    target_reached = serializers.SerializerMethodField()
    link_url = serializers.SerializerMethodField()
    bank_details = serializers.SerializerMethodField()
    payment_reference = serializers.SerializerMethodField()

    # Nested fields
    savings_goal_name = serializers.CharField(source='savings_goal.name', read_only=True)
    savings_goal_target = serializers.DecimalField(source='savings_goal.target_amount', max_digits=15, decimal_places=2, read_only=True)
    savings_goal_current = serializers.DecimalField(source='savings_goal.amount', max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = PaymentLink
        fields = [
            'id', 'token', 'link_type', 'savings_goal', 'savings_goal_name',
            'savings_goal_target', 'savings_goal_current', 'event_name', 'event_date',
            'event_description', 'target_amount', 'allow_custom_amount', 'fixed_amount',
            'show_contributors', 'custom_message', 'description', 'is_active',
            'expires_at', 'one_time_use', 'used', 'created_at', 'updated_at',
            'total_raised', 'contributor_count', 'target_reached', 'link_url',
            'bank_details', 'payment_reference'
        ]
        read_only_fields = ['id', 'token', 'created_at', 'updated_at', 'used',
                            'total_raised', 'contributor_count', 'target_reached',
                            'link_url', 'bank_details', 'payment_reference']

    def get_total_raised(self, obj):
        return str(obj.get_total_raised())

    def get_contributor_count(self, obj):
        return obj.get_contributor_count()

    def get_target_reached(self, obj):
        return obj.is_target_reached()

    def get_link_url(self, obj):
        from django.conf import settings
        base_url = getattr(settings, 'FRONTEND_URL', 'https://gidinest.com')
        return f"{base_url}/pay/{obj.token}"

    def get_bank_details(self, obj):
        """
        Return bank account details for contributors to make payments.
        This is populated from the goal owner's wallet.
        """
        try:
            wallet = obj.user.wallet
            return {
                'bank_name': wallet.bank or '',
                'bank_code': wallet.bank_code or '',
                'account_number': wallet.account_number or '',
                'account_name': wallet.account_name or '',
                'currency': wallet.currency or 'NGN'
            }
        except Exception:
            return {
                'bank_name': '',
                'bank_code': '',
                'account_number': '',
                'account_name': '',
                'currency': 'NGN'
            }

    def get_payment_reference(self, obj):
        """
        Generate a unique payment reference for this payment link.
        Format: PL-{token}-{timestamp}
        Contributors MUST use this reference when making payments.
        """
        import time
        timestamp = int(time.time())
        return f"PL-{obj.token}-{timestamp}"

    def validate(self, data):
        # Validate link_type specific requirements
        link_type = data.get('link_type')

        if link_type == 'savings_goal':
            if not data.get('savings_goal'):
                raise serializers.ValidationError({
                    'savings_goal': 'Savings goal is required for savings_goal link type'
                })

        if link_type == 'event':
            if not data.get('event_name'):
                raise serializers.ValidationError({
                    'event_name': 'Event name is required for event link type'
                })

        # Validate fixed amount
        if not data.get('allow_custom_amount', True) and not data.get('fixed_amount'):
            raise serializers.ValidationError({
                'fixed_amount': 'Fixed amount is required when custom amounts are not allowed'
            })

        return data


class PaymentLinkPublicSerializer(serializers.ModelSerializer):
    """
    Public serializer for payment link - shows info to contributors (non-owners).
    Hides sensitive owner information.
    """
    # Computed fields
    total_raised = serializers.SerializerMethodField()
    contributor_count = serializers.SerializerMethodField()
    target_reached = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    can_accept_payments = serializers.SerializerMethodField()
    recent_contributors = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    bank_details = serializers.SerializerMethodField()
    payment_reference = serializers.SerializerMethodField()

    # Nested fields
    savings_goal_name = serializers.CharField(source='savings_goal.name', read_only=True)
    savings_goal_target = serializers.DecimalField(source='savings_goal.target_amount', max_digits=15, decimal_places=2, read_only=True)
    savings_goal_current = serializers.DecimalField(source='savings_goal.amount', max_digits=15, decimal_places=2, read_only=True)
    savings_goal_description = serializers.CharField(source='savings_goal.description', read_only=True)

    class Meta:
        model = PaymentLink
        fields = [
            'token', 'link_type', 'savings_goal_name', 'savings_goal_target',
            'savings_goal_current', 'savings_goal_description', 'event_name',
            'event_date', 'event_description', 'target_amount', 'allow_custom_amount',
            'fixed_amount', 'show_contributors', 'custom_message', 'description',
            'total_raised', 'contributor_count', 'target_reached', 'is_expired',
            'can_accept_payments', 'recent_contributors', 'progress_percentage',
            'bank_details', 'payment_reference'
        ]

    def get_total_raised(self, obj):
        return str(obj.get_total_raised())

    def get_contributor_count(self, obj):
        return obj.get_contributor_count()

    def get_target_reached(self, obj):
        return obj.is_target_reached()

    def get_is_expired(self, obj):
        if not obj.expires_at:
            return False
        return timezone.now() > obj.expires_at

    def get_can_accept_payments(self, obj):
        if not obj.is_active:
            return False
        if obj.one_time_use and obj.used:
            return False
        if obj.expires_at and timezone.now() > obj.expires_at:
            return False
        return True

    def get_progress_percentage(self, obj):
        if not obj.target_amount or obj.target_amount == 0:
            return 0
        total_raised = obj.get_total_raised()
        percentage = (total_raised / obj.target_amount) * 100
        return min(round(percentage, 2), 100)  # Cap at 100%

    def get_recent_contributors(self, obj):
        # Respect privacy settings
        if obj.show_contributors == 'anonymous':
            return []

        # Get recent contributions (last 10)
        contributions = obj.contributions.filter(status='completed').order_by('-created_at')[:10]

        result = []
        for contrib in contributions:
            if obj.show_contributors == 'public':
                result.append({
                    'name': contrib.contributor_name or 'Anonymous',
                    'amount': str(contrib.amount),
                    'message': contrib.message,
                    'created_at': contrib.created_at
                })
            elif obj.show_contributors == 'private':
                result.append({
                    'name': contrib.contributor_name or 'Anonymous',
                    'message': contrib.message,
                    'created_at': contrib.created_at
                })

        return result

    def get_bank_details(self, obj):
        """
        Return bank account details for contributors to make payments.
        This is populated from the goal owner's wallet.
        """
        try:
            wallet = obj.user.wallet
            return {
                'bank_name': wallet.bank or '',
                'bank_code': wallet.bank_code or '',
                'account_number': wallet.account_number or '',
                'account_name': wallet.account_name or '',
                'currency': wallet.currency or 'NGN'
            }
        except Exception:
            return {
                'bank_name': '',
                'bank_code': '',
                'account_number': '',
                'account_name': '',
                'currency': 'NGN'
            }

    def get_payment_reference(self, obj):
        """
        Generate a unique payment reference for this payment link.
        Format: PL-{token}-{timestamp}
        Contributors MUST use this reference when making payments.
        """
        import time
        timestamp = int(time.time())
        return f"PL-{obj.token}-{timestamp}"
