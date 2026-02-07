from django.contrib.auth import get_user_model
import secrets


class EmailAuthBackend:
    def authenticate(self, request, email=None, password=None):
        user_model = get_user_model()
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
    # Generate a cryptographically secure 6-digit OTP
    otp = str(secrets.randbelow(900000) + 100000)
    return otp