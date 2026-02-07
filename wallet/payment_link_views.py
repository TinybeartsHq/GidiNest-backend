# wallet/payment_link_views.py
import uuid
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from core.helpers.response import success_response, error_response, validation_error_response
from wallet.models import PaymentLink, PaymentLinkContribution
from wallet.serializers import PaymentLinkSerializer, PaymentLinkPublicSerializer, PaymentLinkContributionSerializer
from wallet.payment_link_helpers import try_match_contribution_to_deposit, _complete_contribution
from savings.models import SavingsGoalModel


class CreateGoalPaymentLinkAPIView(APIView):
    """
    Create a payment link for a specific savings goal.
    POST /api/v2/payment-links/create-goal-link
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Create goal payment link request data: {request.data}")

        # Check if user has a wallet
        try:
            wallet = request.user.wallet
            if not wallet.account_number:
                logger.error(f"User {request.user.email} wallet not fully set up")
                return error_response("Your wallet is not fully set up. Please complete wallet setup first.")
        except ObjectDoesNotExist:
            logger.error(f"User {request.user.email} has no wallet")
            return error_response("You don't have a wallet yet. Please verify your BVN or NIN to activate your wallet.")

        goal_id = request.data.get('goal_id')
        description = request.data.get('description', '')
        target_amount = request.data.get('target_amount')
        show_contributors = request.data.get('show_contributors', 'public')
        expires_at = request.data.get('expires_at')
        custom_message = request.data.get('custom_message', 'Thank you for your contribution!')

        logger.info(f"Attempting to create payment link for goal_id: {goal_id}")

        # Validate goal
        if not goal_id:
            logger.error("No goal_id provided")
            return validation_error_response({'goal_id': 'Goal ID is required'})

        try:
            goal = SavingsGoalModel.objects.get(id=goal_id, user=request.user)
            logger.info(f"Found goal: {goal.name}")
        except SavingsGoalModel.DoesNotExist:
            logger.error(f"Goal {goal_id} not found for user {request.user.email}")
            return error_response('Savings goal not found or does not belong to you')
        except Exception as e:
            logger.error(f"Error finding goal: {str(e)}")
            return error_response(f'Error finding goal: {str(e)}')

        # Create payment link
        try:
            payment_link = PaymentLink.objects.create(
                user=request.user,
                link_type='savings_goal',
                savings_goal=goal,
                description=description or f"Help fund {goal.name}",
                target_amount=target_amount if target_amount else goal.target_amount,
                show_contributors=show_contributors,
                expires_at=expires_at,
                custom_message=custom_message,
                allow_custom_amount=True
            )

            logger.info(f"Payment link created successfully: {payment_link.token}")
            serializer = PaymentLinkSerializer(payment_link)
            return success_response(
                message="Payment link created successfully",
                data=serializer.data
            )

        except Exception as e:
            logger.error(f"Failed to create payment link: {str(e)}", exc_info=True)
            return error_response(f"Failed to create payment link: {str(e)}")


class CreateEventPaymentLinkAPIView(APIView):
    """
    Create a payment link for an event.
    POST /api/v2/payment-links/create-event-link
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Check if user has a wallet
        try:
            wallet = request.user.wallet
            if not wallet.account_number:
                return error_response("Your wallet is not fully set up. Please complete wallet setup first.")
        except ObjectDoesNotExist:
            return error_response("You don't have a wallet yet. Please verify your BVN or NIN to activate your wallet.")

        event_name = request.data.get('event_name')
        event_date = request.data.get('event_date')
        event_description = request.data.get('event_description', '')
        target_amount = request.data.get('target_amount')
        link_to_goal = request.data.get('link_to_goal', False)
        goal_name = request.data.get('goal_name')
        show_contributors = request.data.get('show_contributors', 'public')
        custom_message = request.data.get('custom_message', 'Thank you for celebrating with us!')
        expires_at = request.data.get('expires_at')
        allow_custom_amount = request.data.get('allow_custom_amount', True)

        # Validate event name
        if not event_name:
            return validation_error_response({'event_name': 'Event name is required'})

        # Create payment link
        try:
            with transaction.atomic():
                # Optionally create a savings goal for the event
                savings_goal = None
                if link_to_goal:
                    goal_name = goal_name or f"{event_name} Fund"
                    savings_goal = SavingsGoalModel.objects.create(
                        user=request.user,
                        name=goal_name,
                        target_amount=target_amount or Decimal('0'),
                        description=event_description or f"Savings for {event_name}",
                        status='active'
                    )

                payment_link = PaymentLink.objects.create(
                    user=request.user,
                    link_type='event',
                    savings_goal=savings_goal,
                    event_name=event_name,
                    event_date=event_date,
                    event_description=event_description,
                    target_amount=target_amount,
                    show_contributors=show_contributors,
                    expires_at=expires_at,
                    custom_message=custom_message,
                    allow_custom_amount=allow_custom_amount
                )

                serializer = PaymentLinkSerializer(payment_link)
                return success_response(
                    message="Event payment link created successfully",
                    data=serializer.data
                )

        except Exception as e:
            return error_response(f"Failed to create payment link: {str(e)}")


