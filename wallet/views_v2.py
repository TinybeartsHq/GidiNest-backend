# wallet/views_v2.py
"""
V2 Mobile - Enhanced Wallet Views
Streamlined wallet operations for mobile app with improved error handling
"""
from decimal import Decimal
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from core.helpers.response import success_response, validation_error_response, error_response
from .models import Wallet, WalletTransaction, WithdrawalRequest
from .serializers import WalletBalanceSerializer, WalletTransactionSerializer
from savings.models import SavingsGoalModel
from savings.serializers import SavingsGoalSerializer

# Optional push notification import
try:
    from notification.helper.push import send_push_notification_to_user
    PUSH_NOTIFICATIONS_AVAILABLE = True
except (ImportError, FileNotFoundError, Exception):
    PUSH_NOTIFICATIONS_AVAILABLE = False
    def send_push_notification_to_user(*args, **kwargs):
        pass

# Notification helper
try:
    from notification.helper.notifications import notify_withdrawal_requested
except (ImportError, Exception):
    def notify_withdrawal_requested(*args, **kwargs):
        pass


class WalletDetailAPIView(APIView):
    """
    V2 Mobile - Get Wallet Details

    Returns comprehensive wallet information including:
    - Balance and account details
    - Savings goals summary
    - Transaction PIN status
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V2 - Wallet'],
        summary='Get Wallet Details',
        description='Retrieve user wallet information including balance, account details, and savings goals',
        responses={
            200: {
                'description': 'Wallet details retrieved successfully',
                'content': {
                    'application/json': {
                        'example': {
                            'success': True,
                            'message': 'Wallet details retrieved successfully',
                            'data': {
                                'wallet': {
                                    'id': 'uuid',
                                    'balance': '50000.00',
                                    'account_number': '1234567890',
                                    'bank_name': 'Embedly Virtual Bank',
                                    'bank_code': '001',
                                    'account_name': 'John Doe',
                                    'currency': 'NGN',
                                    'created_at': '2025-01-01T00:00:00Z'
                                },
                                'savings_goals': [
                                    {
                                        'id': 'uuid',
                                        'name': 'Emergency Fund',
                                        'target_amount': '100000.00',
                                        'amount': '50000.00',
                                        'status': 'active'
                                    }
                                ],
                                'transaction_pin_set': True
                            }
                        }
                    }
                }
            },
            404: {'description': 'Wallet not found - user needs to verify BVN/NIN'}
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Get wallet details for authenticated user
        """
        try:
            wallet = request.user.wallet
        except ObjectDoesNotExist:
            return error_response(
                message="You don't have a wallet yet. Please verify your BVN or NIN to activate your wallet.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Serialize wallet
        wallet_serializer = WalletBalanceSerializer(wallet)

        # Get user's savings goals
        goals = SavingsGoalModel.objects.filter(user=request.user)
        goals_serializer = SavingsGoalSerializer(goals, many=True)

        # Refresh user to get latest transaction_pin_set status
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=request.user.id)

        response_data = {
            'wallet': wallet_serializer.data,
            'savings_goals': goals_serializer.data,
            'transaction_pin_set': user.transaction_pin_set
        }

        return success_response(
            data=response_data,
            message="Wallet details retrieved successfully"
        )


