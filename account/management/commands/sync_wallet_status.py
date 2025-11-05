"""
Alternative sync approach: Query wallet status directly instead of customer details.

Since the GET customer endpoint returns empty, we'll check wallet status directly
using the embedly_wallet_id or try to create wallets for verified users who don't have them.

Usage:
    python manage.py sync_wallet_status
    python manage.py sync_wallet_status --emails user@example.com
"""
from django.core.management.base import BaseCommand
from django.db.models import Q
from account.models.users import UserModel
from wallet.models import Wallet
from providers.helpers.embedly import EmbedlyClient


class Command(BaseCommand):
    help = 'Sync wallet status by checking if verified users have wallets and creating them if missing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--emails',
            nargs='+',
            help='Sync specific users by email addresses',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('WALLET STATUS SYNC'))
        self.stdout.write(self.style.SUCCESS('='*60))

        # Get users who are verified but don't have wallets
        if options['emails']:
            users = UserModel.objects.filter(email__in=options['emails'])
        else:
            users = UserModel.objects.filter(
                Q(has_bvn=True) | Q(has_nin=True)
            ).exclude(
                embedly_customer_id=""
            ).exclude(
                embedly_customer_id__isnull=True
            )

        self.stdout.write(f'\nChecking {users.count()} verified users...\n')

        embedly_client = EmbedlyClient()
        results = {
            'checked': 0,
            'has_wallet': 0,
            'created_wallet': 0,
            'failed': 0,
        }

        for user in users:
            results['checked'] += 1

            # Check if user already has wallet with account number
            try:
                wallet = user.wallet
                if wallet.account_number:
                    results['has_wallet'] += 1
                    self.stdout.write(f"✓ {user.email}: Already has wallet ({wallet.account_number})")
                    continue
            except Wallet.DoesNotExist:
                pass

            # User needs a wallet - they're verified but don't have one
            if options['dry_run']:
                self.stdout.write(
                    self.style.WARNING(
                        f"○ {user.email}: Would create wallet (BVN:{user.has_bvn}, NIN:{user.has_nin})"
                    )
                )
                results['created_wallet'] += 1
                continue

            # Try to create wallet
            try:
                wallet_res = embedly_client.create_wallet(
                    customer_id=user.embedly_customer_id,
                    name=f"{user.first_name} {user.last_name}",
                    phone=user.phone
                )

                if wallet_res.get("success"):
                    data = wallet_res["data"]["virtualAccount"]
                    wallet, _ = Wallet.objects.get_or_create(user=user)

                    wallet.account_name = f"{user.first_name} {user.last_name}"
                    wallet.account_number = data.get("accountNumber")
                    wallet.bank = data.get("bankName")
                    wallet.bank_code = data.get("bankCode")
                    wallet.embedly_wallet_id = wallet_res["data"]["id"]
                    wallet.save()

                    user.embedly_wallet_id = wallet_res["data"]["id"]
                    user.has_virtual_wallet = True
                    user.save(update_fields=["embedly_wallet_id", "has_virtual_wallet"])

                    results['created_wallet'] += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ {user.email}: Created wallet ({data.get('accountNumber')})"
                        )
                    )
                else:
                    results['failed'] += 1
                    error_msg = wallet_res.get('message', 'Unknown error')
                    self.stdout.write(
                        self.style.ERROR(
                            f"✗ {user.email}: Failed - {error_msg}"
                        )
                    )

            except Exception as e:
                results['failed'] += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ {user.email}: Exception - {str(e)}"
                    )
                )

        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write('='*60)
        self.stdout.write(f"Users checked: {results['checked']}")
        self.stdout.write(self.style.SUCCESS(f"Already have wallets: {results['has_wallet']}"))
        self.stdout.write(self.style.SUCCESS(f"Wallets created: {results['created_wallet']}"))
        self.stdout.write(self.style.ERROR(f"Failed: {results['failed']}"))

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\n*** DRY RUN - No changes made ***'))

        self.stdout.write('')
