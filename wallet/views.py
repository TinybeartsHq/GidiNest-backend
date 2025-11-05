# wallet/views.py
from django.db import IntegrityError
from django.http import JsonResponse
import requests
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist

from core.helpers.response import success_response, error_response
from notification.helper.email import MailClient
from providers.helpers.cuoral import CuoralAPI
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

from decimal import Decimal


class WalletBalanceAPIView(APIView):
    """
    API endpoint to retrieve the authenticated user's wallet balance.
    """
    permission_classes = [IsAuthenticated]

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

        data = {
            'wallet':serializer.data,
            "user_goals":SavingsGoalSerializer(SavingsGoalModel.objects.filter(user=request.user), many=True).data
        }
        return success_response(data)
    



class WalletTransactionHistoryAPIView(APIView):
    """
    API endpoint to retrieve the authenticated user's wallet transaction history.
    """
    permission_classes = [IsAuthenticated]

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


    def post(self, request, *args, **kwargs):
        # Parse the input data
        bank_name = request.data.get('bank_name')
        account_number = request.data.get('account_number')
        withdrawal_amount = request.data.get('amount')
        bank_code = request.data.get('bank_code')  # Assuming bank code is passed

        # Validate inputs
        if not bank_name or not account_number or not withdrawal_amount or not bank_code:
            return Response({"detail": "All fields (bank_account_name, bank_name, account_number, amount, bank_code) are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            withdrawal_amount = float(withdrawal_amount)
        except ValueError:
            return Response({"detail": "Invalid amount."}, status=status.HTTP_400_BAD_REQUEST)

        if withdrawal_amount <= 0:
            return Response({"detail": "Amount must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)


        try:
            wallet = request.user.wallet
        except ObjectDoesNotExist:
            # Don't create wallet here - user needs to verify BVN/NIN first
            return Response({
                "detail": "You don't have a wallet yet. Please verify your BVN or NIN to activate your wallet."
            }, status=status.HTTP_404_NOT_FOUND)


        if wallet.balance < withdrawal_amount:
            return Response({"detail": "Insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)
        
        withdrawal_request = WithdrawalRequest.objects.create(
            user=request.user,
            amount=withdrawal_amount,
            bank_name=bank_name,
            account_number=account_number,
            status='pending' 
        )

        

        wallet.balance -= Decimal(str(withdrawal_amount))
        wallet.save()


        # Serialize and return the withdrawal request details
        withdrawal_request_serializer = WithdrawalRequestSerializer(withdrawal_request)
        return Response({
            "status":True,
            "detail": "Withdrawal initiated successfully.",
            "withdrawal_request": withdrawal_request_serializer.data
        }, status=status.HTTP_200_OK)
    




class ResolveBankAccountAPIView(APIView):
    """
    API endpoint to resolve and fetch bank account details from Embedly.
    Uses Embedly's Payout/name-enquiry endpoint.
    """
    permission_classes = [IsAuthenticated]

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
    



class GetBanksAPIView(APIView):
    """
    API endpoint to get list of banks available for transfers.
    """
    permission_classes = [IsAuthenticated]

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


class EmbedlyWebhookView(APIView):

    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        signature = request.headers.get('x-embedly-signature')
        raw_body = request.body.decode('utf-8')

        # Check if signature or body is missing
        if not signature or not raw_body:
            return JsonResponse({'error': 'Missing signature or body'}, status=400)

        # Define your API key (preferably from settings)
        api_key = settings.EMBEDLY_API_KEY_PRODUCTION

        # Compute the expected signature using HMAC and sha512
        hmac_object = hmac.new(api_key.encode('utf-8'), raw_body.encode('utf-8'), hashlib.sha512)
        computed_signature = hmac_object.hexdigest()

        # Verify the signature
        if not hmac.compare_digest(computed_signature, signature):
            return JsonResponse({'error': 'Invalid signature - authentication failed'}, status=403)

        # Parse the JSON payload
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        # Check the event type
        if payload.get('event') == 'nip':
            return self.handle_nip_event(payload)
        else:
            return JsonResponse({'error': 'Unsupported event'}, status=400)

    def handle_nip_event(self, payload):
        # Extract transaction data
        data = payload.get('data', {})
        account_number = data.get('accountNumber')
        reference = data.get('reference')
        senderBank = data.get('senderBank')
        amount = data.get('amount')
        sender_name = data.get('senderName')
 
        try:
            wallet = Wallet.objects.get(account_number=account_number)
        except Wallet.DoesNotExist:
            return JsonResponse({'error': 'Wallet not found'}, status=404)

        try:
            transaction = WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='credit',  # This is a credit to the wallet
                amount=amount,
                description=f"Transfer from {sender_name} via NIP reference {reference}",
                sender_name=sender_name,
                sender_account=senderBank,
                external_reference=reference
            )
        except IntegrityError as e:
            return JsonResponse({'error': f'Transaction with this reference has been processed'}, status=200)

        # Update the wallet balance
        wallet.deposit(amount)

        #send notification to user sms and email
        cuoral_client = CuoralAPI()
        cuoral_client.send_sms(wallet.user.phone,f"You just received {wallet.currency} {amount} from {sender_name}.")

        emailclient = MailClient()
        emailclient.send_email(
                to_email=wallet.user.email,
                subject="Credit Alert",
                template_name="emails/credit.html",
                context= {
                    "sender_name": sender_name,
                    "amount": f"{wallet.currency} {amount}",
                },
                to_name=wallet.user.first_name
            )

        # Return a success response
        return JsonResponse({
            'status': 'success',
            'message': 'Webhook received and wallet updated',
            'data': payload,
            'timestamp': str(transaction.created_at)
        }, status=200)