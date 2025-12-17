# wallet/views_v2_9psb.py
"""
V2 - 9PSB Wallet Operations
All 9PSB WAAS API integrations for production launch
"""
import logging
import uuid
from decimal import Decimal
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction as db_transaction
from django.utils import timezone

from core.helpers.response import success_response, validation_error_response, error_response
from .models import Wallet, WalletTransaction
from providers.helpers.psb9 import PSB9Client

logger = logging.getLogger(__name__)


class WalletEnquiryAPIView(APIView):
    """
    Test Case 3: Wallet Enquiry
    Get wallet balance and details from 9PSB
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get wallet balance from 9PSB"""
        user = request.user

        try:
            wallet = user.wallet
            if not wallet.psb9_account_number:
                return error_response(
                    message="No wallet account found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            # Get balance from 9PSB
            psb9_client = PSB9Client()
            result = psb9_client.get_wallet_balance(wallet.psb9_account_number)

            if result.get("status") == "success":
                balance_data = result.get("data", {})

                # Update local wallet balance
                wallet_balance = Decimal(balance_data.get("availableBalance", "0"))
                wallet.balance = wallet_balance
                wallet.save()

                return success_response(
                    message="Wallet details retrieved successfully",
                    data={
                        "account_number": wallet.account_number,
                        "account_name": wallet.account_name,
                        "bank": wallet.bank,
                        "balance": str(wallet.balance),
                        "currency": wallet.currency,
                        "psb9_data": balance_data
                    }
                )
            else:
                return error_response(
                    message=result.get("message", "Failed to retrieve wallet balance"),
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Wallet.DoesNotExist:
            return error_response(
                message="Wallet not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Wallet enquiry error: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to retrieve wallet details",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DebitWalletAPIView(APIView):
    """
    Test Case 4: Debit Wallet
    Debit funds from wallet
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Debit wallet"""
        user = request.user
        amount = request.data.get('amount')
        narration = request.data.get('narration', 'Debit transaction')

        # Validation
        if not amount:
            return validation_error_response({"amount": ["Amount is required"]})

        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                return validation_error_response({"amount": ["Amount must be greater than 0"]})
        except:
            return validation_error_response({"amount": ["Invalid amount format"]})

        try:
            wallet = user.wallet
            if not wallet.psb9_account_number:
                return error_response(
                    message="No wallet account found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            # Check balance
            if wallet.balance < amount_decimal:
                return error_response(
                    message="Insufficient balance",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Generate unique transaction ID
            transaction_id = f"DEB_{user.id}_{uuid.uuid4().hex[:12].upper()}"

            # Debit via 9PSB
            psb9_client = PSB9Client()
            result = psb9_client.debit_wallet(
                account_number=wallet.psb9_account_number,
                amount=float(amount_decimal),
                transaction_id=transaction_id,
                narration=narration
            )

            if result.get("status") == "success":
                with db_transaction.atomic():
                    # Update wallet balance
                    wallet.balance -= amount_decimal
                    wallet.save()

                    # Create transaction record
                    wallet_transaction = WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_type='debit',
                        amount=amount_decimal,
                        description=narration,
                        reference=transaction_id,
                        status='completed'
                    )

                    return success_response(
                        message="Debit successful",
                        data={
                            "transaction_id": transaction_id,
                            "amount": str(amount_decimal),
                            "new_balance": str(wallet.balance),
                            "reference": str(wallet_transaction.id)
                        }
                    )
            else:
                return error_response(
                    message=result.get("message", "Debit failed"),
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Wallet.DoesNotExist:
            return error_response(
                message="Wallet not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Debit wallet error: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to debit wallet",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreditWalletAPIView(APIView):
    """
    Test Case 5: Credit Wallet
    Credit funds to wallet (admin operation)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Credit wallet"""
        # This should be admin-only in production
        if not request.user.is_staff:
            return error_response(
                message="Unauthorized - Admin access required",
                status_code=status.HTTP_403_FORBIDDEN
            )

        account_number = request.data.get('account_number')
        amount = request.data.get('amount')
        narration = request.data.get('narration', 'Credit transaction')

        # Validation
        if not account_number or not amount:
            return validation_error_response({
                "account_number": ["Account number is required"] if not account_number else [],
                "amount": ["Amount is required"] if not amount else []
            })

        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                return validation_error_response({"amount": ["Amount must be greater than 0"]})
        except:
            return validation_error_response({"amount": ["Invalid amount format"]})

        try:
            wallet = Wallet.objects.get(psb9_account_number=account_number)

            # Generate unique transaction ID
            transaction_id = f"CRD_{wallet.user.id}_{uuid.uuid4().hex[:12].upper()}"

            # Credit via 9PSB
            psb9_client = PSB9Client()
            result = psb9_client.credit_wallet(
                account_number=account_number,
                amount=float(amount_decimal),
                transaction_id=transaction_id,
                narration=narration
            )

            if result.get("status") == "success":
                with db_transaction.atomic():
                    # Update wallet balance
                    wallet.balance += amount_decimal
                    wallet.save()

                    # Create transaction record
                    wallet_transaction = WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_type='credit',
                        amount=amount_decimal,
                        description=narration,
                        reference=transaction_id,
                        status='completed'
                    )

                    return success_response(
                        message="Credit successful",
                        data={
                            "transaction_id": transaction_id,
                            "amount": str(amount_decimal),
                            "new_balance": str(wallet.balance),
                            "reference": str(wallet_transaction.id)
                        }
                    )
            else:
                return error_response(
                    message=result.get("message", "Credit failed"),
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Wallet.DoesNotExist:
            return error_response(
                message="Wallet not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Credit wallet error: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to credit wallet",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetBanksAPIView(APIView):
    """
    Test Case 14: Get Banks
    Get list of Nigerian banks
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get list of banks"""
        try:
            psb9_client = PSB9Client()
            result = psb9_client.get_banks()

            if result.get("status") == "success":
                return success_response(
                    message="Banks retrieved successfully",
                    data=result.get("data", [])
                )
            else:
                return error_response(
                    message=result.get("message", "Failed to retrieve banks"),
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(f"Get banks error: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to retrieve banks",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OtherBanksAccountEnquiryAPIView(APIView):
    """
    Test Case 6: Other Banks Account Enquiry
    Verify account name for other banks
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Verify account name"""
        account_number = request.data.get('account_number')
        bank_code = request.data.get('bank_code')

        if not account_number or not bank_code:
            return validation_error_response({
                "account_number": ["Account number is required"] if not account_number else [],
                "bank_code": ["Bank code is required"] if not bank_code else []
            })

        try:
            psb9_client = PSB9Client()
            result = psb9_client.other_banks_enquiry(
                account_number=account_number,
                bank_code=bank_code
            )

            if result.get("status") == "success":
                return success_response(
                    message="Account verified successfully",
                    data=result.get("data", {})
                )
            else:
                return error_response(
                    message=result.get("message", "Account verification failed"),
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(f"Account enquiry error: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to verify account",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OtherBanksTransferAPIView(APIView):
    """
    Test Case 7: Other Banks Transfer
    Transfer to other banks
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Transfer to other bank"""
        user = request.user
        amount = request.data.get('amount')
        account_number = request.data.get('account_number')
        bank_code = request.data.get('bank_code')
        account_name = request.data.get('account_name')
        narration = request.data.get('narration', 'Bank transfer')

        # Validation
        errors = {}
        if not amount:
            errors['amount'] = ["Amount is required"]
        if not account_number:
            errors['account_number'] = ["Account number is required"]
        if not bank_code:
            errors['bank_code'] = ["Bank code is required"]
        if not account_name:
            errors['account_name'] = ["Account name is required"]

        if errors:
            return validation_error_response(errors)

        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                return validation_error_response({"amount": ["Amount must be greater than 0"]})
        except:
            return validation_error_response({"amount": ["Invalid amount format"]})

        try:
            wallet = user.wallet
            if not wallet.psb9_account_number:
                return error_response(
                    message="No wallet account found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            # Check balance
            if wallet.balance < amount_decimal:
                return error_response(
                    message="Insufficient balance",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Generate unique transaction ID
            transaction_id = f"TRF_{user.id}_{uuid.uuid4().hex[:12].upper()}"

            # Transfer via 9PSB
            psb9_client = PSB9Client()
            result = psb9_client.other_banks_transfer(
                sender_account_number=wallet.psb9_account_number,
                receiver_account_number=account_number,
                bank_code=bank_code,
                amount=float(amount_decimal),
                transaction_id=transaction_id,
                narration=narration
            )

            if result.get("status") == "success":
                with db_transaction.atomic():
                    # Update wallet balance
                    wallet.balance -= amount_decimal
                    wallet.save()

                    # Create transaction record
                    wallet_transaction = WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_type='debit',
                        amount=amount_decimal,
                        description=f"Transfer to {account_name} - {bank_code}",
                        reference=transaction_id,
                        sender_name=user.get_full_name(),
                        sender_account=wallet.account_number,
                        status='completed'
                    )

                    return success_response(
                        message="Transfer successful",
                        data={
                            "transaction_id": transaction_id,
                            "amount": str(amount_decimal),
                            "recipient": account_name,
                            "account_number": account_number,
                            "new_balance": str(wallet.balance),
                            "reference": str(wallet_transaction.id)
                        }
                    )
            else:
                return error_response(
                    message=result.get("message", "Transfer failed"),
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Wallet.DoesNotExist:
            return error_response(
                message="Wallet not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Transfer error: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to process transfer",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WalletTransactionHistoryAPIView(APIView):
    """
    Test Case 8: Wallet Transaction History
    Get transaction history from 9PSB
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get transaction history"""
        user = request.user
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        try:
            wallet = user.wallet
            if not wallet.psb9_account_number:
                return error_response(
                    message="No wallet account found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            psb9_client = PSB9Client()
            result = psb9_client.get_wallet_transactions(
                account_number=wallet.psb9_account_number,
                start_date=start_date,
                end_date=end_date
            )

            if result.get("status") == "success":
                return success_response(
                    message="Transaction history retrieved successfully",
                    data=result.get("data", [])
                )
            else:
                return error_response(
                    message=result.get("message", "Failed to retrieve transactions"),
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Wallet.DoesNotExist:
            return error_response(
                message="Wallet not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Transaction history error: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to retrieve transaction history",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WalletTransactionRequeryAPIView(APIView):
    """
    Test Case 11: Wallet Transaction Requery
    Check transaction status
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Requery transaction"""
        transaction_id = request.data.get('transaction_id')

        if not transaction_id:
            return validation_error_response({"transaction_id": ["Transaction ID is required"]})

        try:
            psb9_client = PSB9Client()
            result = psb9_client.transaction_requery(transaction_id=transaction_id)

            if result.get("status") == "success":
                return success_response(
                    message="Transaction status retrieved successfully",
                    data=result.get("data", {})
                )
            else:
                return error_response(
                    message=result.get("message", "Transaction not found"),
                    status_code=status.HTTP_404_NOT_FOUND
                )

        except Exception as e:
            logger.error(f"Transaction requery error: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to requery transaction",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WalletStatusAPIView(APIView):
    """
    Test Case 9: Wallet Status
    Check wallet status
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get wallet status"""
        user = request.user

        try:
            wallet = user.wallet
            if not wallet.psb9_account_number:
                return error_response(
                    message="No wallet account found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            psb9_client = PSB9Client()
            result = psb9_client.get_wallet_status(wallet.psb9_account_number)

            if result.get("status") == "success":
                return success_response(
                    message="Wallet status retrieved successfully",
                    data=result.get("data", {})
                )
            else:
                return error_response(
                    message=result.get("message", "Failed to retrieve wallet status"),
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Wallet.DoesNotExist:
            return error_response(
                message="Wallet not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Wallet status error: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to retrieve wallet status",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChangeWalletStatusAPIView(APIView):
    """
    Test Case 10: Change Wallet Status
    Admin: Activate/suspend wallet
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Change wallet status"""
        # Admin only
        if not request.user.is_staff:
            return error_response(
                message="Unauthorized - Admin access required",
                status_code=status.HTTP_403_FORBIDDEN
            )

        account_number = request.data.get('account_number')
        new_status = request.data.get('status')  # 'active' or 'suspended'

        if not account_number or not new_status:
            return validation_error_response({
                "account_number": ["Account number is required"] if not account_number else [],
                "status": ["Status is required"] if not new_status else []
            })

        if new_status not in ['active', 'suspended']:
            return validation_error_response({"status": ["Status must be 'active' or 'suspended'"]})

        try:
            psb9_client = PSB9Client()
            result = psb9_client.change_wallet_status(
                account_number=account_number,
                status=new_status
            )

            if result.get("status") == "success":
                return success_response(
                    message=f"Wallet status changed to {new_status}",
                    data=result.get("data", {})
                )
            else:
                return error_response(
                    message=result.get("message", "Failed to change wallet status"),
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(f"Change wallet status error: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to change wallet status",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
