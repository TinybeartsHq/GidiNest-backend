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
            print(f"Wallet created for {instance.email}")
        except Exception as e:
            print(f"Failed to create wallet for {instance.email}: {e}")
            
 
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
                print(f"Successfully created Embedly customer for user {instance.email}: {embedly_customer_id}")
            else:
                print(f"Failed to create Embedly customer for user {instance.email}: {response.get('message')}")
        except Exception as e:
            print(f"An error occurred while creating Embedly customer: {e}")