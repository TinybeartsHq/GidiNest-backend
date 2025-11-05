#!/usr/bin/env python
"""
Sync wallet transaction history from Embedly API.
Useful for finding missing transactions that didn't come through webhook.

Usage:
    python manage.py sync_wallet_history --email user@example.com  # Sync specific user
    python manage.py sync_wallet_history --days 7                   # Sync all users (last 7 days)
    python manage.py sync_wallet_history --email user@example.com --days 30  # Specific user, 30 days
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from wallet.models import Wallet, WalletTransaction
from providers.helpers.embedly import EmbedlyClient

User = get_user_model()

import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync wallet transaction history from Embedly'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email of specific user to sync'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to look back (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be synced without making changes'
        )

    def handle(self, *args, **options):
        email = options.get('email')
        days = options['days']
        dry_run = options['dry_run']

        self.stdout.write('=' * 70)
        self.stdout.write('Syncing Wallet History from Embedly')
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        self.stdout.write(f'Time range: Last {days} day(s)')
        self.stdout.write('=' * 70)

        # Calculate date range
        to_date = timezone.now()
        from_date = to_date - timedelta(days=days)

        # Format dates for Embedly (ISO 8601)
        from_date_str = from_date.isoformat()
        to_date_str = to_date.isoformat()

        # Get wallets to sync
        if email:
            try:
                user = User.objects.get(email=email)
                wallets = [user.wallet]
                self.stdout.write(f'Syncing wallet for: {email}\n')
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User not found: {email}'))
                return
            except Wallet.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User has no wallet: {email}'))
                return
        else:
            wallets = Wallet.objects.filter(embedly_wallet_id__isnull=False)
            self.stdout.write(f'Syncing {wallets.count()} wallet(s)\n')

        embedly_client = EmbedlyClient()
        total_synced = 0
        total_new = 0
        total_errors = 0

        for wallet in wallets:
            if not wallet.embedly_wallet_id:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Skipping {wallet.user.email}: No embedly_wallet_id')
                )
                continue

            self.stdout.write(f'\nSyncing {wallet.user.email}...')

            try:
                # Fetch history from Embedly
                result = embedly_client.get_wallet_history(
                    wallet_id=wallet.embedly_wallet_id,
                    from_date=from_date_str,
                    to_date=to_date_str,
                    page=1,
                    page_size=100
                )

                if not result.get("success"):
                    self.stdout.write(
                        self.style.ERROR(f'  ❌ API Error: {result.get("message")}')
                    )
                    total_errors += 1
                    continue

                # Extract transactions
                data = result.get("data", {})
                transactions = data.get("transactions", [])

                if not transactions:
                    self.stdout.write(f'  ℹ️  No transactions found')
                    continue

                self.stdout.write(f'  Found {len(transactions)} transaction(s) from Embedly')

                new_count = 0
                for txn in transactions:
                    reference = txn.get('reference') or txn.get('transactionReference')

                    if not reference:
                        continue

                    # Check if transaction already exists
                    exists = WalletTransaction.objects.filter(
                        external_reference=reference
                    ).exists()

                    if exists:
                        continue

                    # Determine transaction type and amount
                    txn_type = txn.get('transactionType', '').lower()
                    amount = Decimal(str(txn.get('amount', 0)))
                    description = txn.get('narration') or txn.get('description', '')

                    # Map Embedly transaction type to our types
                    if 'credit' in txn_type or 'deposit' in txn_type:
                        our_txn_type = 'credit'
                    elif 'debit' in txn_type or 'withdrawal' in txn_type:
                        our_txn_type = 'debit'
                    else:
                        # Skip unknown transaction types
                        continue

                    if dry_run:
                        self.stdout.write(
                            f'    [DRY RUN] Would create: {our_txn_type} NGN {amount} - {description[:50]}'
                        )
                        new_count += 1
                    else:
                        # Create transaction
                        try:
                            WalletTransaction.objects.create(
                                wallet=wallet,
                                transaction_type=our_txn_type,
                                amount=amount,
                                description=description,
                                external_reference=reference
                            )
                            new_count += 1
                            self.stdout.write(
                                f'    ✅ Created: {our_txn_type} NGN {amount}'
                            )
                        except Exception as create_error:
                            self.stdout.write(
                                self.style.ERROR(f'    ❌ Failed to create transaction: {create_error}')
                            )

                if new_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ Synced {new_count} new transaction(s)')
                    )
                    total_new += new_count
                else:
                    self.stdout.write(f'  ℹ️  All transactions already synced')

                total_synced += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Error: {str(e)}')
                )
                logger.error(f"Error syncing wallet history for {wallet.user.email}: {str(e)}", exc_info=True)
                total_errors += 1

        # Summary
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('Summary:'))
        self.stdout.write(f'  Wallets synced: {total_synced}')
        self.stdout.write(f'  New transactions: {total_new}')
        self.stdout.write(f'  Errors: {total_errors}')
        if dry_run:
            self.stdout.write(self.style.WARNING('  (DRY RUN - No actual changes made)'))
        self.stdout.write('=' * 70)
