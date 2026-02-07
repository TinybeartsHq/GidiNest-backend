# wallet/models.py
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.db import models, transaction
from django.db.models import F
from core.helpers.model import BaseModel
import uuid
import secrets

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

    # V2 Fields - 9PSB (9 Payment Service Bank) Integration
    provider_version = models.CharField(
        max_length=10,
        default='v1',
        choices=[('v1', 'V1 - Embedly'), ('v2', 'V2 - 9PSB')],
        help_text="Which wallet provider is being used for this wallet."
    )
    psb9_customer_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="9PSB customer ID (for V2 wallets)"
    )
    psb9_account_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        unique=True,
        help_text="9PSB account number (for V2 wallets)"
    )
    psb9_wallet_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="9PSB wallet ID (for V2 wallets)"
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

            # Refresh the instance to get the actual balance value
            # (after F() expression, the balance field contains an expression object, not a number)
            wallet.refresh_from_db()

            # Update self to reflect the new balance
            self.balance = wallet.balance

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

            # Refresh the instance to get the actual balance value
            # (after F() expression, the balance field contains an expression object, not a number)
            wallet.refresh_from_db()

            # Update self to reflect the new balance
            self.balance = wallet.balance

 

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
    transaction_ref = models.CharField(max_length=255, null=True, blank=True, unique=True, help_text="Embedly transaction reference")
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

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    reference = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="Internal transaction reference (e.g., DEB_, CRD_, TRF_ prefixed IDs)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed',
        help_text="Transaction status"
    )

    # Fee tracking fields
    fee_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text="Transfer/processing fee charged"
    )
    vat_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text="VAT charged (on fee/commission, not on principal)"
    )
    emtl_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text="EMTL/Stamp Duty charged"
    )
    commission_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text="Commission charged (for payment link transactions)"
    )
    total_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text="Total fees deducted (fee + vat + emtl + commission)"
    )
    net_amount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        help_text="Amount after fee deductions (what recipient actually receives)"
    )
    fee_config = models.ForeignKey(
        'FeeConfiguration',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="Fee configuration active when this transaction was processed"
    )

    class Meta:
        verbose_name = "Wallet Transaction"
        verbose_name_plural = "Wallet Transactions"
        ordering = ['-created_at']

    def __str__(self):
        return (f"Wallet transaction '{self.wallet.account_number}' - {self.get_transaction_type_display()} of "
                f"{self.amount} on {self.created_at.strftime('%Y-%m-%d %H:%M')}")


