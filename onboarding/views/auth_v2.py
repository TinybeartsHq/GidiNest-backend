"""
V2 Mobile App Authentication Views
Simplified authentication flows for mobile applications
"""

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import logging
import hashlib

from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from account.models.users import UserModel
from account.models.sessions import UserSession
from account.models.devices import UserDevices
from core.helpers.response import error_response, success_response, validation_error_response
from onboarding.serializers_v2 import (
    SignUpSerializer,
    SignInSerializer,
    PasscodeSetupSerializer,
    PasscodeVerifySerializer,
    PasscodeChangeSerializer,
    PINSetupSerializer,
    PINVerifySerializer,
    PINChangeSerializer,
    UserProfileV2Serializer,
)
from notification.helper.email import MailClient

logger = logging.getLogger(__name__)


class SignUpView(APIView):
    """
    V2 Mobile: Single-step user registration
    POST /api/v2/auth/signup
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        try:
            user = serializer.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            # Update last login
            user.last_login_at = timezone.now()
            user.save(update_fields=['last_login_at'])

            # Create user session if device info provided
            device_id = request.data.get('device_id', '').strip()
            if device_id:
                self._create_user_session(
                    user=user,
                    refresh_token=str(refresh),
                    device_id=device_id,
                    device_name=request.data.get('device_name', ''),
                    device_type=request.data.get('device_type', 'unknown'),
                    ip_address=self._get_client_ip(request),
                    location=request.data.get('location', ''),
                )

            # Send welcome email
            try:
                client = MailClient()
                client.send_email(
                    to_email=user.email,
                    subject="Welcome to GidiNest",
                    template_name="emails/welcome.html",
                    context={
                        "first_name": user.first_name,
                        "year": timezone.now().year,
                    },
                    to_name=user.first_name or "User"
                )
            except Exception as e:
                logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")

            # Prepare response
            token_data = {
                "access_token": str(access_token),
                "refresh_token": str(refresh),
                "expires_in": 3600,  # 1 hour in seconds
            }

            user_data = UserProfileV2Serializer(user).data

            return success_response(
                data={
                    "user": user_data,
                    "tokens": token_data,
                },
                message="Registration successful"
            )

        except Exception as e:
            logger.error(f"SignUp error: {str(e)}")
            return error_response("Registration failed. Please try again.", status_code=500)

    def _create_user_session(self, user, refresh_token, device_id, device_name='', device_type='unknown', ip_address=None, location=''):
        """Create or update user session"""
        try:
            # Hash refresh token for storage
            refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

            # Calculate expiry (30 days from now)
            expires_at = timezone.now() + timezone.timedelta(days=30)

            UserSession.objects.create(
                user=user,
                device_id=device_id,
                device_name=device_name or f"{device_type.title()} Device",
                device_type=device_type,
                ip_address=ip_address,
                location=location,
                refresh_token_hash=refresh_token_hash,
                expires_at=expires_at,
                is_active=True,
            )
        except Exception as e:
            logger.error(f"Failed to create user session: {str(e)}")

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SignInView(APIView):
    """
    V2 Mobile: User sign in with email/password or passcode
    POST /api/v2/auth/signin
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SignInSerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        email = serializer.validated_data['email']
        password = serializer.validated_data.get('password', '').strip()
        passcode = serializer.validated_data.get('passcode', '').strip()
        device_id = serializer.validated_data.get('device_id', '').strip()

        try:
            user = UserModel.objects.get(email=email)

            # Authenticate with password or passcode
            if password:
                user = authenticate(email=email, password=password)
                if not user:
                    return error_response("Invalid email or password", status_code=401)
            elif passcode:
                if not user.passcode_set:
                    return error_response("Passcode not set. Please use password to sign in.", status_code=400)
                if not user.verify_passcode(passcode):
                    return error_response("Invalid passcode", status_code=401)
            else:
                return error_response("Either password or passcode must be provided", status_code=400)

            if not user.is_active:
                return error_response("This account is not active", status_code=403)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            # Update last login
            user.last_login_at = timezone.now()
            user.save(update_fields=['last_login_at'])

            # Create or update user session (only if device_id provided)
            if device_id:
                self._create_or_update_session(
                    user=user,
                    refresh_token=str(refresh),
                    device_id=device_id,
                    device_name=serializer.validated_data.get('device_name', ''),
                    device_type=serializer.validated_data.get('device_type', 'unknown'),
                    ip_address=serializer.validated_data.get('ip_address') or self._get_client_ip(request),
                    location=serializer.validated_data.get('location', ''),
                )

                # Update device record
                self._update_device_record(
                    user=user,
                    device_id=device_id,
                    device_os=request.data.get('device_os', ''),
                    device_info=request.data.get('device_info', ''),
                )

            # Prepare response
            token_data = {
                "access_token": str(access_token),
                "refresh_token": str(refresh),
                "expires_in": 3600,  # 1 hour in seconds
            }

            user_data = UserProfileV2Serializer(user).data

            return success_response(
                data={
                    "user": user_data,
                    "tokens": token_data,
                },
                message="Sign in successful"
            )

        except UserModel.DoesNotExist:
            return error_response("Invalid email or password", status_code=401)
        except Exception as e:
            logger.error(f"SignIn error: {str(e)}")
            return error_response("Sign in failed. Please try again.", status_code=500)

    def _create_or_update_session(self, user, refresh_token, device_id, device_name='', device_type='unknown', ip_address=None, location=''):
        """Create or update user session"""
        try:
            refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            expires_at = timezone.now() + timezone.timedelta(days=30)

            # Check if session exists for this device
            session, created = UserSession.objects.get_or_create(
                user=user,
                device_id=device_id,
                defaults={
                    'device_name': device_name or f"{device_type.title()} Device",
                    'device_type': device_type,
                    'ip_address': ip_address,
                    'location': location,
                    'refresh_token_hash': refresh_token_hash,
                    'expires_at': expires_at,
                    'is_active': True,
                }
            )

            if not created:
                # Update existing session
                session.refresh_token_hash = refresh_token_hash
                session.expires_at = expires_at
                session.is_active = True
                session.last_active_at = timezone.now()
                session.save(update_fields=['refresh_token_hash', 'expires_at', 'is_active', 'last_active_at'])

        except Exception as e:
            logger.error(f"Failed to create/update user session: {str(e)}")

    def _update_device_record(self, user, device_id, device_os='', device_info=''):
        """Update user device record"""
        try:
            device, created = UserDevices.objects.get_or_create(
                user=user,
                device_id=device_id,
            )
            if device_os:
                device.device_os = device_os
            if device_info:
                device.device_info = device_info
            device.active = True
            device.save()

            # Deactivate other devices
            UserDevices.objects.filter(user=user).exclude(device_id=device_id).update(active=False)
        except Exception as e:
            logger.error(f"Failed to update device record: {str(e)}")

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RefreshTokenView(TokenRefreshView):
    """
    V2 Mobile: Refresh access token
    POST /api/v2/auth/refresh
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Update session activity
            refresh_token = request.data.get('refresh')
            if refresh_token:
                try:
                    refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
                    session = UserSession.objects.get(refresh_token_hash=refresh_token_hash, is_active=True)
                    session.update_activity()
                except UserSession.DoesNotExist:
                    pass  # Session not found, but token refresh still succeeds
        
        return response


class LogoutView(APIView):
    """
    V2 Mobile: Logout user and invalidate session
    POST /api/v2/auth/logout
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Get refresh token from request
            refresh_token = request.data.get('refresh_token')
            device_id = request.data.get('device_id')

            if refresh_token:
                # Invalidate specific session
                refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
                try:
                    session = UserSession.objects.get(
                        user=request.user,
                        refresh_token_hash=refresh_token_hash,
                        is_active=True
                    )
                    session.invalidate()
                except UserSession.DoesNotExist:
                    pass
            elif device_id:
                # Invalidate session for specific device
                UserSession.objects.filter(
                    user=request.user,
                    device_id=device_id,
                    is_active=True
                ).update(is_active=False)
            else:
                # Invalidate all sessions for user
                UserSession.objects.filter(
                    user=request.user,
                    is_active=True
                ).update(is_active=False)

            return success_response(message="Logged out successfully")

        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return error_response("Logout failed", status_code=500)


