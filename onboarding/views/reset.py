from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
import random
from django.utils import timezone
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from onboarding.models import PasswordResetOTP, User
from onboarding.serializers import RequestOTPSerializer, VerifyOTPSerializer, ResetPasswordSerializer



class RequestOTPView(APIView):

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                otp = str(random.randint(100000, 999999))
                PasswordResetOTP.objects.create(user=user, otp=otp)
                
                try:
                    send_mail(
                        'Your Password Reset OTP',
                        f'Use this OTP to reset your password: {otp}',
                        'no-reply@gidinest.com',
                        [email],
                    )
                except:
                    pass

                return Response({'detail': 'OTP sent to your email.'}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'detail': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            try:
                user = User.objects.get(email=email)
                otp_record = PasswordResetOTP.objects.filter(user=user, otp=otp, is_used=False).first()
                
                if otp_record and not otp_record.has_expired():
                    return Response({'detail': 'OTP is valid.'}, status=status.HTTP_200_OK)
                return Response({'detail': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({'detail': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']
            try:
                user = User.objects.get(email=email)
                otp_record = PasswordResetOTP.objects.filter(user=user, otp=otp, is_used=False).first()
                
                if otp_record and not otp_record.has_expired():
                    # Reset the password
                    user.password = make_password(new_password)
                    user.save()
                    
                    # Mark OTP as used
                    otp_record.is_used = True
                    otp_record.save()
                    
                    return Response({'detail': 'Password reset successful.'}, status=status.HTTP_200_OK)
                return Response({'detail': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({'detail': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)