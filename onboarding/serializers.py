from rest_framework import serializers
from account.models.users import UserModel




class RegisterInitiateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone = serializers.CharField(required=True)
    first_name = serializers.CharField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    oauth_provider = serializers.CharField(required=False,allow_blank=True)



class RegisterOTPSerializer(serializers.Serializer):
    otp = serializers.CharField(required=True)
    session_id = serializers.CharField(required=True)
   



class RegisterCompleteSerializer(serializers.Serializer):
    session_id = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    country = serializers.CharField(required=True)
    state = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    dob = serializers.CharField(required=True)
    device_id = serializers.CharField(required=False,allow_blank=True)
    device_os =  serializers.CharField(required=False,allow_blank=True)
    device_info =  serializers.CharField(required=False,allow_blank=True)



class UserSerializer(serializers.ModelSerializer):
    country = serializers.CharField(required=True)
    state = serializers.CharField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    dob = serializers.CharField(required=True)

    class Meta:
        model = UserModel
        fields = ('email','phone', 'first_name', 'last_name','country', 'state','address', 'dob', 'password','is_verified',)
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        country = validated_data['country']
        state = validated_data['state']
        address = validated_data['address']
        dob = validated_data['dob']
        
      
        # Create the user
        user = UserModel.objects.create_user(
            email=validated_data['email'],
            phone=validated_data['phone'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],
            country=country,
            state=state,
            address=address,
            dob=dob,
            is_verified=True
        )
        user.currency = "NGN" if country == "Nigeria" else "USD"
        user.save()
        
        return user



class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(allow_blank=True)
    phone = serializers.CharField(allow_blank=True)
    password = serializers.CharField(write_only=True)
    login_type = serializers.CharField(required=True)
    login_with = serializers.CharField(required=True)
    oauth_type = serializers.CharField(required=False,allow_blank=True)
    device_id = serializers.CharField(required=False,allow_blank=True)
    device_os =  serializers.CharField(required=False,allow_blank=True)
    device_info =  serializers.CharField(required=False,allow_blank=True)

 

 



class RequestOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)


class ActivateEmailSerializer(serializers.Serializer):
    session_id = serializers.CharField()


class DeviceFCMSerializer(serializers.Serializer):
    device_id = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
 