# dashboard/views.py
"""
Dashboard Views for Mobile App V2 API
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, Q
from decimal import Decimal
from datetime import datetime, timedelta

from wallet.models import Wallet, WalletTransaction
from savings.models import SavingsGoalModel, SavingsGoalTransaction


class DashboardView(APIView):
    """
    Unified Dashboard API
    Returns all dashboard data in one optimized request

    GET /api/v2/dashboard/

    Returns:
    - User info (name, email, tier, flags)
    - Wallet info (balance, account number)
    - Quick stats (total savings, active goals, monthly contributions)
    - Recent transactions (last 5)
    - Active savings goals
    - Restriction status

    Cached for 30 seconds using Redis
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Try cache first
        cache_key = f'dashboard_{user.id}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response({
                "success": True,
                "data": cached_data
            }, status=status.HTTP_200_OK)

        # Build dashboard data
        data = {
            "user": self._get_user_data(user),
            "wallet": self._get_wallet_data(user),
            "quick_stats": self._get_quick_stats(user),
            "recent_transactions": self._get_recent_transactions(user),
            "savings_goals": self._get_savings_goals(user),
            "restrictions": self._get_restriction_status(user)
        }

        # Cache for 30 seconds
        cache.set(cache_key, data, 30)

        return Response({
            "success": True,
            "data": data
        }, status=status.HTTP_200_OK)

    def _get_user_data(self, user):
        """Get user profile data"""
        return {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone or "",
            "account_tier": user.account_tier or "Tier 1",
            "has_passcode": getattr(user, 'passcode_set', False),
            "has_pin": getattr(user, 'transaction_pin_set', False),
            "is_verified": user.is_verified,
            "verification_method": getattr(user, 'verification_method', None),
            "biometric_enabled": getattr(user, 'biometric_enabled', False)
        }

    def _get_wallet_data(self, user):
        """Get wallet balance and info"""
        try:
            wallet = user.wallet
            return {
                "balance": str(wallet.balance),
                "account_number": wallet.account_number or "",
                "bank_name": wallet.bank or "Embedly Virtual Bank",
                "bank_code": wallet.bank_code or "",
                "account_name": wallet.account_name or f"{user.first_name} {user.last_name}",
                "currency": wallet.currency or "NGN"
            }
        except ObjectDoesNotExist:
            # User doesn't have a wallet yet
            return None

    def _get_quick_stats(self, user):
        """Calculate quick statistics"""
        # Get all active savings goals
        active_goals = SavingsGoalModel.objects.filter(
            user=user,
            status='active'
        )

        # Total savings across all goals
        total_savings = active_goals.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        # Active goals count
        active_goals_count = active_goals.count()

        # This month's contributions (from goal transactions)
        this_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month_contributions = SavingsGoalTransaction.objects.filter(
            goal__user=user,
            transaction_type='contribution',
            timestamp__gte=this_month_start
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        return {
            "total_savings": str(total_savings),
            "active_goals": active_goals_count,
            "this_month_contributions": str(this_month_contributions)
        }

    def _get_recent_transactions(self, user):
        """Get last 5 transactions (wallet + goal transactions)"""
        transactions = []

        # Get wallet transactions
        try:
            wallet = user.wallet
            wallet_txns = WalletTransaction.objects.filter(
                wallet=wallet
            ).order_by('-created_at')[:5]

            for txn in wallet_txns:
                transactions.append({
                    "id": str(txn.id),
                    "type": txn.transaction_type,  # 'credit' or 'debit'
                    "amount": str(txn.amount),
                    "description": txn.description or "Wallet transaction",
                    "sender_name": txn.sender_name,
                    "sender_account": txn.sender_account,
                    "external_reference": txn.external_reference,
                    "created_at": txn.created_at.isoformat(),
                    "source": "wallet"
                })
        except ObjectDoesNotExist:
            pass  # No wallet yet

        # Sort by date (most recent first)
        transactions.sort(key=lambda x: x['created_at'], reverse=True)

        # Return only last 5
        return transactions[:5]

    def _get_savings_goals(self, user):
        """Get active savings goals"""
        active_goals = SavingsGoalModel.objects.filter(
            user=user,
            status='active'
        ).order_by('-created_at')

        goals = []
        for goal in active_goals:
            # Calculate progress percentage
            if goal.target_amount > 0:
                progress = (goal.amount / goal.target_amount) * 100
            else:
                progress = 0

            goals.append({
                "id": str(goal.id),
                "name": goal.name,
                "target_amount": str(goal.target_amount),
                "current_amount": str(goal.amount),
                "progress_percentage": round(float(progress), 2),
                "interest_rate": str(goal.interest_rate),
                "accrued_interest": str(goal.accrued_interest),
                "status": goal.status,
                "created_at": goal.created_at.isoformat()
            })

        return goals

    def _get_restriction_status(self, user):
        """Check if user has active restrictions"""
        # Check if user has restriction methods
        is_restricted = False
        restricted_until = None
        restricted_limit = None

        if hasattr(user, 'limit_restricted_until') and user.limit_restricted_until:
            # Check if restriction is still active
            if user.limit_restricted_until > datetime.now().astimezone():
                is_restricted = True
                restricted_until = user.limit_restricted_until.isoformat()
                restricted_limit = user.restricted_limit if hasattr(user, 'restricted_limit') else None

        return {
            "is_restricted": is_restricted,
            "restricted_until": restricted_until,
            "restricted_limit": restricted_limit
        }
