# savings/models.py
from django.db import models
from django.conf import settings 



class SavingsGoalModel(models.Model):
    """
    Represents a savings goal created by a user.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  
        on_delete=models.CASCADE,
        related_name='savings_goals'
    )
    name = models.CharField(max_length=255, help_text="Name of the savings goal (e.g., 'New Car', 'Education Fund')")
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Current amount saved towards the goal"
    )
    target_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Target amount to reach for this goal"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Current status of the savings goal"
    )
    interest_rate = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=10.0,
        help_text="Interest rate on the goal"
    )

    accrued_interest= models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.0,
        help_text="Interest accrued on the goal"
    )

    # Locked savings fields
    is_locked = models.BooleanField(
        default=False,
        help_text="Whether withdrawals are locked until maturity date"
    )
    lock_period_months = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duration of lock period in months (e.g., 3, 6, 12)"
    )
    maturity_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when the locked goal matures and becomes withdrawable"
    )
    early_withdrawal_penalty_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Penalty percentage for early withdrawal (e.g., 5.00 for 5%)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Savings Goal"
        verbose_name_plural = "Savings Goals"
        ordering = ['-created_at'] # Order by newest first

    def __str__(self):
        return f"{self.user.email}'s {self.name} ({self.status})"

    def is_currently_locked(self):
        """
        Check if the goal is currently locked (before maturity date).
        Returns True if locked and maturity date hasn't been reached.
        """
        if not self.is_locked:
            return False

        if self.maturity_date is None:
            return False

        from django.utils import timezone
        return timezone.now() < self.maturity_date

    def calculate_early_withdrawal_penalty(self, amount):
        """
        Calculate the penalty amount for early withdrawal.
        Returns the penalty amount to be deducted.
        """
        if self.early_withdrawal_penalty_percent <= 0:
            return 0

        from decimal import Decimal
        penalty = (amount * self.early_withdrawal_penalty_percent) / Decimal('100')
        return penalty

    def days_until_maturity(self):
        """
        Calculate days remaining until maturity.
        Returns None if not locked or no maturity date set.
        """
        if not self.is_locked or self.maturity_date is None:
            return None

        from django.utils import timezone
        delta = self.maturity_date - timezone.now()
        return max(0, delta.days)
    



class SavingsGoalTransaction(models.Model):
    """
    Records contributions to and withdrawals from a specific savings goal.
    Note: The actual money movement still involves the central Wallet.
    This model tracks allocation/deallocation to/from the specific goal.
    """
    TRANSACTION_TYPES = [
        ('contribution', 'Contribution'), # Money moved from Wallet to this goal
        ('withdrawal', 'Withdrawal'),     # Money moved from this goal back to Wallet
    ]

    goal = models.ForeignKey(
        SavingsGoalModel,
        on_delete=models.CASCADE,
        related_name='transactions',
        help_text="The savings goal involved in this transaction."
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        help_text="Type of transaction (e.g., contribution to goal, withdrawal from goal)."
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
    # The 'balance' here refers to the goal's amount *after* this transaction
    goal_current_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Amount saved in the goal after this transaction occurred."
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Savings Goal Transaction"
        verbose_name_plural = "Savings Goal Transactions"
        ordering = ['-timestamp']

    def __str__(self):
        return (f"Goal '{self.goal.name}' - {self.get_transaction_type_display()} of "
                f"{self.amount} on {self.timestamp.strftime('%Y-%m-%d %H:%M')}")
