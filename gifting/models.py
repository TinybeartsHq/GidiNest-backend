# gifting/models.py
"""
Models for the GidiNest gifting flow.

BabyFund: A mother creates a fund to receive gifts from family/friends.
Gift: An individual contribution to a baby fund via Paystack.
"""
import secrets
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models, transaction
from django.db.models import Sum, F
from core.helpers.model import BaseModel


class BabyFund(BaseModel):
    """
    A baby fund that a mother creates to receive monetary gifts.
    Shareable via gidinest.com/fund/{token}.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
    ]

    PRIVACY_CHOICES = [
        ('public', 'Public - Show name and amount'),
        ('private', 'Private - Show only name'),
        ('anonymous', 'Anonymous - Hide all contributor details'),
    ]

    # Owner
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='baby_funds',
    )

    # Fund identity
    token = models.CharField(max_length=64, unique=True, editable=False, db_index=True)
    name = models.CharField(max_length=255, help_text="e.g. 'Baby Ade's Arrival Fund'")
    description = models.TextField(blank=True, default='')

    # Optional targeting
    target_amount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        help_text="Optional fundraising target",
    )
    due_date = models.DateField(
        null=True, blank=True,
        help_text="Expected due date / event date",
    )

    # Balance — internal ledger (not a virtual bank account)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    # Messaging
    thank_you_message = models.TextField(
        default='Thank you for your generous gift!',
        help_text="Shown to contributor after successful payment",
    )

    # Privacy
    show_contributors = models.CharField(
        max_length=20, choices=PRIVACY_CHOICES, default='public',
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.user.first_name})"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def credit(self, amount):
        """Atomically credit the fund balance."""
        amount = Decimal(str(amount))
        with transaction.atomic():
            BabyFund.objects.filter(pk=self.pk).select_for_update().update(
                balance=F('balance') + amount
            )
            self.refresh_from_db(fields=['balance'])

    def debit(self, amount):
        """Atomically debit the fund balance. Raises ValueError if insufficient."""
        amount = Decimal(str(amount))
        with transaction.atomic():
            updated = BabyFund.objects.filter(
                pk=self.pk, balance__gte=amount
            ).select_for_update().update(
                balance=F('balance') - amount
            )
            if not updated:
                raise ValueError("Insufficient fund balance")
            self.refresh_from_db(fields=['balance'])

    def get_total_gifts(self):
        """Total gross amount of completed gifts."""
        return self.gifts.filter(
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    def get_gift_count(self):
        """Number of completed gifts."""
        return self.gifts.filter(status='completed').count()

    def is_target_reached(self):
        if not self.target_amount:
            return False
        return self.get_total_gifts() >= self.target_amount


class Gift(BaseModel):
    """
    An individual gift (contribution) to a baby fund.
    Paid via Paystack — no manual bank transfers.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),       # Paystack transaction initialized
        ('completed', 'Completed'),   # Webhook confirmed payment
        ('failed', 'Failed'),         # Payment failed or expired
    ]

    # Link to fund
    baby_fund = models.ForeignKey(
        BabyFund,
        on_delete=models.CASCADE,
        related_name='gifts',
    )

    # Payment
    amount = models.DecimalField(max_digits=15, decimal_places=2, help_text="Gross gift amount")
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    net_amount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        help_text="Amount credited to mother after 1.5% fee",
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Paystack references
    paystack_reference = models.CharField(max_length=255, unique=True, db_index=True)
    paystack_access_code = models.CharField(max_length=255, blank=True, default='')

    # Contributor info (no login required)
    contributor_name = models.CharField(max_length=255)
    contributor_email = models.EmailField(
        blank=True, default='',
        help_text="Optional — used for Paystack + receipt email",
    )
    contributor_phone = models.CharField(max_length=20, blank=True, default='')
    message = models.TextField(blank=True, default='', help_text="Personal message to the mother")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['baby_fund', 'status']),
            models.Index(fields=['paystack_reference']),
        ]

    def __str__(self):
        return f"{self.contributor_name} — NGN {self.amount} to {self.baby_fund.name}"
