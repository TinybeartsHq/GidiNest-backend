from django.urls import path
from onboarding.views import RegisterInitiateView,RegisterVerifyOTPView,RegisterCompleteView,LoginView, RequestOTPView, VerifyOTPView, ResetPasswordView
from onboarding.views.auth import ActivateEmailView
from onboarding.views.device import DeviceFCMVIew

urlpatterns = [
    #registration endpoints
    path('register/initiate', RegisterInitiateView.as_view(), name='register-initiate'),
    path('register/verify-otp', RegisterVerifyOTPView.as_view(), name='register-otp'),
    path('register/complete', RegisterCompleteView.as_view(), name='register-complete'),

    path('register/email/activation', ActivateEmailView.as_view(), name='register-email-activation'),
    
    #login endpoints
    path('login', LoginView.as_view(), name='login'),

    #password reset endpoint
    path('request-otp', RequestOTPView.as_view(), name='request-otp'),
    path('verify-otp', VerifyOTPView.as_view(), name='verify-otp'),
    path('reset-password', ResetPasswordView.as_view(), name='reset-password'),


    path('device-fcm-token', DeviceFCMVIew.as_view(), name='device-fcm-token'),

]