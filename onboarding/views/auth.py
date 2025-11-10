from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from account.models.devices import UserDevices
from account.serializers import UserProfileSerializer
from core.helpers.response import error_response, success_response, validation_error_response
from notification.helper.email import MailClient
from onboarding.serializers import ActivateEmailSerializer, RegisterCompleteSerializer, RegisterInitiateSerializer, RegisterOTPSerializer, UserSerializer, LoginSerializer
from account.models.users import UserModel
from rest_framework_simplejwt.tokens import RefreshToken
import random
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from onboarding.models import PasswordResetOTP, RegisterTempData, User
from onboarding.serializers import RequestOTPSerializer, VerifyOTPSerializer, ResetPasswordSerializer
from django.contrib.auth import authenticate
from django.conf import settings
from django.db.models import Q


class RegisterInitiateView(APIView):
    """
    Endpoint to initiate user registration, handling both direct email and OAuth flows.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
 
        serializer = RegisterInitiateSerializer(data=request.data)
        if serializer.is_valid():
            email = request.data.get('email')
            phone = request.data.get('phone')
            first_name = request.data.get('first_name')
            last_name = request.data.get('last_name')
            auth_id = request.data.get('auth_id')
            oauth_provider = request.data.get('oauth_provider') # e.g., 'google', 'apple'

            # check if user with email or phone number already exist
            user_exists = UserModel.objects.filter(
                Q(email=email) | Q(phone=phone)
            ).exists()

            if user_exists:
                return Response({"error": "User with this email or phone already exists."}, status=400)
            
            
            if oauth_provider == "google":
                # OAuth Flow
                temp_data = RegisterTempData.objects.create(
                    email=email,
                    phone=phone,
                    first_name=first_name,
                    last_name=last_name,
                    oauth_provider=oauth_provider, # save provider
                    auth_id=auth_id,
                    is_oauth=True
                )
                session_id = str(temp_data.id) 
                return success_response(data={"session_id": session_id}, message= "Registration Initialized")
        

            else:
                # Direct Email Flow: Send OTP via Email
                otp = str(random.randint(100000, 999999))
                print(otp)
             
                temp_data = RegisterTempData.objects.create(
                    email=email,
                    phone=phone,
                    first_name=first_name,
                    last_name=last_name,
                    oauth_provider=oauth_provider,
                    otp = otp
                ) 
                session_id = str(temp_data.id)

                # Send OTP via email using MailClient
                client = MailClient()
                email_result = client.send_email(
                    to_email=email,
                    subject="Verify Your Email - Gidinest",
                    template_name="emails/otp.html",
                    context={
                        "otp": otp,
                        "user_name": first_name or "User",
                        "year": timezone.now().year,
                    },
                    to_name=first_name or "User"
                )
                
                # Check if email was sent successfully
                if email_result.get("status") != "success":
                    # Delete the temp_data since OTP sending failed
                    temp_data.delete()
                    return error_response("Failed to send OTP email. Please try again later.")
  
                return success_response(data={"session_id": session_id},  message= "OTP sent to your email address")
        return validation_error_response(serializer.errors)


class RegisterVerifyOTPView(APIView):
    """
    Endpoint to verify the OTP entered by the user.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegisterOTPSerializer(data=request.data)
        if serializer.is_valid():
    
            otp = request.data.get('otp')
            session_id = request.data.get('session_id')

            try:
                session = RegisterTempData.objects.get(id=session_id)
            except RegisterTempData.DoesNotExist:
                return error_response("Invalid session ID. Please restart the registration process.")
            
            # Check if this is an OAuth session (shouldn't require OTP verification)
            if session.is_oauth:
                return error_response("OTP verification is not required for OAuth registration.")
      
            stored_otp = session.otp #retrieve otp
    
            if stored_otp and str(stored_otp) == str(otp):
                session.otp_verified = True # set session
                session.save()

                client = MailClient()
                client.send_email(
                        to_email=session.email,
                        subject="Active your email address",
                        template_name="emails/activate.html",
                        context= {
                            "url": f"{settings.ACTIVATION_URL}{session_id}",
                            "year": timezone.now().year,
                        },
                        to_name=session.first_name
                    )

                return success_response( message= "OTP verified")
            else:
                return error_response("Invalid OTP provided")
        return validation_error_response(serializer.errors)


