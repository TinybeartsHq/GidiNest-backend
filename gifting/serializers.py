# gifting/serializers.py
from decimal import Decimal
from rest_framework import serializers
from django.conf import settings
from django.utils import timezone
from gifting.models import BabyFund, Gift


class GiftSerializer(serializers.ModelSerializer):
    """Read-only serializer for individual gifts (contributions)."""

    class Meta:
        model = Gift
        fields = [
            'id', 'amount', 'fee_amount', 'net_amount', 'status',
            'contributor_name', 'message', 'created_at',
        ]
        read_only_fields = fields


class BabyFundSerializer(serializers.ModelSerializer):
    """Full serializer for fund owners — create + manage."""
    total_gifts = serializers.SerializerMethodField()
    gift_count = serializers.SerializerMethodField()
    target_reached = serializers.SerializerMethodField()
    fund_url = serializers.SerializerMethodField()

    class Meta:
        model = BabyFund
        fields = [
            'id', 'token', 'name', 'description', 'target_amount',
            'due_date', 'balance', 'thank_you_message', 'show_contributors',
            'status', 'is_active', 'created_at', 'updated_at',
            'total_gifts', 'gift_count', 'target_reached', 'fund_url',
        ]
        read_only_fields = [
            'id', 'token', 'balance', 'created_at', 'updated_at',
            'total_gifts', 'gift_count', 'target_reached', 'fund_url',
        ]

    def get_total_gifts(self, obj):
        return str(obj.get_total_gifts())

    def get_gift_count(self, obj):
        return obj.get_gift_count()

    def get_target_reached(self, obj):
        return obj.is_target_reached()

    def get_fund_url(self, obj):
        base_url = getattr(settings, 'FRONTEND_URL', 'https://gidinest.com')
        return f"{base_url}/fund/{obj.token}"


class BabyFundPublicSerializer(serializers.ModelSerializer):
    """
    Public serializer — shown to gift senders (no auth required).
    Hides balance and sensitive owner info.
    """
    owner_first_name = serializers.CharField(source='user.first_name', read_only=True)
    total_raised = serializers.SerializerMethodField()
    gift_count = serializers.SerializerMethodField()
    target_reached = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    can_accept_gifts = serializers.SerializerMethodField()
    recent_contributors = serializers.SerializerMethodField()

    class Meta:
        model = BabyFund
        fields = [
            'token', 'name', 'description', 'target_amount', 'due_date',
            'thank_you_message', 'show_contributors',
            'owner_first_name', 'total_raised', 'gift_count',
            'target_reached', 'progress_percentage',
            'can_accept_gifts', 'recent_contributors',
        ]

    def get_total_raised(self, obj):
        return str(obj.get_total_gifts())

    def get_gift_count(self, obj):
        return obj.get_gift_count()

    def get_target_reached(self, obj):
        return obj.is_target_reached()

    def get_progress_percentage(self, obj):
        if not obj.target_amount or obj.target_amount == 0:
            return 0
        total = obj.get_total_gifts()
        return min(round(float(total / obj.target_amount) * 100, 2), 100)

    def get_can_accept_gifts(self, obj):
        return obj.is_active and obj.status == 'active'

    def get_recent_contributors(self, obj):
        if obj.show_contributors == 'anonymous':
            return []

        gifts = obj.gifts.filter(status='completed').order_by('-created_at')[:10]
        result = []
        for gift in gifts:
            entry = {
                'name': gift.contributor_name or 'Anonymous',
                'message': gift.message,
                'created_at': gift.created_at,
            }
            if obj.show_contributors == 'public':
                entry['amount'] = str(gift.amount)
            result.append(entry)
        return result
