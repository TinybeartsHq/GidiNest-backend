"""
Find users who are verified but don't have wallets.
These are users affected by the wallet creation bug.

Usage:
    python manage.py find_affected_users
"""
from django.core.management.base import BaseCommand
from django.db.models import Q
from account.models.users import UserModel


class Command(BaseCommand):
    help = 'Find verified users who do not have wallets (affected by bug)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('FINDING AFFECTED USERS'))
        self.stdout.write(self.style.SUCCESS('='*60))

        # Users verified but no wallet
        affected = UserModel.objects.filter(
            has_virtual_wallet=False
        ).filter(
            Q(has_bvn=True) | Q(has_nin=True)
        ).exclude(
            embedly_customer_id=""
        ).exclude(
            embedly_customer_id__isnull=True
        )

        count = affected.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('\n✓ No affected users found!'))
            self.stdout.write('All verified users have wallets.')
            return

        self.stdout.write(f'\n⚠️  Found {count} verified users without wallets:\n')

        for user in affected:
            self.stdout.write(
                self.style.WARNING(
                    f"  - {user.email}: "
                    f"BVN={user.has_bvn}, "
                    f"NIN={user.has_nin}, "
                    f"Tier={user.account_tier}"
                )
            )

        self.stdout.write('\n' + '='*60)
        self.stdout.write('REMEDIATION')
        self.stdout.write('='*60)
        self.stdout.write('\nTo fix these users, run:')
        self.stdout.write(self.style.SUCCESS('  python manage.py sync_wallet_status'))
        self.stdout.write('\nOr fix individually:')
        self.stdout.write(self.style.SUCCESS('  python manage.py manual_verify_user --email user@example.com --create-wallet'))
        self.stdout.write('')