class CreateWalletPaymentLinkAPIView(APIView):
    """
    Create a general wallet funding payment link.
    POST /api/v2/payment-links/create-wallet-link
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Check if user has a wallet
        try:
            wallet = request.user.wallet
            if not wallet.account_number:
                return error_response("Your wallet is not fully set up. Please complete wallet setup first.")
        except ObjectDoesNotExist:
            return error_response("You don't have a wallet yet. Please verify your BVN or NIN to activate your wallet.")

        description = request.data.get('description', 'Fund my wallet')
        target_amount = request.data.get('target_amount')
        show_contributors = request.data.get('show_contributors', 'public')
        expires_at = request.data.get('expires_at')
        custom_message = request.data.get('custom_message', 'Thank you for your contribution!')
        allow_custom_amount = request.data.get('allow_custom_amount', True)

        try:
            payment_link = PaymentLink.objects.create(
                user=request.user,
                link_type='wallet',
                description=description,
                target_amount=target_amount,
                show_contributors=show_contributors,
                expires_at=expires_at,
                custom_message=custom_message,
                allow_custom_amount=allow_custom_amount
            )

            serializer = PaymentLinkSerializer(payment_link)
            return success_response(
                message="Wallet payment link created successfully",
                data=serializer.data
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create wallet payment link: {str(e)}", exc_info=True)
            return error_response(f"Failed to create payment link: {str(e)}")


class ViewPaymentLinkPublicAPIView(APIView):
    """
    View payment link details (public - accessible to anyone with the token).
    GET /api/v2/payment-links/{token}/
    """
    permission_classes = [AllowAny]

    def get(self, request, token, *args, **kwargs):
        try:
            payment_link = PaymentLink.objects.select_related('savings_goal', 'user__wallet').get(token=token)

            # Check if link is active
            if not payment_link.is_active:
                return error_response('This payment link is no longer active')

            # Check expiry
            if payment_link.expires_at and timezone.now() > payment_link.expires_at:
                return error_response('This payment link has expired')

            # Check one-time use
            if payment_link.one_time_use and payment_link.used:
                return error_response('This payment link has already been used')

            serializer = PaymentLinkPublicSerializer(payment_link)
            return success_response(data=serializer.data)

        except PaymentLink.DoesNotExist:
            return error_response('Payment link not found', status_code=status.HTTP_404_NOT_FOUND)


class PaymentLinkAnalyticsAPIView(APIView):
    """
    Get analytics for a payment link (owner only).
    GET /api/v2/payment-links/{token}/analytics
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, token, *args, **kwargs):
        try:
            payment_link = PaymentLink.objects.select_related('savings_goal').get(
                token=token,
                user=request.user
            )

            # Get all contributions
            contributions = payment_link.contributions.filter(status='completed').order_by('-created_at')

            analytics = {
                'link': PaymentLinkSerializer(payment_link).data,
                'total_raised': str(payment_link.get_total_raised()),
                'contributor_count': payment_link.get_contributor_count(),
                'target_reached': payment_link.is_target_reached(),
                'recent_contributions': PaymentLinkContributionSerializer(contributions[:20], many=True).data,
            }

            return success_response(data=analytics)

        except PaymentLink.DoesNotExist:
            return error_response('Payment link not found', status_code=status.HTTP_404_NOT_FOUND)


