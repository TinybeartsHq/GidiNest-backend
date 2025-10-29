# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

from wallet.models import Wallet
from .models import UserModel
from providers.helpers.embedly import EmbedlyClient 
 

@receiver(post_save, sender=UserModel)
def create_embedly_customer(sender, instance, created, **kwargs):
    """
    Signal receiver to create an Embedly customer when a new UserModel instance is created.
    """
    if created and not instance.embedly_customer_id:

        try:
            Wallet.objects.create(user=instance)
        except Exception as e:
            pass  # Wallet creation failure is logged in DB
            
 
        client = EmbedlyClient()
        
        customer_data = {
            "firstName": instance.first_name,
            "lastName": instance.last_name,
            "emailAddress": instance.email,
            "mobileNumber": instance.phone,
            "dob": instance.dob,
            "address": instance.address,
            "city": instance.state,
            "country": instance.country,
        }

        # Call the Embedly API
        try:
            response = client.create_customer(customer_data)
            if response.get("success"):
                embedly_customer_id = response['data']['id']
                instance.embedly_customer_id = embedly_customer_id
                instance.save(update_fields=['embedly_customer_id'])
        except Exception as e:
            pass  # Errors are logged in ProviderRequestLog