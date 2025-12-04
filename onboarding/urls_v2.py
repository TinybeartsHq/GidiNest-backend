# onboarding/urls_v2.py
"""
V2 URLs for Mobile App - Authentication & User Management
Enhanced authentication with passcode, OAuth, and improved flows
"""

from django.urls import path
from onboarding.views.auth_v2 import (
    SignUpView,
    SignInView,
    RefreshTokenView,
    LogoutView,
    PasscodeSetupView,
    PasscodeVerifyView,
    PasscodeChangeView,
    PINSetupView,
    PINVerifyView,
    PINChangeView,
    PINStatusView,
)
from onboarding.views.onboarding_v2 import (
    OnboardingProfileAPIView,
    UserDeviceAPIView,
    CheckOnboardingStatusAPIView,
)

# Placeholder views for OAuth (to be implemented)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class OAuthPlaceholderView(APIView):
    """Placeholder for OAuth endpoints - to be implemented"""
    def post(self, request, *args, **kwargs):
        return Response({
            "success": False,
            "message": "OAuth endpoints coming soon",
            "endpoint": request.path
        }, status=status.HTTP_501_NOT_IMPLEMENTED)

urlpatterns = [
    # ==========================================
    # AUTHENTICATION
    # ==========================================

    # Registration & Login
    path('signup', SignUpView.as_view(), name='v2-signup'),
    path('signin', SignInView.as_view(), name='v2-signin'),

    # OAuth (Placeholder - to be implemented)
    path('oauth/google', OAuthPlaceholderView.as_view(), name='v2-oauth-google'),
    path('oauth/apple', OAuthPlaceholderView.as_view(), name='v2-oauth-apple'),

    # Token Management
    path('refresh', RefreshTokenView.as_view(), name='v2-refresh-token'),
    path('logout', LogoutView.as_view(), name='v2-logout'),

    # ==========================================
    # PASSCODE MANAGEMENT (Mobile-Only)
    # ==========================================
    path('passcode/setup', PasscodeSetupView.as_view(), name='v2-passcode-setup'),
    path('passcode/verify', PasscodeVerifyView.as_view(), name='v2-passcode-verify'),
    path('passcode/change', PasscodeChangeView.as_view(), name='v2-passcode-change'),

    # ==========================================
    # PIN MANAGEMENT (Enhanced from V1)
    # ==========================================
    path('pin/setup', PINSetupView.as_view(), name='v2-pin-setup'),
    path('pin/verify', PINVerifyView.as_view(), name='v2-pin-verify'),
    path('pin/change', PINChangeView.as_view(), name='v2-pin-change'),
    path('pin/status', PINStatusView.as_view(), name='v2-pin-status'),

    # ==========================================
    # ONBOARDING PROFILE (Mobile-Only Rich Experience)
    # ==========================================
    path('onboarding/profile', OnboardingProfileAPIView.as_view(), name='v2-onboarding-profile'),
    path('onboarding/status', CheckOnboardingStatusAPIView.as_view(), name='v2-onboarding-status'),

    # ==========================================
    # DEVICE MANAGEMENT
    # ==========================================
    path('devices', UserDeviceAPIView.as_view(), name='v2-user-devices'),
]
