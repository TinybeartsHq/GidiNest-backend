"""
Django management command to check recent webhook errors and transactions.

Usage:
    python manage.py check_webhook_errors
    python manage.py check_webhook_errors --hours 24
    python manage.py check_webhook_errors --user-email user@example.com
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
from wallet.models import WalletTransaction, Wallet
from account.models.users import UserModel


class Command(BaseCommand):
    help = 'Check recent webhook errors and transaction status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Number of hours to look back (default: 24)',
        )
        parser.add_argument(
            '--user-email',
            type=str,
            help='Filter by user email',
        )
        parser.add_argument(
            '--account-number',
            type=str,
            help='Filter by account number',
        )

    def handle(self, *args, **options):
        hours = options['hours']
        user_email = options.get('user_email')
        account_number = options.get('account_number')

        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('WEBHOOK TRANSACTION CHECK'))
        self.stdout.write(self.style.SUCCESS('='*70))

        # Calculate time range
        since = timezone.now() - timedelta(hours=hours)
        self.stdout.write(f'\nChecking transactions since: {since.strftime("%Y-%m-%d %H:%M:%S")}')

        # Build query
        transactions = WalletTransaction.objects.filter(created_at__gte=since)

        if user_email:
            try:
                user = UserModel.objects.get(email=user_email)
                wallet = user.wallet
                transactions = transactions.filter(wallet=wallet)
                self.stdout.write(f'\nFiltering for user: {user_email}')
            except UserModel.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User {user_email} not found'))
                return

        if account_number:
            try:
                wallet = Wallet.objects.get(account_number=account_number)
                transactions = transactions.filter(wallet=wallet)
                self.stdout.write(f'\nFiltering for account: {account_number}')
            except Wallet.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Wallet with account {account_number} not found'))
                return

        # Get credit transactions (deposits)
        credit_txns = transactions.filter(transaction_type='credit').order_by('-created_at')
        debit_txns = transactions.filter(transaction_type='debit').order_by('-created_at')

        self.stdout.write('\n' + '-'*70)
        self.stdout.write(self.style.SUCCESS(f'CREDIT TRANSACTIONS (Deposits): {credit_txns.count()}'))
        self.stdout.write('-'*70)

        if credit_txns.exists():
            for txn in credit_txns[:20]:  # Show last 20
                wallet = txn.wallet
                self.stdout.write(
                    f"\n[{txn.created_at.strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"User: {wallet.user.email} | "
                    f"Account: {wallet.account_number} | "
                    f"Amount: {wallet.currency} {txn.amount} | "
                    f"Ref: {txn.external_reference or 'N/A'} | "
                    f"Sender: {txn.sender_name or 'N/A'}"
                )
                self.stdout.write(f"  Description: {txn.description}")
        else:
            self.stdout.write(self.style.WARNING('  No credit transactions found'))

        self.stdout.write('\n' + '-'*70)
        self.stdout.write(self.style.SUCCESS(f'DEBIT TRANSACTIONS (Withdrawals): {debit_txns.count()}'))
        self.stdout.write('-'*70)

        if debit_txns.exists():
            for txn in debit_txns[:10]:  # Show last 10
                wallet = txn.wallet
                self.stdout.write(
                    f"\n[{txn.created_at.strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"User: {wallet.user.email} | "
                    f"Amount: {wallet.currency} {txn.amount} | "
                    f"Ref: {txn.external_reference or 'N/A'}"
                )
                self.stdout.write(f"  Description: {txn.description}")
        else:
            self.stdout.write(self.style.WARNING('  No debit transactions found'))

        # Check for potential issues
        self.stdout.write('\n' + '-'*70)
        self.stdout.write(self.style.SUCCESS('POTENTIAL ISSUES'))
        self.stdout.write('-'*70)

        # Check for transactions without external reference (might indicate webhook issues)
        missing_ref = credit_txns.filter(external_reference__isnull=True)
        if missing_ref.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  Found {missing_ref.count()} credit transactions without external_reference'
                )
            )

        # Check for duplicate external references
        from django.db.models import Count
        duplicates = (
            credit_txns.values('external_reference')
            .annotate(count=Count('external_reference'))
            .filter(count__gt=1, external_reference__isnull=False)
        )
        if duplicates.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  Found duplicate external_references: {duplicates.count()}'
                )
            )
            for dup in duplicates[:5]:
                self.stdout.write(f"  Ref: {dup['external_reference']} appears {dup['count']} times")

        # Check wallet balances
        if user_email or account_number:
            self.stdout.write('\n' + '-'*70)
            self.stdout.write(self.style.SUCCESS('WALLET BALANCE'))
            self.stdout.write('-'*70)
            try:
                if account_number:
                    wallet = Wallet.objects.get(account_number=account_number)
                else:
                    user = UserModel.objects.get(email=user_email)
                    wallet = user.wallet

                self.stdout.write(
                    f"\nUser: {wallet.user.email}"
                )
                self.stdout.write(
                    f"Account: {wallet.account_number}"
                )
                self.stdout.write(
                    f"Balance: {wallet.currency} {wallet.balance:,.2f}"
                )
                self.stdout.write(
                    f"Last Updated: {wallet.updated_at.strftime('%Y-%m-%d %H:%M:%S')}"
                )

                # Calculate expected balance from transactions
                total_credits = credit_txns.filter(wallet=wallet).aggregate(
                    total=Sum('amount')
                )['total'] or 0
                total_debits = debit_txns.filter(wallet=wallet).aggregate(
                    total=Sum('amount')
                )['total'] or 0

                self.stdout.write(
                    f"\nTransactions Summary (last {hours}h):"
                )
                self.stdout.write(f"  Total Credits: {wallet.currency} {total_credits:,.2f}")
                self.stdout.write(f"  Total Debits: {wallet.currency} {total_debits:,.2f}")
                self.stdout.write(f"  Net: {wallet.currency} {total_credits - total_debits:,.2f}")

            except (UserModel.DoesNotExist, Wallet.DoesNotExist) as e:
                self.stdout.write(self.style.ERROR(f'  Error: {str(e)}'))

        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('Check complete!'))
        self.stdout.write('='*70 + '\n')

