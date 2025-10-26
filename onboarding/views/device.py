from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from account.models.devices import UserDevices
from core.helpers.response import error_response, success_response, validation_error_response
from onboarding.serializers import DeviceFCMSerializer, RegisterCompleteSerializer, RegisterInitiateSerializer, RegisterOTPSerializer, UserSerializer, LoginSerializer
from account.models.users import UserModel
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import permissions
import random
from django.utils import timezone
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

 


class DeviceFCMVIew(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = DeviceFCMSerializer(data=request.data)
        if serializer.is_valid():

         
            device_id = serializer.validated_data.get('device_id')
            token =  serializer.validated_data.get('token')
       
            device,_ = UserDevices.objects.get_or_create(
                user=request.user,
                device_id = device_id)
            device.fcm_token = token
            device.active =  True
            device.save()

            print(f"Device registered: {device_id} with token: {token}")

      
            return success_response({'detail': 'Device registered successfully.'})
        return validation_error_response(serializer.errors)
    


 