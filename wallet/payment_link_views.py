# wallet/payment_link_views.py
from decimal import Decimal
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
from savings.models import SavingsGoalModel


class CreateGoalPaymentLinkAPIView(APIView):
    """
    Create a payment link for a specific savings goal.
    POST /api/v2/payment-links/create-goal-link
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

        goal_id = request.data.get('goal_id')
        description = request.data.get('description', '')
        target_amount = request.data.get('target_amount')
        show_contributors = request.data.get('show_contributors', 'public')
        expires_at = request.data.get('expires_at')
        custom_message = request.data.get('custom_message', 'Thank you for your contribution!')

        # Validate goal
        if not goal_id:
            return validation_error_response({'goal_id': 'Goal ID is required'})

        try:
            goal = SavingsGoalModel.objects.get(id=goal_id, user=request.user)
        except SavingsGoalModel.DoesNotExist:
            return error_response('Savings goal not found or does not belong to you')

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

            serializer = PaymentLinkSerializer(payment_link)
            return success_response(
                message="Payment link created successfully",
                data=serializer.data
            )

        except Exception as e:
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
