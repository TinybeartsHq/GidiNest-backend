from rest_framework import serializers
from account.models.users import UserModel


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone','dob', 'address',
            'country', 'state', 'currency','is_active', 'is_verified', 'is_admin','image',
             'last_login','has_bvn','account_tier','bvn','phone','bvn_dob','email_verified',
        ]
        read_only_fields = ['email', 'username', 'is_active', 'is_verified', 'is_admin', 'last_login','bvn','phone','bvn_dob',]


class UpdateUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ['first_name', 'last_name', 'phone', 'address', 'country', 'state','image',]


class UpdateUserBVNSerializer(serializers.ModelSerializer):
    bvn = serializers.CharField(required=True)
    
    class Meta:
        model = UserModel
        fields = ['bvn',]
