from rest_framework import serializers
from account.models.users import UserModel
from account.models.sessions import UserSession


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone','dob', 'address',
            'country', 'state', 'currency','is_active', 'is_verified', 'is_admin','image',
            'last_login','has_bvn','account_tier','email_verified',
            'has_nin', 'has_virtual_wallet',
        ]
        read_only_fields = ['email', 'username', 'is_active', 'is_verified', 'is_admin', 'last_login',
                           'phone', 'has_virtual_wallet',]


class UpdateUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ['first_name', 'last_name', 'phone', 'address', 'country', 'state','image',]


class UpdateUserBVNSerializer(serializers.ModelSerializer):
    bvn = serializers.CharField(required=True)

    class Meta:
        model = UserModel
        fields = ['bvn',]


class UpdateUserNINSerializer(serializers.Serializer):
    """Serializer for NIN verification - fields are for API call, not model update"""
    nin = serializers.CharField(
        required=True,
        max_length=11,
        min_length=11,
        help_text="11-digit NIN",
        error_messages={
            'required': 'NIN is required',
            'min_length': 'NIN must be exactly 11 digits',
            'max_length': 'NIN must be exactly 11 digits',
        }
    )
    firstname = serializers.CharField(
        required=True,
        max_length=200,
        help_text="First name as on NIN",
        error_messages={'required': 'First name is required (use "firstname" field)'}
    )
    lastname = serializers.CharField(
        required=True,
        max_length=200,
        help_text="Last name as on NIN",
        error_messages={'required': 'Last name is required (use "lastname" field)'}
    )
    dob = serializers.CharField(
        required=True,
        help_text="Date of birth in format: YYYY-MM-DD or YYYY-MM-DDTHH",
        error_messages={'required': 'Date of birth is required'}
    )

    def validate_nin(self, value):
        """Validate NIN is exactly 11 digits"""
        if not value.isdigit():
            raise serializers.ValidationError("NIN must contain only digits (0-9)")
        return value

    def validate_dob(self, value):
        """Validate and transform DOB to Embedly format"""
        # Accept both YYYY-MM-DD and YYYY-MM-DDTHH formats
        # If it's just YYYY-MM-DD, convert to YYYY-MM-DDT09
        if len(value) == 10 and value.count('-') == 2:
            # Format: YYYY-MM-DD, convert to YYYY-MM-DDT09
            return f"{value}T09"
        elif 'T' in value:
            # Already has time component
            return value
        else:
            raise serializers.ValidationError("Date of birth must be in format YYYY-MM-DD or YYYY-MM-DDTHH")

    def validate(self, data):
        """Cross-field validation"""
        # Ensure all required fields are present
        required_fields = ['nin', 'firstname', 'lastname', 'dob']
        missing = [f for f in required_fields if f not in data or not data[f]]
        if missing:
            raise serializers.ValidationError({
                'error': f'Missing required fields: {", ".join(missing)}. Expected fields: nin, firstname, lastname, dob'
            })
        return data


class UserSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for user session information.
    Used for listing and displaying session details in the mobile app.
    """
    is_current = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = UserSession
        fields = [
            'id',
            'device_name',
            'device_type',
            'device_id',
            'ip_address',
            'location',
            'is_active',
            'is_current',
            'is_expired',
            'created_at',
            'last_active_at',
            'expires_at',
        ]
        read_only_fields = fields

    def get_is_current(self, obj):
        """
        Determine if this session is the current one making the request.
        Compares against the request context if available.
        """
        request = self.context.get('request')
        if request and hasattr(request, 'auth') and request.auth:
            # Check if the refresh token from the request matches this session
            # This requires the refresh token to be available in the request context
            current_token_hash = self.context.get('current_token_hash')
            if current_token_hash:
                return obj.refresh_token_hash == current_token_hash
        return False

    def get_is_expired(self, obj):
        """Check if the session has expired"""
        return obj.is_expired()


# ============================================
# V2 KYC Serializers (Prembly Integration)
# ============================================

class V2BVNVerifySerializer(serializers.Serializer):
    """
    Serializer for V2 BVN verification (Step 1: Verify)
    Used to validate BVN input before calling Prembly API
    """
    bvn = serializers.CharField(
        required=True,
        max_length=11,
        min_length=11,
        help_text="11-digit Bank Verification Number",
        error_messages={
            'required': 'BVN is required',
            'min_length': 'BVN must be exactly 11 digits',
            'max_length': 'BVN must be exactly 11 digits',
        }
    )

    def validate_bvn(self, value):
        """Validate BVN is exactly 11 digits"""
        if not value.isdigit():
            raise serializers.ValidationError("BVN must contain only digits (0-9)")
        return value


class V2BVNConfirmSerializer(serializers.Serializer):
    """
    Serializer for V2 BVN confirmation (Step 2: Confirm)
    User confirms the BVN details returned from Prembly
    """
    bvn = serializers.CharField(
        required=True,
        max_length=11,
        min_length=11,
        help_text="11-digit BVN being confirmed"
    )
    confirmed = serializers.BooleanField(
        required=True,
        help_text="User confirmation that BVN details are correct"
    )

    def validate_confirmed(self, value):
        """Ensure user confirmed the details"""
        if not value:
            raise serializers.ValidationError("You must confirm that the BVN details are correct")
        return value


class V2NINVerifySerializer(serializers.Serializer):
    """
    Serializer for V2 NIN verification (Step 1: Verify)
    Used to validate NIN input before calling Prembly API
    """
    nin = serializers.CharField(
        required=True,
        max_length=11,
        min_length=11,
        help_text="11-digit National Identification Number",
        error_messages={
            'required': 'NIN is required',
            'min_length': 'NIN must be exactly 11 digits',
            'max_length': 'NIN must be exactly 11 digits',
        }
    )
    first_name = serializers.CharField(
        required=False,
        max_length=200,
        help_text="First name (optional, for matching)"
    )
    last_name = serializers.CharField(
        required=False,
        max_length=200,
        help_text="Last name (optional, for matching)"
    )
    dob = serializers.CharField(
        required=False,
        help_text="Date of birth in format: YYYY-MM-DD (optional, for matching)"
    )

    def validate_nin(self, value):
        """Validate NIN is exactly 11 digits"""
        if not value.isdigit():
            raise serializers.ValidationError("NIN must contain only digits (0-9)")
        return value


class V2NINConfirmSerializer(serializers.Serializer):
    """
    Serializer for V2 NIN confirmation (Step 2: Confirm)
    User confirms the NIN details returned from Prembly
    """
    nin = serializers.CharField(
        required=True,
        max_length=11,
        min_length=11,
        help_text="11-digit NIN being confirmed"
    )
    confirmed = serializers.BooleanField(
        required=True,
        help_text="User confirmation that NIN details are correct"
    )

    def validate_confirmed(self, value):
        """Ensure user confirmed the details"""
        if not value:
            raise serializers.ValidationError("You must confirm that the NIN details are correct")
        return value
