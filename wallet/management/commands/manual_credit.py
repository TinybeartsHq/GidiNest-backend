"""
Django management command to manually credit a wallet
Usage: python manage.py manual_credit <account_number> <amount> <reference>

Use this ONLY when webhooks are failing and you need to manually credit verified deposits.
Always verify the deposit with the user first!
"""
from django.core.management.base import BaseCommand
from wallet.models import Wallet, WalletTransaction
from decimal import Decimal
from django.db import transaction


class Command(BaseCommand):
    help = 'Manually credit a wallet (use only when webhooks fail)'

    def add_arguments(self, parser):
        parser.add_argument('account_number', type=str, help='Wallet account number')
        parser.add_argument('amount', type=str, help='Amount to credit (e.g., 10000.00)')
        parser.add_argument('reference', type=str, help='Unique reference for this credit')
        parser.add_argument('--sender', type=str, default='Bank Transfer', help='Sender name')
        parser.add_argument('--confirm', action='store_true', help='Confirm the credit (required)')

    def handle(self, *args, **options):
        account_number = options['account_number']
        amount_str = options['amount']
        reference = options['reference']
        sender = options['sender']
        confirm = options['confirm']

        # Validate amount
        try:
            amount = Decimal(amount_str)
            if amount <= 0:
                self.stdout.write(self.style.ERROR('Amount must be positive'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Invalid amount: {e}'))
            return

        # Find wallet
        try:
            wallet = Wallet.objects.get(account_number=account_number)
        except Wallet.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Wallet not found for account: {account_number}'))
            return

        # Check for duplicate reference
        if WalletTransaction.objects.filter(external_reference=reference).exists():
            self.stdout.write(self.style.ERROR(f'Reference already exists: {reference}'))
            self.stdout.write('This deposit may have already been credited!')
            return

        # Show details and require confirmation
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('MANUAL CREDIT DETAILS'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'User: {wallet.user.email}')
        self.stdout.write(f'Name: {wallet.user.first_name} {wallet.user.last_name}')
        self.stdout.write(f'Account: {account_number}')
        self.stdout.write(f'Current balance: ₦{wallet.balance}')
        self.stdout.write(f'Amount to credit: ₦{amount}')
        self.stdout.write(f'New balance: ₦{wallet.balance + amount}')
        self.stdout.write(f'Reference: {reference}')
        self.stdout.write(f'Sender: {sender}')
        self.stdout.write('=' * 60)
        self.stdout.write('')

        if not confirm:
            self.stdout.write(self.style.ERROR('⚠ Add --confirm flag to proceed with this credit'))
            self.stdout.write('')
            self.stdout.write('IMPORTANT: Before confirming:')
            self.stdout.write('1. Verify the user actually made this deposit')
            self.stdout.write('2. Check their bank statement or Embedly dashboard')
            self.stdout.write('3. Ensure this is not a duplicate credit')
            self.stdout.write('4. Document this manual credit for reconciliation')
            self.stdout.write('')
            self.stdout.write(f'To confirm: python manage.py manual_credit {account_number} {amount_str} {reference} --confirm')
            return

        # Perform the credit
        try:
            with transaction.atomic():
                # Create transaction record
                wallet_transaction = WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='credit',
                    amount=amount,
                    description=f'Manual credit - Webhook failed - From {sender}',
                    sender_name=sender,
                    external_reference=reference
                )

                # Credit wallet
                wallet.deposit(amount)

                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('✓ CREDIT SUCCESSFUL'))
                self.stdout.write(f'Transaction ID: {wallet_transaction.id}')
                self.stdout.write(f'New balance: ₦{wallet.balance}')
                self.stdout.write('')
                self.stdout.write('Next steps:')
                self.stdout.write('1. Document this manual credit in your records')
                self.stdout.write('2. Notify the user their wallet has been credited')
                self.stdout.write('3. Investigate why the webhook failed')
                self.stdout.write('')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ CREDIT FAILED: {str(e)}'))
            import traceback
            traceback.print_exc()
