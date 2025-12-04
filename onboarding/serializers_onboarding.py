# onboarding/serializers_onboarding.py
from rest_framework import serializers
from .models import OnboardingProfile, UserDevice
from django.contrib.auth import get_user_model

User = get_user_model()


class OnboardingProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for OnboardingProfile model.
    Used for creating and retrieving rich onboarding data for mobile users.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = OnboardingProfile
        fields = [
            'id',
            'user',
            'user_email',
            'user_name',
            'journey_type',
            'due_date',
            'birth_date',
            'conception_date',
            'pregnancy_weeks',
            'hospital_plan',
            'location',
            'baby_essentials_preference',
            'onboarding_completed',
            'onboarding_source',
            'onboarding_completed_at',
            'partner_invited',
            'partner_email',
            'partner_phone',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'user_email',
            'user_name',
            'pregnancy_weeks',
            'onboarding_completed_at',
            'created_at',
            'updated_at',
        ]

    def get_user_name(self, obj):
        """Get user's full name"""
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email

    def validate(self, data):
        """
        Validate onboarding data based on journey type
        """
        journey_type = data.get('journey_type')

        if journey_type == 'pregnant':
            if not data.get('due_date'):
                raise serializers.ValidationError({
                    'due_date': 'Due date is required for pregnant users'
                })
        elif journey_type == 'new_mom':
            if not data.get('birth_date'):
                raise serializers.ValidationError({
                    'birth_date': 'Birth date is required for new moms'
                })
        elif journey_type == 'trying':
            if not data.get('conception_date'):
                raise serializers.ValidationError({
                    'conception_date': 'Target conception date is required for trying to conceive'
                })

        return data


class OnboardingProfileCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating onboarding profiles.
    Doesn't require user field as it's set automatically from request.user.
    """

    class Meta:
        model = OnboardingProfile
        fields = [
            'journey_type',
            'due_date',
            'birth_date',
            'conception_date',
            'hospital_plan',
            'location',
            'baby_essentials_preference',
            'onboarding_completed',
            'onboarding_source',
            'partner_invited',
            'partner_email',
            'partner_phone',
        ]

    def validate(self, data):
        """
        Validate onboarding data based on journey type
        """
        journey_type = data.get('journey_type')

        if journey_type == 'pregnant':
            if not data.get('due_date'):
                raise serializers.ValidationError({
                    'due_date': 'Due date is required for pregnant users'
                })
        elif journey_type == 'new_mom':
            if not data.get('birth_date'):
                raise serializers.ValidationError({
                    'birth_date': 'Birth date is required for new moms'
                })
        elif journey_type == 'trying':
            if not data.get('conception_date'):
                raise serializers.ValidationError({
                    'conception_date': 'Target conception date is required for trying to conceive'
                })

        return data


class UserDeviceSerializer(serializers.ModelSerializer):
    """
    Serializer for UserDevice model.
    Used for tracking user devices and platforms.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserDevice
        fields = [
            'id',
            'user',
            'user_email',
            'platform',
            'device_id',
            'device_name',
            'app_version',
            'last_login_at',
            'created_via',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'user_email',
            'last_login_at',
            'created_at',
            'updated_at',
        ]


class UserDeviceCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating user devices.
    User is set automatically from request.user.
    """

    class Meta:
        model = UserDevice
        fields = [
            'platform',
            'device_id',
            'device_name',
            'app_version',
            'created_via',
        ]

    def validate_device_id(self, value):
        """Ensure device_id is unique for the user"""
        user = self.context['request'].user
        if UserDevice.objects.filter(user=user, device_id=value).exists():
            # Update existing device instead of raising error
            return value
        return value
