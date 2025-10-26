from django.apps import AppConfig


class AccountConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'account'


    def ready(self):
        # Import the signals module here
        import account.signals 

