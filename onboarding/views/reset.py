from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
import secrets
import logging
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from onboarding.models import PasswordResetOTP, User
from onboarding.serializers import RequestOTPSerializer, VerifyOTPSerializer, ResetPasswordSerializer
from notification.helper.email import MailClient

logger = logging.getLogger(__name__)



class RequestOTPView(APIView):
    """
    Request a password reset OTP.
    Sends a 6-digit OTP to the user's email for password reset verification.
    Rate limited to 3 requests per hour per IP address.
    """
    permission_classes = [permissions.AllowAny]

    @method_decorator(ratelimit(key='ip', rate='3/h', method='POST', block=True))
    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']

            # Check if user exists
            try:
                user = User.objects.get(email=email)
                logger.info(f"Password reset OTP requested for user: {email}")
            except User.DoesNotExist:
                # Don't reveal whether user exists or not (security best practice)
                # Log this for security monitoring
                logger.warning(f"Password reset OTP requested for non-existent email: {email}")
                return Response({
                    'detail': 'If an account exists with this email, an OTP has been sent.'
                }, status=status.HTTP_200_OK)

            # Generate cryptographically secure OTP
            otp = str(secrets.randbelow(900000) + 100000)
            otp_record = PasswordResetOTP.objects.create(user=user, otp=otp)
            logger.info(f"OTP record created for user {email} (ID: {otp_record.id})")

            # Send OTP via email using MailClient
            try:
                client = MailClient()
                email_result = client.send_email(
                    to_email=email,
                    subject="Password Reset OTP",
                    template_name="emails/reset_password.html",
                    context={
                        "otp": otp,
                        "user_name": user.first_name or "User",
                        "year": timezone.now().year,
                    },
                    to_name=user.first_name or "User"
                )

                # Handle None response (should not happen with new MailClient, but be defensive)
                if email_result is None:
                    logger.error(f"MailClient returned None for {email} - unexpected behavior")
                    otp_record.delete()
                    return Response({
                        'detail': 'Failed to send OTP email. Please try again later.'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                # Check if email sending failed
                if email_result.get('status') == 'error':
                    logger.error(f"Failed to send password reset OTP to {email}: {email_result.get('message')}")
                    # Delete the OTP since email failed
                    otp_record.delete()
                    return Response({
                        'detail': 'Failed to send OTP email. Please try again later.'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                logger.info(f"Password reset OTP email sent successfully to {email}")
                return Response({
                    'detail': 'OTP sent to your email. Please check your inbox.'
                }, status=status.HTTP_200_OK)

            except Exception as e:
                logger.exception(f"Unexpected exception sending password reset OTP to {email}: {str(e)}")
                # Delete the OTP since email failed
                otp_record.delete()
                return Response({
                    'detail': 'An error occurred while sending OTP. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    """
    Verify password reset OTP.
    Rate limited to 10 attempts per hour per IP to prevent brute force attacks.
    """
    permission_classes = [permissions.AllowAny]

    @method_decorator(ratelimit(key='ip', rate='10/h', method='POST', block=True))
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            try:
                user = User.objects.get(email=email)
                otp_record = PasswordResetOTP.objects.filter(user=user, otp=otp, is_used=False).first()

                if otp_record and not otp_record.has_expired():
                    logger.info(f"OTP verified successfully for user: {email}")
                    return Response({'detail': 'OTP is valid.'}, status=status.HTTP_200_OK)

                if otp_record and otp_record.has_expired():
                    logger.warning(f"Expired OTP verification attempt for user: {email}")
                else:
                    logger.warning(f"Invalid OTP verification attempt for user: {email}")

                return Response({'detail': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                logger.warning(f"OTP verification attempted for non-existent user: {email}")
                return Response({'detail': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    """
    Reset user password with verified OTP.
    Rate limited to 5 attempts per hour per IP.
    """
    permission_classes = [permissions.AllowAny]

    @method_decorator(ratelimit(key='ip', rate='5/h', method='POST', block=True))
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']
            try:
                user = User.objects.get(email=email)
                otp_record = PasswordResetOTP.objects.filter(user=user, otp=otp, is_used=False).first()

                if otp_record and not otp_record.has_expired():
                    # Reset the password
                    user.password = make_password(new_password)
                    user.save()

                    # Mark OTP as used
                    otp_record.is_used = True
                    otp_record.save()

                    logger.info(f"Password reset successful for user: {email}")
                    return Response({'detail': 'Password reset successful.'}, status=status.HTTP_200_OK)

                if otp_record and otp_record.has_expired():
                    logger.warning(f"Password reset attempted with expired OTP for user: {email}")
                elif otp_record and otp_record.is_used:
                    logger.warning(f"Password reset attempted with already-used OTP for user: {email}")
                else:
                    logger.warning(f"Password reset attempted with invalid OTP for user: {email}")

                return Response({'detail': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                logger.warning(f"Password reset attempted for non-existent user: {email}")
                return Response({'detail': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)