class PaymentLink(BaseModel):
    """
    Payment link for receiving contributions to wallet, savings goals, or events.
    Supports multiple use cases: general wallet funding, goal contributions, event funding.
    """
    LINK_TYPE_CHOICES = [
        ('wallet', 'Wallet Funding'),
        ('savings_goal', 'Savings Goal Contribution'),
        ('event', 'Event Funding'),
    ]

    PRIVACY_CHOICES = [
        ('public', 'Public - Show name and amount'),
        ('private', 'Private - Show only name'),
        ('anonymous', 'Anonymous - Hide all contributor details'),
    ]

    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payment_links',
        help_text="The user who owns this payment link"
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        help_text="Unique token for accessing the payment link"
    )

    # Link configuration
    link_type = models.CharField(
        max_length=20,
        choices=LINK_TYPE_CHOICES,
        default='wallet',
        help_text="Type of payment link"
    )

    # Optional savings goal link
    savings_goal = models.ForeignKey(
        'savings.SavingsGoalModel',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='payment_links',
        help_text="Linked savings goal (if link_type is savings_goal)"
    )

    # Event details (for event type links)
    event_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Name of the event (e.g., 'Baby Shower - March 2025')"
    )
    event_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of the event"
    )
    event_description = models.TextField(
        null=True,
        blank=True,
        help_text="Description of the event or purpose"
    )

    # Link settings
    target_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Optional target amount for progress tracking"
    )
    allow_custom_amount = models.BooleanField(
        default=True,
        help_text="Allow contributors to pay any amount"
    )
    fixed_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Fixed amount if allow_custom_amount is False"
    )

    # Privacy settings
    show_contributors = models.CharField(
        max_length=20,
        choices=PRIVACY_CHOICES,
        default='public',
        help_text="Privacy setting for contributor list"
    )

    # Custom messaging
    custom_message = models.TextField(
        null=True,
        blank=True,
        help_text="Thank you message shown after successful payment"
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Description shown on the payment link page"
    )

    # Link status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the link is active and accepting payments"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional expiry date for the link"
    )

    # One-time use option
    one_time_use = models.BooleanField(
        default=False,
        help_text="Deactivate link after first successful payment"
    )
    used = models.BooleanField(
        default=False,
        help_text="Track if one-time link has been used"
    )

    class Meta:
        verbose_name = "Payment Link"
        verbose_name_plural = "Payment Links"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        if self.link_type == 'savings_goal' and self.savings_goal:
            return f"Payment Link for {self.savings_goal.name}"
        elif self.link_type == 'event' and self.event_name:
            return f"Payment Link for {self.event_name}"
        return f"Payment Link - {self.get_link_type_display()}"

    def save(self, *args, **kwargs):
        # Generate unique token on creation
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def get_total_raised(self):
        """Calculate total amount raised through this link"""
        from django.db.models import Sum, Q
        total = self.contributions.filter(
            status='completed'
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0
        return total

    def get_contributor_count(self):
        """Get count of unique contributors"""
        return self.contributions.filter(status='completed').count()

    def is_target_reached(self):
        """Check if target amount has been reached"""
        if not self.target_amount:
            return False
        return self.get_total_raised() >= self.target_amount


class PaymentLinkContribution(BaseModel):
    """
    Tracks individual contributions made through payment links.
    Links payments to payment links and tracks contributor information.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_link = models.ForeignKey(
        PaymentLink,
        on_delete=models.CASCADE,
        related_name='contributions',
        help_text="The payment link this contribution is for"
    )

    # Transaction details
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Amount contributed"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Status of the contribution"
    )

    # Link to wallet transaction
    wallet_transaction = models.ForeignKey(
        WalletTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_link_contributions',
        help_text="Associated wallet transaction"
    )

    # Contributor information (optional - may be anonymous)
    contributor_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Name of the contributor (if provided)"
    )
    contributor_email = models.EmailField(
        null=True,
        blank=True,
        help_text="Email of the contributor (if provided)"
    )
    contributor_phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Phone of the contributor (if provided)"
    )

    # Payment reference
    external_reference = models.CharField(
        max_length=255,
        unique=True,
        help_text="External payment reference from payment provider"
    )

    # Optional message from contributor
    message = models.TextField(
        null=True,
        blank=True,
        help_text="Optional message from contributor"
    )

    # Fee tracking
    commission_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text="Commission deducted from this contribution"
    )
    vat_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text="VAT on commission"
    )
    total_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text="Total fees deducted (commission + VAT)"
    )
    net_amount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        help_text="Net amount credited to link owner after fees"
    )

    class Meta:
        verbose_name = "Payment Link Contribution"
        verbose_name_plural = "Payment Link Contributions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_link', 'status']),
            models.Index(fields=['external_reference']),
        ]

    def __str__(self):
        contributor = self.contributor_name or "Anonymous"
        return f"{contributor} - {self.amount} to {self.payment_link}"


class FeeConfiguration(BaseModel):
    """
    Admin-editable fee configuration for all wallet transactions.
    Only one configuration should be active at a time (is_active=True).
    Creating a new active config automatically deactivates the old one.
    """
    # Transfer fee tiers
    transfer_fee_tier1_max = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('5000.00'),
        help_text="Upper bound for Tier 1. Amounts <= this get tier1 fee."
    )
    transfer_fee_tier1_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('10.00'),
        help_text="Fee for amounts <= tier1_max (e.g., ₦10)"
    )
    transfer_fee_tier2_max = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('50000.00'),
        help_text="Upper bound for Tier 2. Amounts <= this get tier2 fee."
    )
    transfer_fee_tier2_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('25.00'),
        help_text="Fee for tier1_max < amount <= tier2_max (e.g., ₦25)"
    )
    transfer_fee_tier3_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('50.00'),
        help_text="Fee for amounts > tier2_max (e.g., ₦50)"
    )

    # VAT
    vat_rate = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.0750'),
        help_text="VAT rate as decimal (0.075 = 7.5%). Applied to fee/commission, NOT principal."
    )

    # EMTL / Stamp Duty
    emtl_threshold = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('10000.00'),
        help_text="Minimum transaction amount to trigger EMTL/Stamp Duty"
    )
    emtl_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('50.00'),
        help_text="Fixed EMTL/Stamp Duty charge (e.g., ₦50)"
    )

    # Payment Link commission
    payment_link_commission_rate = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.0500'),
        help_text="Payment link commission rate as decimal (0.05 = 5%)"
    )

    # Activation
    is_active = models.BooleanField(
        default=True,
        help_text="Only one configuration should be active at a time."
    )
    name = models.CharField(
        max_length=100, default='Default',
        help_text="Human-readable name for this config"
    )
    notes = models.TextField(
        blank=True, null=True,
        help_text="Admin notes about why this config was created/changed"
    )

    class Meta:
        verbose_name = "Fee Configuration"
        verbose_name_plural = "Fee Configurations"
        ordering = ['-created_at']

    def __str__(self):
        active_str = " [ACTIVE]" if self.is_active else ""
        return f"{self.name}{active_str}"

    def save(self, *args, **kwargs):
        if self.is_active:
            FeeConfiguration.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_active(cls):
        """Return the currently active fee configuration, creating defaults if none exists."""
        config = cls.objects.filter(is_active=True).first()
        if config is None:
            config = cls.objects.create(name='System Default', is_active=True)
        return config


class PlatformWallet(BaseModel):
    """
    Singleton wallet that accumulates all platform fee revenue.
    Only one record should exist (enforced by get_instance()).
    """
    WALLET_TYPES = [
        ('fee_revenue', 'Fee Revenue'),
    ]

    wallet_type = models.CharField(
        max_length=20, choices=WALLET_TYPES, default='fee_revenue', unique=True,
        help_text="Type of platform wallet"
    )
    balance = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'),
        help_text="Current accumulated fee revenue"
    )
    total_transfer_fees = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'),
        help_text="Lifetime total of transfer fees collected"
    )
    total_vat = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'),
        help_text="Lifetime total of VAT collected"
    )
    total_emtl = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'),
        help_text="Lifetime total of EMTL/Stamp Duty collected"
    )
    total_commission = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'),
        help_text="Lifetime total of payment link commissions collected"
    )

    class Meta:
        verbose_name = "Platform Wallet"
        verbose_name_plural = "Platform Wallets"

    def __str__(self):
        return f"Platform Wallet: ₦{self.balance:,.2f}"

    def deposit(self, fee_amount=Decimal('0.00'), vat_amount=Decimal('0.00'),
                emtl_amount=Decimal('0.00'), commission_amount=Decimal('0.00')):
        """
        Deposit fee revenue into the platform wallet atomically.
        Tracks each fee component separately for reporting.
        """
        total = fee_amount + vat_amount + emtl_amount + commission_amount
        if total <= 0:
            return

        with transaction.atomic():
            pw = PlatformWallet.objects.select_for_update().get(pk=self.pk)
            pw.balance = F('balance') + total
            pw.total_transfer_fees = F('total_transfer_fees') + fee_amount
            pw.total_vat = F('total_vat') + vat_amount
            pw.total_emtl = F('total_emtl') + emtl_amount
            pw.total_commission = F('total_commission') + commission_amount
            pw.save(update_fields=[
                'balance', 'total_transfer_fees', 'total_vat',
                'total_emtl', 'total_commission', 'updated_at'
            ])
            pw.refresh_from_db()
            self.balance = pw.balance

    @classmethod
    def get_instance(cls):
        """Get or create the singleton platform wallet."""
        pw, _ = cls.objects.get_or_create(wallet_type='fee_revenue')
        return pw
