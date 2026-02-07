"""
V2 Mobile App Authentication Views
Simplified authentication flows for mobile applications
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
import hashlib

from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

from account.models.users import UserModel
from account.models.sessions import UserSession
from account.serializers import UserProfileSerializer
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


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def create_user_session(user, refresh_token, device_id, device_name, device_type, ip_address=None, location=None):
    """Create a user session record"""
    # Hash the refresh token for storage
    refresh_token_hash = hashlib.sha256(str(refresh_token).encode()).hexdigest()
    
    # Calculate expiration (30 days from now, matching SIMPLE_JWT settings)
    expires_at = timezone.now() + timedelta(days=30)
    
    # Default device info if not provided
    if not device_id:
        device_id = f"unknown_{user.id}"
    if not device_name:
        device_name = "Unknown Device"
    if not device_type:
        device_type = "unknown"
    
    session = UserSession.objects.create(
        user=user,
        device_id=device_id,
        device_name=device_name,
        device_type=device_type,
        ip_address=ip_address,
        location=location,
        refresh_token_hash=refresh_token_hash,
        expires_at=expires_at,
        is_active=True,
    )
    
    return session


class SignUpView(APIView):
    """
    V2 Mobile Sign Up
    Single-step registration (simplified from V1's 3-step process)
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Get device info from request
            device_id = request.data.get('device_id', '')
            device_name = request.data.get('device_name', 'Unknown Device')
            device_type = request.data.get('device_type', 'unknown')
            ip_address = request.data.get('ip_address') or get_client_ip(request)
            location = request.data.get('location', '')
            
            # Create user session
            if device_id:
                create_user_session(
                    user=user,
                    refresh_token=refresh,
                    device_id=device_id,
                    device_name=device_name,
                    device_type=device_type,
                    ip_address=ip_address,
                    location=location,
                )
            
            # Update last login
            user.last_login_at = timezone.now()
            user.save(update_fields=['last_login_at'])
            
            token_data = {
                "access": str(access_token),
                "refresh": str(refresh),
            }
            
            return success_response(
                data={
                    'user': UserProfileV2Serializer(user).data,
                    'tokens': token_data,
                },
                message="Registration successful"
            )
        
        return validation_error_response(serializer.errors)


class SignInView(APIView):
    """
    V2 Mobile Sign In
    Supports email/password and passcode authentication
    """
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='10/h', method='POST', block=True))
    def post(self, request, *args, **kwargs):
        serializer = SignInSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data.get('password', '').strip()
            passcode = serializer.validated_data.get('passcode', '').strip()
            
            try:
                user = UserModel.objects.get(email=email)
            except UserModel.DoesNotExist:
                return error_response("Invalid email or password", status_code=status.HTTP_401_UNAUTHORIZED)
            
            # Authenticate with password or passcode
            authenticated = False
            if password:
                user_auth = authenticate(email=email, password=password)
                authenticated = user_auth is not None and user_auth == user
            elif passcode:
                authenticated = user.verify_passcode(passcode)
            
            if not authenticated:
                return error_response("Invalid email or password", status_code=status.HTTP_401_UNAUTHORIZED)
            
            if not user.is_active:
                return error_response("This account is not active", status_code=status.HTTP_403_FORBIDDEN)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Get device info from request
            device_id = serializer.validated_data.get('device_id', '')
            device_name = serializer.validated_data.get('device_name', 'Unknown Device')
            device_type = serializer.validated_data.get('device_type', 'unknown')
            ip_address = serializer.validated_data.get('ip_address') or get_client_ip(request)
            location = serializer.validated_data.get('location', '')
            
            # Create user session
            if device_id:
                create_user_session(
                    user=user,
                    refresh_token=refresh,
                    device_id=device_id,
                    device_name=device_name,
                    device_type=device_type,
                    ip_address=ip_address,
                    location=location,
                )
            
            # Update last login
            user.last_login_at = timezone.now()
            user.save(update_fields=['last_login_at'])
            
            token_data = {
                "access": str(access_token),
                "refresh": str(refresh),
            }
            
            return success_response(
                data={
                    'user': UserProfileV2Serializer(user).data,
                    'tokens': token_data,
                },
                message="Sign in successful"
            )
        
        return validation_error_response(serializer.errors)


class RefreshTokenView(TokenRefreshView):
    """
    V2 Mobile Refresh Token
    Uses simplejwt's TokenRefreshView with token rotation
    """
    permission_classes = [AllowAny]


class LogoutView(APIView):
    """
    V2 Mobile Logout
    Invalidates refresh token and session
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh_token', '')
        device_id = request.data.get('device_id', '')
        
        if refresh_token:
            try:
                # Try to blacklist the refresh token (if blacklist app is installed)
                token = RefreshToken(refresh_token)
                try:
                    token.blacklist()
                except AttributeError:
                    # Blacklist app not installed, skip blacklisting
                    pass
            except Exception:
                # Token might already be blacklisted or invalid, continue anyway
                pass
            
            # Invalidate session by refresh token hash
            refresh_token_hash = hashlib.sha256(str(refresh_token).encode()).hexdigest()
            UserSession.objects.filter(
                user=request.user,
                refresh_token_hash=refresh_token_hash,
                is_active=True
            ).update(is_active=False)
            
            # Also invalidate by device_id if provided
            if device_id:
                UserSession.objects.filter(
                    user=request.user,
                    device_id=device_id,
                    is_active=True
                ).update(is_active=False)
        
        return success_response(
            data={'message': 'Logged out successfully'},
            message="Logged out successfully"
        )


class PasscodeSetupView(APIView):
    """
    V2 Mobile Passcode Setup
    Set 6-digit passcode for quick login
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PasscodeSetupSerializer(data=request.data)
        if serializer.is_valid():
            passcode = serializer.validated_data['passcode']
            
            try:
                request.user.set_passcode(passcode)
                return success_response(
                    data={
                        'has_passcode': True,
                    },
                    message="Passcode set successfully"
                )
            except ValueError as e:
                return error_response(str(e), status_code=status.HTTP_400_BAD_REQUEST)
        
        return validation_error_response(serializer.errors)


