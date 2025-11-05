"""
Django management command to create wallets for verified users who don't have them.

Usage:
    python manage.py fix_missing_wallets                    # Fix all eligible users
    python manage.py fix_missing_wallets --limit 100         # Fix first 100 users
    python manage.py fix_missing_wallets --emails user1@example.com user2@example.com
    python manage.py fix_missing_wallets --dry-run           # Show what would be fixed without making changes
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db import models
from account.models.users import UserModel
from wallet.models import Wallet
from providers.helpers.embedly import EmbedlyClient


class Command(BaseCommand):
    help = 'Create wallets for verified users (BVN/NIN) who do not have virtual wallets'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit the number of users to fix',
        )
        parser.add_argument(
            '--emails',
            nargs='+',
            help='Fix specific users by email addresses',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually creating wallets',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed results for each user',
        )

    def handle(self, *args, **options):
        embedly_client = EmbedlyClient()

        self.stdout.write(self.style.SUCCESS('Starting wallet fix for verified users...'))

        # Get users who need wallet creation
        if options['emails']:
            users = UserModel.objects.filter(email__in=options['emails'])
            self.stdout.write(f"Processing {len(options['emails'])} specific users...")
        else:
            # Users who are verified (BVN or NIN) but don't have virtual wallet
            users = UserModel.objects.filter(
                has_virtual_wallet=False
            ).filter(
                models.Q(has_bvn=True) | models.Q(has_nin=True)
            ).exclude(
                embedly_customer_id=""
            ).exclude(
                embedly_customer_id__isnull=True
            )

            if options.get('limit'):
                users = users[:options['limit']]
                self.stdout.write(f"Processing up to {options['limit']} users...")
            else:
                self.stdout.write(f"Processing {users.count()} verified users without wallets...")

        results = {
            'total_users': users.count(),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }

        for user in users:
            result = self._fix_user_wallet(user, embedly_client, dry_run=options['dry_run'])
            results['details'].append(result)

            if result['status'] == 'success':
                results['successful'] += 1
            elif result['status'] == 'skipped':
                results['skipped'] += 1
            else:
                results['failed'] += 1

            if options['verbose']:
                self._print_user_result(result)

        # Display summary
        self.stdout.write(self.style.SUCCESS('\n=== Fix Summary ==='))
        self.stdout.write(f"Total users processed: {results['total_users']}")
        self.stdout.write(self.style.SUCCESS(f"Successful: {results['successful']}"))
        self.stdout.write(self.style.WARNING(f"Skipped: {results['skipped']}"))
        self.stdout.write(self.style.ERROR(f"Failed: {results['failed']}"))

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\n*** DRY RUN - No changes were made ***'))

        # Show detailed results if not verbose (summary only)
        if not options['verbose'] and results['details']:
            self.stdout.write(self.style.SUCCESS('\n=== User List ==='))
            for detail in results['details']:
                status_symbol = '✓' if detail['status'] == 'success' else ('○' if detail['status'] == 'skipped' else '✗')
                status_style = self.style.SUCCESS if detail['status'] == 'success' else (
                    self.style.WARNING if detail['status'] == 'skipped' else self.style.ERROR
                )
                self.stdout.write(
                    status_style(f"{status_symbol} {detail['email']}: {detail['message']}")
                )

        # Exit with error code if any fixes failed
        if results['failed'] > 0:
            raise CommandError(f"{results['failed']} wallet creation(s) failed")

        self.stdout.write(self.style.SUCCESS('\nWallet fix completed successfully!'))

    def _fix_user_wallet(self, user, embedly_client, dry_run=False):
        """Fix wallet for a single user."""
        result = {
            'email': user.email,
            'status': 'failed',
            'message': '',
            'user_id': user.id,
            'has_bvn': user.has_bvn,
            'has_nin': user.has_nin,
        }

        try:
            # Check if user has Embedly customer ID
            if not user.embedly_customer_id:
                result['status'] = 'skipped'
                result['message'] = 'No Embedly customer ID (not eligible)'
                return result

            # Check if user is verified
            if not user.has_bvn and not user.has_nin:
                result['status'] = 'skipped'
                result['message'] = 'User not verified (no BVN or NIN)'
                return result

            # Check if user already has virtual wallet
            if user.has_virtual_wallet:
                result['status'] = 'skipped'
                result['message'] = 'User already has virtual wallet'
                return result

            if dry_run:
                result['status'] = 'success'
                result['message'] = f'Would create wallet (BVN: {user.has_bvn}, NIN: {user.has_nin})'
                return result

            # Create wallet via Embedly
            wallet_res = embedly_client.create_wallet(
                customer_id=user.embedly_customer_id,
                name=f"{user.first_name} {user.last_name}",
                phone=user.phone
            )

            if not wallet_res.get("success"):
                result['status'] = 'failed'
                result['message'] = f"Embedly API error: {wallet_res.get('message', 'Unknown error')}"
                return result

            # Create or update wallet in database
            with transaction.atomic():
                data = wallet_res["data"]["virtualAccount"]
                wallet, created = Wallet.objects.get_or_create(user=user)

                wallet.account_name = f"{user.first_name} {user.last_name}"
                wallet.account_number = data.get("accountNumber")
                wallet.bank = data.get("bankName")
                wallet.bank_code = data.get("bankCode")
                wallet.embedly_wallet_id = wallet_res["data"]["id"]
                wallet.save()

                user.embedly_wallet_id = wallet_res["data"]["id"]
                user.has_virtual_wallet = True
                user.save(update_fields=["embedly_wallet_id", "has_virtual_wallet"])

            result['status'] = 'success'
            result['message'] = f"Wallet created successfully (Account: {data.get('accountNumber')})"
            result['account_number'] = data.get("accountNumber")
            result['bank'] = data.get("bankName")

        except Exception as e:
            result['status'] = 'failed'
            result['message'] = f"Error: {str(e)}"

        return result

    def _print_user_result(self, result):
        """Print detailed result for a user."""
        if result['status'] == 'success':
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ {result['email']}: {result['message']}"
                )
            )
        elif result['status'] == 'skipped':
            self.stdout.write(
                self.style.WARNING(
                    f"○ {result['email']}: {result['message']}"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"✗ {result['email']}: {result['message']}"
                )
            )
