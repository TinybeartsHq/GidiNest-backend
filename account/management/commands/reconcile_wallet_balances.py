"""
Reconcile wallet balances from Embedly.

This fixes issues where deposits weren't recorded due to webhook misconfiguration.
Fetches actual balance from Embedly and updates local database.

Usage:
    python manage.py reconcile_wallet_balances
    python manage.py reconcile_wallet_balances --dry-run
    python manage.py reconcile_wallet_balances --emails user1@example.com user2@example.com
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from account.models.users import UserModel
from wallet.models import Wallet, WalletTransaction
from providers.helpers.embedly import EmbedlyClient
from decimal import Decimal
from datetime import datetime


class Command(BaseCommand):
    help = 'Reconcile wallet balances by fetching actual balances from Embedly'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--emails',
            nargs='+',
            help='Reconcile specific users by email addresses',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('WALLET BALANCE RECONCILIATION'))
        self.stdout.write(self.style.SUCCESS('='*70))

        embedly_client = EmbedlyClient()

        # Get users with wallets
        if options['emails']:
            users = UserModel.objects.filter(email__in=options['emails'])
        else:
            users = UserModel.objects.filter(
                has_virtual_wallet=True
            ).exclude(
                embedly_wallet_id=""
            ).exclude(
                embedly_wallet_id__isnull=True
            )

        total_users = users.count()
        self.stdout.write(f'\nProcessing {total_users} users with wallets...\n')

        results = {
            'processed': 0,
            'updated': 0,
            'no_change': 0,
            'errors': 0,
            'total_difference': Decimal('0.00'),
        }

        for user in users:
            results['processed'] += 1

            try:
                wallet = user.wallet
            except Wallet.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"✗ {user.email}: No wallet found in database")
                )
                results['errors'] += 1
                continue

            # Get actual balance from Embedly
            self.stdout.write(f"\n📊 Processing: {user.email}")
            self.stdout.write(f"   Local Balance: {wallet.currency} {wallet.balance}")
            self.stdout.write(f"   Account: {wallet.account_number} ({wallet.bank})")

            # Fetch wallet info from Embedly
            try:
                wallet_info = embedly_client.get_wallet_info(wallet.account_number)

                if not wallet_info.get("success"):
                    self.stdout.write(
                        self.style.ERROR(f"   ✗ Failed to fetch from Embedly: {wallet_info.get('message')}")
                    )
                    results['errors'] += 1
                    continue

                embedly_data = wallet_info.get("data", {})
                embedly_balance = Decimal(str(embedly_data.get("availableBalance", 0)))

                self.stdout.write(f"   Embedly Balance: {wallet.currency} {embedly_balance}")

                # Calculate difference
                difference = embedly_balance - Decimal(str(wallet.balance))

                if difference == 0:
                    self.stdout.write(self.style.SUCCESS("   ✓ Balances match - no action needed"))
                    results['no_change'] += 1
                    continue

                self.stdout.write(
                    self.style.WARNING(f"   ⚠️  MISMATCH: Difference of {wallet.currency} {difference}")
                )

                if options['dry_run']:
                    self.stdout.write(
                        self.style.WARNING(f"   [DRY RUN] Would update balance to {embedly_balance}")
                    )
                    results['updated'] += 1
                    results['total_difference'] += difference
                    continue

                # Update balance
                with transaction.atomic():
                    # Create reconciliation transaction
                    if difference > 0:
                        # Missed deposits
                        txn = WalletTransaction.objects.create(
                            wallet=wallet,
                            transaction_type='credit',
                            amount=difference,
                            description=f"Reconciliation: Missed deposits (webhook misconfiguration)",
                            sender_name="System Reconciliation",
                            external_reference=f"RECON_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user.id}"
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"   ✓ Created credit transaction: {wallet.currency} {difference}"
                            )
                        )
                    else:
                        # Over-credited (rare)
                        txn = WalletTransaction.objects.create(
                            wallet=wallet,
                            transaction_type='debit',
                            amount=abs(difference),
                            description=f"Reconciliation: Balance correction",
                            sender_name="System Reconciliation",
                            external_reference=f"RECON_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user.id}"
                        )
                        self.stdout.write(
                            self.style.WARNING(
                                f"   ⚠️  Created debit transaction: {wallet.currency} {abs(difference)}"
                            )
                        )

                    # Update wallet balance directly
                    old_balance = wallet.balance
                    wallet.balance = embedly_balance
                    wallet.save(update_fields=['balance', 'updated_at'])

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"   ✓ Updated: {wallet.currency} {old_balance} → {wallet.currency} {embedly_balance}"
                        )
                    )

                results['updated'] += 1
                results['total_difference'] += difference

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"   ✗ Error processing {user.email}: {str(e)}")
                )
                results['errors'] += 1
                import traceback
                self.stdout.write(traceback.format_exc())

        # Summary
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('RECONCILIATION SUMMARY'))
        self.stdout.write('='*70)
        self.stdout.write(f"Total users processed: {results['processed']}")
        self.stdout.write(self.style.SUCCESS(f"Balances updated: {results['updated']}"))
        self.stdout.write(f"No changes needed: {results['no_change']}")
        self.stdout.write(self.style.ERROR(f"Errors: {results['errors']}"))
        self.stdout.write(f"\nTotal amount reconciled: NGN {results['total_difference']}")

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\n*** DRY RUN - No changes were made ***'))
            self.stdout.write('Run without --dry-run to apply changes')

        self.stdout.write('')
