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
from wallet.payment_link_helpers import process_payment_link_contribution, try_match_deposit_to_pending_contribution

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


class PSB9WebhookView(APIView):
    """
    9PSB Webhook Handler - Processes deposit notifications from 9 Payment Service Bank

    This endpoint receives webhook notifications when deposits are made to user wallets.
    9PSB sends POST requests with transaction details when:
    - A transfer is made to a user's virtual account
    - An account upgrade is completed

    Security: Webhook signature verification is required
    """
    permission_classes = []  # Public endpoint, secured by signature verification

    @extend_schema(
        tags=['Webhooks'],
        summary='9PSB Webhook Handler',
        description='Receives and processes deposit notifications from 9 Payment Service Bank',
        exclude=True  # Hide from public API docs
    )
    def post(self, request, *args, **kwargs):
        """
        Handle incoming 9PSB webhook for deposits

        Expected payload from 9PSB:
        {
            "event": "transfer.credit",
            "data": {
                "reference": "PSB9_TXN_123456",
                "accountNumber": "0123456789",
                "accountName": "John Doe",
                "amount": 10000.00,
                "narration": "Transfer from GTBank",
                "senderName": "Jane Smith",
                "senderAccount": "9876543210",
                "senderBank": "GTBank",
                "transactionDate": "2025-12-15T10:30:00Z",
                "sessionId": "SESSION_123"
            }
        }
        """
        import logging
        import hashlib
        import hmac
        from django.conf import settings
        from django.views.decorators.csrf import csrf_exempt

        logger = logging.getLogger(__name__)

        # Get raw body for signature verification
        try:
            raw_body = request.body.decode('utf-8')
        except Exception as e:
            logger.error(f"9PSB webhook: Failed to decode request body: {e}")
            return error_response(
                message="Invalid request body",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Verify webhook signature
        signature_header = request.headers.get('X-9PSB-Signature') or request.headers.get('X-Webhook-Signature')

        if not signature_header:
            logger.error("9PSB webhook: Missing signature header")
            return error_response(
                message="Webhook signature missing",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # Verify signature using 9PSB client secret (used for webhook signing)
        client_secret = getattr(settings, 'PSB9_CLIENT_SECRET', '')
        if not client_secret:
            logger.error("9PSB webhook: PSB9_CLIENT_SECRET not configured")
            return error_response(
                message="Webhook verification failed: Configuration error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Calculate expected signature (9PSB uses HMAC-SHA256)
        expected_signature = hmac.new(
            client_secret.encode('utf-8'),
            raw_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Compare signatures securely
        if not hmac.compare_digest(expected_signature, signature_header.strip()):
            logger.error(f"9PSB webhook: Invalid signature. Expected: {expected_signature[:10]}..., Got: {signature_header[:10]}...")
            return error_response(
                message="Invalid webhook signature",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        logger.info("9PSB webhook: Signature verified successfully")

        # Parse webhook data
        webhook_data = request.data
        event_type = webhook_data.get('event')
        data = webhook_data.get('data', {})

        # Only process credit/deposit events
        if event_type != 'transfer.credit':
            logger.info(f"9PSB webhook: Ignoring event type: {event_type}")
            return success_response(
                message="Event acknowledged",
                data={"event": event_type, "status": "ignored"}
            )

        # Extract transaction details
        reference = data.get('reference')
        account_number = data.get('accountNumber')
        amount = data.get('amount')
        narration = data.get('narration', '')
        sender_name = data.get('senderName', '')
        sender_account = data.get('senderAccount', '')
        transaction_date = data.get('transactionDate')

        # Validate required fields
        if not all([reference, account_number, amount]):
            logger.error(f"9PSB webhook: Missing required fields. Data: {data}")
            return error_response(
                message="Missing required fields in webhook data",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Check for duplicate transaction
        if WalletTransaction.objects.filter(external_reference=reference).exists():
            logger.warning(f"9PSB webhook: Duplicate transaction {reference}, skipping")
            return success_response(
                message="Transaction already processed",
                data={"reference": reference, "status": "duplicate"}
            )

        # Find wallet by 9PSB account number
        try:
            wallet = Wallet.objects.get(psb9_account_number=account_number)
        except Wallet.DoesNotExist:
            logger.error(f"9PSB webhook: Wallet not found for account {account_number}")
            return error_response(
                message=f"Wallet not found for account number {account_number}",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Process the deposit
        try:
            with transaction.atomic():
                # Convert amount to Decimal
                amount_decimal = Decimal(str(amount))

                # Credit wallet
                wallet.deposit(amount_decimal)

                # Create transaction record
                wallet_transaction = WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='credit',
                    amount=amount_decimal,
                    description=narration or f"Deposit from {sender_name or 'Bank Transfer'}",
                    sender_name=sender_name,
                    sender_account=sender_account,
                    external_reference=reference
                )

                logger.info(
                    f"9PSB webhook: Deposit processed successfully. "
                    f"User: {wallet.user.email}, Amount: {amount_decimal}, Reference: {reference}"
                )

                # Check if this is a payment link contribution
                is_payment_link_contribution = False
                try:
                    is_pl, payment_link = process_payment_link_contribution(
                        reference=reference,
                        wallet_transaction=wallet_transaction,
                        sender_name=sender_name,
                        narration=narration,
                    )
                    if is_pl:
                        is_payment_link_contribution = True
                        logger.info(
                            f"9PSB: Payment link contribution processed. "
                            f"Reference: {reference}, Payment Link: {payment_link.token}"
                        )
                except Exception as pl_error:
                    logger.error(
                        f"9PSB: Failed to process payment link contribution. "
                        f"Reference: {reference}, Narration: {narration}, Error: {str(pl_error)}",
                        exc_info=True
                    )

                # If no PL- reference matched, try to match against pending contributions
                if not is_payment_link_contribution:
                    try:
                        matched, matched_link = try_match_deposit_to_pending_contribution(wallet_transaction)
                        if matched:
                            is_payment_link_contribution = True
                            logger.info(
                                f"9PSB: Reverse-matched deposit {reference} to pending contribution "
                                f"for link={matched_link.token}"
                            )
                    except Exception as match_error:
                        logger.error(f"9PSB: Failed reverse-match for deposit {reference}: {str(match_error)}", exc_info=True)

                # Send notifications (skip generic ones for payment link contributions)
                if not is_payment_link_contribution:
                    # Send push notification to user
                    try:
                        if PUSH_NOTIFICATIONS_AVAILABLE:
                            send_push_notification_to_user(
                                user=wallet.user,
                                title="Deposit Received",
                                body=f"Your wallet has been credited with ₦{amount_decimal:,.2f}",
                                data={
                                    'type': 'wallet_credit',
                                    'amount': str(amount_decimal),
                                    'reference': reference
                                }
                            )
                    except Exception as e:
                        logger.warning(f"9PSB webhook: Failed to send push notification: {e}")

                    # Send in-app notification
                    try:
                        from notification.models import Notification
                        Notification.objects.create(
                            user=wallet.user,
                            title="Deposit Received",
                            message=f"Your wallet has been credited with ₦{amount_decimal:,.2f}",
                            notification_type='wallet_credit',
                            data={
                                'amount': str(amount_decimal),
                                'reference': reference,
                                'transaction_id': str(wallet_transaction.id)
                            }
                        )
                    except Exception as e:
                        logger.warning(f"9PSB webhook: Failed to create in-app notification: {e}")

                return success_response(
                    message="Deposit processed successfully",
                    data={
                        "reference": reference,
                        "account_number": account_number,
                        "amount": str(amount_decimal),
                        "new_balance": str(wallet.balance),
                        "transaction_id": str(wallet_transaction.id),
                        "status": "success"
                    }
                )

        except Exception as e:
            logger.error(f"9PSB webhook: Error processing deposit: {str(e)}", exc_info=True)
            return error_response(
                message=f"Failed to process deposit: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