class ListUserPaymentLinksAPIView(APIView):
    """
    List all payment links for the authenticated user.
    GET /api/v2/payment-links/my-links
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        payment_links = PaymentLink.objects.filter(user=request.user).select_related('savings_goal').order_by('-created_at')
        serializer = PaymentLinkSerializer(payment_links, many=True)
        return success_response(data=serializer.data)


class UpdatePaymentLinkAPIView(APIView):
    """
    Update a payment link (toggle active status, update description, etc.).
    PATCH /api/v2/payment-links/{token}/
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, token, *args, **kwargs):
        try:
            payment_link = PaymentLink.objects.get(token=token, user=request.user)

            # Update allowed fields
            allowed_fields = ['is_active', 'description', 'custom_message', 'show_contributors', 'expires_at']
            for field in allowed_fields:
                if field in request.data:
                    setattr(payment_link, field, request.data[field])

            payment_link.save()

            serializer = PaymentLinkSerializer(payment_link)
            return success_response(
                message="Payment link updated successfully",
                data=serializer.data
            )

        except PaymentLink.DoesNotExist:
            return error_response('Payment link not found', status_code=status.HTTP_404_NOT_FOUND)


class DeletePaymentLinkAPIView(APIView):
    """
    Delete a payment link.
    DELETE /api/v2/payment-links/{token}/
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, token, *args, **kwargs):
        try:
            payment_link = PaymentLink.objects.get(token=token, user=request.user)

            # Check if there are contributions
            if payment_link.contributions.filter(status='completed').exists():
                # Don't delete, just deactivate
                payment_link.is_active = False
                payment_link.save()
                return success_response(message="Payment link deactivated (has contributions)")
            else:
                # Safe to delete
                payment_link.delete()
                return success_response(message="Payment link deleted successfully")

        except PaymentLink.DoesNotExist:
            return error_response('Payment link not found', status_code=status.HTTP_404_NOT_FOUND)


class ConfirmPaymentLinkContributionAPIView(APIView):
    """
    Contributor confirms they've made a bank transfer for a payment link.
    Creates a pending contribution and tries to auto-match against recent deposits.
    POST /api/v2/payment-links/{token}/confirm-payment
    """
    permission_classes = [AllowAny]

    def post(self, request, token, *args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)

        # Find the payment link
        try:
            payment_link = PaymentLink.objects.select_related(
                'savings_goal', 'user__wallet'
            ).get(token=token)
        except PaymentLink.DoesNotExist:
            return error_response('Payment link not found', status_code=status.HTTP_404_NOT_FOUND)

        # Validate link is usable
        if not payment_link.is_active:
            return error_response('This payment link is no longer active')
        if payment_link.expires_at and timezone.now() > payment_link.expires_at:
            return error_response('This payment link has expired')
        if payment_link.one_time_use and payment_link.used:
            return error_response('This payment link has already been used')

        # Validate required fields
        contributor_name = request.data.get('contributor_name')
        amount = request.data.get('amount')

        if not contributor_name:
            return validation_error_response({'contributor_name': 'Contributor name is required'})
        if not amount:
            return validation_error_response({'amount': 'Amount is required'})

        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                return validation_error_response({'amount': 'Amount must be greater than zero'})
        except (InvalidOperation, ValueError):
            return validation_error_response({'amount': 'Invalid amount'})

        # Check fixed amount if applicable
        if not payment_link.allow_custom_amount and payment_link.fixed_amount:
            if amount != payment_link.fixed_amount:
                return validation_error_response({
                    'amount': f'This payment link requires exactly {payment_link.fixed_amount}'
                })

        # Optional fields
        contributor_email = request.data.get('contributor_email', '')
        contributor_phone = request.data.get('contributor_phone', '')
        message = request.data.get('message', '')

        # Create pending contribution
        contribution = PaymentLinkContribution.objects.create(
            payment_link=payment_link,
            amount=amount,
            status='pending',
            contributor_name=contributor_name,
            contributor_email=contributor_email or None,
            contributor_phone=contributor_phone or None,
            message=message or None,
            external_reference=f"CONFIRM-{payment_link.token}-{uuid.uuid4().hex[:8]}"
        )

        # Try to auto-match against a recent deposit
        matched_transaction = try_match_contribution_to_deposit(contribution)
        if matched_transaction:
            try:
                _complete_contribution(contribution, matched_transaction)
                logger.info(f"Auto-matched contribution {contribution.id} to deposit {matched_transaction.external_reference}")
                return success_response(
                    message="Payment confirmed and matched successfully!",
                    data={
                        'contribution_id': str(contribution.id),
                        'status': 'completed',
                        'amount': str(amount),
                    }
                )
            except Exception as e:
                logger.error(f"Failed to complete auto-matched contribution: {str(e)}", exc_info=True)

        # No auto-match — stays pending, will be matched when deposit arrives
        return success_response(
            message="Payment confirmation received. We'll match it once the transfer arrives.",
            data={
                'contribution_id': str(contribution.id),
                'status': 'pending',
                'amount': str(amount),
            }
        )
