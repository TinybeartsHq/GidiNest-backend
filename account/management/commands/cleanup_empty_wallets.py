"""
Django management command to clean up empty wallet records.

This removes Wallet objects that were created by the old signal but never populated
with account numbers. These users can get proper wallets when they verify BVN/NIN.

Usage:
    python manage.py cleanup_empty_wallets                    # Clean all empty wallets
    python manage.py cleanup_empty_wallets --dry-run          # Preview without deleting
"""
from django.core.management.base import BaseCommand
from wallet.models import Wallet
from django.db.models import Q


class Command(BaseCommand):
    help = 'Remove empty wallet records (no account number) for unverified users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting empty wallet cleanup...'))

        # Find empty wallets (no account number and user not verified)
        empty_wallets = Wallet.objects.filter(
            Q(account_number='') | Q(account_number__isnull=True)
        ).filter(
            user__has_virtual_wallet=False
        )

        total = empty_wallets.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('✓ No empty wallets found. Database is clean!'))
            return

        self.stdout.write(f'Found {total} empty wallet records to clean up:\n')

        # Show details
        for wallet in empty_wallets[:10]:
            user = wallet.user
            self.stdout.write(
                f'  - {user.email}: '
                f'BVN={user.has_bvn}, NIN={user.has_nin}, '
                f'has_virtual_wallet={user.has_virtual_wallet}'
            )

        if total > 10:
            self.stdout.write(f'  ... and {total - 10} more')

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\n*** DRY RUN - No wallets were deleted ***'))
            self.stdout.write(f'Would delete {total} empty wallet records')
        else:
            # Delete the empty wallets
            deleted_count, _ = empty_wallets.delete()
            self.stdout.write(self.style.SUCCESS(f'\n✓ Deleted {deleted_count} empty wallet records'))
            self.stdout.write(
                '\nThese users will get proper wallets when they verify BVN or NIN.'
            )
