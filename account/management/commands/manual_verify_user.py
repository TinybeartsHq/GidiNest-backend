"""
Manually update user verification status and create wallet.
Use this for users who verified via Postman but local DB wasn't updated.

Usage:
    python manage.py manual_verify_user --email user@example.com --bvn
    python manage.py manual_verify_user --email user@example.com --nin
    python manage.py manual_verify_user --email user@example.com --bvn --nin
    python manage.py manual_verify_user --email user@example.com --bvn --create-wallet
"""
from django.core.management.base import BaseCommand, CommandError
from account.models.users import UserModel
from wallet.models import Wallet
from providers.helpers.embedly import EmbedlyClient


class Command(BaseCommand):
    help = 'Manually mark user as verified and optionally create wallet'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='User email address',
        )
        parser.add_argument(
            '--bvn',
            action='store_true',
            help='Mark BVN as verified',
        )
        parser.add_argument(
            '--nin',
            action='store_true',
            help='Mark NIN as verified',
        )
        parser.add_argument(
            '--create-wallet',
            action='store_true',
            help='Create wallet for user',
        )

    def handle(self, *args, **options):
        email = options['email']
        mark_bvn = options['bvn']
        mark_nin = options['nin']
        create_wallet = options['create_wallet']

        if not mark_bvn and not mark_nin:
            raise CommandError('You must specify at least --bvn or --nin')

        self.stdout.write(f'\nProcessing user: {email}')

        # Get user
        try:
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            raise CommandError(f'User with email {email} not found')

        self.stdout.write(f'Found user: {user.first_name} {user.last_name}')
        self.stdout.write(f'Current status:')
        self.stdout.write(f'  - has_bvn: {user.has_bvn}')
        self.stdout.write(f'  - has_nin: {user.has_nin}')
        self.stdout.write(f'  - account_tier: {user.account_tier}')
        self.stdout.write(f'  - has_virtual_wallet: {user.has_virtual_wallet}')

        # Update verification status
        changes = []
        if mark_bvn and not user.has_bvn:
            user.has_bvn = True
            changes.append('has_bvn')
            self.stdout.write(self.style.SUCCESS('\n✓ Marked BVN as verified'))

        if mark_nin and not user.has_nin:
            user.has_nin = True
            changes.append('has_nin')
            self.stdout.write(self.style.SUCCESS('✓ Marked NIN as verified'))

        # Update tier
        old_tier = user.account_tier
        if user.has_bvn and user.has_nin:
            user.account_tier = "Tier 2"
        elif user.has_bvn or user.has_nin:
            user.account_tier = "Tier 1"

        if old_tier != user.account_tier:
            changes.append('account_tier')
            self.stdout.write(self.style.SUCCESS(f'✓ Updated tier: {old_tier} → {user.account_tier}'))

        # Save changes
        if changes:
            user.save(update_fields=changes)
            self.stdout.write(self.style.SUCCESS(f'\n✓ User updated successfully'))
        else:
            self.stdout.write(self.style.WARNING('\nNo changes needed - user already marked as verified'))

        # Create wallet if requested
        if create_wallet:
            self.stdout.write('\nCreating wallet...')

            if not user.embedly_customer_id:
                raise CommandError('User has no embedly_customer_id. Cannot create wallet.')

            # Check if user already has wallet
            try:
                wallet = user.wallet
                if wallet.account_number:
                    self.stdout.write(
                        self.style.WARNING(
                            f'User already has wallet: {wallet.account_number} ({wallet.bank})'
                        )
                    )
                    return
            except Wallet.DoesNotExist:
                pass

            # Create wallet via Embedly
            embedly_client = EmbedlyClient()

            try:
                wallet_res = embedly_client.create_wallet(
                    customer_id=user.embedly_customer_id,
                    name=f"{user.first_name} {user.last_name}",
                    phone=user.phone
                )

                if wallet_res.get("success"):
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

                    self.stdout.write(self.style.SUCCESS(f'\n✓ Wallet created successfully!'))
                    self.stdout.write(f'  Account Number: {wallet.account_number}')
                    self.stdout.write(f'  Bank: {wallet.bank}')
                    self.stdout.write(f'  Account Name: {wallet.account_name}')
                else:
                    error_msg = wallet_res.get('message', 'Unknown error')
                    raise CommandError(f'Failed to create wallet: {error_msg}')

            except Exception as e:
                raise CommandError(f'Error creating wallet: {str(e)}')

        # Final summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('FINAL STATUS'))
        self.stdout.write('='*60)
        # Refresh from DB
        user.refresh_from_db()
        self.stdout.write(f'User: {user.email}')
        self.stdout.write(f'  - has_bvn: {user.has_bvn}')
        self.stdout.write(f'  - has_nin: {user.has_nin}')
        self.stdout.write(f'  - account_tier: {user.account_tier}')
        self.stdout.write(f'  - has_virtual_wallet: {user.has_virtual_wallet}')

        if user.has_virtual_wallet:
            try:
                wallet = user.wallet
                self.stdout.write(f'  - wallet_account: {wallet.account_number}')
                self.stdout.write(f'  - wallet_bank: {wallet.bank}')
            except:
                pass

        self.stdout.write('')