class PasscodeSetupView(APIView):
    """
    V2 Mobile: Setup 6-digit passcode
    POST /api/v2/auth/passcode/setup
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasscodeSetupSerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        try:
            passcode = serializer.validated_data['passcode']
            request.user.set_passcode(passcode)

            return success_response(
                data={
                    "has_passcode": True,
                },
                message="Passcode set successfully"
            )

        except ValueError as e:
            return error_response(str(e), status_code=400)
        except Exception as e:
            logger.error(f"Passcode setup error: {str(e)}")
            return error_response("Failed to set passcode", status_code=500)


class PasscodeVerifyView(APIView):
    """
    V2 Mobile: Verify 6-digit passcode
    POST /api/v2/auth/passcode/verify
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasscodeVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        try:
            passcode = serializer.validated_data['passcode']
            is_valid = request.user.verify_passcode(passcode)

            if is_valid:
                return success_response(message="Passcode verified")
            else:
                return error_response("Invalid passcode", status_code=401)

        except Exception as e:
            logger.error(f"Passcode verify error: {str(e)}")
            return error_response("Failed to verify passcode", status_code=500)


class PasscodeChangeView(APIView):
    """
    V2 Mobile: Change existing passcode
    POST /api/v2/auth/passcode/change
    PUT /api/v2/auth/passcode/change (also supported)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return self._change_passcode(request)
    
    def put(self, request):
        return self._change_passcode(request)
    
    def _change_passcode(self, request):
        serializer = PasscodeChangeSerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        try:
            current_passcode = serializer.validated_data['current_passcode']
            new_passcode = serializer.validated_data['new_passcode']

            # Verify current passcode
            if not request.user.verify_passcode(current_passcode):
                return error_response("Current passcode is incorrect", status_code=401)

            # Set new passcode (will trigger 24hr restriction)
            request.user.set_passcode(new_passcode)

            return success_response(
                data={
                    "is_restricted": request.user.is_restricted(),
                    "restricted_until": request.user.limit_restricted_until.isoformat() if request.user.limit_restricted_until else None,
                },
                message="Passcode changed successfully. Transaction limits restricted for 24 hours."
            )

        except ValueError as e:
            return error_response(str(e), status_code=400)
        except Exception as e:
            logger.error(f"Passcode change error: {str(e)}")
            return error_response("Failed to change passcode", status_code=500)


class PINSetupView(APIView):
    """
    V2 Mobile: Setup transaction PIN (4-6 digits)
    POST /api/v2/auth/pin/setup
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PINSetupSerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        try:
            pin = serializer.validated_data['pin']
            request.user.set_transaction_pin(pin)

            return success_response(
                data={
                    "has_pin": True,
                },
                message="Transaction PIN set successfully"
            )

        except ValueError as e:
            return error_response(str(e), status_code=400)
        except Exception as e:
            logger.error(f"PIN setup error: {str(e)}")
            return error_response("Failed to set transaction PIN", status_code=500)


