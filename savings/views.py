# savings/views.py
import logging
from decimal import Decimal
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.helpers.response import success_response, validation_error_response, error_response
from django.core.cache import cache

logger = logging.getLogger(__name__)
from wallet.models import Wallet, WalletTransaction
from .models import SavingsGoalModel, SavingsGoalTransaction
from .serializers import SavingsGoalSerializer, SavingsGoalTransactionSerializer
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction  
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal  



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
            # Invalidate dashboard cache so new goal shows immediately
            cache.delete(f'dashboard_{request.user.id}')
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
            cache.delete(f'dashboard_{request.user.id}')
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

                # Invalidate dashboard cache
                cache.delete(f'dashboard_{request.user.id}')

                return success_response(message = f"{transaction_type.capitalize()} successful for goal: {goal.name}")

            except ValueError as e:
               logger.warning(f"Savings transaction validation error: {e}")
               return error_response("An error occurred during transaction. Please try again.")
            except Exception as e:
                logger.error(f"Savings transaction error: {e}", exc_info=True)
                return error_response("An error occurred during transaction. Please try again.")


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
    - Total Savings Balance
    - Active Savings Goals count
    - Monthly Contributions (sum of contributions in the current month)
    - Goals Achieved (Year-To-Date)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        analytics_data = {}

        try:
            wallet = user.wallet
            analytics_data['total_savings_balance'] = wallet.balance
            analytics_data['currency'] = wallet.currency
        except Wallet.DoesNotExist:
            analytics_data['total_savings_balance'] = Decimal('0.00')
            analytics_data['currency'] = 'NGN' 

        active_goals_count = SavingsGoalModel.objects.filter(user=user, status='active').count()
        analytics_data['active_savings_goals'] = active_goals_count

        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        monthly_contributions = SavingsGoalTransaction.objects.filter(
            goal__user=user, 
            transaction_type='contribution',
            timestamp__gte=start_of_month
        ).aggregate(
            total_sum=Coalesce(Sum('amount'), Decimal('0.00'))  
        )['total_sum']
        analytics_data['monthly_contributions'] = monthly_contributions

 
        start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        goals_achieved_ytd = SavingsGoalModel.objects.filter(
            user=user,
            status='completed',
            updated_at__gte=start_of_year
        ).count()
        analytics_data['goals_achieved_ytd'] = goals_achieved_ytd

 
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

        analytics_data['monthly_contributions_change_percent'] = round(float(change), 2) # Convert Decimal to float for JSON

 
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


        return success_response(analytics_data)
