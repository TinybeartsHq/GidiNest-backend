# gifting/views.py
"""
API views for the GidiNest gifting flow.

Mother (fund owner) endpoints — require auth:
  - CreateBabyFundAPIView      POST   /api/v2/funds/create
  - ListMyFundsAPIView         GET    /api/v2/funds/my-funds
  - FundAnalyticsAPIView       GET    /api/v2/funds/{token}/analytics
  - UpdateBabyFundAPIView      PATCH  /api/v2/funds/{token}/update
  - DeactivateBabyFundAPIView  DELETE /api/v2/funds/{token}/deactivate

Gift sender (contributor) endpoints — no auth:
  - ViewFundPublicAPIView      GET    /api/v2/funds/{token}/
  - InitializeGiftAPIView      POST   /api/v2/funds/{token}/gift
  - GiftCallbackAPIView        GET    /api/v2/funds/{token}/success
"""
import uuid
import logging
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from core.helpers.response import success_response, error_response, validation_error_response
from gifting.models import BabyFund, Gift
from gifting.serializers import BabyFundSerializer, BabyFundPublicSerializer, GiftSerializer
from providers.helpers.paystack import PaystackAPI
from wallet.fee_utils import calculate_gift_fees, settle_fees_to_platform

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Mother (fund owner) endpoints
# ------------------------------------------------------------------

class CreateBabyFundAPIView(APIView):
    """
    Create a new baby fund. No wallet or KYC required.
    POST /api/v2/funds/create
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        name = request.data.get('name')
        if not name:
            return validation_error_response({'name': 'Fund name is required'})

        fund = BabyFund.objects.create(
            user=request.user,
            name=name,
            description=request.data.get('description', ''),
            target_amount=request.data.get('target_amount'),
            due_date=request.data.get('due_date'),
            thank_you_message=request.data.get(
                'thank_you_message', 'Thank you for your generous gift!'
            ),
            show_contributors=request.data.get('show_contributors', 'public'),
        )

        logger.info(f"Baby fund created: {fund.token} by {request.user.email}")
        return success_response(
            message="Baby fund created successfully",
            data=BabyFundSerializer(fund).data,
            status_code=201,
        )


class ListMyFundsAPIView(APIView):
    """
    List all funds for the authenticated mother.
    GET /api/v2/funds/my-funds
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        funds = BabyFund.objects.filter(user=request.user).order_by('-created_at')
        return success_response(data=BabyFundSerializer(funds, many=True).data)


class FundAnalyticsAPIView(APIView):
    """
    Analytics for a fund (owner only).
    GET /api/v2/funds/{token}/analytics
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, token):
        try:
            fund = BabyFund.objects.get(token=token, user=request.user)
        except BabyFund.DoesNotExist:
            return error_response('Fund not found', status_code=404)

        gifts = fund.gifts.filter(status='completed').order_by('-created_at')

        return success_response(data={
            'fund': BabyFundSerializer(fund).data,
            'total_raised': str(fund.get_total_gifts()),
            'gift_count': fund.get_gift_count(),
            'target_reached': fund.is_target_reached(),
            'recent_gifts': GiftSerializer(gifts[:20], many=True).data,
        })


class UpdateBabyFundAPIView(APIView):
    """
    Update fund details (owner only).
    PATCH /api/v2/funds/{token}/update
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, token):
        try:
            fund = BabyFund.objects.get(token=token, user=request.user)
        except BabyFund.DoesNotExist:
            return error_response('Fund not found', status_code=404)

        allowed = ['name', 'description', 'target_amount', 'due_date',
                    'thank_you_message', 'show_contributors', 'is_active']
        for field in allowed:
            if field in request.data:
                setattr(fund, field, request.data[field])

        fund.save()
        return success_response(
            message="Fund updated successfully",
            data=BabyFundSerializer(fund).data,
        )


