from django.contrib.auth import get_user_model
import random


class EmailAuthBackend:
    def authenticate(self, request, email=None, password=None):
        user_model = get_user_model()
        print(user_model)
        try:
            user = user_model.objects.get(email=email)
            if user.check_password(password):
                return user
        except user_model.DoesNotExist:
            return None

    def get_user(self, user_id):
        user_model = get_user_model()
        try:
            return user_model.objects.get(pk=user_id)
        except user_model.DoesNotExist:
            return None



def generate_otp():
    # Generate a 6-digit random OTP
    otp = f"{random.randint(100000, 999999)}"
    return otp