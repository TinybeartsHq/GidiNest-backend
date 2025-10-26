from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import SavingsGoalModel


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_default_savings_goal(sender, instance, created, **kwargs):
    """
    Signal receiver to create a default savings goal for a new user.
    """
    if created:
        templates = settings.SAVINGS_TEMPLATES
        for template in templates:
            if not SavingsGoalModel.objects.filter(user=instance, name=template).exists():
                SavingsGoalModel.objects.create(
                    user=instance,
                    name=template,
                    target_amount=100000.00, 
                    amount=0.00,   
                    status='active'
                )
                print(f"Created default savings goal for new user: {instance.email}")