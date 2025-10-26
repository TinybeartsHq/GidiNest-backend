from django.apps import AppConfig

class SavingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'savings'

    def ready(self):
        # Import the signals module here
        # This ensures the signals are registered when the app is ready
        import savings.signals  