class RegisterCompleteView(APIView):
    """
    Endpoint to complete the registration process, handling both flows.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegisterCompleteSerializer(data=request.data)
        if serializer.is_valid():
        
            session_id = serializer.validated_data.get('session_id')
            password = serializer.validated_data.get('password')
            country = serializer.validated_data.get('country')
            state = serializer.validated_data.get('state')
            address = serializer.validated_data.get('address')
            dob = serializer.validated_data.get('dob')
            device_id = serializer.validated_data.get('device_id')
            device_os =  serializer.validated_data.get('device_os')
            device_info =  serializer.validated_data.get('device_info')

     
            if session_id:

                try:
                    temp_data = RegisterTempData.objects.get(id=session_id)
                except RegisterTempData.DoesNotExist:
                    return error_response("Invalid session ID")
                   
                if temp_data.is_oauth:

                    user_data = {
                        'email': temp_data.email,
                        'first_name': temp_data.first_name,
                        'last_name': temp_data.last_name,
                        'password': password,   
                        'country': country,
                        'state': state,
                        'auth_id':temp_data.auth_id,
                        'address': address,
                        'dob': dob,
                    }

                    serializer = UserSerializer(data=user_data)

                    if serializer.is_valid():
                        user = serializer.save()

                        user.google_id = temp_data.auth_id
                        user.save()

                        tokens = RefreshToken.for_user(user)
                        token_data = {
                            "refresh": str(tokens),
                            "access": str(tokens.access_token)
                        }
                        
                        temp_data.delete()  # Clean up

                        client = MailClient()
                        client.send_email(
                                to_email=user.email,
                                subject="Welcome to Gidinest",
                                template_name="emails/welcome.html",
                                context={"user": user},
                            )

                        return success_response( data={
                            'user': UserSerializer(user).data,
                            'token': token_data
                        },message="Registration successful")
                    return validation_error_response(serializer.errors)
                else:
                    # Direct Email Flow: Complete registration using data from session
                    otp_verified = temp_data.otp_verified
                    if not otp_verified:
                        return error_response("OTP not verified")  

              
                    user_data = {
                        'email': temp_data.email,
                        'phone':temp_data.phone,
                        'first_name': temp_data.first_name,
                        'last_name': temp_data.last_name,
                        'password': password,
                        'country': country,
                        'state': state,
                        'address': address,
                        'dob': dob,
                    }

                    serializer = UserSerializer(data=user_data)
                    if serializer.is_valid():
                        user = serializer.save()
                        tokens = RefreshToken.for_user(user)
                        token_data = {
                            "refresh": str(tokens),
                            "access": str(tokens.access_token)
                        }
                        
                        if device_id:
                            #create user device record
                            UserDevices.objects.create(
                                user=user,
                                device_id = device_id,
                                device_os =  device_os,
                                device_info =  device_info)
                        
                        client = MailClient()
                        client.send_email(
                                to_email=temp_data.email,
                                subject="Welcome to Gidinest",
                                template_name="emails/welcome.html",
                                context= {
                                    "first_name": temp_data.first_name,
                                    "year": timezone.now().year,
                                },
                                to_name=temp_data.first_name
                            )


                        return success_response( data={
                            'user': UserProfileSerializer(user).data,
                            'token': token_data
                        },message="Registration successful")
                    return validation_error_response(serializer.errors)

        return validation_error_response(serializer.errors)


class LoginView(APIView):

    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():

            login_type = serializer.validated_data.get('login_type')
            login_with = serializer.validated_data.get('login_with')
            email = serializer.validated_data.get('email')
            phone = serializer.validated_data.get('phone')
            password =serializer.validated_data.get('password')
            oauth_type = serializer.validated_data.get('oauth_type')
            device_id = serializer.validated_data.get('device_id')
            device_os =  serializer.validated_data.get('device_os')
            device_info =  serializer.validated_data.get('device_info')


            user = None

            if login_type == "oauth":
                if oauth_type == "google":
                    try:
                        user = UserModel.objects.get(email=email,google_id=password)
                    except:
                        return error_response("Invalid email, please sign up for an account")

            else:
                print(login_with)
                if login_with == "email":
                
                    user = authenticate(email=email, password=password)
                else:
                    try:
                        user = UserModel.objects.get(phone=phone)
                        print(user)

                        user = authenticate(email=user.email, password=password)
                        if not user:
                            return error_response("Invalid phone or password")
                    except:
                        return error_response("Invalid phone or password")
                    
                if user is None:
                    return error_response("Invalid email or password")
                if not user.is_active:
                    return error_response("This account is not active")

            if not user:
                return error_response("Invalid email or password")
            
            # generate token for user
            tokens = RefreshToken.for_user(user)

            if device_id:
                #create user device record
                device,_ = UserDevices.objects.get_or_create(
                    user=user,
                    device_id = device_id)
                device.device_os =  device_os
                device.device_info =  device_info
                device.active =  True
                device.save()

                #make other devices inactive
                UserDevices.objects.filter(user=user).exclude(device_id=device_id).update(active=False)
        
            token_data = {
                "refresh": str(tokens),
                "access": str(tokens.access_token)
            }
    
            return success_response({'token': token_data,'user': UserProfileSerializer(user).data}) 
        return validation_error_response(serializer.errors)
    

class ActivateEmailView(APIView):

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ActivateEmailSerializer(data=request.data)
        if serializer.is_valid():
            session_id =request.data.get('session_id')
           
            try:
                temp = RegisterTempData.objects.get(id=session_id)
                user = UserModel.objects.get(email=temp.email)

                user.email_verified = True
                user.save()
                return Response({'detail': 'Email activated'}, status=status.HTTP_200_OK)
            except UserModel.DoesNotExist:
                return Response({'detail': 'An error occurred while activating email please contact support.'}, status=status.HTTP_400_BAD_REQUEST)
            except RegisterTempData.DoesNotExist:
                return Response({'detail': 'Invalid Activation token.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
