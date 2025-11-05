# wallet/models.py
from django.db import models
from django.conf import settings
from django.db import models, transaction
from django.db.models import F
from core.helpers.model import BaseModel  

class Wallet(models.Model):
    """
    Represents a central wallet for a user, holding their total savings balance.
    All deposits and withdrawals flow through this wallet.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, # Links to your custom User model
        on_delete=models.CASCADE,
        related_name='wallet', # Access wallet from user: user.wallet
        help_text="The user associated with this wallet."
    )
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="The current balance in the wallet."
    )
    currency = models.CharField(
        max_length=10,
        default='NGN', # Default to Nigerian Naira
        help_text="The currency of the wallet balance."
    )
    account_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique virtual account number for the wallet.",
        null=True
    )
    bank = models.CharField(
        max_length=100,
        default='',
        help_text="The bank where the virtual account is held.",
        null=True
    )
    bank_code = models.CharField(
        max_length=20,
        default='001',
        help_text="The bank code where the virtual account is held.",
        null=True
    )
    account_name = models.CharField(
        max_length=200,
        help_text="The name on the bank account.",
        null=True
    )
    embedly_wallet_id = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="The Embedly wallet ID associated with this wallet."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Wallet"
        verbose_name_plural = "User Wallets"
        ordering = ['user__email'] # Order by user email for display

    def __str__(self):
        return f"{self.user.email}'s Wallet: {self.currency}{self.balance:,.2f}"

    def deposit(self, amount):
        """Deposits funds into the wallet in a transaction-safe way."""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        
        # Start a database transaction
        with transaction.atomic():
            # Lock the row to prevent other operations on the same wallet
            wallet = Wallet.objects.select_for_update().get(id=self.id)
            
            # Update balance atomically
            wallet.balance = F('balance') + amount
            wallet.save(update_fields=['balance', 'updated_at'])

    def withdraw(self, amount):
        """Withdraws funds from the wallet in a transaction-safe way."""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        
        # Start a database transaction
        with transaction.atomic():
            # Lock the row to prevent other operations on the same wallet
            wallet = Wallet.objects.select_for_update().get(id=self.id)
            
            # Check if sufficient funds are available
            if wallet.balance < amount:
                raise ValueError("Insufficient funds in wallet.")
            
            # Update balance atomically
            wallet.balance = F('balance') - amount
            wallet.save(update_fields=['balance', 'updated_at'])

 

class WithdrawalRequest(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bank_name = models.CharField(max_length=255)
    bank_code = models.CharField(max_length=20, null=True, blank=True)
    account_number = models.CharField(max_length=255)
    bank_account_name = models.CharField(max_length=255, null=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=20, default='pending')
    transaction_ref = models.CharField(max_length=255, null=True, blank=True, help_text="Embedly transaction reference")
    error_message = models.TextField(null=True, blank=True, help_text="Error message if transfer failed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} ({self.status})"
    





class WalletTransaction(BaseModel):
    """
      Record wallet transactions such as deposits and withdrawals.
    """
    TRANSACTION_TYPES = [
        ('debit', 'debit'), # Money moved from Wallet  
        ('credit', 'credit'),     # Money moved from wallet
    ]

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='wallet',
        help_text="The wallet associated with this transaction."
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        help_text="Type of transaction"
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Amount of the transaction for this specific goal."
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Optional description for the goal transaction."
    )
    
    sender_name = models.CharField(
        max_length=255,
        null=True,
        help_text="Name of sender"
    )
    sender_account = models.CharField(
        max_length=255,
        null=True,
        help_text="Account of sender"
    )
    external_reference = models.CharField(
        max_length=255,
        null=True,
        unique=True,
        help_text="Reference from external system"
    )

    class Meta:
        verbose_name = "Wallet Transaction"
        verbose_name_plural = "Wallet Transactions"
        ordering = ['-created_at']

    def __str__(self):
        return (f"Wallet transaction '{self.wallet.account_number}' - {self.get_transaction_type_display()} of "
                f"{self.amount} on {self.created_at.strftime('%Y-%m-%d %H:%M')}")
