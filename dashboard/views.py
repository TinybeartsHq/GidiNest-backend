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
from django.utils import timezone

from wallet.models import Wallet, WalletTransaction
from savings.models import SavingsGoalModel, SavingsGoalTransaction
from onboarding.models import OnboardingProfile


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
            "dashboard_type": self._get_dashboard_type(user),
            "user": self._get_user_data(user),
            "wallet": self._get_wallet_data(user),
            "quick_stats": self._get_quick_stats(user),
            "recent_transactions": self._get_recent_transactions(user),
            "savings_goals": self._get_savings_goals(user),
            "restrictions": self._get_restriction_status(user),
            "personalized_data": self._get_personalized_data(user)
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

    def _get_dashboard_type(self, user):
        """Determine dashboard type based on onboarding status"""
        try:
            onboarding = user.onboarding_profile
            if onboarding and onboarding.onboarding_completed:
                return "personalized"
        except ObjectDoesNotExist:
            pass
        return "basic"

    def _get_personalized_data(self, user):
        """
        Get personalized dashboard data based on onboarding profile.
        Returns None for users without onboarding (web users).
        """
        try:
            onboarding = user.onboarding_profile

            if not onboarding or not onboarding.onboarding_completed:
                return None

            # Calculate journey-specific data
            personalized_data = {
                "journey_type": onboarding.journey_type,
                "has_onboarding": True
            }

            # Pregnant users - countdown and trimester tracking
            if onboarding.journey_type == 'pregnant' and onboarding.due_date:
                days_until_due = (onboarding.due_date - timezone.now().date()).days
                weeks_pregnant = onboarding.pregnancy_weeks or 0

                # Determine trimester
                if weeks_pregnant <= 13:
                    trimester = 1
                    trimester_label = "First Trimester"
                elif weeks_pregnant <= 27:
                    trimester = 2
                    trimester_label = "Second Trimester"
                else:
                    trimester = 3
                    trimester_label = "Third Trimester"

                personalized_data.update({
                    "due_date": onboarding.due_date.isoformat(),
                    "days_until_due": days_until_due,
                    "weeks_pregnant": weeks_pregnant,
                    "trimester": trimester,
                    "trimester_label": trimester_label,
                    "countdown_message": self._get_countdown_message(days_until_due, weeks_pregnant)
                })

            # New mom users - baby age tracking
            elif onboarding.journey_type == 'new_mom' and onboarding.birth_date:
                days_since_birth = (timezone.now().date() - onboarding.birth_date).days
                months_old = days_since_birth // 30

                personalized_data.update({
                    "birth_date": onboarding.birth_date.isoformat(),
                    "days_since_birth": days_since_birth,
                    "months_old": months_old,
                    "baby_age_message": self._get_baby_age_message(months_old)
                })

            # Trying to conceive users
            elif onboarding.journey_type == 'trying' and onboarding.conception_date:
                days_until_target = (onboarding.conception_date - timezone.now().date()).days

                personalized_data.update({
                    "conception_date": onboarding.conception_date.isoformat(),
                    "days_until_target": days_until_target,
                    "trying_message": self._get_trying_message(days_until_target)
                })

            # Add planning preferences
            personalized_data.update({
                "hospital_plan": onboarding.hospital_plan,
                "location": onboarding.location,
                "baby_essentials_preference": onboarding.baby_essentials_preference
            })

            return personalized_data

        except ObjectDoesNotExist:
            # No onboarding profile (web users)
            return None

    def _get_countdown_message(self, days_until_due, weeks_pregnant):
        """Generate personalized countdown message for pregnant users"""
        if days_until_due <= 0:
            return "Your due date is here! Wishing you all the best! 💕"
        elif days_until_due <= 7:
            return f"Your baby could arrive any day now! Just {days_until_due} days to go! 🎉"
        elif days_until_due <= 30:
            return f"You're in the home stretch! {days_until_due} days until your due date! 💪"
        elif weeks_pregnant <= 13:
            return f"You're {weeks_pregnant} weeks along in your first trimester! {days_until_due} days to go! 🌸"
        elif weeks_pregnant <= 27:
            return f"You're {weeks_pregnant} weeks along in your second trimester! {days_until_due} days to go! 🌺"
        else:
            return f"You're {weeks_pregnant} weeks along in your third trimester! {days_until_due} days to go! 🌟"

    def _get_baby_age_message(self, months_old):
        """Generate personalized message for new moms"""
        if months_old == 0:
            return "Congratulations on your precious newborn! 👶"
        elif months_old == 1:
            return "Your baby is 1 month old! Time flies! 💕"
        elif months_old < 6:
            return f"Your baby is {months_old} months old! They're growing so fast! 🌟"
        elif months_old < 12:
            return f"Your baby is {months_old} months old! Almost a year! 🎉"
        else:
            return f"Your little one is {months_old} months old! What a journey! 💖"

    def _get_trying_message(self, days_until_target):
        """Generate personalized message for trying to conceive users"""
        if days_until_target <= 0:
            return "You've reached your target date! Best wishes on your journey! 💕"
        elif days_until_target <= 30:
            return f"Your target date is approaching! {days_until_target} days to go! 🌸"
        else:
            return f"Stay positive on your journey! {days_until_target} days until your target date! 💫"
