# savings/views.py
from decimal import Decimal
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.helpers.response import success_response, validation_error_response, error_response
from wallet.models import Wallet, WalletTransaction
from .models import SavingsGoalModel, SavingsGoalTransaction
from .serializers import SavingsGoalSerializer, SavingsGoalTransactionSerializer
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction  
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce, ExtractMonth, ExtractYear
from django.utils import timezone
from datetime import timedelta, datetime
from calendar import month_abbr
from collections import defaultdict
from dateutil.relativedelta import relativedelta  



class SavingsGoalAPIView(APIView):
    """
    API endpoint for creating and retrieving user savings goals.
    - POST: Create a new savings goal.
    - GET: Get all savings goals for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Get all savings goals for the authenticated user.
        """
        user_goals = SavingsGoalModel.objects.filter(user=request.user)
        serializer = SavingsGoalSerializer(user_goals, many=True)
        return success_response(serializer.data)

    def post(self, request, *args, **kwargs):
        """
        Create a new savings goal for the authenticated user.
        Required fields: 'name', 'target_amount'
        Optional fields: 'amount' (defaults to 0), 'status' (defaults to 'active')
        """
        serializer = SavingsGoalSerializer(data=request.data)
        if serializer.is_valid():
            # Associate the goal with the authenticated user
            serializer.save(user=request.user)
            return success_response(message= "Savings goal created successfully", data = serializer.data )
        return validation_error_response(serializer.errors)

    def delete(self, request, *args, **kwargs):
        """
        Delete a specific savings goal for the authenticated user.
        Requires the goal ID as a URL parameter.
        """
        goal_id = kwargs.get('goal_id')
        try:
            goal = SavingsGoalModel.objects.get(id=goal_id, user=request.user)
            if(goal.amount > 0):
                return error_response("Cannot delete a savings goal with a non-zero amount. Please withdraw funds before deleting.")
            goal.delete()
            return success_response(message="Savings goal deleted successfully.")
        except SavingsGoalModel.DoesNotExist:
            return Response(
                {"detail": "Savings goal not found."},
                status=status.HTTP_404_NOT_FOUND
            )
    


class SavingsGoalContributeWithdrawAPIView(APIView):
    """
    API endpoint to contribute to or withdraw from a specific savings goal.
    Expects 'goal_id', 'amount', 'transaction_type' ('contribution' or 'withdrawal').
    This involves moving funds between the user's main Wallet and the SavingsGoal.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        goal_id = request.data.get('goal_id')
        amount = request.data.get('amount')
        transaction_type = request.data.get('transaction_type') # 'contribution' or 'withdrawal'
        description = request.data.get('description', '')
        

        if not all([goal_id, amount, transaction_type]):
            return validation_error_response({"detail": "goal_id, amount, and transaction_type are required."})

        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                raise ValueError("Amount must be a positive number.")
        except (ValueError, TypeError):
            return validation_error_response({"detail": "Invalid amount provided."})

        if transaction_type not in ['contribution', 'withdrawal']:
            return validation_error_response({"detail": "Invalid transaction_type. Must be 'contribution' or 'withdrawal'."})

        try:
            goal = SavingsGoalModel.objects.get(id=goal_id, user=request.user)
            wallet = request.user.wallet # Get the user's central wallet
        except SavingsGoalModel.DoesNotExist:
            return error_response("Savings goal not found or does not belong to user.")
        except ObjectDoesNotExist: # For wallet not found
            return error_response( "User wallet not found. Please contact support.")

        with transaction.atomic(): # Ensure both operations (wallet & goal update) are atomic
            
            try:
                if transaction_type == 'contribution':
                    # Create a WalletTransaction entry (assuming 'credit' is the event type for deposits)
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_type='debit',  # This is a debit to the wallet
                        amount=amount,
                        description=f"Deposit into {goal.name} savings goal.",
                
                    )
                    wallet.withdraw(amount) # Deduct from main wallet

                    goal.amount += amount # Add to goal's tracker
                else: # withdrawal
                    if goal.amount < amount:
                        return error_response("Insufficient funds in savings goal.")
                    goal.amount -= amount # Deduct from goal's tracker

                    # Create a WalletTransaction entry (assuming 'credit' is the event type for deposits)
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_type='credit',  # This is a credit to the wallet
                        amount=amount,
                        description=f"Withrawal from {goal.name} savings goal.",
                
                    )

                    wallet.deposit(amount) # Add to main wallet

                goal.save(update_fields=['amount', 'updated_at']) # Save goal's updated amount

                # Record the transaction for this specific goal
                SavingsGoalTransaction.objects.create(
                    goal=goal,
                    transaction_type=transaction_type,
                    amount=amount,
                    description=description,
                    goal_current_amount=goal.amount # Snapshot of goal's amount after transaction
                )

                return success_response(message = f"{transaction_type.capitalize()} successful for goal: {goal.name}")

            except ValueError as e:
               print(e)
               return error_response(f"An error occurred during transaction: {e}")
            except Exception as e:
                print(e)
                # Catch any other unexpected errors during atomic transaction
                return error_response(f"An error occurred during transaction: {e}")


class UserAllSavingsHistoryAPIView(APIView):
    """
    API endpoint to retrieve ALL savings goal transactions for the authenticated user
    across all their goals.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Get all SavingsGoalTransaction objects belonging to the user's goals
        user_goals_transactions = SavingsGoalTransaction.objects.filter(goal__user=request.user)
        serializer = SavingsGoalTransactionSerializer(user_goals_transactions, many=True)
        return success_response(serializer.data)


