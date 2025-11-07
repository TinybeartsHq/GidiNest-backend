"""
Django management command to reconcile missed deposits during webhook downtime.

This command:
1. Fetches transaction history from Embedly for all wallets
2. Compares with local WalletTransaction records
3. Identifies deposits that were received but not credited
4. Optionally processes them

Usage:
    python manage.py reconcile_missed_deposits
    python manage.py reconcile_missed_deposits --dry-run  # Preview only
    python manage.py reconcile_missed_deposits --since 2025-11-01  # Start from date
    python manage.py reconcile_missed_deposits --wallet-account 9710239954  # Specific wallet
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from wallet.models import Wallet, WalletTransaction
from providers.helpers.embedly import EmbedlyClient

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Reconcile missed deposits from Embedly transaction history'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without applying them',
        )
        parser.add_argument(
            '--since',
            type=str,
            help='Start date (YYYY-MM-DD). Defaults to 7 days ago',
        )
        parser.add_argument(
            '--wallet-account',
            type=str,
            help='Process specific wallet account number only',
        )
        parser.add_argument(
            '--auto-process',
            action='store_true',
            help='Automatically process missing deposits (default: show report only)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        since_date = options.get('since')
        wallet_account = options.get('wallet_account')
        auto_process = options['auto_process']

        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('RECONCILIATION: MISSED DEPOSITS'))
        self.stdout.write(self.style.SUCCESS('='*70))

        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  DRY RUN MODE - No changes will be made\n'))

        # Determine start date
        if since_date:
            try:
                start_date = datetime.strptime(since_date, '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(self.style.ERROR(f'Invalid date format: {since_date}. Use YYYY-MM-DD'))
                return
        else:
            # Default to 7 days ago
            start_date = (timezone.now() - timedelta(days=7)).date()

        self.stdout.write(f'\nChecking transactions since: {start_date}\n')

        # Initialize Embedly client
        try:
            embedly_client = EmbedlyClient()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to initialize Embedly client: {e}'))
            return

        # Get wallets to check
        if wallet_account:
            wallets = Wallet.objects.filter(account_number=wallet_account, embedly_wallet_id__isnull=False)
            if not wallets.exists():
                self.stdout.write(self.style.ERROR(f'Wallet not found or missing embedly_wallet_id: {wallet_account}'))
                return
        else:
            wallets = Wallet.objects.filter(embedly_wallet_id__isnull=False)

        total_missed = 0
        total_amount = Decimal('0')
        processed_count = 0
        error_count = 0

        for wallet in wallets:
            if not wallet.embedly_wallet_id:
                self.stdout.write(
                    self.style.WARNING(f'\n⚠️  Skipping {wallet.account_number}: No embedly_wallet_id')
                )
                continue
                
            self.stdout.write(f'\nChecking wallet: {wallet.account_number} ({wallet.user.email})')
            
            try:
                # Fetch transaction history from Embedly
                # Use wallet_id (UUID) instead of account_number
                from_date = start_date.strftime('%Y-%m-%dT00:00:00Z')
                to_date = timezone.now().strftime('%Y-%m-%dT23:59:59Z')
                
                result = embedly_client.get_wallet_history(
                    wallet_id=wallet.embedly_wallet_id,
                    from_date=from_date,
                    to_date=to_date,
                    page=1,
                    page_size=100
                )

                if not result.get('success'):
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️  Failed to fetch transactions: {result.get("message")}')
                    )
                    continue

                # Extract transactions (support both response shapes)
                data = result.get('data', {})
                transactions = data.get('transactions') or data.get('walletHistories') or []
                
                if not transactions:
                    self.stdout.write(f'  ℹ️  No transactions found')
                    continue
                
                self.stdout.write(f'  Found {len(transactions)} transactions from Embedly')

                # Find missing deposits
                missing_deposits = []
                for txn in transactions:
                    # Determine transaction type
                    txn_type = (txn.get('transactionType') or '').lower()
                    if not txn_type:
                        dci = (txn.get('debitCreditIndicator') or '').upper()
                        if dci == 'C':
                            txn_type = 'credit'
                        elif dci == 'D':
                            txn_type = 'debit'
                    
                    # Only process credit transactions (deposits)
                    if txn_type not in ['credit', 'deposit', 'incoming']:
                        continue

                    reference = txn.get('reference') or txn.get('transactionReference') or txn.get('transactionId')
                    amount = txn.get('amount', 0) or txn.get('transactionAmount', 0)
                    
                    if not reference or not amount:
                        continue

                    # Check if we already have this transaction
                    if WalletTransaction.objects.filter(
                        wallet=wallet,
                        external_reference=reference
                    ).exists():
                        continue

                    # This is a missing deposit
                    missing_deposits.append({
                        'reference': reference,
                        'amount': Decimal(str(amount)),
                        'date': txn.get('date') or txn.get('createdAt') or txn.get('transactionDate'),
                        'sender_name': txn.get('senderName') or txn.get('sender_name') or txn.get('senderAccountName', 'Unknown'),
                        'sender_account': txn.get('senderAccount') or txn.get('sender_account') or txn.get('senderAccountNumber', ''),
                        'description': txn.get('description') or txn.get('narration') or f"Deposit via {reference}",
                    })

                if missing_deposits:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️  Found {len(missing_deposits)} missing deposits:')
                    )
                    
                    for deposit in missing_deposits:
                        self.stdout.write(
                            f'    - {deposit["amount"]} NGN | Ref: {deposit["reference"]} | '
                            f'From: {deposit["sender_name"]} | Date: {deposit["date"]}'
                        )
                        total_missed += 1
                        total_amount += deposit['amount']

                        # Process if auto-process is enabled
                        if auto_process and not dry_run:
                            try:
                                with transaction.atomic():
                                    # Create transaction record
                                    wallet_transaction = WalletTransaction.objects.create(
                                        wallet=wallet,
                                        transaction_type='credit',
                                        amount=deposit['amount'],
                                        description=deposit['description'],
                                        sender_name=deposit['sender_name'],
                                        sender_account=deposit['sender_account'],
                                        external_reference=deposit['reference']
                                    )

                                    # Update wallet balance
                                    wallet.deposit(deposit['amount'])

                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f'      ✅ Processed: Credited {deposit["amount"]} NGN'
                                        )
                                    )
                                    processed_count += 1

                                    # Send notification
                                    try:
                                        from core.helpers.messaging import CuoralAPI
                                        from notification.helper.email import MailClient
                                        
                                        cuoral_client = CuoralAPI()
                                        cuoral_client.send_sms(
                                            wallet.user.phone,
                                            f"You just received {wallet.currency} {deposit['amount']} from {deposit['sender_name']}."
                                        )

                                        emailclient = MailClient()
                                        emailclient.send_email(
                                            to_email=wallet.user.email,
                                            subject="Credit Alert - Reconciliation",
                                            template_name="emails/credit.html",
                                            context={
                                                "sender_name": deposit['sender_name'],
                                                "amount": f"{wallet.currency} {deposit['amount']}",
                                            },
                                            to_name=wallet.user.first_name
                                        )
                                    except Exception as notif_error:
                                        logger.error(f"Failed to send notification: {notif_error}")

                            except Exception as e:
                                self.stdout.write(
                                    self.style.ERROR(f'      ❌ Error processing: {e}')
                                )
                                error_count += 1
                                logger.error(f"Failed to process deposit {deposit['reference']}: {e}", exc_info=True)
                else:
                    self.stdout.write(self.style.SUCCESS('  ✅ No missing deposits found'))

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Error processing wallet: {e}')
                )
                error_count += 1
                logger.error(f"Error processing wallet {wallet.account_number}: {e}", exc_info=True)

        # Summary
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('RECONCILIATION SUMMARY'))
        self.stdout.write('='*70)
        self.stdout.write(f'Total missing deposits found: {total_missed}')
        self.stdout.write(f'Total amount: {total_amount} NGN')
        
        if auto_process and not dry_run:
            self.stdout.write(f'\nProcessed: {processed_count}')
            self.stdout.write(f'Errors: {error_count}')
        else:
            self.stdout.write('\n⚠️  No deposits were processed.')
            self.stdout.write('   Use --auto-process to process missing deposits')
            self.stdout.write('   Use --dry-run to preview changes')

        self.stdout.write('='*70 + '\n')

