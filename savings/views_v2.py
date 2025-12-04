# savings/views_v2.py
"""
V2 Mobile - Enhanced Savings Views with Batch Goal Creation
"""
from decimal import Decimal
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from core.helpers.response import success_response, validation_error_response, error_response
from .models import SavingsGoalModel, SavingsGoalTransaction
from .serializers import SavingsGoalSerializer, SavingsGoalTransactionSerializer
from .utils import (
    calculate_goal_amount,
    get_goal_template_info,
    get_all_templates,
    get_recommended_templates
)
from onboarding.models import OnboardingProfile
from wallet.models import Wallet, WalletTransaction
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

# Notification helpers
try:
    from notification.helper.notifications import (
        notify_goal_created,
        notify_goal_funded,
        notify_goal_withdrawn,
        notify_goal_milestone,
        notify_goal_completed
    )
    NOTIFICATIONS_AVAILABLE = True
except (ImportError, Exception):
    NOTIFICATIONS_AVAILABLE = False
    def notify_goal_created(*args, **kwargs): pass
    def notify_goal_funded(*args, **kwargs): pass
    def notify_goal_withdrawn(*args, **kwargs): pass
    def notify_goal_milestone(*args, **kwargs): pass
    def notify_goal_completed(*args, **kwargs): pass


class BatchCreateGoalsAPIView(APIView):
    """
    V2 Mobile - Batch Create Savings Goals from Templates

    Create multiple savings goals at once using pre-defined templates.
    Amounts are auto-calculated based on user's onboarding profile.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V2 - Savings'],
        summary='Batch Create Goals from Templates',
        description='''
        Create multiple savings goals at once using templates.

        Template IDs:
        - hospital_delivery: Hospital delivery fund (auto-calculated based on plan & location)
        - baby_essentials: Baby essentials (auto-calculated based on preference)
        - emergency_fund: Emergency medical fund (₦150,000)
        - postpartum_care: Postpartum care (₦100,000)
        - baby_clothing: Baby clothing (₦75,000)
        - maternity_items: Maternity items (₦50,000)

        Amounts are auto-calculated based on user's onboarding profile data.
        If onboarding profile doesn't exist, default values are used.
        ''',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'template_ids': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'Array of template IDs to create goals from'
                    },
                    'auto_calculate_amounts': {
                        'type': 'boolean',
                        'description': 'Whether to auto-calculate amounts (default: true)'
                    }
                },
                'required': ['template_ids']
            }
        },
        responses={
            201: SavingsGoalSerializer(many=True),
            400: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                'Create Multiple Goals',
                value={
                    'template_ids': ['hospital_delivery', 'baby_essentials', 'emergency_fund'],
                    'auto_calculate_amounts': True
                }
            ),
        ]
    )
    def post(self, request, *args, **kwargs):
        """
        Batch create savings goals from templates
        """
        template_ids = request.data.get('template_ids', [])
        auto_calculate = request.data.get('auto_calculate_amounts', True)

        if not template_ids or not isinstance(template_ids, list):
            return validation_error_response({
                'template_ids': 'Must provide a list of template IDs'
            })

        # Get onboarding context for calculations
        onboarding_context = {}
        try:
            onboarding_profile = OnboardingProfile.objects.get(user=request.user)
            onboarding_context = {
                'hospital_plan': onboarding_profile.hospital_plan,
                'location': onboarding_profile.location,
                'baby_essentials_preference': onboarding_profile.baby_essentials_preference,
                'journey_type': onboarding_profile.journey_type,
            }
        except OnboardingProfile.DoesNotExist:
            # Use defaults if no onboarding profile
            onboarding_context = {
                'hospital_plan': 'private',
                'location': 'Lagos',
                'baby_essentials_preference': 'comfort',
                'journey_type': None,
            }

        created_goals = []
        errors = []

        with transaction.atomic():
            for template_id in template_ids:
                template_info = get_goal_template_info(template_id)

                if not template_info:
                    errors.append({
                        'template_id': template_id,
                        'error': f'Unknown template: {template_id}'
                    })
                    continue

                # Calculate target amount
                if auto_calculate:
                    target_amount = calculate_goal_amount(template_id, onboarding_context)
                else:
                    target_amount = Decimal('0')

                # Create the goal
                try:
                    goal = SavingsGoalModel.objects.create(
                        user=request.user,
                        name=template_info['name'],
                        target_amount=target_amount,
                        amount=Decimal('0'),
                        status='active',
                        # Store template metadata
                        description=template_info.get('description', '')
                    )
                    created_goals.append(goal)
                except Exception as e:
                    errors.append({
                        'template_id': template_id,
                        'error': str(e)
                    })

        if errors:
            return validation_error_response({
                'errors': errors,
                'created_count': len(created_goals)
            })

        serializer = SavingsGoalSerializer(created_goals, many=True)
        return success_response(
            data=serializer.data,
            message=f"{len(created_goals)} savings goals created successfully",
            status_code=status.HTTP_201_CREATED
        )


class GoalTemplatesAPIView(APIView):
    """
    V2 Mobile - Get Available Goal Templates

    Returns all available goal templates with their configuration.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V2 - Savings'],
        summary='Get Goal Templates',
        description='Get all available goal templates with their configuration',
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request, *args, **kwargs):
        """
        Get all available goal templates
        """
        templates = get_all_templates()

        # Get onboarding context for calculations
        onboarding_context = {}
        try:
            onboarding_profile = OnboardingProfile.objects.get(user=request.user)
            onboarding_context = {
                'hospital_plan': onboarding_profile.hospital_plan,
                'location': onboarding_profile.location,
                'baby_essentials_preference': onboarding_profile.baby_essentials_preference,
                'journey_type': onboarding_profile.journey_type,
            }
        except OnboardingProfile.DoesNotExist:
            onboarding_context = {
                'hospital_plan': 'private',
                'location': 'Lagos',
                'baby_essentials_preference': 'comfort',
                'journey_type': None,
            }

        # Calculate estimated amounts for each template
        templates_with_amounts = {}
        for template_id, template_data in templates.items():
            estimated_amount = calculate_goal_amount(template_id, onboarding_context)
            templates_with_amounts[template_id] = {
                **template_data,
                'estimated_amount': float(estimated_amount),
                'template_id': template_id
            }

        return success_response(
            data={
                'templates': templates_with_amounts,
                'onboarding_context': onboarding_context
            },
            message="Goal templates retrieved successfully"
        )


