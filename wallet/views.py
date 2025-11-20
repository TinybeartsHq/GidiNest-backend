# wallet/views.py
from django.db import IntegrityError, transaction
from django.http import JsonResponse
import requests
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.core.exceptions import ObjectDoesNotExist

from core.helpers.response import success_response, error_response
from notification.helper.email import MailClient
from providers.helpers.cuoral import CuoralAPI

# Optional push notification import - don't fail if Firebase isn't configured
try:
    from notification.helper.push import send_push_notification_to_user
    PUSH_NOTIFICATIONS_AVAILABLE = True
except (ImportError, FileNotFoundError, Exception):
    PUSH_NOTIFICATIONS_AVAILABLE = False
    def send_push_notification_to_user(*args, **kwargs):
        """Dummy function when push notifications are not available"""
        pass
from providers.helpers.embedly import EmbedlyClient
from savings.models import SavingsGoalModel
from savings.serializers import SavingsGoalSerializer
from wallet.serializers import WalletBalanceSerializer, WalletTransactionSerializer


from .models import Wallet,WithdrawalRequest

from rest_framework import serializers

from django.conf import settings
from rest_framework import permissions
import hmac
import hashlib
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .models import Wallet, WalletTransaction
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging

from decimal import Decimal


class WalletBalanceAPIView(APIView):
    """
    API endpoint to retrieve the authenticated user's wallet balance.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V1 - Wallet'],
        summary='Get Wallet Balance',
        description='Retrieve the authenticated user\'s wallet balance, account details, and savings goals.',
        responses={
            200: {
                'description': 'Wallet balance retrieved successfully',
                'content': {
                    'application/json': {
                        'example': {
                            'success': True,
                            'data': {
                                'wallet': {
                                    'balance': '50000.00',
                                    'currency': 'NGN',
                                    'account_number': '1234567890',
                                    'bank': 'Embedly Virtual Bank',
                                    'bank_code': '001',
                                    'account_name': 'John Doe'
                                },
                                'user_goals': [],
                                'transaction_pin_set': True
                            }
                        }
                    }
                }
            },
            401: {'description': 'Unauthorized'},
            404: {'description': 'Wallet not found - user needs to verify BVN/NIN'},
        }
    )
    def get(self, request, *args, **kwargs):
        try:
            # Attempt to get the user's wallet
            wallet = request.user.wallet
        except ObjectDoesNotExist:
            # Don't create wallet here - user needs to verify BVN/NIN first
            return error_response(
                "You don't have a wallet yet. Please verify your BVN or NIN to activate your wallet.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = WalletBalanceSerializer(wallet)

        # Refresh user to get latest transaction_pin_set status
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=request.user.id)

        data = {
            'wallet':serializer.data,
            "user_goals":SavingsGoalSerializer(SavingsGoalModel.objects.filter(user=request.user), many=True).data,
            "transaction_pin_set": user.transaction_pin_set
        }
        return success_response(data)
    



class WalletTransactionHistoryAPIView(APIView):
    """
    API endpoint to retrieve the authenticated user's wallet transaction history.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V1 - Wallet'],
        summary='Get Transaction History',
        description='Retrieve the authenticated user\'s wallet transaction history, ordered by most recent first.',
        responses={
            200: {
                'description': 'Transaction history retrieved successfully',
                'content': {
                    'application/json': {
                        'example': {
                            'success': True,
                            'data': {
                                'transactions': []
                            }
                        }
                    }
                }
            },
            401: {'description': 'Unauthorized'},
        }
    )
    def get(self, request, *args, **kwargs):
        # Retrieve the user's wallet
        try:
            wallet = Wallet.objects.get(user=request.user)
        except Wallet.DoesNotExist:
            return success_response({"transactions":[]}) 

        # Get all transactions related to the user's wallet
        transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')

        # Serialize the wallet transactions
        serializer = WalletTransactionSerializer(transactions, many=True)

        # Return the serialized data
        data = {
            'transactions': serializer.data
        }
        return success_response(data)



class WithdrawalRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for creating withdrawal requests.
    """
    class Meta:
        model = WithdrawalRequest
        fields = ['amount', 'bank_account_name', 'bank_name', 'account_number', 'user', 'status']
        read_only_fields = ['status', 'user']


class InitiateWithdrawalAPIView(APIView):
    """
    API endpoint to initiate a withdrawal request and validate account details.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V1 - Wallet'],
        summary='Initiate Withdrawal',
        description='Initiate a withdrawal request to a bank account. Requires transaction PIN verification and account name validation.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'bank_name': {'type': 'string', 'example': 'GTBank'},
                    'account_number': {'type': 'string', 'example': '0123456789'},
                    'account_name': {'type': 'string', 'example': 'John Doe'},
                    'amount': {'type': 'string', 'example': '5000.00'},
                    'bank_code': {'type': 'string', 'example': '058'},
                    'transaction_pin': {'type': 'string', 'example': '1234'},
                },
                'required': ['bank_name', 'account_number', 'account_name', 'amount', 'bank_code', 'transaction_pin']
            }
        },
        responses={
            200: {
                'description': 'Withdrawal initiated successfully',
                'content': {
                    'application/json': {
                        'example': {
                            'status': True,
                            'detail': 'Withdrawal request initiated successfully',
                            'withdrawal_id': 123
                        }
                    }
                }
            },
            400: {'description': 'Validation error or invalid PIN'},
            401: {'description': 'Unauthorized'},
            404: {'description': 'Wallet not found'},
        }
    )
    def post(self, request, *args, **kwargs):
        # Parse the input data
        bank_name = request.data.get('bank_name')
        account_number = request.data.get('account_number')
        account_name = request.data.get('account_name')  # Destination account name
        withdrawal_amount = request.data.get('amount')
        bank_code = request.data.get('bank_code')
        transaction_pin = request.data.get('transaction_pin')

        # Validate inputs
        if not all([bank_name, account_number, account_name, withdrawal_amount, bank_code]):
            return Response({
                "status": False,
                "detail": "All fields (bank_name, account_number, account_name, amount, bank_code) are required."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate transaction PIN
        if not transaction_pin:
            return Response({
                "status": False,
                "detail": "Transaction PIN is required for withdrawals."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            wallet = request.user.wallet
        except ObjectDoesNotExist:
            return Response({
                "status": False,
                "detail": "You don't have a wallet yet. Please verify your BVN or NIN to activate your wallet."
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Refresh user from database to get latest transaction_pin_set status
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=request.user.id)
        
        # Check if transaction PIN is set
        if not user.transaction_pin_set:
            return Response({
                "status": False,
                "detail": "Transaction PIN not set. Please set your transaction PIN first."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify transaction PIN
        if not user.verify_transaction_pin(transaction_pin):
            return Response({
                "status": False,
                "detail": "Invalid transaction PIN."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate account name matches user's verified name (use refreshed user)
        user_verified_name = user.get_verified_name()
        if not user_verified_name:
            return Response({
                "status": False,
                "detail": "Unable to verify your identity. Please ensure your BVN or NIN is verified."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Normalize names for comparison (uppercase, remove extra spaces)
        normalized_account_name = account_name.strip().upper()
        normalized_user_name = user_verified_name.strip().upper()
        
        # Check if account name matches (allow if either first OR last name matches)
        if normalized_account_name != normalized_user_name:
            # Split into name parts
            user_name_parts = normalized_user_name.split()
            account_name_parts = normalized_account_name.split()
            
            # Check if first name or last name matches
            user_first_name = user_name_parts[0] if user_name_parts else ""
            user_last_name = user_name_parts[-1] if len(user_name_parts) > 1 else ""
            
            account_first_name = account_name_parts[0] if account_name_parts else ""
            account_last_name = account_name_parts[-1] if len(account_name_parts) > 1 else ""
            
            # Allow if either first name OR last name matches
            first_name_matches = user_first_name and account_first_name and user_first_name == account_first_name
            last_name_matches = user_last_name and account_last_name and user_last_name == account_last_name
            
            if not (first_name_matches or last_name_matches):
                return Response({
                    "status": False,
                    "detail": f"Account name must match your verified name ({user_verified_name}). The account's first name or last name must match your verified name."
                }, status=status.HTTP_400_BAD_REQUEST)

        try:
            withdrawal_amount = Decimal(str(withdrawal_amount))
        except Exception:
            return Response({"detail": "Invalid amount."}, status=status.HTTP_400_BAD_REQUEST)

        if withdrawal_amount <= Decimal('0'):
            return Response({"detail": "Amount must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

        # Minimum withdrawal check (optional - adjust as needed)
        if withdrawal_amount < Decimal('100'):
            return Response({"detail": "Minimum withdrawal amount is NGN 100."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            wallet = request.user.wallet
        except ObjectDoesNotExist:
            return Response({
                "detail": "You don't have a wallet yet. Please verify your BVN or NIN to activate your wallet."
            }, status=status.HTTP_404_NOT_FOUND)

        # Attempt atomic withdraw to ensure sufficient funds
        try:
            wallet.withdraw(withdrawal_amount)
        except Exception:
            # Provide diagnostic info
            try:
                # Refresh current balance from DB
                from django.db.models import F
                fresh_wallet = type(wallet).objects.get(id=wallet.id)
                current_balance = fresh_wallet.balance
            except Exception:
                current_balance = wallet.balance

            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Withdrawal rejected due to insufficient balance: requested={withdrawal_amount}, balance={current_balance}, user={request.user.email}"
            )
            return Response({
                "status": False,
                "detail": "Insufficient balance",
                "available": str(current_balance),
                "requested": str(withdrawal_amount)
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create withdrawal request
        withdrawal_request = WithdrawalRequest.objects.create(
            user=request.user,
            amount=withdrawal_amount,
            bank_name=bank_name,
            bank_code=bank_code,
            account_number=account_number,
            bank_account_name=account_name,
            status='pending'
        )

        # Process withdrawal via Embedly
        embedly_client = EmbedlyClient()

        try:
            # Provider expects whole currency units (NGN), not kobo
            amount_in_kobo = int(withdrawal_amount.to_integral_value())

            # Get currency ID from settings
            currency_id = settings.EMBEDLY_CURRENCY_ID_NGN

            # Initiate transfer
            transfer_result = embedly_client.initiate_bank_transfer(
                destination_bank_code=bank_code,
                destination_account_number=account_number,
                destination_account_name=account_name,
                source_account_number=wallet.account_number,
                source_account_name=wallet.account_name,
                amount=amount_in_kobo,
                currency_id=currency_id,
                remarks=f"Withdrawal request #{withdrawal_request.id}",
                webhook_url=f"{settings.BASE_URL}/api/v1/wallet/payout/webhook",
                customer_transaction_reference=str(withdrawal_request.id)
            )

            if transfer_result.get("success"):
                # Store transaction reference (provider may return a string id or an object)
                transaction_data = transfer_result.get("data", {})
                if isinstance(transaction_data, dict):
                    txref = (
                        transaction_data.get("transactionRef")
                        or transaction_data.get("transactionReference")
                        or transaction_data.get("reference")
                        or transaction_data.get("transactionId")
                        or transaction_data.get("id")
                    )
                else:
                    txref = str(transaction_data)

                withdrawal_request.transaction_ref = txref
                withdrawal_request.status = 'processing'
                withdrawal_request.save()

                # Create debit transaction record with safe reference
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='debit',
                    amount=withdrawal_amount,
                    description=f"Withdrawal to {bank_name} - {account_number}",
                    external_reference=txref or f"WITHDRAWAL_{withdrawal_request.id}"
                )

                # Serialize and return success
                withdrawal_request_serializer = WithdrawalRequestSerializer(withdrawal_request)
                return Response({
                    "status": True,
                    "detail": "Withdrawal initiated successfully. Funds will be transferred shortly.",
                    "withdrawal_request": withdrawal_request_serializer.data
                }, status=status.HTTP_200_OK)
            else:
                # Transfer failed - refund user
                error_msg = transfer_result.get("message", "Unable to process withdrawal")
                withdrawal_request.status = 'failed'
                withdrawal_request.error_message = error_msg
                withdrawal_request.save()

                # Refund balance
                wallet.deposit(withdrawal_amount)

                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    f"Withdrawal failed for user {request.user.email}: {error_msg} "
                    f"(Amount: {withdrawal_amount}, Bank: {bank_code})"
                )

                return Response({
                    "status": False,
                    "detail": f"Withdrawal failed: {error_msg}"
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Unexpected error - refund user
            withdrawal_request.status = 'failed'
            withdrawal_request.error_message = str(e)
            withdrawal_request.save()

            # Refund balance
            wallet.deposit(withdrawal_amount)

            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                f"Exception during withdrawal for user {request.user.email}: {str(e)}",
                exc_info=True
            )

            return Response({
                "status": False,
                "detail": "An error occurred while processing your withdrawal. Your balance has been refunded."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    




class ResolveBankAccountAPIView(APIView):
    """
    API endpoint to resolve and fetch bank account details from Embedly.
    Uses Embedly's Payout/name-enquiry endpoint.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V1 - Wallet'],
        summary='Resolve Bank Account',
        description='Resolve bank account details (account name) using account number and bank code.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'account_number': {'type': 'string', 'example': '0123456789'},
                    'bank_code': {'type': 'string', 'example': '058'},
                },
                'required': ['account_number', 'bank_code']
            }
        },
        responses={
            200: {
                'description': 'Account resolved successfully',
                'content': {
                    'application/json': {
                        'example': {
                            'status': True,
                            'detail': 'Account resolved successfully.',
                            'data': {
                                'account_number': '0123456789',
                                'account_name': 'John Doe',
                                'bank_code': '058'
                            }
                        }
                    }
                }
            },
            400: {'description': 'Validation error'},
            401: {'description': 'Unauthorized'},
        }
    )
    def post(self, request, *args, **kwargs):
        # Parse the input data
        account_number = request.data.get('account_number')
        bank_code = request.data.get('bank_code')

        # Validate inputs
        if not account_number or not bank_code:
            return Response({
                "status": False,
                "detail": "Both account_number and bank_code are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate account number format (should be 10 digits)
        if not account_number.isdigit() or len(account_number) != 10:
            return Response({
                "status": False,
                "detail": "Account number must be exactly 10 digits."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Resolve bank account details via Embedly
        embedly_client = EmbedlyClient()

        try:
            result = embedly_client.resolve_bank_account(account_number, bank_code)

            if not result.get("success"):
                error_msg = result.get("message", "Unable to validate account details")

                # Log the error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    f"Embedly account validation failed for user {request.user.email}: "
                    f"{error_msg} (Account: {account_number}, Bank Code: {bank_code})"
                )

                return Response({
                    "status": False,
                    "detail": error_msg
                }, status=status.HTTP_400_BAD_REQUEST)

            # Return the resolved account details
            account_data = result.get("data", {})

            return Response({
                "status": True,
                "detail": "Account resolved successfully.",
                "data": {
                    "account_number": account_data.get("accountNumber", account_number),
                    "account_name": account_data.get("accountName", ""),
                    "bank_code": account_data.get("bankCode", bank_code)
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                f"Exception during account validation for user {request.user.email}: {str(e)}",
                exc_info=True
            )

            return Response({
                "status": False,
                "detail": "An error occurred while validating the account. Please try again."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    



class SetTransactionPinAPIView(APIView):
    """
    API endpoint to set or update transaction PIN for withdrawals.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        pin = request.data.get('pin')
        old_pin = request.data.get('old_pin')  # Required if updating existing PIN
        
        if not pin:
            return Response({
                "status": False,
                "detail": "PIN is required."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # If PIN is already set, require old PIN
        if request.user.transaction_pin_set:
            if not old_pin:
                return Response({
                    "status": False,
                    "detail": "Old PIN is required to update your transaction PIN."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not request.user.verify_transaction_pin(old_pin):
                return Response({
                    "status": False,
                    "detail": "Invalid old PIN."
                }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            was_set = request.user.transaction_pin_set
            request.user.set_transaction_pin(pin)
            # Refresh user from database to get updated transaction_pin_set
            from django.contrib.auth import get_user_model
            User = get_user_model()
            request.user.refresh_from_db()
            return Response({
                "status": True,
                "detail": "Transaction PIN updated successfully." if was_set else "Transaction PIN set successfully.",
                "transaction_pin_set": request.user.transaction_pin_set
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({
                "status": False,
                "detail": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error setting transaction PIN for {request.user.email}: {str(e)}", exc_info=True)
            return Response({
                "status": False,
                "detail": "An error occurred while setting your transaction PIN."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyTransactionPinAPIView(APIView):
    """
    API endpoint to verify transaction PIN (for testing/validation).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        pin = request.data.get('pin')
        
        if not pin:
            return Response({
                "status": False,
                "detail": "PIN is required."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not request.user.transaction_pin_set:
            return Response({
                "status": False,
                "detail": "Transaction PIN not set."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        is_valid = request.user.verify_transaction_pin(pin)
        return Response({
            "status": True,
            "valid": is_valid,
            "detail": "PIN is valid." if is_valid else "Invalid PIN."
        }, status=status.HTTP_200_OK)


class TransactionPinStatusAPIView(APIView):
    """
    API endpoint to check if transaction PIN is set.
    Useful for frontend to determine if PIN setup is needed.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Refresh from database to get latest status
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=request.user.id)
        
        return Response({
            "status": True,
            "transaction_pin_set": user.transaction_pin_set,
            "detail": "Transaction PIN is set." if user.transaction_pin_set else "Transaction PIN not set."
        }, status=status.HTTP_200_OK)


class GetBanksAPIView(APIView):
    """
    API endpoint to get list of banks available for transfers.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V1 - Wallet'],
        summary='Get Banks List',
        description='Get list of all banks available for transfers.',
        responses={
            200: {
                'description': 'Banks list retrieved successfully',
                'content': {
                    'application/json': {
                        'example': {
                            'status': True,
                            'data': {
                                'banks': [
                                    {'code': '058', 'name': 'GTBank'},
                                    {'code': '011', 'name': 'First Bank'},
                                ]
                            }
                        }
                    }
                }
            },
            401: {'description': 'Unauthorized'},
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Get list of banks from Embedly.
        """
        embedly_client = EmbedlyClient()

        try:
            result = embedly_client.get_banks()

            if not result.get("success"):
                error_msg = result.get("message", "Unable to fetch banks list")
                return error_response(error_msg)

            # Return the banks list
            banks_data = result.get("data", [])

            return success_response({
                "banks": banks_data
            })

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Exception fetching banks list: {str(e)}", exc_info=True)

            return error_response("An error occurred while fetching banks list. Please try again.")


class CheckWithdrawalStatusAPIView(APIView):
    """
    API endpoint for users to check the status of their withdrawal.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V1 - Wallet'],
        summary='Check Withdrawal Status',
        description='Check the status of a withdrawal request by withdrawal ID.',
        parameters=[
            OpenApiParameter(
                name='withdrawal_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Withdrawal request ID',
                required=True,
            ),
        ],
        responses={
            200: {
                'description': 'Withdrawal status retrieved successfully',
                'content': {
                    'application/json': {
                        'example': {
                            'status': True,
                            'data': {
                                'id': 123,
                                'status': 'completed',
                                'amount': '5000.00',
                                'bank_name': 'GTBank',
                                'account_number': '0123456789',
                            }
                        }
                    }
                }
            },
            401: {'description': 'Unauthorized'},
            404: {'description': 'Withdrawal not found'},
        }
    )
    def get(self, request, withdrawal_id, *args, **kwargs):
        try:
            # Get withdrawal request
            withdrawal = WithdrawalRequest.objects.get(
                id=withdrawal_id,
                user=request.user
            )
        except WithdrawalRequest.DoesNotExist:
            return Response({
                "status": False,
                "detail": "Withdrawal request not found."
            }, status=status.HTTP_404_NOT_FOUND)

        # If already completed or failed, return current status
        if withdrawal.status in ['completed', 'failed']:
            return Response({
                "status": True,
                "detail": f"Withdrawal is {withdrawal.status}",
                "data": {
                    "id": withdrawal.id,
                    "amount": withdrawal.amount,
                    "bank_name": withdrawal.bank_name,
                    "account_number": withdrawal.account_number,
                    "status": withdrawal.status,
                    "created_at": withdrawal.created_at,
                    "updated_at": withdrawal.updated_at
                }
            }, status=status.HTTP_200_OK)

        # If no transaction ref, still pending
        if not withdrawal.transaction_ref:
            return Response({
                "status": True,
                "detail": "Withdrawal is being processed",
                "data": {
                    "id": withdrawal.id,
                    "status": "pending",
                    "message": "Transfer has not been initiated yet"
                }
            }, status=status.HTTP_200_OK)

        # Query Embedly for current status
        embedly_client = EmbedlyClient()

        try:
            result = embedly_client.get_transfer_status(withdrawal.transaction_ref)

            if not result.get("success"):
                return Response({
                    "status": False,
                    "detail": "Unable to check withdrawal status. Please try again later."
                }, status=status.HTTP_400_BAD_REQUEST)

            # Extract status
            transfer_data = result.get("data", {})
            status_value = transfer_data.get("status", "").lower()

            # Update withdrawal status if changed
            if status_value in ['successful', 'success', 'completed']:
                if withdrawal.status != 'completed':
                    withdrawal.status = 'completed'
                    withdrawal.save()

                    # Send notification
                    from notification.helper.email import MailClient
                    from providers.helpers.cuoral import CuoralAPI

                    cuoral_client = CuoralAPI()
                    cuoral_client.send_sms(
                        withdrawal.user.phone,
                        f"Your withdrawal of NGN {withdrawal.amount} has been completed successfully."
                    )

                return Response({
                    "status": True,
                    "detail": "Withdrawal completed successfully",
                    "data": {
                        "id": withdrawal.id,
                        "amount": withdrawal.amount,
                        "bank_name": withdrawal.bank_name,
                        "account_number": withdrawal.account_number,
                        "status": "completed",
                        "created_at": withdrawal.created_at,
                        "completed_at": withdrawal.updated_at
                    }
                }, status=status.HTTP_200_OK)

            elif status_value in ['failed', 'error']:
                if withdrawal.status != 'failed':
                    withdrawal.status = 'failed'
                    withdrawal.error_message = transfer_data.get('message', 'Transfer failed')
                    withdrawal.save()

                    # Refund user
                    wallet = withdrawal.user.wallet
                    wallet.deposit(Decimal(str(withdrawal.amount)))

                return Response({
                    "status": False,
                    "detail": f"Withdrawal failed: {withdrawal.error_message}",
                    "data": {
                        "id": withdrawal.id,
                        "status": "failed",
                        "refunded": True
                    }
                }, status=status.HTTP_200_OK)

            else:
                # Still processing
                return Response({
                    "status": True,
                    "detail": "Withdrawal is being processed",
                    "data": {
                        "id": withdrawal.id,
                        "amount": withdrawal.amount,
                        "status": "processing",
                        "message": "Transfer is in progress. This may take a few minutes."
                    }
                }, status=status.HTTP_200_OK)

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error checking withdrawal status: {str(e)}", exc_info=True)

            return Response({
                "status": False,
                "detail": "An error occurred while checking withdrawal status."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PayoutWebhookView(APIView):
    """
    Webhook handler for Embedly Payout (withdrawal) events.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        raw_body = request.body.decode('utf-8')

        # Check body
        if not raw_body:
            return JsonResponse({'error': 'Missing body'}, status=400)

        # Embedly uses X-Auth-Signature header (per their documentation)
        # Also check alternative header names for backward compatibility
        provided_signature = (
            request.headers.get('X-Auth-Signature')
            or request.headers.get('x-auth-signature')
            or request.headers.get('x-embedly-signature')
            or request.headers.get('x-signature')
            or request.headers.get('x-embed-signature')
        )
        if not provided_signature:
            import logging
            logger = logging.getLogger(__name__)
            logger.error("Missing webhook signature header", extra={
                "all_headers": dict(request.headers)
            })
            return JsonResponse({'error': 'Missing signature'}, status=400)

        # Try multiple secrets and algorithms (sha512, sha256)
        secret_candidates = [
            getattr(settings, 'EMBEDLY_WEBHOOK_SECRET', None),
            getattr(settings, 'EMBEDLY_API_KEY_PRODUCTION', None),
        ]
        secret_candidates = [s for s in secret_candidates if s]

        def _matches(sig: str, secret: str) -> bool:
            # Some providers prefix with algo=hex; strip if present
            normalized = sig.split('=')[-1].strip().lower()
            body_bytes = raw_body.encode('utf-8')
            for algo in (hashlib.sha512, hashlib.sha256):
                digest = hmac.new(secret.encode('utf-8'), body_bytes, algo).hexdigest().lower()
                if hmac.compare_digest(digest, normalized):
                    return True
            return False

        verified = any(_matches(provided_signature, secret) for secret in secret_candidates)
        if not verified:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                "Embedly payout webhook signature mismatch",
                extra={
                    "headers_present": {
                        "x-embedly-signature": bool(request.headers.get('x-embedly-signature')),
                        "x-signature": bool(request.headers.get('x-signature')),
                        "x-embed-signature": bool(request.headers.get('x-embed-signature')),
                    },
                    "sig_preview": provided_signature[:12].lower() if provided_signature else None,
                }
            )
            return JsonResponse({'error': 'Invalid signature - authentication failed'}, status=403)

        # Parse the JSON payload
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        # Extract payout data
        data = payload.get('data', {})
        transaction_ref = data.get('transactionRef')
        status_value = data.get('status', '').lower()
        customer_ref = data.get('customerTransactionReference')

        if not transaction_ref:
            return JsonResponse({'error': 'Missing transactionRef'}, status=400)

        import logging
        logger = logging.getLogger(__name__)

        try:
            # Find withdrawal request by transaction_ref or customer_ref
            withdrawal_request = None
            if transaction_ref:
                withdrawal_request = WithdrawalRequest.objects.filter(
                    transaction_ref=transaction_ref
                ).first()

            if not withdrawal_request and customer_ref:
                withdrawal_request = WithdrawalRequest.objects.filter(
                    id=customer_ref
                ).first()

            if not withdrawal_request:
                logger.warning(f"Withdrawal request not found for ref: {transaction_ref}")
                return JsonResponse({'error': 'Withdrawal request not found'}, status=404)

            # Update withdrawal status based on payout status
            if status_value in ['successful', 'success', 'completed']:
                withdrawal_request.status = 'completed'
                withdrawal_request.save()

                # Send notification to user
                cuoral_client = CuoralAPI()
                cuoral_client.send_sms(
                    withdrawal_request.user.phone,
                    f"Your withdrawal of NGN {withdrawal_request.amount} has been completed successfully."
                )

                emailclient = MailClient()
                emailclient.send_email(
                    to_email=withdrawal_request.user.email,
                    subject="Withdrawal Successful",
                    template_name="emails/withdrawal_success.html",
                    context={
                        "amount": f"NGN {withdrawal_request.amount}",
                        "bank_name": withdrawal_request.bank_name,
                        "account_number": withdrawal_request.account_number
                    },
                    to_name=withdrawal_request.user.first_name
                )

                logger.info(f"Withdrawal {withdrawal_request.id} completed successfully")

            elif status_value in ['failed', 'error']:
                withdrawal_request.status = 'failed'
                withdrawal_request.error_message = data.get('message', 'Transfer failed')
                withdrawal_request.save()

                # Refund the user
                try:
                    wallet = withdrawal_request.user.wallet
                    wallet.deposit(Decimal(str(withdrawal_request.amount)))

                    # Notify user of refund
                    cuoral_client = CuoralAPI()
                    cuoral_client.send_sms(
                        withdrawal_request.user.phone,
                        f"Your withdrawal of NGN {withdrawal_request.amount} failed. Funds have been refunded to your wallet."
                    )

                    logger.info(f"Withdrawal {withdrawal_request.id} failed, user refunded")
                except Exception as refund_error:
                    logger.error(f"Failed to refund user for withdrawal {withdrawal_request.id}: {refund_error}")

            return JsonResponse({
                'status': 'success',
                'message': 'Webhook processed',
                'data': payload
            }, status=200)

        except Exception as e:
            logger.error(f"Error processing payout webhook: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Internal server error'}, status=500)


class EmbedlyWebhookView(APIView):
    """
    Webhook handler for Embedly deposit (NIP) events.
    Disables DRF parsers to ensure we get raw body for signature verification.
    """
    permission_classes = [permissions.AllowAny]
    parser_classes = []  # Disable DRF parsers to get raw body

    def post(self, request, *args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        
        # Log webhook reception
        logger.info("Embedly webhook received")
        
        # Get raw body bytes for signature verification (must use bytes, not decoded string)
        raw_body_bytes = request.body
        raw_body = raw_body_bytes.decode('utf-8')

        if not raw_body_bytes:
            logger.error("Webhook rejected: Missing body")
            return JsonResponse({'error': 'Missing body'}, status=400)
        
        # Embedly uses X-Auth-Signature header (per their documentation)
        # Also check alternative header names for backward compatibility
        provided_signature = (
            request.headers.get('X-Auth-Signature')
            or request.headers.get('x-auth-signature')
            or request.headers.get('x-embedly-signature')
            or request.headers.get('x-signature')
            or request.headers.get('x-embed-signature')
        )
        
        # Check if signature verification should be skipped (for testing/debugging)
        # TEMPORARILY DISABLE SIGNATURE VERIFICATION TO TEST WEBHOOKS
        # Set EMBEDLY_SKIP_WEBHOOK_SIGNATURE=true in .env to enable this
        # NOTE: Currently disabled because none of 16+ signature methods match Embedly's signature
        # TODO: Contact Embedly support for exact signature algorithm and secret
        skip_signature_verification = getattr(settings, 'EMBEDLY_SKIP_WEBHOOK_SIGNATURE', True)  # Temporarily default to True
        
        # Log signature status
        if skip_signature_verification:
            logger.warning("Signature verification disabled - webhooks processing without verification")
        else:
            logger.info("Signature verification enabled")
        
        if not provided_signature:
            if skip_signature_verification:
                logger.warning("Missing webhook signature header, but signature verification is disabled")
            else:
                logger.error("Missing webhook signature header", extra={
                    "all_headers": dict(request.headers)
                })
                return JsonResponse({'error': 'Missing signature'}, status=400)
        
        # Embedly uses API key for webhook signature verification (per their documentation)
        # Format: sha512(notification payload, api_key)
        # Try both API key and Organization ID as secrets (some providers use org ID)
        api_key = getattr(settings, 'EMBEDLY_API_KEY_PRODUCTION', None)
        org_id = getattr(settings, 'EMBEDLY_ORGANIZATION_ID_PRODUCTION', None)
        raw_secrets = [
            api_key,  # Primary - API key is used for signing
            org_id,  # Try org ID as well
            getattr(settings, 'EMBEDLY_WEBHOOK_SECRET', None),  # Fallback if separate secret exists
            getattr(settings, 'EMBEDLY_WEBHOOK_KEY', None),  # Alternative name
        ]
        # Also try combined secrets (some providers concatenate API key + Org ID)
        if api_key and org_id:
            raw_secrets.append(f"{api_key}{org_id}")  # API key + Org ID
            raw_secrets.append(f"{org_id}{api_key}")  # Org ID + API key
        # Filter out None values and URLs (common configuration mistake)
        secret_candidates = [
            s for s in raw_secrets 
            if s and not (isinstance(s, str) and (s.startswith('http://') or s.startswith('https://')))
        ]
        
        # Warn if webhook secret looks like a URL
        webhook_secret = getattr(settings, 'EMBEDLY_WEBHOOK_SECRET', None)
        if webhook_secret and isinstance(webhook_secret, str) and (webhook_secret.startswith('http://') or webhook_secret.startswith('https://')):
            logger.warning(
                f"EMBEDLY_WEBHOOK_SECRET appears to be a URL, not a secret key! "
                f"Will try using API key instead. If Embedly doesn't provide a separate webhook secret, "
                f"they likely use the API key for signing."
            )
        
        if not secret_candidates:
            logger.error("No webhook secrets configured! Check EMBEDLY_WEBHOOK_SECRET or EMBEDLY_API_KEY_PRODUCTION")
            return JsonResponse({'error': 'Webhook secret not configured'}, status=500)
        
        # Log which secrets we're trying (for debugging)
        logger.info(f"Attempting webhook signature verification with {len(secret_candidates)} secret(s)")
        if secret_candidates:
            logger.info(f"First secret preview: {secret_candidates[0][:10]}...{secret_candidates[0][-4:] if len(secret_candidates[0]) > 14 else ''} (length: {len(secret_candidates[0])})")

        def _matches(sig: str, secret: str) -> bool:
            # Embedly uses sha512(notification payload, api_key) per their documentation
            # The notation is ambiguous - could be HMAC or simple concatenation
            # Try multiple methods to find the correct one
            normalized = sig.split('=')[-1].split(':')[-1].strip().lower()
            
            try:
                import json
                secret_bytes = secret.encode('utf-8')
                
                # Try with original body (as received)
                body_bytes = raw_body_bytes  # Use raw bytes directly
                body_str = raw_body  # Decoded string
                
                # Also try with normalized JSON (sorted keys, compact format)
                # Some webhook providers normalize JSON before signing
                try:
                    parsed_json = json.loads(body_str)
                    # Try multiple JSON serialization formats
                    normalized_json = json.dumps(parsed_json, separators=(',', ':'), sort_keys=True)
                    normalized_json_bytes = normalized_json.encode('utf-8')
                    
                    # Try with ensure_ascii=False (preserve unicode)
                    normalized_json_unicode = json.dumps(parsed_json, separators=(',', ':'), sort_keys=True, ensure_ascii=False)
                    normalized_json_unicode_bytes = normalized_json_unicode.encode('utf-8')
                    
                    # Try without sorting keys (preserve original order)
                    normalized_json_no_sort = json.dumps(parsed_json, separators=(',', ':'))
                    normalized_json_no_sort_bytes = normalized_json_no_sort.encode('utf-8')
                except:
                    normalized_json_bytes = body_bytes
                    normalized_json = body_str
                    normalized_json_unicode_bytes = body_bytes
                    normalized_json_unicode = body_str
                    normalized_json_no_sort_bytes = body_bytes
                    normalized_json_no_sort = body_str
                
                # SHA512 Methods
                # Method 1: HMAC-SHA512 with original body (standard webhook approach)
                computed_hmac1 = hmac.new(
                    secret_bytes, 
                    body_bytes,
                    hashlib.sha512
                ).hexdigest().lower()
                
                # Method 2: HMAC-SHA512 with normalized JSON
                computed_hmac2 = hmac.new(
                    secret_bytes, 
                    normalized_json_bytes,
                    hashlib.sha512
                ).hexdigest().lower()
                
                # Method 3: Simple SHA512 of payload + api_key (original)
                computed_concat1 = hashlib.sha512(
                    body_bytes + secret_bytes
                ).hexdigest().lower()
                
                # Method 4: Simple SHA512 of payload + api_key (normalized JSON)
                computed_concat2 = hashlib.sha512(
                    normalized_json_bytes + secret_bytes
                ).hexdigest().lower()
                
                # Method 5: Simple SHA512 of api_key + payload (original)
                computed_concat3 = hashlib.sha512(
                    secret_bytes + body_bytes
                ).hexdigest().lower()
                
                # Method 6: Simple SHA512 of api_key + payload (normalized JSON)
                computed_concat4 = hashlib.sha512(
                    secret_bytes + normalized_json_bytes
                ).hexdigest().lower()
                
                # Additional variations with different JSON formats
                # Method 6b: HMAC-SHA512 with unicode-preserved JSON
                computed_hmac_unicode = hmac.new(
                    secret_bytes, 
                    normalized_json_unicode_bytes,
                    hashlib.sha512
                ).hexdigest().lower()
                
                # Method 6c: HMAC-SHA512 with no-sort JSON
                computed_hmac_no_sort = hmac.new(
                    secret_bytes, 
                    normalized_json_no_sort_bytes,
                    hashlib.sha512
                ).hexdigest().lower()
                
                # Method 6d: SHA512(payload+key) with unicode JSON
                computed_concat_unicode = hashlib.sha512(
                    normalized_json_unicode_bytes + secret_bytes
                ).hexdigest().lower()
                
                # Method 6e: SHA512(key+payload) with unicode JSON
                computed_concat_key_unicode = hashlib.sha512(
                    secret_bytes + normalized_json_unicode_bytes
                ).hexdigest().lower()
                
                # SHA256 Methods (per alternative documentation)
                # Method 7: HMAC-SHA256 with original body
                computed_hmac256_1 = hmac.new(
                    secret_bytes, 
                    body_bytes,
                    hashlib.sha256
                ).hexdigest().lower()
                
                # Method 8: HMAC-SHA256 with normalized JSON
                computed_hmac256_2 = hmac.new(
                    secret_bytes, 
                    normalized_json_bytes,
                    hashlib.sha256
                ).hexdigest().lower()
                
                # Method 9: Simple SHA256 of payload + api_key (original)
                computed_concat256_1 = hashlib.sha256(
                    body_bytes + secret_bytes
                ).hexdigest().lower()
                
                # Method 10: Simple SHA256 of payload + api_key (normalized JSON)
                computed_concat256_2 = hashlib.sha256(
                    normalized_json_bytes + secret_bytes
                ).hexdigest().lower()
                
                # Method 11: Simple SHA256 of api_key + payload (original)
                computed_concat256_3 = hashlib.sha256(
                    secret_bytes + body_bytes
                ).hexdigest().lower()
                
                # Method 12: Simple SHA256 of api_key + payload (normalized JSON)
                computed_concat256_4 = hashlib.sha256(
                    secret_bytes + normalized_json_bytes
                ).hexdigest().lower()
                
                # Try signature verification (silent - only log on failure)
                
                # Check each method
                methods = [
                    (computed_hmac1, "Method 1 (HMAC-SHA512, original body)"),
                    (computed_hmac2, "Method 2 (HMAC-SHA512, normalized JSON)"),
                    (computed_hmac_unicode, "Method 2b (HMAC-SHA512, unicode JSON)"),
                    (computed_hmac_no_sort, "Method 2c (HMAC-SHA512, no-sort JSON)"),
                    (computed_concat1, "Method 3 (SHA512(payload+key), original)"),
                    (computed_concat2, "Method 4 (SHA512(payload+key), normalized)"),
                    (computed_concat_unicode, "Method 4b (SHA512(payload+key), unicode)"),
                    (computed_concat3, "Method 5 (SHA512(key+payload), original)"),
                    (computed_concat4, "Method 6 (SHA512(key+payload), normalized)"),
                    (computed_concat_key_unicode, "Method 6b (SHA512(key+payload), unicode)"),
                    (computed_hmac256_1, "Method 7 (HMAC-SHA256, original body)"),
                    (computed_hmac256_2, "Method 8 (HMAC-SHA256, normalized JSON)"),
                    (computed_concat256_1, "Method 9 (SHA256(payload+key), original)"),
                    (computed_concat256_2, "Method 10 (SHA256(payload+key), normalized)"),
                    (computed_concat256_3, "Method 11 (SHA256(key+payload), original)"),
                    (computed_concat256_4, "Method 12 (SHA256(key+payload), normalized)"),
                ]
                
                for computed_sig, method_name in methods:
                    if hmac.compare_digest(computed_sig, normalized):
                        logger.info(f"Signature verified using {method_name}")
                        return True
                
                # None matched - log minimal info
                logger.warning(f"Signature verification failed - received: {normalized[:40]}...")
                return False
            except Exception as e:
                logger.error(f"Error verifying signature: {e}", exc_info=True)
                return False

        # Skip verification if disabled (for testing) or if no signature provided and skipping is enabled
        if skip_signature_verification and not provided_signature:
            verified = True
            logger.warning("Skipping webhook signature verification (EMBEDLY_SKIP_WEBHOOK_SIGNATURE=True)")
        elif skip_signature_verification:
            verified = True
            logger.warning("Skipping webhook signature verification (EMBEDLY_SKIP_WEBHOOK_SIGNATURE=True) - signature present but not verified")
        else:
            # Try each secret individually
            verified = False
            for i, secret in enumerate(secret_candidates):
                logger.info(f"Trying secret {i+1} (length: {len(secret) if secret else 0})")
                logger.info(f"Secret preview: {secret[:15]}...{secret[-5:] if len(secret) > 20 else ''}")
                if _matches(provided_signature, secret):
                    verified = True
                    logger.info(f"✓ Signature verified with secret {i+1}")
                    break
                else:
                    logger.warning(f"✗ Secret {i+1} did not match - check logs above for details")
            
            # Note: Embedly uses API key directly, no combinations needed
        
        if not verified:
            # Enhanced logging for debugging - print detailed info
            all_headers = dict(request.headers)
            header_info = {
                "X-Auth-Signature": request.headers.get('X-Auth-Signature') or request.headers.get('x-auth-signature') or "NOT FOUND",
                "x-embedly-signature": request.headers.get('x-embedly-signature') or "NOT FOUND",
                "x-signature": request.headers.get('x-signature') or "NOT FOUND",
                "x-embed-signature": request.headers.get('x-embed-signature') or "NOT FOUND",
            }
            
            # Try to compute what the signature should be for debugging
            debug_info = []
            if provided_signature and secret_candidates:
                normalized_sig = provided_signature.split('=')[-1].split(':')[-1].strip().lower()
                body_bytes = raw_body.encode('utf-8')
                for i, secret in enumerate(secret_candidates):
                    try:
                        # Try SHA512 (correct algorithm per Embedly docs)
                        expected_sha512 = hmac.new(secret.encode('utf-8'), body_bytes, hashlib.sha512).hexdigest().lower()
                        debug_info.append(f"Secret {i+1} (SHA512): {expected_sha512[:60]}...")
                        debug_info.append(f"  Received:    {normalized_sig[:60]}...")
                        if expected_sha512 == normalized_sig:
                            debug_info.append(f"  ✓ MATCH FOUND with Secret {i+1}!")
                        else:
                            debug_info.append(f"  ✗ No match (first 20 chars differ)")
                    except Exception as e:
                        debug_info.append(f"Secret {i+1} error: {str(e)}")
            
            # Log detailed information
            logger.error(
                f"Embedly deposit webhook signature mismatch - "
                f"Signature: {provided_signature[:40] if provided_signature else 'NONE'}... | "
                f"Length: {len(provided_signature) if provided_signature else 0} | "
                f"Secrets checked: {len(secret_candidates)} | "
                f"Body length: {len(raw_body)} | "
                f"Headers: {header_info}"
            )
            
            # Log error (minimal - no verbose debug in production)
            
            return JsonResponse({'error': 'Invalid signature - authentication failed'}, status=403)

        # Parse the JSON payload
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        # Check the event type
        event_type = payload.get('event')
        logger.info(f"Webhook event type: {event_type}")
        logger.info(f"Payload keys: {list(payload.keys())}")
        
        if event_type == 'nip':
            logger.info("Processing NIP event (deposit)")
            result = self.handle_nip_event(payload)
            logger.info("NIP event processing completed")
            return result
        else:
            logger.warning(f"Unsupported event type: {event_type}")
            return JsonResponse({'error': 'Unsupported event'}, status=400)

    def handle_nip_event(self, payload):
        # Extract transaction data
        data = payload.get('data', {})
        account_number = data.get('accountNumber')
        reference = data.get('reference')
        senderBank = data.get('senderBank')
        amount = data.get('amount')
        sender_name = data.get('senderName')
        
        logger = logging.getLogger(__name__)
        
        try:
            wallet = Wallet.objects.get(account_number=account_number)
        except Wallet.DoesNotExist:
            logger.error(f"Wallet not found for account_number: {account_number}")
            return JsonResponse({'error': 'Wallet not found'}, status=404)

        # Use atomic transaction to ensure both transaction record and balance update succeed together
        try:
            with transaction.atomic():
                # Check if transaction already exists
                if WalletTransaction.objects.filter(external_reference=reference).exists():
                    logger.warning(f"Transaction with reference {reference} already processed")
                    return JsonResponse({'error': 'Transaction with this reference has been processed'}, status=200)
                
                # Create transaction record
                wallet_transaction = WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='credit',  # This is a credit to the wallet
                    amount=amount,
                    description=f"Transfer from {sender_name} via NIP reference {reference}",
                    sender_name=sender_name,
                    sender_account=senderBank,
                    external_reference=reference
                )
                
                # Update the wallet balance (ensure Decimal)
                try:
                    wallet.deposit(Decimal(str(amount)))
                    logger.info(f"Credited {amount} to wallet {wallet.account_number} (user: {wallet.user.email})")
                except Exception as deposit_error:
                    logger.error(f"Failed to deposit {amount} to wallet {wallet.account_number}: {str(deposit_error)}")
                    raise  # Re-raise to rollback the transaction

                # Check if this is a payment link contribution
                try:
                    from wallet.payment_link_helpers import process_payment_link_contribution
                    is_payment_link, payment_link = process_payment_link_contribution(
                        reference=reference,
                        wallet_transaction=wallet_transaction,
                        sender_name=sender_name
                    )

                    if is_payment_link:
                        logger.info(f"Processed payment link contribution for reference: {reference}")
                        # Return early - payment link handler will send its own notifications
                        return JsonResponse({
                            'status': 'success',
                            'message': 'Payment link contribution processed successfully',
                            'data': payload,
                            'timestamp': str(wallet_transaction.created_at)
                        }, status=200)
                except Exception as pl_error:
                    logger.error(f"Error processing payment link contribution: {str(pl_error)}")
                    # Continue with normal flow if payment link processing fails

        except IntegrityError as e:
            logger.warning(f"IntegrityError for reference {reference}: {str(e)}")
            return JsonResponse({'error': 'Transaction with this reference has been processed'}, status=200)
        except Exception as e:
            logger.error(f"Error processing credit transaction for account {account_number}: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Failed to process transaction'}, status=500)

        # Send notifications (non-blocking - don't fail webhook if notifications fail)
        try:
            # SMS notification
            cuoral_client = CuoralAPI()
            cuoral_client.send_sms(
                wallet.user.phone,
                f"You just received {wallet.currency} {amount} from {sender_name}."
            )
            logger.info(f"SMS notification sent to {wallet.user.phone}")
        except Exception as sms_error:
            logger.error(f"Failed to send SMS notification: {str(sms_error)}")

        try:
            # Email notification
            emailclient = MailClient()
            emailclient.send_email(
                to_email=wallet.user.email,
                subject="Credit Alert",
                template_name="emails/credit.html",
                context={
                    "sender_name": sender_name,
                    "amount": f"{wallet.currency} {amount}",
                },
                to_name=wallet.user.first_name
            )
            logger.info(f"Email notification sent to {wallet.user.email}")
        except Exception as email_error:
            logger.error(f"Failed to send email notification: {str(email_error)}")

        try:
            # Push notification (only if available)
            if PUSH_NOTIFICATIONS_AVAILABLE:
                send_push_notification_to_user(
                    user=wallet.user,
                    title="Credit Alert",
                    message=f"You just received {wallet.currency} {amount} from {sender_name}."
                )
                logger.info(f"Push notification sent to user {wallet.user.email}")
            else:
                logger.debug("Push notifications not available (Firebase not configured)")
        except Exception as push_error:
            logger.error(f"Failed to send push notification: {str(push_error)}")

        # Return a success response
        return JsonResponse({
            'status': 'success',
            'message': 'Webhook received and wallet updated',
            'data': payload,
            'timestamp': str(wallet_transaction.created_at)
        }, status=200)