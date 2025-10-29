from rest_framework import serializers
from account.models.users import UserModel


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone','dob', 'address',
            'country', 'state', 'currency','is_active', 'is_verified', 'is_admin','image',
            'last_login','has_bvn','account_tier','bvn','phone','bvn_dob','email_verified',
            'has_nin', 'nin', 'nin_dob', 'nin_first_name', 'nin_last_name',
            'bvn_first_name', 'bvn_last_name', 'has_virtual_wallet',
        ]
        read_only_fields = ['email', 'username', 'is_active', 'is_verified', 'is_admin', 'last_login',
                           'bvn','phone','bvn_dob', 'nin', 'nin_dob', 'bvn_first_name', 'bvn_last_name',
                           'nin_first_name', 'nin_last_name', 'has_virtual_wallet',]


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