class DeactivateBabyFundAPIView(APIView):
    """
    Deactivate a fund (owner only). Does not delete — preserves gift history.
    DELETE /api/v2/funds/{token}/deactivate
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, token):
        try:
            fund = BabyFund.objects.get(token=token, user=request.user)
        except BabyFund.DoesNotExist:
            return error_response('Fund not found', status_code=404)

        fund.is_active = False
        fund.status = 'closed'
        fund.save(update_fields=['is_active', 'status', 'updated_at'])

        return success_response(message="Fund deactivated successfully")


# ------------------------------------------------------------------
# Gift sender (contributor) endpoints — public, no auth
# ------------------------------------------------------------------

class ViewFundPublicAPIView(APIView):
    """
    Public view of a baby fund. No auth required.
    GET /api/v2/funds/{token}/
    """
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            fund = BabyFund.objects.select_related('user').get(token=token)
        except BabyFund.DoesNotExist:
            return error_response('Fund not found', status_code=404)

        if not fund.is_active or fund.status != 'active':
            return error_response('This fund is no longer accepting gifts')

        return success_response(data=BabyFundPublicSerializer(fund).data)


class InitializeGiftAPIView(APIView):
    """
    Initialize a Paystack payment for a gift.
    No auth required — this is for gift senders.

    POST /api/v2/funds/{token}/gift
    Body: {amount, contributor_name, contributor_email (optional), message (optional)}

    Returns: {authorization_url, reference, gift_id}
    """
    permission_classes = [AllowAny]

    def post(self, request, token):
        # Find fund
        try:
            fund = BabyFund.objects.select_related('user').get(token=token)
        except BabyFund.DoesNotExist:
            return error_response('Fund not found', status_code=404)

        if not fund.is_active or fund.status != 'active':
            return error_response('This fund is no longer accepting gifts')

        # Validate inputs
        contributor_name = request.data.get('contributor_name')
        amount = request.data.get('amount')

        if not contributor_name:
            return validation_error_response({'contributor_name': 'Name is required'})
        if not amount:
            return validation_error_response({'amount': 'Amount is required'})

        try:
            amount = Decimal(str(amount))
            if amount < Decimal('100'):
                return validation_error_response({'amount': 'Minimum gift amount is NGN 100'})
        except (InvalidOperation, ValueError):
            return validation_error_response({'amount': 'Invalid amount'})

        contributor_email = request.data.get('contributor_email', '')
        # Paystack requires an email — use a placeholder if not provided
        paystack_email = contributor_email or f"guest+{uuid.uuid4().hex[:8]}@gidinest.com"

        message = request.data.get('message', '')
        contributor_phone = request.data.get('contributor_phone', '')

        # Generate unique reference
        reference = f"GIFT-{fund.token[:8]}-{uuid.uuid4().hex[:12]}"

        # Build callback URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://gidinest.com')
        callback_url = f"{frontend_url}/fund/{fund.token}/success?reference={reference}"

        # Initialize Paystack transaction
        try:
            paystack = PaystackAPI()
            result = paystack.initialize_transaction(
                amount_naira=amount,
                email=paystack_email,
                callback_url=callback_url,
                metadata={
                    'fund_token': fund.token,
                    'contributor_name': contributor_name,
                    'gift_reference': reference,
                },
                reference=reference,
            )
        except ValueError:
            logger.error("Paystack API not configured")
            return error_response("Payment service is not configured. Please try again later.")

        if not result:
            return error_response("Failed to initialize payment. Please try again.")

        # Create pending gift record
        gift = Gift.objects.create(
            baby_fund=fund,
            amount=amount,
            status='pending',
            paystack_reference=reference,
            paystack_access_code=result.get('access_code', ''),
            contributor_name=contributor_name,
            contributor_email=contributor_email,
            contributor_phone=contributor_phone,
            message=message,
        )

        logger.info(f"Gift initialized: {reference} — NGN {amount} to fund {fund.token}")

        return success_response(
            message="Payment initialized. Redirect to Paystack.",
            data={
                'authorization_url': result['authorization_url'],
                'access_code': result['access_code'],
                'reference': reference,
                'gift_id': str(gift.id),
            },
        )


class GiftCallbackAPIView(APIView):
    """
    Verify payment after Paystack redirect.
    Called by the frontend after the contributor returns from Paystack.

    GET /api/v2/funds/{token}/success?reference=GIFT-xxx
    """
    permission_classes = [AllowAny]

    def get(self, request, token):
        reference = request.query_params.get('reference')
        if not reference:
            return error_response('Payment reference is required')

        try:
            gift = Gift.objects.select_related('baby_fund').get(paystack_reference=reference)
        except Gift.DoesNotExist:
            return error_response('Gift not found', status_code=404)

        # If already completed (webhook beat us), just return success
        if gift.status == 'completed':
            return success_response(
                message="Gift confirmed!",
                data={
                    'status': 'completed',
                    'amount': str(gift.amount),
                    'fund_name': gift.baby_fund.name,
                    'thank_you_message': gift.baby_fund.thank_you_message,
                },
            )

        # Verify with Paystack
        try:
            paystack = PaystackAPI()
            tx_data = paystack.verify_transaction(reference)
        except ValueError:
            return error_response("Payment verification unavailable")

        if not tx_data or tx_data.get('status') != 'success':
            return success_response(
                message="Payment is being processed. You'll receive a confirmation shortly.",
                data={'status': 'pending', 'reference': reference},
            )

        # Payment confirmed — process if webhook hasn't already
        if gift.status == 'pending':
            _process_completed_gift(gift)

        return success_response(
            message="Gift confirmed! Thank you for your generosity.",
            data={
                'status': 'completed',
                'amount': str(gift.amount),
                'fund_name': gift.baby_fund.name,
                'thank_you_message': gift.baby_fund.thank_you_message,
            },
        )


# ------------------------------------------------------------------
# Paystack webhook
# ------------------------------------------------------------------

class PaystackWebhookAPIView(APIView):
    """
    Paystack webhook handler.
    POST /api/webhooks/paystack/

    Handles:
    - charge.success → complete gift, credit fund, deduct fee
    - transfer.success → mark withdrawal as completed
    - transfer.failed → mark withdrawal as failed
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Verify webhook signature
        signature = request.META.get('HTTP_X_PAYSTACK_SIGNATURE', '')
        if not PaystackAPI.verify_webhook_signature(request.body, signature):
            logger.warning("Paystack webhook: invalid signature")
            return error_response("Invalid signature", status_code=401)

        payload = request.data
        event = payload.get('event')
        data = payload.get('data', {})

        logger.info(f"Paystack webhook received: {event}")

        if event == 'charge.success':
            self._handle_charge_success(data)
        elif event == 'transfer.success':
            self._handle_transfer_success(data)
        elif event == 'transfer.failed':
            self._handle_transfer_failed(data)

        # Always return 200 to Paystack (even if we can't process)
        return success_response(message="Webhook received")

    def _handle_charge_success(self, data):
        """Process successful payment — credit the baby fund."""
        reference = data.get('reference')
        if not reference:
            logger.error("Paystack charge.success: no reference")
            return

        try:
            gift = Gift.objects.select_related('baby_fund', 'baby_fund__user').get(
                paystack_reference=reference
            )
        except Gift.DoesNotExist:
            logger.warning(f"Paystack charge.success: gift not found for ref {reference}")
            return

        if gift.status == 'completed':
            logger.info(f"Gift {reference} already completed — skipping")
            return

        _process_completed_gift(gift)

    def _handle_transfer_success(self, data):
        """Mark a withdrawal as completed. (Phase 2 — disbursements)"""
        reference = data.get('reference')
        logger.info(f"Transfer success: {reference} (disbursement handling TBD in Phase 2)")

    def _handle_transfer_failed(self, data):
        """Mark a withdrawal as failed. (Phase 2 — disbursements)"""
        reference = data.get('reference')
        logger.info(f"Transfer failed: {reference} (disbursement handling TBD in Phase 2)")


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _process_completed_gift(gift):
    """
    Process a confirmed gift payment:
    1. Calculate 1.5% fee
    2. Credit net amount to baby fund
    3. Settle fee to platform wallet
    4. Mark gift as completed
    5. Send notifications
    """
    from django.db import transaction

    fees = calculate_gift_fees(gift.amount)

    try:
        with transaction.atomic():
            # Update gift record with fee breakdown
            gift.fee_amount = fees.gift_fee
            gift.net_amount = fees.net_amount
            gift.status = 'completed'
            gift.save(update_fields=[
                'fee_amount', 'net_amount', 'status', 'updated_at'
            ])

            # Credit the baby fund (atomic)
            gift.baby_fund.credit(fees.net_amount)

        # Settle platform fee (outside main atomic block — non-critical)
        settle_fees_to_platform(fees)

        logger.info(
            f"Gift completed: {gift.paystack_reference} — "
            f"gross={gift.amount}, fee={fees.gift_fee}, net={fees.net_amount}"
        )

        # Send notifications
        try:
            _send_gift_notifications(gift)
        except Exception as e:
            logger.error(f"Gift notification failed: {e}")

    except Exception as e:
        logger.error(f"Failed to process gift {gift.paystack_reference}: {e}", exc_info=True)


