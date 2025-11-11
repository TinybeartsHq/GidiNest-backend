from django.db import models
from django.contrib.auth import get_user_model
from core.helpers.model import BaseModel

User = get_user_model()


class UserBankAccount(BaseModel):
    """
    Store user's saved bank accounts for quick withdrawals
    """

    class Meta:
        db_table = 'user_bank_accounts'
        verbose_name = "User Bank Account"
        verbose_name_plural = "User Bank Accounts"
        ordering = ['-is_default', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_default']),
            models.Index(fields=['account_number', 'bank_code']),
        ]
        unique_together = [['user', 'account_number', 'bank_code']]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bank_accounts',
        help_text="User who owns this bank account"
    )

    bank_name = models.CharField(
        max_length=100,
        help_text="Name of the bank (e.g., 'Access Bank')"
    )

    bank_code = models.CharField(
        max_length=10,
        help_text="Bank code for Nigeria (e.g., '044')"
    )

    account_number = models.CharField(
        max_length=20,
        help_text="Bank account number"
    )

    account_name = models.CharField(
        max_length=255,
        help_text="Account holder name (verified via bank)"
    )

    is_verified = models.BooleanField(
        default=False,
        help_text="Whether account has been verified via Embedly"
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When account was verified"
    )

    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the default account for withdrawals"
    )

    def __str__(self):
        return f"{self.user.email} - {self.bank_name} {self.account_number}"

    def save(self, *args, **kwargs):
        """
        Ensure only one default account per user
        """
        if self.is_default:
            # Set all other accounts for this user as non-default
            UserBankAccount.objects.filter(user=self.user, is_default=True).update(is_default=False)

        super().save(*args, **kwargs)

    def set_as_default(self):
        """Set this account as the default"""
        UserBankAccount.objects.filter(user=self.user, is_default=True).update(is_default=False)
        self.is_default = True
        self.save(update_fields=['is_default'])

    def mark_verified(self):
        """Mark account as verified"""
        from django.utils import timezone
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save(update_fields=['is_verified', 'verified_at'])
