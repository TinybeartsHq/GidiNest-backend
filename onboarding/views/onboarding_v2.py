# onboarding/views/onboarding_v2.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist
from core.helpers.response import success_response, validation_error_response, error_response
from ..models import OnboardingProfile, UserDevice
from ..serializers_onboarding import (
    OnboardingProfileSerializer,
    OnboardingProfileCreateUpdateSerializer,
    UserDeviceSerializer,
    UserDeviceCreateSerializer
)
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes


class OnboardingProfileAPIView(APIView):
    """
    V2 Mobile - Onboarding Profile Management

    GET: Retrieve user's onboarding profile
    POST: Create/Update user's onboarding profile
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V2 - Onboarding'],
        summary='Get User Onboarding Profile',
        description='Retrieve the authenticated user\'s onboarding profile. Returns 404 if profile doesn\'t exist.',
        responses={
            200: OnboardingProfileSerializer,
            404: OpenApiTypes.OBJECT
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Get the user's onboarding profile.
        Returns 404 if profile doesn't exist (e.g., web users).
        """
        try:
            profile = OnboardingProfile.objects.get(user=request.user)
            serializer = OnboardingProfileSerializer(profile)
            return success_response(data=serializer.data, message="Onboarding profile retrieved successfully")
        except OnboardingProfile.DoesNotExist:
            return error_response(
                message="No onboarding profile found. User may have registered via web.",
                status_code=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        tags=['V2 - Onboarding'],
        summary='Create/Update Onboarding Profile',
        description='Create or update the authenticated user\'s onboarding profile. If profile exists, it will be updated.',
        request=OnboardingProfileCreateUpdateSerializer,
        responses={
            200: OnboardingProfileSerializer,
            201: OnboardingProfileSerializer,
            400: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                'Pregnant User',
                value={
                    'journey_type': 'pregnant',
                    'due_date': '2025-08-15',
                    'hospital_plan': 'private',
                    'location': 'Lagos',
                    'baby_essentials_preference': 'comfort',
                    'onboarding_completed': True,
                    'onboarding_source': 'mobile'
                }
            ),
            OpenApiExample(
                'New Mom',
                value={
                    'journey_type': 'new_mom',
                    'birth_date': '2024-10-01',
                    'hospital_plan': 'basic',
                    'location': 'Abuja',
                    'baby_essentials_preference': 'minimalist',
                    'onboarding_completed': True,
                    'onboarding_source': 'mobile'
                }
            ),
        ]
    )
    def post(self, request, *args, **kwargs):
        """
        Create or update user's onboarding profile.
        """
        try:
            # Try to get existing profile
            profile = OnboardingProfile.objects.get(user=request.user)
            serializer = OnboardingProfileCreateUpdateSerializer(profile, data=request.data, partial=True)
            is_update = True
        except OnboardingProfile.DoesNotExist:
            # Create new profile
            serializer = OnboardingProfileCreateUpdateSerializer(data=request.data)
            is_update = False

        if serializer.is_valid():
            if is_update:
                profile = serializer.save()
                response_serializer = OnboardingProfileSerializer(profile)
                return success_response(
                    data=response_serializer.data,
                    message="Onboarding profile updated successfully",
                    status_code=status.HTTP_200_OK
                )
            else:
                profile = serializer.save(user=request.user)
                response_serializer = OnboardingProfileSerializer(profile)
                return success_response(
                    data=response_serializer.data,
                    message="Onboarding profile created successfully",
                    status_code=status.HTTP_201_CREATED
                )

        return validation_error_response(serializer.errors)


class UserDeviceAPIView(APIView):
    """
    V2 Mobile - User Device Management

    GET: List user's devices
    POST: Register a new device
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V2 - Onboarding'],
        summary='List User Devices',
        description='Get all devices registered for the authenticated user',
        responses={200: UserDeviceSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        """
        Get all devices for the authenticated user.
        """
        devices = UserDevice.objects.filter(user=request.user)
        serializer = UserDeviceSerializer(devices, many=True)
        return success_response(data=serializer.data, message="User devices retrieved successfully")

    @extend_schema(
        tags=['V2 - Onboarding'],
        summary='Register Device',
        description='Register a new device or update existing device information',
        request=UserDeviceCreateSerializer,
        responses={
            200: UserDeviceSerializer,
            201: UserDeviceSerializer,
            400: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                'iOS Device',
                value={
                    'platform': 'mobile_ios',
                    'device_id': 'ABC123XYZ789',
                    'device_name': 'iPhone 14 Pro',
                    'app_version': '1.0.0',
                    'created_via': 'mobile_ios'
                }
            ),
            OpenApiExample(
                'Android Device',
                value={
                    'platform': 'mobile_android',
                    'device_id': 'DEF456UVW012',
                    'device_name': 'Samsung Galaxy S23',
                    'app_version': '1.0.0',
                    'created_via': 'mobile_android'
                }
            ),
        ]
    )
    def post(self, request, *args, **kwargs):
        """
        Register a new device or update existing device.
        If device_id already exists, update the device info.
        """
        device_id = request.data.get('device_id')

        if device_id:
            # Check if device already exists
            try:
                device = UserDevice.objects.get(user=request.user, device_id=device_id)
                serializer = UserDeviceCreateSerializer(device, data=request.data, partial=True, context={'request': request})
                is_update = True
            except UserDevice.DoesNotExist:
                serializer = UserDeviceCreateSerializer(data=request.data, context={'request': request})
                is_update = False
        else:
            serializer = UserDeviceCreateSerializer(data=request.data, context={'request': request})
            is_update = False

        if serializer.is_valid():
            if is_update:
                device = serializer.save()
                response_serializer = UserDeviceSerializer(device)
                return success_response(
                    data=response_serializer.data,
                    message="Device updated successfully",
                    status_code=status.HTTP_200_OK
                )
            else:
                device = serializer.save(user=request.user)
                response_serializer = UserDeviceSerializer(device)
                return success_response(
                    data=response_serializer.data,
                    message="Device registered successfully",
                    status_code=status.HTTP_201_CREATED
                )

        return validation_error_response(serializer.errors)


class CheckOnboardingStatusAPIView(APIView):
    """
    V2 Mobile - Check if user has completed onboarding

    Lightweight endpoint to check onboarding status without fetching full profile.
    Useful for mobile app to decide navigation flow on login.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['V2 - Onboarding'],
        summary='Check Onboarding Status',
        description='Check if user has completed onboarding. Returns simple boolean response.',
        responses={
            200: OpenApiTypes.OBJECT
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Check if user has completed onboarding.
        Returns: { has_onboarding: boolean, onboarding_completed: boolean }
        """
        try:
            profile = OnboardingProfile.objects.get(user=request.user)
            return success_response(
                data={
                    'has_onboarding': True,
                    'onboarding_completed': profile.onboarding_completed,
                    'journey_type': profile.journey_type,
                    'onboarding_source': profile.onboarding_source
                },
                message="Onboarding status retrieved"
            )
        except OnboardingProfile.DoesNotExist:
            return success_response(
                data={
                    'has_onboarding': False,
                    'onboarding_completed': False,
                    'journey_type': None,
                    'onboarding_source': None
                },
                message="No onboarding profile found"
            )
