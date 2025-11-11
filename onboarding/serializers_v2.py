"""
V2 Mobile App Serializers
Simplified authentication flows for mobile applications
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from account.models.users import UserModel
from account.models.sessions import UserSession
import hashlib


class SignUpSerializer(serializers.Serializer):
    """
    Single-step registration serializer for V2 Mobile
    Simplified from V1's 3-step process
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        help_text="Password must be at least 8 characters"
    )
    password_confirmation = serializers.CharField(
        write_only=True,
        required=True,
        help_text="Password confirmation must match password"
    )
    first_name = serializers.CharField(required=True, max_length=200)
    last_name = serializers.CharField(required=True, max_length=200)
    phone = serializers.CharField(required=True, max_length=20)
    referral_code = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional referral code"
    )

    def validate_email(self, value):
        """Check if email already exists"""
        if UserModel.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_phone(self, value):
        """Check if phone already exists"""
        if UserModel.objects.filter(phone=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value

    def validate_password(self, value):
        """Validate password strength"""
        validate_password(value)
        return value

    def validate(self, data):
        """Cross-field validation"""
        if data['password'] != data['password_confirmation']:
            raise serializers.ValidationError({
                'password_confirmation': 'Passwords do not match.'
            })
        return data

    def create(self, validated_data):
        """Create new user account"""
        validated_data.pop('password_confirmation')
        password = validated_data.pop('password')
        referral_code = validated_data.pop('referral_code', None)

        # Create user
        user = UserModel.objects.create_user(
            email=validated_data['email'],
            password=password,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data['phone'],
            currency='NGN',  # Default to NGN for Nigeria
            verification_status='pending',
        )

        # TODO: Handle referral code if needed
        # TODO: Create wallet via Embedly
        # TODO: Send welcome email
        # TODO: Create welcome notification

        return user


class SignInSerializer(serializers.Serializer):
    """
    Sign in serializer for V2 Mobile
    Supports email/password and passcode authentication
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Password (required if not using passcode)"
    )
    passcode = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        max_length=6,
        min_length=6,
        help_text="6-digit passcode (alternative to password)"
    )
    device_id = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Unique device identifier (optional for web/testing)"
    )
    device_name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Device name (e.g., 'iPhone 14 Pro')"
    )
    device_type = serializers.ChoiceField(
        choices=['ios', 'android', 'web', 'unknown'],
        default='unknown',
        required=False
    )
    ip_address = serializers.IPAddressField(required=False, allow_null=True)
    location = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Approximate location (e.g., 'Lagos, Nigeria')"
    )

    def validate(self, data):
        """Validate that either password or passcode is provided"""
        password = data.get('password', '').strip()
        passcode = data.get('passcode', '').strip()

        if not password and not passcode:
            raise serializers.ValidationError({
                'non_field_errors': ['Either password or passcode must be provided.']
            })

        if password and passcode:
            raise serializers.ValidationError({
                'non_field_errors': ['Provide either password or passcode, not both.']
            })

        return data

    def validate_email(self, value):
        """Check if user exists"""
        try:
            user = UserModel.objects.get(email=value)
            if not user.is_active:
                raise serializers.ValidationError("This account is not active.")
            return value
        except UserModel.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")


class PasscodeSetupSerializer(serializers.Serializer):
    """
    Serializer for setting up 6-digit passcode
    """
    passcode = serializers.CharField(
        required=True,
        max_length=6,
        min_length=6,
        help_text="6-digit passcode"
    )
    passcode_confirmation = serializers.CharField(
        required=True,
        max_length=6,
        min_length=6,
        help_text="Confirm 6-digit passcode"
    )

    def validate_passcode(self, value):
        """Validate passcode format and rules"""
        if not value.isdigit():
            raise serializers.ValidationError("Passcode must contain only digits.")

        # Check for sequential numbers (123456, 654321)
        is_sequential_asc = all(int(value[i]) == int(value[i-1]) + 1 for i in range(1, 6))
        is_sequential_desc = all(int(value[i]) == int(value[i-1]) - 1 for i in range(1, 6))
        if is_sequential_asc or is_sequential_desc:
            raise serializers.ValidationError("Passcode cannot be sequential (e.g., 123456, 654321).")

        # Check for all same digits (111111, 222222, etc.)
        if len(set(value)) == 1:
            raise serializers.ValidationError("Passcode cannot be all the same digit (e.g., 111111).")

        return value

    def validate(self, data):
        """Cross-field validation"""
        if data['passcode'] != data['passcode_confirmation']:
            raise serializers.ValidationError({
                'passcode_confirmation': 'Passcodes do not match.'
            })
        return data


class PasscodeVerifySerializer(serializers.Serializer):
    """
    Serializer for verifying 6-digit passcode
    """
    passcode = serializers.CharField(
        required=True,
        max_length=6,
        min_length=6,
        help_text="6-digit passcode"
    )

    def validate_passcode(self, value):
        """Validate passcode format"""
        if not value.isdigit():
            raise serializers.ValidationError("Passcode must contain only digits.")
        return value


class PasscodeChangeSerializer(serializers.Serializer):
    """
    Serializer for changing existing passcode
    Requires current passcode verification
    Accepts both 'old_passcode' and 'current_passcode' for flexibility
    """
    old_passcode = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=6,
        min_length=6,
        help_text="Current 6-digit passcode (alias: current_passcode)"
    )
    current_passcode = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=6,
        min_length=6,
        help_text="Current 6-digit passcode (alias: old_passcode)"
    )
    new_passcode = serializers.CharField(
        required=True,
        max_length=6,
        min_length=6,
        help_text="New 6-digit passcode"
    )
    new_passcode_confirmation = serializers.CharField(
        required=True,
        max_length=6,
        min_length=6,
        help_text="Confirm new 6-digit passcode"
    )

    def validate_old_passcode(self, value):
        """Validate old passcode format"""
        if value and not value.isdigit():
            raise serializers.ValidationError("Passcode must contain only digits.")
        return value

    def validate_current_passcode(self, value):
        """Validate current passcode format"""
        if value and not value.isdigit():
            raise serializers.ValidationError("Passcode must contain only digits.")
        return value

    def validate_new_passcode(self, value):
        """Validate new passcode format and rules"""
        if not value or not value.isdigit():
            raise serializers.ValidationError("Passcode must contain only digits.")

        # Check for sequential numbers
        is_sequential_asc = all(int(value[i]) == int(value[i-1]) + 1 for i in range(1, 6))
        is_sequential_desc = all(int(value[i]) == int(value[i-1]) - 1 for i in range(1, 6))
        if is_sequential_asc or is_sequential_desc:
            raise serializers.ValidationError("Passcode cannot be sequential (e.g., 123456, 654321).")

        # Check for all same digits
        if len(set(value)) == 1:
            raise serializers.ValidationError("Passcode cannot be all the same digit (e.g., 111111).")

        return value

    def validate(self, attrs):
        """Cross-field validation"""
        # Get current passcode from either field (handle both None and empty string)
        old_passcode = attrs.get('old_passcode', '').strip() if attrs.get('old_passcode') else ''
        current_passcode = attrs.get('current_passcode', '').strip() if attrs.get('current_passcode') else ''
        current_passcode_value = old_passcode or current_passcode
        
        if not current_passcode_value:
            raise serializers.ValidationError({
                'non_field_errors': ['Either old_passcode or current_passcode must be provided.']
            })

        if attrs['new_passcode'] != attrs['new_passcode_confirmation']:
            raise serializers.ValidationError({
                'new_passcode_confirmation': 'New passcodes do not match.'
            })

        if current_passcode_value == attrs['new_passcode']:
            raise serializers.ValidationError({
                'new_passcode': 'New passcode must be different from current passcode.'
            })

        # Normalize to 'current_passcode' for consistency
        attrs['current_passcode'] = current_passcode_value
        return attrs


class PINSetupSerializer(serializers.Serializer):
    """
    Serializer for setting up transaction PIN (4-6 digits)
    """
    pin = serializers.CharField(
        required=True,
        min_length=4,
        max_length=6,
        help_text="Transaction PIN (4-6 digits)"
    )
    pin_confirmation = serializers.CharField(
        required=True,
        min_length=4,
        max_length=6,
        help_text="Confirm transaction PIN"
    )

    def validate_pin(self, value):
        """Validate PIN format"""
        if not value.isdigit():
            raise serializers.ValidationError("PIN must contain only digits.")
        return value

    def validate(self, data):
        """Cross-field validation"""
        if data['pin'] != data['pin_confirmation']:
            raise serializers.ValidationError({
                'pin_confirmation': 'PINs do not match.'
            })
        return data


class PINVerifySerializer(serializers.Serializer):
    """
    Serializer for verifying transaction PIN
    """
    pin = serializers.CharField(
        required=True,
        min_length=4,
        max_length=6,
        help_text="Transaction PIN (4-6 digits)"
    )

    def validate_pin(self, value):
        """Validate PIN format"""
        if not value.isdigit():
            raise serializers.ValidationError("PIN must contain only digits.")
        return value


class PINChangeSerializer(serializers.Serializer):
    """
    Serializer for changing existing transaction PIN
    Requires current PIN verification
    Accepts both 'old_pin' and 'current_pin' for flexibility
    """
    old_pin = serializers.CharField(
        required=False,
        allow_blank=True,
        min_length=4,
        max_length=6,
        help_text="Current transaction PIN (alias: current_pin)"
    )
    current_pin = serializers.CharField(
        required=False,
        allow_blank=True,
        min_length=4,
        max_length=6,
        help_text="Current transaction PIN (alias: old_pin)"
    )
    new_pin = serializers.CharField(
        required=True,
        min_length=4,
        max_length=6,
        help_text="New transaction PIN"
    )
    new_pin_confirmation = serializers.CharField(
        required=True,
        min_length=4,
        max_length=6,
        help_text="Confirm new transaction PIN"
    )

    def validate_old_pin(self, value):
        """Validate old PIN format"""
        if value and not value.isdigit():
            raise serializers.ValidationError("PIN must contain only digits.")
        return value

    def validate_current_pin(self, value):
        """Validate current PIN format"""
        if value and not value.isdigit():
            raise serializers.ValidationError("PIN must contain only digits.")
        return value

    def validate_new_pin(self, value):
        """Validate new PIN format"""
        if not value or not value.isdigit():
            raise serializers.ValidationError("PIN must contain only digits.")
        return value

    def validate(self, attrs):
        """Cross-field validation"""
        # Get current PIN from either field (handle both None and empty string)
        old_pin = attrs.get('old_pin', '').strip() if attrs.get('old_pin') else ''
        current_pin = attrs.get('current_pin', '').strip() if attrs.get('current_pin') else ''
        current_pin_value = old_pin or current_pin
        
        if not current_pin_value:
            raise serializers.ValidationError({
                'non_field_errors': ['Either old_pin or current_pin must be provided.']
            })

        if attrs['new_pin'] != attrs['new_pin_confirmation']:
            raise serializers.ValidationError({
                'new_pin_confirmation': 'New PINs do not match.'
            })

        if current_pin_value == attrs['new_pin']:
            raise serializers.ValidationError({
                'new_pin': 'New PIN must be different from current PIN.'
            })

        # Normalize to 'current_pin' for consistency
        attrs['current_pin'] = current_pin_value
        return attrs


class UserProfileV2Serializer(serializers.ModelSerializer):
    """
    V2 User Profile Serializer
    Includes mobile-specific fields
    """
    has_passcode = serializers.BooleanField(source='passcode_set', read_only=True)
    has_pin = serializers.BooleanField(source='transaction_pin_set', read_only=True)
    biometric_enabled = serializers.BooleanField(read_only=True)
    verification_status = serializers.CharField(read_only=True)
    is_restricted = serializers.SerializerMethodField()
    effective_per_transaction_limit = serializers.SerializerMethodField()
    effective_daily_limit = serializers.SerializerMethodField()

    class Meta:
        model = UserModel
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'phone',
            'is_verified',
            'has_passcode',
            'has_pin',
            'biometric_enabled',
            'verification_status',
            'is_restricted',
            'effective_per_transaction_limit',
            'effective_daily_limit',
            'account_tier',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'email',
            'is_verified',
            'has_passcode',
            'has_pin',
            'biometric_enabled',
            'verification_status',
            'is_restricted',
            'effective_per_transaction_limit',
            'effective_daily_limit',
            'account_tier',
            'created_at',
        ]

    def get_is_restricted(self, obj):
        """Check if user is currently restricted"""
        return obj.is_restricted()

    def get_effective_per_transaction_limit(self, obj):
        """Get effective per-transaction limit"""
        return obj.get_effective_per_transaction_limit()

    def get_effective_daily_limit(self, obj):
        """Get effective daily limit"""
        return obj.get_effective_daily_limit()