def _send_gift_notifications(gift):
    """Send notifications to mother and contributor after a successful gift."""
    from notification.helper.notifications import create_notification
    from notification.helper.email import MailClient

    fund = gift.baby_fund
    mother = fund.user
    amount_str = f"NGN {gift.amount:,.2f}"

    # In-app + push notification to mother
    create_notification(
        user=mother,
        title="New Gift Received!",
        message=f"{gift.contributor_name} sent {amount_str} to your fund '{fund.name}'",
        notification_type='gift_received',
        data={
            'fund_token': fund.token,
            'gift_id': str(gift.id),
            'amount': str(gift.amount),
        },
    )

    # Email to mother
    try:
        email_client = MailClient()
        email_client.send_email(
            to_email=mother.email,
            subject="New Gift Received!",
            template_name="emails/gift_received.html",
            context={
                'contributor_name': gift.contributor_name,
                'amount': amount_str,
                'fund_name': fund.name,
                'total_raised': f"NGN {fund.get_total_gifts():,.2f}",
                'target_amount': f"NGN {fund.target_amount:,.2f}" if fund.target_amount else "No target set",
                'message': gift.message,
            },
            to_name=mother.first_name,
        )
    except Exception as e:
        logger.error(f"Failed to send gift email to mother: {e}")

    # Email receipt to contributor (if email provided)
    if gift.contributor_email:
        try:
            email_client = MailClient()
            email_client.send_email(
                to_email=gift.contributor_email,
                subject="Gift Confirmed - Thank You!",
                template_name="emails/gift_confirmation.html",
                context={
                    'fund_name': fund.name,
                    'mother_name': mother.first_name,
                    'amount': amount_str,
                    'reference': gift.paystack_reference,
                    'thank_you_message': fund.thank_you_message,
                },
                to_name=gift.contributor_name,
            )
        except Exception as e:
            logger.error(f"Failed to send gift receipt to contributor: {e}")