class RecommendedGoalsAPIView(APIView):
    """
    V2 Mobile - Get Recommended Goals Based on Journey

    Returns recommended goal templates based on user's journey type.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V2 - Savings'],
        summary='Get Recommended Goals',
        description='Get recommended goal templates based on user\'s journey type from onboarding profile',
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request, *args, **kwargs):
        """
        Get recommended goals based on user's journey
        """
        try:
            onboarding_profile = OnboardingProfile.objects.get(user=request.user)
            journey_type = onboarding_profile.journey_type

            recommended_template_ids = get_recommended_templates(journey_type)

            # Get full template info and calculate amounts
            onboarding_context = {
                'hospital_plan': onboarding_profile.hospital_plan,
                'location': onboarding_profile.location,
                'baby_essentials_preference': onboarding_profile.baby_essentials_preference,
                'journey_type': onboarding_profile.journey_type,
            }

            recommended_goals = []
            for template_id in recommended_template_ids:
                template_info = get_goal_template_info(template_id)
                if template_info:
                    estimated_amount = calculate_goal_amount(template_id, onboarding_context)
                    recommended_goals.append({
                        'template_id': template_id,
                        **template_info,
                        'estimated_amount': float(estimated_amount)
                    })

            return success_response(
                data={
                    'recommended_goals': recommended_goals,
                    'journey_type': journey_type
                },
                message=f"Found {len(recommended_goals)} recommended goals for your journey"
            )

        except OnboardingProfile.DoesNotExist:
            # Return generic recommendations if no onboarding
            return success_response(
                data={
                    'recommended_goals': [],
                    'journey_type': None,
                    'message': 'Complete onboarding to get personalized recommendations'
                },
                message="No onboarding profile found"
            )


class GoalsListCreateAPIView(APIView):
    """
    V2 Mobile - List and Create Savings Goals

    GET: List all savings goals for the authenticated user
    POST: Create a new savings goal
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V2 - Savings'],
        summary='List Savings Goals',
        description='Get all savings goals for the authenticated user',
        responses={200: SavingsGoalSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        """
        Get all savings goals for the authenticated user.
        """
        user_goals = SavingsGoalModel.objects.filter(user=request.user).order_by('-created_at')
        serializer = SavingsGoalSerializer(user_goals, many=True)
        return success_response(
            data=serializer.data,
            message="Savings goals retrieved successfully"
        )

    @extend_schema(
        tags=['V2 - Savings'],
        summary='Create Savings Goal',
        description='Create a new savings goal for the authenticated user',
        request=SavingsGoalSerializer,
        responses={
            201: SavingsGoalSerializer,
            400: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                'Create Goal',
                value={
                    'name': 'Emergency Fund',
                    'target_amount': '100000.00',
                    'description': 'My emergency savings',
                    'interest_rate': '10.00'
                }
            )
        ]
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new savings goal for the authenticated user.
        Required fields: 'name', 'target_amount'
        Optional fields: 'amount' (defaults to 0), 'status' (defaults to 'active')
        """
        serializer = SavingsGoalSerializer(data=request.data)
        if serializer.is_valid():
            goal = serializer.save(user=request.user)

            # Send notification
            try:
                notify_goal_created(
                    user=request.user,
                    goal_name=goal.name,
                    goal_id=goal.id
                )
            except Exception:
                pass  # Don't fail if notification fails

            return success_response(
                message="Savings goal created successfully",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED
            )
        return validation_error_response(serializer.errors)


class GoalDetailAPIView(APIView):
    """
    V2 Mobile - Savings Goal Details

    GET: Retrieve a specific savings goal
    PUT: Update a specific savings goal
    DELETE: Delete a specific savings goal
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, goal_id, user):
        """Helper method to get goal and check ownership"""
        try:
            return SavingsGoalModel.objects.get(id=goal_id, user=user)
        except SavingsGoalModel.DoesNotExist:
            return None

    @extend_schema(
        tags=['V2 - Savings'],
        summary='Get Goal Details',
        description='Retrieve details of a specific savings goal',
        responses={
            200: SavingsGoalSerializer,
            404: OpenApiTypes.OBJECT
        }
    )
    def get(self, request, goal_id, *args, **kwargs):
        """
        Get a specific savings goal for the authenticated user.
        """
        goal = self.get_object(goal_id, request.user)
        if not goal:
            return error_response(
                message="Savings goal not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = SavingsGoalSerializer(goal)
        return success_response(
            data=serializer.data,
            message="Goal details retrieved successfully"
        )

    @extend_schema(
        tags=['V2 - Savings'],
        summary='Update Savings Goal',
        description='Update a specific savings goal',
        request=SavingsGoalSerializer,
        responses={
            200: SavingsGoalSerializer,
            404: OpenApiTypes.OBJECT
        }
    )
    def put(self, request, goal_id, *args, **kwargs):
        """
        Update a specific savings goal for the authenticated user.
        """
        goal = self.get_object(goal_id, request.user)
        if not goal:
            return error_response(
                message="Savings goal not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = SavingsGoalSerializer(goal, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success_response(
                message="Savings goal updated successfully",
                data=serializer.data
            )
        return validation_error_response(serializer.errors)

    @extend_schema(
        tags=['V2 - Savings'],
        summary='Delete Savings Goal',
        description='Delete a specific savings goal (only if balance is zero)',
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        }
    )
    def delete(self, request, goal_id, *args, **kwargs):
        """
        Delete a specific savings goal for the authenticated user.
        Can only delete if goal has zero balance.
        """
        goal = self.get_object(goal_id, request.user)
        if not goal:
            return error_response(
                message="Savings goal not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        if goal.amount > 0:
            return error_response(
                message=f"Cannot delete a savings goal with balance of ₦{goal.amount}. Please withdraw funds first.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        goal_name = goal.name
        goal.delete()
        return success_response(
            message=f"Savings goal '{goal_name}' deleted successfully"
        )


class GoalFundAPIView(APIView):
    """
    V2 Mobile - Fund Savings Goal

    Transfer money from wallet to a specific savings goal
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V2 - Savings'],
        summary='Fund Savings Goal',
        description='Transfer money from wallet to a savings goal',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'amount': {'type': 'number', 'description': 'Amount to transfer'},
                    'description': {'type': 'string', 'description': 'Optional description'}
                },
                'required': ['amount']
            }
        },
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                'Fund Goal',
                value={'amount': 5000, 'description': 'Monthly savings'}
            )
        ]
    )
    def post(self, request, goal_id, *args, **kwargs):
        """
        Fund a savings goal from wallet
        """
        amount = request.data.get('amount')
        description = request.data.get('description', '')

        # Validate amount
        if not amount:
            return validation_error_response({'amount': 'Amount is required'})

        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                return validation_error_response({'amount': 'Amount must be greater than zero'})
        except (ValueError, TypeError):
            return validation_error_response({'amount': 'Invalid amount format'})

        # Get goal and wallet
        try:
            goal = SavingsGoalModel.objects.get(id=goal_id, user=request.user)
            wallet = request.user.wallet
        except SavingsGoalModel.DoesNotExist:
            return error_response(
                message="Savings goal not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except ObjectDoesNotExist:
            return error_response(
                message="Wallet not found. Please verify your account first.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Check wallet balance
        if wallet.balance < amount_decimal:
            return error_response(
                message=f"Insufficient wallet balance. Available: ₦{wallet.balance}",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Perform transfer
        try:
            with transaction.atomic():
                # Deduct from wallet
                wallet.withdraw(amount_decimal)

                # Create wallet transaction
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='debit',
                    amount=amount_decimal,
                    description=f"Transfer to {goal.name}",
                )

                # Add to goal
                goal.amount += amount_decimal
                goal.save(update_fields=['amount', 'updated_at'])

                # Create goal transaction
                SavingsGoalTransaction.objects.create(
                    goal=goal,
                    transaction_type='contribution',
                    amount=amount_decimal,
                    description=description or f"Funded from wallet",
                    goal_current_amount=goal.amount
                )

            # Calculate progress
            progress = (float(goal.amount) / float(goal.target_amount) * 100) if goal.target_amount > 0 else 0

            # Send notifications
            try:
                notify_goal_funded(
                    user=request.user,
                    goal_name=goal.name,
                    amount=amount_decimal,
                    goal_id=goal.id,
                    new_balance=goal.amount
                )

                # Check for milestones (25%, 50%, 75%, 100%)
                for milestone in [25, 50, 75, 100]:
                    if progress >= milestone and (progress - (float(amount_decimal) / float(goal.target_amount) * 100)) < milestone:
                        if milestone == 100:
                            notify_goal_completed(
                                user=request.user,
                                goal_name=goal.name,
                                goal_id=goal.id,
                                amount=goal.target_amount
                            )
                        else:
                            notify_goal_milestone(
                                user=request.user,
                                goal_name=goal.name,
                                goal_id=goal.id,
                                percentage=milestone
                            )
                        break
            except Exception:
                pass  # Don't fail if notification fails

            return success_response(
                message=f"Successfully funded {goal.name} with ₦{amount_decimal}",
                data={
                    'goal_id': str(goal.id),
                    'goal_name': goal.name,
                    'amount_added': str(amount_decimal),
                    'new_balance': str(goal.amount),
                    'target_amount': str(goal.target_amount),
                    'progress_percentage': round(progress, 2),
                    'wallet_balance': str(wallet.balance)
                }
            )
        except Exception as e:
            return error_response(
                message=f"Failed to fund goal: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GoalWithdrawAPIView(APIView):
    """
    V2 Mobile - Withdraw from Savings Goal

    Transfer money from savings goal back to wallet
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V2 - Savings'],
        summary='Withdraw from Savings Goal',
        description='Transfer money from a savings goal back to wallet',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'amount': {'type': 'number', 'description': 'Amount to withdraw'},
                    'description': {'type': 'string', 'description': 'Optional description'}
                },
                'required': ['amount']
            }
        },
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                'Withdraw from Goal',
                value={'amount': 2000, 'description': 'Emergency withdrawal'}
            )
        ]
    )
    def post(self, request, goal_id, *args, **kwargs):
        """
        Withdraw from a savings goal to wallet
        """
        amount = request.data.get('amount')
        description = request.data.get('description', '')

        # Validate amount
        if not amount:
            return validation_error_response({'amount': 'Amount is required'})

        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                return validation_error_response({'amount': 'Amount must be greater than zero'})
        except (ValueError, TypeError):
            return validation_error_response({'amount': 'Invalid amount format'})

        # Get goal and wallet
        try:
            goal = SavingsGoalModel.objects.get(id=goal_id, user=request.user)
            wallet = request.user.wallet
        except SavingsGoalModel.DoesNotExist:
            return error_response(
                message="Savings goal not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except ObjectDoesNotExist:
            return error_response(
                message="Wallet not found. Please verify your account first.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Check if goal is locked
        if goal.is_currently_locked():
            return error_response(
                message=f"This goal is locked until {goal.maturity_date.strftime('%B %d, %Y')}",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Check goal balance
        if goal.amount < amount_decimal:
            return error_response(
                message=f"Insufficient goal balance. Available: ₦{goal.amount}",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Calculate penalty if applicable
        penalty_amount = Decimal('0')
        if goal.early_withdrawal_penalty_percent and goal.maturity_date:
            from django.utils import timezone
            if timezone.now().date() < goal.maturity_date:
                penalty_amount = amount_decimal * (goal.early_withdrawal_penalty_percent / Decimal('100'))

        # Perform withdrawal
        try:
            with transaction.atomic():
                # Deduct from goal
                goal.amount -= amount_decimal
                goal.save(update_fields=['amount', 'updated_at'])

                # Calculate net amount after penalty
                net_amount = amount_decimal - penalty_amount

                # Add to wallet
                wallet.deposit(net_amount)

                # Create wallet transaction
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='credit',
                    amount=net_amount,
                    description=f"Withdrawal from {goal.name}",
                )

                # Create goal transaction
                SavingsGoalTransaction.objects.create(
                    goal=goal,
                    transaction_type='withdrawal',
                    amount=amount_decimal,
                    description=description or f"Withdrawn to wallet",
                    goal_current_amount=goal.amount
                )

            # Send notification
            try:
                notify_goal_withdrawn(
                    user=request.user,
                    goal_name=goal.name,
                    amount=amount_decimal,
                    goal_id=goal.id
                )
            except Exception:
                pass  # Don't fail if notification fails

            response_data = {
                'goal_id': str(goal.id),
                'goal_name': goal.name,
                'amount_withdrawn': str(amount_decimal),
                'penalty_amount': str(penalty_amount),
                'net_amount': str(net_amount),
                'new_goal_balance': str(goal.amount),
                'wallet_balance': str(wallet.balance)
            }

            if penalty_amount > 0:
                message = f"Withdrew ₦{amount_decimal} from {goal.name} (₦{penalty_amount} early withdrawal penalty applied)"
            else:
                message = f"Successfully withdrew ₦{amount_decimal} from {goal.name}"

            return success_response(
                message=message,
                data=response_data
            )
        except Exception as e:
            return error_response(
                message=f"Failed to withdraw from goal: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GoalTransactionsAPIView(APIView):
    """
    V2 Mobile - Get Goal Transaction History

    Retrieve transaction history for a specific savings goal
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V2 - Savings'],
        summary='Get Goal Transaction History',
        description='Retrieve transaction history for a specific savings goal',
        responses={
            200: SavingsGoalTransactionSerializer(many=True),
            404: OpenApiTypes.OBJECT
        }
    )
    def get(self, request, goal_id, *args, **kwargs):
        """
        Get transaction history for a specific goal
        """
        try:
            goal = SavingsGoalModel.objects.get(id=goal_id, user=request.user)
        except SavingsGoalModel.DoesNotExist:
            return error_response(
                message="Savings goal not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        transactions = goal.transactions.all().order_by('-created_at')
        serializer = SavingsGoalTransactionSerializer(transactions, many=True)

        return success_response(
            data=serializer.data,
            message="Goal transaction history retrieved successfully"
        )
