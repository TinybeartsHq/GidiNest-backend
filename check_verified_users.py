#!/usr/bin/env python
"""
Quick script to check verified users and wallet status.
Run this with: python check_verified_users.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gidinest_backend.settings')
django.setup()

from account.models.users import UserModel
from wallet.models import Wallet
from django.db.models import Q

print('=== User Verification Statistics ===')
print(f'Total users: {UserModel.objects.count()}')
print(f'Users with BVN verified (has_bvn=True): {UserModel.objects.filter(has_bvn=True).count()}')
print(f'Users with NIN verified (has_nin=True): {UserModel.objects.filter(has_nin=True).count()}')
print(f'Users with BVN OR NIN: {UserModel.objects.filter(Q(has_bvn=True) | Q(has_nin=True)).count()}')
print(f'Users with virtual wallet flag (has_virtual_wallet=True): {UserModel.objects.filter(has_virtual_wallet=True).count()}')
print(f'Users with embedly_customer_id: {UserModel.objects.exclude(embedly_customer_id="").exclude(embedly_customer_id__isnull=True).count()}')
print()

print('=== Wallet Statistics ===')
print(f'Total wallet records: {Wallet.objects.count()}')
print(f'Wallets with account_number: {Wallet.objects.exclude(account_number="").exclude(account_number__isnull=True).count()}')
print(f'Wallets without account_number: {Wallet.objects.filter(Q(account_number="") | Q(account_number__isnull=True)).count()}')
print()

print('=== Users Needing Wallet Fix ===')
# Users who are verified but don't have virtual wallet flag
verified_no_wallet = UserModel.objects.filter(
    has_virtual_wallet=False
).filter(
    Q(has_bvn=True) | Q(has_nin=True)
)
print(f'Verified users without has_virtual_wallet=True: {verified_no_wallet.count()}')

# Users verified with embedly_customer_id
verified_with_embedly = verified_no_wallet.exclude(embedly_customer_id="").exclude(embedly_customer_id__isnull=True)
print(f'  - Of those, with embedly_customer_id: {verified_with_embedly.count()}')
print(f'  - Of those, without embedly_customer_id: {verified_no_wallet.filter(Q(embedly_customer_id="") | Q(embedly_customer_id__isnull=True)).count()}')

print()

# Show detailed info for verified users
all_verified = UserModel.objects.filter(Q(has_bvn=True) | Q(has_nin=True))
if all_verified.exists():
    print(f'\n=== All Verified Users ({all_verified.count()} total) ===')
    for user in all_verified[:10]:
        wallet_status = "NO WALLET"
        try:
            wallet = user.wallet
            if wallet.account_number:
                wallet_status = f"Wallet with account: {wallet.account_number}"
            else:
                wallet_status = "Wallet exists but NO account number"
        except Wallet.DoesNotExist:
            wallet_status = "NO WALLET object"

        print(f'\nUser: {user.email}')
        print(f'  - has_bvn: {user.has_bvn}')
        print(f'  - has_nin: {user.has_nin}')
        print(f'  - has_virtual_wallet flag: {user.has_virtual_wallet}')
        print(f'  - embedly_customer_id: {user.embedly_customer_id[:30] if user.embedly_customer_id else "None"}...')
        print(f'  - embedly_wallet_id: {user.embedly_wallet_id[:30] if user.embedly_wallet_id else "None"}...')
        print(f'  - Wallet status: {wallet_status}')

    if all_verified.count() > 10:
        print(f'\n... and {all_verified.count() - 10} more verified users')

print('\n=== Summary ===')
if verified_with_embedly.count() > 0:
    print(f'⚠️  Found {verified_with_embedly.count()} verified users who need wallets!')
    print('    Run: python manage.py fix_missing_wallets')
else:
    print('✓ All verified users either have wallets or need embedly_customer_id setup')
