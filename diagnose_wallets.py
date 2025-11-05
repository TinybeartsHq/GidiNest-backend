#!/usr/bin/env python
"""
Diagnostic script to understand why verified users don't have wallets.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gidinest_backend.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from account.models.users import UserModel
from wallet.models import Wallet
from django.db.models import Q

print('='*60)
print('WALLET DIAGNOSIS FOR VERIFIED USERS')
print('='*60)

# Get all verified users
all_verified = UserModel.objects.filter(Q(has_bvn=True) | Q(has_nin=True))
print(f'\n✓ Total verified users (has_bvn=True OR has_nin=True): {all_verified.count()}')

# Break them down by category
with_virtual_wallet_flag = all_verified.filter(has_virtual_wallet=True)
without_virtual_wallet_flag = all_verified.filter(has_virtual_wallet=False)

print(f'  - With has_virtual_wallet=True: {with_virtual_wallet_flag.count()}')
print(f'  - With has_virtual_wallet=False: {without_virtual_wallet_flag.count()}')

# Check embedly_customer_id status
with_embedly = all_verified.exclude(embedly_customer_id="").exclude(embedly_customer_id__isnull=True)
without_embedly = all_verified.filter(Q(embedly_customer_id="") | Q(embedly_customer_id__isnull=True))

print(f'\n  - With embedly_customer_id: {with_embedly.count()}')
print(f'  - Without embedly_customer_id: {without_embedly.count()}')

# Check actual wallet objects
users_with_wallet_objects = 0
users_without_wallet_objects = 0
users_with_complete_wallets = 0

for user in all_verified:
    try:
        wallet = user.wallet
        users_with_wallet_objects += 1
        if wallet.account_number:
            users_with_complete_wallets += 1
    except Wallet.DoesNotExist:
        users_without_wallet_objects += 1

print(f'\n  - With Wallet database object: {users_with_wallet_objects}')
print(f'    └─ Of those, with account_number: {users_with_complete_wallets}')
print(f'  - Without Wallet database object: {users_without_wallet_objects}')

print('\n' + '='*60)
print('PROBLEM CATEGORIES')
print('='*60)

# Category 1: Verified but has_virtual_wallet=False (these should get fixed)
category1 = all_verified.filter(has_virtual_wallet=False)
print(f'\n1. Verified but has_virtual_wallet=False: {category1.count()} users')
if category1.exists():
    cat1_with_embedly = category1.exclude(embedly_customer_id="").exclude(embedly_customer_id__isnull=True)
    cat1_without_embedly = category1.filter(Q(embedly_customer_id="") | Q(embedly_customer_id__isnull=True))
    print(f'   - With embedly_customer_id (can fix now): {cat1_with_embedly.count()}')
    print(f'   - Without embedly_customer_id (need embedly setup first): {cat1_without_embedly.count()}')

    if cat1_with_embedly.count() > 0:
        print(f'\n   Sample users who can be fixed now:')
        for user in cat1_with_embedly[:3]:
            print(f'   - {user.email} (BVN:{user.has_bvn}, NIN:{user.has_nin})')

# Category 2: has_virtual_wallet=True but wallet object missing or incomplete
category2_users = []
for user in with_virtual_wallet_flag:
    try:
        wallet = user.wallet
        if not wallet.account_number:
            category2_users.append(user)
    except Wallet.DoesNotExist:
        category2_users.append(user)

print(f'\n2. has_virtual_wallet=True but wallet incomplete: {len(category2_users)} users')
if category2_users:
    print(f'   Sample users:')
    for user in category2_users[:3]:
        print(f'   - {user.email}')

print('\n' + '='*60)
print('RECOMMENDED ACTIONS')
print('='*60)

if cat1_with_embedly.count() > 0:
    print(f'\n✓ Run this to fix {cat1_with_embedly.count()} users:')
    print('  python manage.py fix_missing_wallets')

if cat1_without_embedly.count() > 0:
    print(f'\n⚠️  {cat1_without_embedly.count()} verified users need embedly_customer_id first')
    print('  These users verified but embedly customer creation failed')
    print('  Consider re-running embedly customer creation for them')

if len(category2_users) > 0:
    print(f'\n⚠️  {len(category2_users)} users have has_virtual_wallet=True but incomplete wallets')
    print('  These need manual investigation')

print('\n' + '='*60)