class WalletDepositAPIView(APIView):
    """
    V2 Mobile - Initiate Wallet Deposit

    Initiates a deposit into user's wallet via bank transfer.
    Returns account details for user to transfer to.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V2 - Wallet'],
        summary='Initiate Wallet Deposit',
        description='Get account details to deposit money into wallet. User transfers to this account and webhook processes the deposit.',
        responses={
            200: {
                'description': 'Deposit instructions provided',
                'content': {
                    'application/json': {
                        'example': {
                            'success': True,
                            'message': 'Transfer to the account below to fund your wallet',
                            'data': {
                                'account_number': '1234567890',
                                'account_name': 'John Doe',
                                'bank_name': 'Embedly Virtual Bank',
                                'bank_code': '001',
                                'amount': '10000.00',
                                'instructions': [
                                    'Transfer the amount to the account above',
                                    'Your wallet will be credited automatically',
                                    'Credit typically happens within 1-5 minutes'
                                ]
                            }
                        }
                    }
                }
            },
            404: {'description': 'Wallet not found'}
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Initiate wallet deposit - returns account details
        """
        amount = request.data.get('amount')

        # Validate amount
        if not amount:
            return validation_error_response({'amount': 'Amount is required'})

        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                return validation_error_response({'amount': 'Amount must be greater than zero'})
        except (ValueError, TypeError):
            return validation_error_response({'amount': 'Invalid amount format'})

        # Check if user has wallet
        try:
            wallet = request.user.wallet
        except ObjectDoesNotExist:
            return error_response(
                message="You don't have a wallet yet. Please verify your BVN or NIN to activate your wallet.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Return account details for deposit
        response_data = {
            'account_number': wallet.account_number,
            'account_name': wallet.account_name,
            'bank_name': wallet.bank_name,
            'bank_code': wallet.bank_code,
            'amount': str(amount_decimal),
            'currency': 'NGN',
            'instructions': [
                'Transfer the amount to the account above',
                'Your wallet will be credited automatically',
                'Credit typically happens within 1-5 minutes',
                'Use any banking app or USSD to make the transfer'
            ]
        }

        return success_response(
            data=response_data,
            message="Transfer to the account below to fund your wallet"
        )


class WalletWithdrawAPIView(APIView):
    """
    V2 Mobile - Initiate Wallet Withdrawal

    Creates a withdrawal request to transfer money from wallet to user's bank account.
    Requires transaction PIN for security.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V2 - Wallet'],
        summary='Initiate Wallet Withdrawal',
        description='Request to withdraw money from wallet to a bank account. Requires transaction PIN.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'amount': {'type': 'number', 'description': 'Amount to withdraw'},
                    'bank_name': {'type': 'string', 'description': 'Destination bank name'},
                    'account_number': {'type': 'string', 'description': 'Destination account number'},
                    'account_name': {'type': 'string', 'description': 'Destination account name'},
                    'bank_code': {'type': 'string', 'description': 'Bank code (e.g., 058 for GTBank)'},
                    'transaction_pin': {'type': 'string', 'description': '4-digit transaction PIN'}
                },
                'required': ['amount', 'bank_name', 'account_number', 'account_name', 'bank_code', 'transaction_pin']
            }
        },
        responses={
            201: {
                'description': 'Withdrawal request created',
                'content': {
                    'application/json': {
                        'example': {
                            'success': True,
                            'message': 'Withdrawal request submitted successfully',
                            'data': {
                                'withdrawal_id': 'uuid',
                                'amount': '10000.00',
                                'status': 'pending',
                                'bank_name': 'GTBank',
                                'account_number': '0123456789',
                                'account_name': 'John Doe',
                                'created_at': '2025-01-15T10:00:00Z',
                                'estimated_completion': '1-24 hours'
                            }
                        }
                    }
                }
            },
            400: {'description': 'Validation error'},
            401: {'description': 'Invalid transaction PIN'},
            404: {'description': 'Wallet not found'}
        },
        examples=[
            OpenApiExample(
                'Withdrawal Request',
                value={
                    'amount': 10000,
                    'bank_name': 'GTBank',
                    'account_number': '0123456789',
                    'account_name': 'John Doe',
                    'bank_code': '058',
                    'transaction_pin': '1234'
                }
            )
        ]
    )
    def post(self, request, *args, **kwargs):
        """
        Initiate withdrawal from wallet
        """
        # Parse input
        amount = request.data.get('amount')
        bank_name = request.data.get('bank_name')
        account_number = request.data.get('account_number')
        account_name = request.data.get('account_name')
        bank_code = request.data.get('bank_code')
        transaction_pin = request.data.get('transaction_pin')

        # Validate required fields
        errors = {}
        if not amount:
            errors['amount'] = 'Amount is required'
        if not bank_name:
            errors['bank_name'] = 'Bank name is required'
        if not account_number:
            errors['account_number'] = 'Account number is required'
        if not account_name:
            errors['account_name'] = 'Account name is required'
        if not bank_code:
            errors['bank_code'] = 'Bank code is required'
        if not transaction_pin:
            errors['transaction_pin'] = 'Transaction PIN is required'

        if errors:
            return validation_error_response(errors)

        # Validate amount
        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                return validation_error_response({'amount': 'Amount must be greater than zero'})
        except (ValueError, TypeError):
            return validation_error_response({'amount': 'Invalid amount format'})

        # Verify transaction PIN
        if not request.user.check_transaction_pin(transaction_pin):
            return error_response(
                message="Invalid transaction PIN",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # Check if user has wallet
        try:
            wallet = request.user.wallet
        except ObjectDoesNotExist:
            return error_response(
                message="You don't have a wallet yet. Please verify your BVN or NIN to activate your wallet.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Check sufficient balance
        if wallet.balance < amount_decimal:
            return error_response(
                message=f"Insufficient balance. Available: ₦{wallet.balance}",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Create withdrawal request
        try:
            with transaction.atomic():
                withdrawal_request = WithdrawalRequest.objects.create(
                    user=request.user,
                    amount=amount_decimal,
                    bank_name=bank_name,
                    bank_account_name=account_name,
                    account_number=account_number,
                    bank_code=bank_code,
                    status='pending'
                )

                # Deduct from wallet immediately (will be refunded if withdrawal fails)
                wallet.balance -= amount_decimal
                wallet.save(update_fields=['balance'])

                # Create transaction record
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='debit',
                    amount=amount_decimal,
                    description=f'Withdrawal to {bank_name} - {account_number}',
                    status='pending',
                    metadata={
                        'withdrawal_id': str(withdrawal_request.id),
                        'bank_name': bank_name,
                        'account_number': account_number,
                        'account_name': account_name
                    }
                )

            # Create in-app notification
            try:
                notify_withdrawal_requested(
                    user=request.user,
                    amount=amount_decimal,
                    withdrawal_id=withdrawal_request.id
                )
            except Exception:
                pass  # Don't fail if notification fails

            response_data = {
                'withdrawal_id': str(withdrawal_request.id),
                'amount': str(amount_decimal),
                'status': 'pending',
                'bank_name': bank_name,
                'account_number': account_number,
                'account_name': account_name,
                'created_at': withdrawal_request.created_at.isoformat(),
                'estimated_completion': '1-24 hours'
            }

            return success_response(
                data=response_data,
                message="Withdrawal request submitted successfully",
                status_code=status.HTTP_201_CREATED
            )

        except Exception as e:
            return error_response(
                message=f"Failed to process withdrawal: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