class PasscodeVerifyView(APIView):
    """
    V2 Mobile Passcode Verify
    Verify 6-digit passcode
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PasscodeVerifySerializer(data=request.data)
        if serializer.is_valid():
            passcode = serializer.validated_data['passcode']
            
            if request.user.verify_passcode(passcode):
                return success_response(
                    data={'verified': True},
                    message="Passcode verified"
                )
            else:
                return error_response("Invalid passcode", status_code=status.HTTP_400_BAD_REQUEST)
        
        return validation_error_response(serializer.errors)


class PasscodeChangeView(APIView):
    """
    V2 Mobile Passcode Change
    Change existing passcode (applies 24-hour restriction)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        serializer = PasscodeChangeSerializer(data=request.data)
        if serializer.is_valid():
            current_passcode = serializer.validated_data['current_passcode']
            new_passcode = serializer.validated_data['new_passcode']
            
            # Verify current passcode
            if not request.user.verify_passcode(current_passcode):
                return error_response("Current passcode is incorrect", status_code=status.HTTP_400_BAD_REQUEST)
            
            try:
                was_set = request.user.passcode_set
                request.user.set_passcode(new_passcode)
                
                # Check if restriction was applied (only if passcode was changed, not first-time set)
                restriction_applied = was_set
                restricted_until = None
                restricted_limit = None
                
                if restriction_applied:
                    restricted_until = request.user.limit_restricted_until
                    restricted_limit = request.user.restricted_limit
                
                return success_response(
                    data={
                        'has_passcode': True,
                        'restriction_applied': restriction_applied,
                        'restricted_until': restricted_until.isoformat() if restricted_until else None,
                        'restricted_limit': restricted_limit,
                    },
                    message="Passcode changed successfully. Transaction limit restricted to ₦10,000 for 24 hours." if restriction_applied else "Passcode changed successfully"
                )
            except ValueError as e:
                return error_response(str(e), status_code=status.HTTP_400_BAD_REQUEST)
        
        return validation_error_response(serializer.errors)


class PINSetupView(APIView):
    """
    V2 Mobile PIN Setup
    Set transaction PIN (4-6 digits)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PINSetupSerializer(data=request.data)
        if serializer.is_valid():
            pin = serializer.validated_data['pin']
            
            try:
                request.user.set_transaction_pin(pin)
                return success_response(
                    data={
                        'has_pin': True,
                    },
                    message="Transaction PIN set successfully"
                )
            except ValueError as e:
                return error_response(str(e), status_code=status.HTTP_400_BAD_REQUEST)
        
        return validation_error_response(serializer.errors)


class PINVerifyView(APIView):
    """
    V2 Mobile PIN Verify
    Verify transaction PIN
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PINVerifySerializer(data=request.data)
        if serializer.is_valid():
            pin = serializer.validated_data['pin']
            
            if request.user.verify_transaction_pin(pin):
                return success_response(
                    data={'verified': True},
                    message="PIN verified"
                )
            else:
                return error_response("Invalid PIN", status_code=status.HTTP_400_BAD_REQUEST)
        
        return validation_error_response(serializer.errors)


class PINChangeView(APIView):
    """
    V2 Mobile PIN Change
    Change existing transaction PIN (applies 24-hour restriction)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        serializer = PINChangeSerializer(data=request.data)
        if serializer.is_valid():
            current_pin = serializer.validated_data['current_pin']
            new_pin = serializer.validated_data['new_pin']
            
            # Verify current PIN
            if not request.user.verify_transaction_pin(current_pin):
                return error_response("Current PIN is incorrect", status_code=status.HTTP_400_BAD_REQUEST)
            
            try:
                was_set = request.user.transaction_pin_set
                request.user.set_transaction_pin(new_pin)
                
                # Check if restriction was applied (only if PIN was changed, not first-time set)
                restriction_applied = was_set
                restricted_until = None
                restricted_limit = None
                
                if restriction_applied:
                    restricted_until = request.user.limit_restricted_until
                    restricted_limit = request.user.restricted_limit
                
                return success_response(
                    data={
                        'has_pin': True,
                        'restriction_applied': restriction_applied,
                        'restricted_until': restricted_until.isoformat() if restricted_until else None,
                        'restricted_limit': restricted_limit,
                    },
                    message="PIN changed successfully. Transaction limit restricted to ₦10,000 for 24 hours." if restriction_applied else "PIN changed successfully"
                )
            except ValueError as e:
                return error_response(str(e), status_code=status.HTTP_400_BAD_REQUEST)
        
        return validation_error_response(serializer.errors)


class PINStatusView(APIView):
    """
    V2 Mobile PIN Status
    Check if transaction PIN is set
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        has_pin = request.user.transaction_pin_set
        
        return Response({
            'status': has_pin,
            'transaction_pin_set': has_pin,
            'detail': 'Transaction PIN is set.' if has_pin else 'Transaction PIN is not set.'
        }, status=status.HTTP_200_OK)
