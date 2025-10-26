# wallet/signals.py
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.conf import settings
# from .models import Wallet

# @receiver(post_save, sender=settings.AUTH_USER_MODEL)
# def create_user_wallet(sender, instance, created, **kwargs):
#     if created:
#         Wallet.objects.create(user=instance)
#         print(f"Wallet created for {instance.email}")

# @receiver(post_save, sender=settings.AUTH_USER_MODEL)
# def save_user_wallet(sender, instance, **kwargs):
#     try:
#         instance.wallet.save()
#     except Wallet.DoesNotExist:
#         # This handles cases where the user might already exist but no wallet was created
#         # e.g., if signals were not yet configured or an old user.
#         # In such a case, you might want to create it here too.
#         Wallet.objects.create(user=instance)
#         print(f"Wallet created (on save) for {instance.email}")