class SpecificSavingsGoalHistoryAPIView(APIView):
    """
    API endpoint to retrieve the transaction history for a specific savings goal.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, goal_id, *args, **kwargs):
        try:
            goal = SavingsGoalModel.objects.get(id=goal_id, user=request.user)
        except SavingsGoalModel.DoesNotExist:
            return error_response({"detail": "Savings goal not found or does not belong to user."}, status=status.HTTP_404_NOT_FOUND)

        goal_transactions = goal.transactions.all() # Access via related_name
        serializer = SavingsGoalTransactionSerializer(goal_transactions, many=True)
        return success_response(serializer.data)


class SavingsDashboardAnalyticsAPIView(APIView):
    """
    API endpoint to provide dashboard analytics for user savings.
    Includes:
    - Total Savings Balance (wallet + all savings goals)
    - Active Savings Goals count
    - Monthly Contributions (sum of contributions in the current month)
    - Goals Achieved (Year-To-Date)
    - Savings Growth Chart Data (last 12 months)
    - Goal Progress Chart Data
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        analytics_data = {}
        now = timezone.now()

        # Get wallet balance
        try:
            wallet = user.wallet
            wallet_balance = wallet.balance
            currency_symbol = '₦' if wallet.currency == 'NGN' else wallet.currency
        except Wallet.DoesNotExist:
            wallet_balance = Decimal('0.00')
            currency_symbol = '₦'

        # Calculate total savings balance (wallet + all savings goals)
        total_goals_amount = SavingsGoalModel.objects.filter(
            user=user,
            status__in=['active', 'completed']  # Include active and completed goals
        ).aggregate(
            total_sum=Coalesce(Sum('amount'), Decimal('0.00'))
        )['total_sum']
        
        total_savings_balance = wallet_balance + total_goals_amount
        analytics_data['total_savings_balance'] = str(total_savings_balance)
        analytics_data['currency'] = currency_symbol

        # Active savings goals count
        active_goals_count = SavingsGoalModel.objects.filter(user=user, status='active').count()
        analytics_data['active_savings_goals'] = active_goals_count

        # Monthly contributions (current month)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_contributions = SavingsGoalTransaction.objects.filter(
            goal__user=user, 
            transaction_type='contribution',
            timestamp__gte=start_of_month
        ).aggregate(
            total_sum=Coalesce(Sum('amount'), Decimal('0.00'))  
        )['total_sum']
        analytics_data['monthly_contributions'] = str(monthly_contributions)

        # Goals achieved YTD
        start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        goals_achieved_ytd = SavingsGoalModel.objects.filter(
            user=user,
            status='completed',
            updated_at__gte=start_of_year
        ).count()
        analytics_data['goals_achieved_ytd'] = goals_achieved_ytd

        # Monthly contributions change percent
        last_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
        last_month_end = start_of_month - timedelta(microseconds=1)  

        prev_month_contributions = SavingsGoalTransaction.objects.filter(
            goal__user=user,
            transaction_type='contribution',
            timestamp__gte=last_month_start,
            timestamp__lt=last_month_end
        ).aggregate(
            total_sum=Coalesce(Sum('amount'), Decimal('0.00'))
        )['total_sum']

        if prev_month_contributions > 0:
            change = ((monthly_contributions - prev_month_contributions) / prev_month_contributions) * 100
        elif monthly_contributions > 0:
            change = 100.0  
        else:
            change = 0.0 

        analytics_data['monthly_contributions_change_percent'] = round(float(change), 2)

        # Goals achieved YTD change percent
        last_year_start = (start_of_year - timedelta(days=1)).replace(month=1, day=1)
        last_year_end = start_of_year - timedelta(microseconds=1)

        goals_achieved_last_year = SavingsGoalModel.objects.filter(
            user=user,
            status='completed',
            updated_at__gte=last_year_start,
            updated_at__lt=last_year_end
        ).count()

        if goals_achieved_last_year > 0:
            change_goals = ((goals_achieved_ytd - goals_achieved_last_year) / goals_achieved_last_year) * 100
        elif goals_achieved_ytd > 0:
            change_goals = 100.0
        else:
            change_goals = 0.0

        analytics_data['goals_achieved_ytd_change_percent'] = round(float(change_goals), 2)

        # Savings Growth Chart Data (last 12 months)
        savings_growth_data = self._get_savings_growth_data(user, now)
        analytics_data['savings_growth_data'] = savings_growth_data

        # Goal Progress Chart Data
        goal_progress_data = self._get_goal_progress_data(user)
        analytics_data['goal_progress_data'] = goal_progress_data

        return success_response(
            message="Dashboard analytics retrieved successfully",
            data=analytics_data
        )

    def _get_savings_growth_data(self, user, now):
        """
        Generate savings growth data for the last 12 months.
        Returns categories (month labels), total_savings_series, and monthly_deposits_series.
        """
        categories = []
        total_savings_series = []
        monthly_deposits_series = []

        # Get all user's goals
        user_goals = SavingsGoalModel.objects.filter(user=user)
        
        # Calculate data for each of the last 12 months
        for i in range(11, -1, -1):  # From 11 months ago to current month
            # Calculate month date using relativedelta for accurate month handling
            month_date = now - relativedelta(months=i)
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Calculate next month start for range
            next_month_start = month_start + relativedelta(months=1)
            
            # Get monthly deposits (contributions) for this month
            monthly_deposits = SavingsGoalTransaction.objects.filter(
                goal__user=user,
                transaction_type='contribution',
                timestamp__gte=month_start,
                timestamp__lt=next_month_start
            ).aggregate(
                total_sum=Coalesce(Sum('amount'), Decimal('0.00'))
            )['total_sum']

            # Calculate total savings balance at end of this month
            # This is wallet balance + sum of all goal amounts up to this point
            goals_amount_at_month_end = Decimal('0.00')
            for goal in user_goals:
                # Get goal amount at end of this month (sum of contributions up to this point)
                goal_contributions = SavingsGoalTransaction.objects.filter(
                    goal=goal,
                    transaction_type='contribution',
                    timestamp__lte=next_month_start - timedelta(microseconds=1)
                ).aggregate(
                    total_sum=Coalesce(Sum('amount'), Decimal('0.00'))
                )['total_sum']
                
                goal_withdrawals = SavingsGoalTransaction.objects.filter(
                    goal=goal,
                    transaction_type='withdrawal',
                    timestamp__lte=next_month_start - timedelta(microseconds=1)
                ).aggregate(
                    total_sum=Coalesce(Sum('amount'), Decimal('0.00'))
                )['total_sum']
                
                goals_amount_at_month_end += (goal_contributions - goal_withdrawals)

            # Calculate wallet balance at end of this month
            # Start with current balance and adjust for transactions after this month
            try:
                current_wallet_balance = user.wallet.balance
            except Wallet.DoesNotExist:
                current_wallet_balance = Decimal('0.00')

            # Get contributions and withdrawals that happened AFTER this month
            # These need to be subtracted/added to get the balance at end of this month
            contributions_after = SavingsGoalTransaction.objects.filter(
                goal__user=user,
                transaction_type='contribution',
                timestamp__gt=next_month_start - timedelta(microseconds=1)
            ).aggregate(
                total_sum=Coalesce(Sum('amount'), Decimal('0.00'))
            )['total_sum']

            withdrawals_after = SavingsGoalTransaction.objects.filter(
                goal__user=user,
                transaction_type='withdrawal',
                timestamp__gt=next_month_start - timedelta(microseconds=1)
            ).aggregate(
                total_sum=Coalesce(Sum('amount'), Decimal('0.00'))
            )['total_sum']

            # Wallet balance at end of month = current - contributions after + withdrawals after
            wallet_balance_at_month_end = current_wallet_balance - contributions_after + withdrawals_after

            # Also need to account for external wallet transactions (deposits/withdrawals not related to goals)
            # Get external credits (deposits) up to end of month
            external_credits_after = WalletTransaction.objects.filter(
                wallet__user=user,
                transaction_type='credit',
                created_at__gt=next_month_start - timedelta(microseconds=1)
            ).exclude(
                description__icontains='savings goal'  # Exclude goal-related transactions
            ).aggregate(
                total_sum=Coalesce(Sum('amount'), Decimal('0.00'))
            )['total_sum']

            external_debits_after = WalletTransaction.objects.filter(
                wallet__user=user,
                transaction_type='debit',
                created_at__gt=next_month_start - timedelta(microseconds=1)
            ).exclude(
                description__icontains='savings goal'  # Exclude goal-related transactions
            ).aggregate(
                total_sum=Coalesce(Sum('amount'), Decimal('0.00'))
            )['total_sum']

            # Adjust for external transactions
            wallet_balance_at_month_end = wallet_balance_at_month_end - external_credits_after + external_debits_after

            total_savings_at_month_end = wallet_balance_at_month_end + goals_amount_at_month_end

            # Add to series
            categories.append(month_abbr[month_date.month])
            total_savings_series.append(float(total_savings_at_month_end))
            monthly_deposits_series.append(float(monthly_deposits))

        return {
            'categories': categories,
            'total_savings_series': total_savings_series,
            'monthly_deposits_series': monthly_deposits_series
        }

    def _get_goal_progress_data(self, user):
        """
        Generate goal progress data grouped by goal name.
        Returns categories (goal names), progress_series, and target_series.
        """
        # Get all active and completed goals (limit to top 5 for chart)
        goals = SavingsGoalModel.objects.filter(
            user=user,
            status__in=['active', 'completed']
        ).order_by('-amount')[:5]  # Top 5 goals by amount

        categories = []
        progress_series = []
        target_series = []

        for goal in goals:
            categories.append(goal.name)
            progress_series.append(float(goal.amount))
            target_series.append(float(goal.target_amount))

        # If no goals, return empty data
        if not categories:
            return {
                'categories': [],
                'progress_series': [],
                'target_series': []
            }

        return {
            'categories': categories,
            'progress_series': progress_series,
            'target_series': target_series
        }
