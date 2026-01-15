# URGENT: Wallet Deposit Fix Action Plan

## Problem Summary
Users cannot receive deposits because Embedly webhooks are failing signature verification.

**Evidence:**
- User: Faithfulness Ekeh (faithfulekeh@gmail.com)
- Account: 9710306989
- Balance: ₦0.00
- Transactions: 0 (none recorded)
- Logs show: "Embedly deposit webhook signature mismatch" (Jan 9-15)

## Root Cause
Embedly is sending webhooks with a signature that doesn't match what we're expecting. This means either:
1. The `EMBEDLY_API_KEY_PRODUCTION` in `.env` is incorrect
2. Embedly is using a different secret for webhooks than the API key
3. The signature algorithm or format has changed

## Immediate Action Required

### Step 1: Restart Gunicorn (Apply Enhanced Logging)
```bash
cd /var/www/GidiNest-backend
sudo systemctl restart gunicorn
```

This applies the new enhanced logging that will show:
- Exact signature Embedly sent
- Exact signature we expected
- Request body for debugging

### Step 2: Trigger a Test Deposit
Ask Faithfulness Ekeh (or any user) to make a small test transfer:
- To: 9710306989 (Sterling Bank)
- Amount: Any amount (e.g., ₦100)

### Step 3: Capture Detailed Debug Info
```bash
# Wait 30 seconds after the transfer, then check logs:
sudo journalctl -u gunicorn -n 50 | grep -A 15 "EMBEDLY WEBHOOK SIGNATURE MISMATCH"
```

You should now see detailed output like:
```
EMBEDLY WEBHOOK SIGNATURE MISMATCH - DETAILED DEBUG INFO
Provided signature: abc123def456...
Signature length: 128
Body length: 234
Body preview: {"event":"nip","data":{...}}
Secret used (preview): sk_test_12...34 (len=80)
Expected SHA-512: xyz789abc123...
Expected SHA-256: def456ghi789...
```

### Step 4: Analyze the Results

**Scenario A: Signatures are close but different**
- Likely cause: Wrong secret or algorithm mismatch
- Action: Contact Embedly support with the debug info

**Scenario B: Body format is different**
- Likely cause: Embedly changed their payload format
- Action: Update webhook handler to match new format

**Scenario C: No webhook received**
- Likely cause: Webhook URL not registered with Embedly
- Action: Log into Embedly dashboard and verify webhook URL

## Quick Workaround (NOT RECOMMENDED FOR PRODUCTION)

If you need to urgently allow deposits while investigating:

### Option 1: Temporarily Bypass Signature Verification
**WARNING:** This is INSECURE and should only be used for testing!

Edit `/var/www/GidiNest-backend/wallet/views.py` line 965:
```python
# TEMPORARY - REMOVE AFTER TESTING
if not verified:
    logger.warning("BYPASSING signature verification for testing - REMOVE THIS!")
    verified = True  # TEMPORARY BYPASS

if not verified:  # This will now be False due to above
```

Then restart: `sudo systemctl restart gunicorn`

**CRITICAL:** Revert this immediately after testing! Without signature verification, anyone could credit wallets.

### Option 2: Manual Credit (Safer)
If signature can't be fixed immediately, manually credit affected users:

```bash
cd /var/www/GidiNest-backend
python manage.py shell
```

```python
from wallet.models import Wallet, WalletTransaction
from decimal import Decimal

# Get the wallet
wallet = Wallet.objects.get(account_number='9710306989')

# VERIFY with user first: amount and transfer reference!
amount = Decimal('10000.00')  # Amount user transferred
reference = 'MANUAL_CREDIT_20260115_001'  # Unique reference

# Create transaction and credit wallet
with transaction.atomic():
    WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type='credit',
        amount=amount,
        description=f'Manual credit - Embedly webhook failed - Ref: {reference}',
        sender_name='Bank Transfer',
        external_reference=reference
    )
    wallet.deposit(amount)

print(f"Credited {amount} to {wallet.user.email}")
print(f"New balance: {wallet.balance}")
```

**Important:** Keep records of all manual credits for reconciliation!

## Long-term Solution

### Contact Embedly Support
Once you have the debug info from Step 3:

**Email Embedly Support:**
```
Subject: Webhook Signature Verification Failing - Urgent

Hello Embedly Team,

Our webhook endpoint is rejecting deposit notifications due to signature mismatch.

Environment: Production
Organization ID: [FROM YOUR EMBEDLY ACCOUNT]
Webhook URL: https://app.gidinest.com/wallet/embedly/webhook/secure

Debug Information:
- Signature we received: [FROM LOGS]
- Signature we expected (SHA-512): [FROM LOGS]
- Signature we expected (SHA-256): [FROM LOGS]
- Request body: [FROM LOGS]
- Our API key (first/last 10 chars): [FROM LOGS]

Questions:
1. What secret should we use for webhook signature verification?
2. What algorithm: SHA-512, SHA-256, or other?
3. What format: raw hexdigest or prefixed with "sha512="?

This is affecting all our users' deposits. Please respond urgently.
```

### Verify Webhook Configuration
1. Log into Embedly dashboard
2. Go to Settings → Webhooks
3. Verify URL: `https://app.gidinest.com/wallet/embedly/webhook/secure`
4. Verify secret matches your `.env` file
5. Check for any recent changes or notifications

## Testing After Fix

Once signature issue is resolved:

```bash
# 1. Restart gunicorn
sudo systemctl restart gunicorn

# 2. Ask test user to make ₦100 transfer to 9710306989

# 3. Wait 30 seconds, check if credited:
python manage.py shell -c "
from wallet.models import Wallet
wallet = Wallet.objects.get(account_number='9710306989')
print(f'Balance: ₦{wallet.balance}')
print(f'Recent transaction count: {wallet.wallettransaction_set.count()}')
"

# 4. Check logs for success:
sudo journalctl -u gunicorn -n 20 | grep -i "successfully credited"
```

## Affected Users

To find all users who may have attempted deposits:

```python
# In Django shell
from wallet.models import Wallet
from django.contrib.auth import get_user_model

User = get_user_model()

# Users with wallets but zero transactions (may have tried to deposit)
zero_txn_users = []
for wallet in Wallet.objects.all():
    if wallet.wallettransaction_set.count() == 0:
        zero_txn_users.append(wallet.user.email)

print(f"Users with no transaction history: {len(zero_txn_users)}")
for email in zero_txn_users:
    print(f"  - {email}")
```

Contact these users to check if they attempted deposits.

## Monitoring Going Forward

Set up alerts for:
```bash
# Daily cron job to check deposit health
0 9 * * * cd /var/www/GidiNest-backend && python manage.py diagnose_webhook_issues | grep "NO DEPOSITS" && echo "ALERT: No deposits in 7 days" | mail -s "Deposit System Alert" admin@gidinest.com
```

## Files Modified
- `wallet/models.py` - Fixed deposit/withdraw balance refresh bug
- `wallet/views.py` - Added enhanced debugging for signature failures
- `wallet/management/commands/diagnose_webhook_issues.py` - Diagnostic tool
- `wallet/management/commands/test_webhook_signature.py` - Signature testing tool

## Next Steps
1. ✅ Enhanced logging added
2. ⏳ Restart gunicorn
3. ⏳ Trigger test deposit
4. ⏳ Capture debug info
5. ⏳ Contact Embedly support
6. ⏳ Fix signature verification
7. ⏳ Test with real deposit
8. ⏳ Notify affected users