class PINVerifyView(APIView):
    """
    V2 Mobile: Verify transaction PIN
    POST /api/v2/auth/pin/verify
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PINVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        try:
            pin = serializer.validated_data['pin']
            is_valid = request.user.verify_transaction_pin(pin)

            if is_valid:
                return success_response(message="Transaction PIN verified")
            else:
                return error_response("Invalid transaction PIN", status_code=401)

        except Exception as e:
            logger.error(f"PIN verify error: {str(e)}")
            return error_response("Failed to verify transaction PIN", status_code=500)


class PINChangeView(APIView):
    """
    V2 Mobile: Change existing transaction PIN
    POST /api/v2/auth/pin/change
    PUT /api/v2/auth/pin/change (also supported)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return self._change_pin(request)
    
    def put(self, request):
        return self._change_pin(request)
    
    def _change_pin(self, request):
        serializer = PINChangeSerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        try:
            current_pin = serializer.validated_data['current_pin']
            new_pin = serializer.validated_data['new_pin']

            # Verify current PIN
            if not request.user.verify_transaction_pin(current_pin):
                return error_response("Current transaction PIN is incorrect", status_code=401)

            # Set new PIN (will trigger 24hr restriction)
            request.user.set_transaction_pin(new_pin)

            return success_response(
                data={
                    "is_restricted": request.user.is_restricted(),
                    "restricted_until": request.user.limit_restricted_until.isoformat() if request.user.limit_restricted_until else None,
                },
                message="Transaction PIN changed successfully. Transaction limits restricted for 24 hours."
            )

        except ValueError as e:
            return error_response(str(e), status_code=400)
        except Exception as e:
            logger.error(f"PIN change error: {str(e)}")
            return error_response("Failed to change transaction PIN", status_code=500)


class PINStatusView(APIView):
    """
    V2 Mobile: Get transaction PIN status
    GET /api/v2/auth/pin/status
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(
            data={
                "has_pin": request.user.transaction_pin_set,
            },
            message="PIN status retrieved"
        )

