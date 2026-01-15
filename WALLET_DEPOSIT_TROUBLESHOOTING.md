# Wallet Deposit Troubleshooting Guide

## Issue
Users report that money is not being credited to their wallets when they make bank transfers.

## Root Causes Identified

### 1. Critical Bug Fixed: Wallet Balance Not Refreshing After Deposit/Withdrawal
**Status:** ✅ FIXED

**Problem:**
The `deposit()` and `withdraw()` methods in `wallet/models.py` were using Django's `F()` expression to update balances atomically, but were not refreshing the wallet instance afterward. This meant:
- The wallet instance in memory had an F() expression object instead of the actual balance
- Any code trying to read the balance immediately after would fail
- Serialization of the wallet would fail

**Fix Applied:**
Added `wallet.refresh_from_db()` and `self.balance = wallet.balance` after the atomic update to ensure the instance reflects the actual database state.

### 2. Webhook Issues (Most Likely Cause)

If deposits are not being recorded at all, the webhooks from your payment providers (Embedly and 9PSB) are likely failing. Here are the common causes:

#### A. Webhook Signature Verification Failures
**Symptoms:**
- No deposits recorded in the last 7 days
- 403 Forbidden errors in logs
- "Invalid signature" warnings

**Common Causes:**
- Incorrect webhook secret configured
- Payment provider changed their signature algorithm
- Signature header name mismatch

**How to Check:**
```bash
# Run the diagnostic command
python manage.py diagnose_webhook_issues

# Test signature generation
python manage.py test_webhook_signature
```

**How to Fix:**
1. Check your `.env` file for correct secrets:
   - `EMBEDLY_API_KEY_PRODUCTION` - Must match Embedly's API key
   - `PSB9_CLIENT_SECRET` - Must match 9PSB's client secret

2. Verify webhook URLs are registered with providers:
   - Embedly: `https://your-domain.com/wallet/embedly/webhook/secure`
   - 9PSB: `https://your-domain.com/wallet/9psb/webhook`

3. Check application logs for webhook failures:
   ```bash
   # Look for signature errors
   grep -i "signature" /path/to/logs/*.log

   # Look for webhook errors
   grep -i "webhook" /path/to/logs/*.log
   ```

#### B. Webhook URLs Not Registered
**Symptoms:**
- No webhook requests reaching your server
- No 403 errors in logs

**How to Fix:**
1. Log into Embedly dashboard and verify webhook URL
2. Log into 9PSB dashboard and verify webhook URL
3. Ensure URLs are accessible from the internet (no firewall blocking)

#### C. Account Number Confusion
**Symptoms:**
- Some users' deposits work, others don't
- Users send to wrong virtual account

**How to Check:**
Your system supports TWO payment providers:
- **Embedly (v1):** Uses `wallet.account_number` field
- **9PSB (v2):** Uses `wallet.psb9_account_number` field

**How to Fix:**
1. Check if users have both account numbers:
   ```python
   from wallet.models import Wallet

   # Check user's wallet
   wallet = Wallet.objects.get(user__email='user@example.com')
   print(f"Embedly account: {wallet.account_number}")
   print(f"9PSB account: {wallet.psb9_account_number}")
   ```

2. Ensure users are sending to the correct account number for their provider

## Diagnostic Commands

### 1. Run Full Diagnostic
```bash
python manage.py diagnose_webhook_issues
```

This will check:
- Webhook configuration
- Recent deposit activity
- Wallet configurations
- Balance mismatches
- Duplicate transactions

### 2. Test Webhook Signatures
```bash
python manage.py test_webhook_signature
```

This generates expected signatures for both providers.

### 3. Check Specific User's Deposits
```python
from wallet.models import Wallet, WalletTransaction
from django.contrib.auth import get_user_model

User = get_user_model()

# Get user
user = User.objects.get(email='user@example.com')
wallet = user.wallet

# Check recent transactions
recent_credits = WalletTransaction.objects.filter(
    wallet=wallet,
    transaction_type='credit'
).order_by('-created_at')[:10]

for txn in recent_credits:
    print(f"{txn.created_at} - ₦{txn.amount} - {txn.description}")
```

### 4. Check for Failed Webhooks in Logs
```bash
# Check for signature failures
grep "Invalid signature" /var/log/django/*.log

# Check for webhook errors
grep "webhook" /var/log/django/*.log | grep -i "error"

# Check for missing wallet errors
grep "Wallet not found" /var/log/django/*.log
```

## Common Scenarios

### Scenario 1: NO deposits in the last 7 days
**Diagnosis:** Webhooks are completely broken

**Actions:**
1. Run `python manage.py diagnose_webhook_issues`
2. Check webhook secrets are configured correctly
3. Verify webhook URLs are registered with providers
4. Check firewall/network settings
5. Contact payment provider support

### Scenario 2: SOME deposits work, others don't
**Diagnosis:** Users are confused about which account to use

**Actions:**
1. Check if affected users have both Embedly and 9PSB accounts
2. Verify they're sending to the correct account number
3. Check if the transfer reference exists in database:
   ```python
   WalletTransaction.objects.filter(external_reference='REF_12345')
   ```

### Scenario 3: Deposit recorded but balance not updated
**Diagnosis:** Balance update logic issue (FIXED)

**Actions:**
1. This should be fixed by the wallet model changes
2. If still occurring, check for database transaction rollbacks in logs
3. Verify no exceptions during `wallet.deposit()` call

### Scenario 4: Duplicate deposits (same money credited twice)
**Diagnosis:** Webhook replay or duplicate reference issue

**Actions:**
1. Check for duplicate external references:
   ```python
   from django.db.models import Count
   WalletTransaction.objects.values('external_reference').annotate(
       count=Count('id')
   ).filter(count__gt=1)
   ```
2. This should be prevented by unique reference check in webhook handler
3. If occurring, investigate why duplicate webhooks are being sent

## Testing Webhooks Manually

### Test Embedly Webhook
```bash
# Generate test signature
SECRET="your_embedly_api_key"
PAYLOAD='{"event":"nip","data":{"accountNumber":"1234567890","reference":"TEST_001","amount":10000,"senderName":"Test User","senderBank":"Test Bank"}}'
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha512 -hmac "$SECRET" -hex | awk '{print $2}')

# Send test webhook
curl -X POST https://your-domain.com/wallet/embedly/webhook/secure \
  -H "Content-Type: application/json" \
  -H "X-Auth-Signature: $SIGNATURE" \
  -d "$PAYLOAD"
```

### Test 9PSB Webhook
```bash
# Generate test signature
SECRET="your_psb9_client_secret"
PAYLOAD='{"event":"transfer.credit","data":{"reference":"TEST_001","accountNumber":"1234567890","amount":10000,"senderName":"Test User"}}'
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" -hex | awk '{print $2}')

# Send test webhook
curl -X POST https://your-domain.com/wallet/9psb/webhook \
  -H "Content-Type: application/json" \
  -H "X-9PSB-Signature: $SIGNATURE" \
  -d "$PAYLOAD"
```

## Monitoring

### Set Up Alerts
Monitor these metrics:
- Number of deposits per day
- Webhook failure rate (403 errors)
- Balance mismatches
- Duplicate references

### Log What to Watch
- `"Invalid signature"` - Webhook authentication failing
- `"Wallet not found"` - Account number mismatch
- `"Failed to deposit"` - Database/balance update errors
- `"Transaction with this reference has been processed"` - Duplicate webhooks

## Prevention

1. **Regular Health Checks:**
   - Run `python manage.py diagnose_webhook_issues` daily
   - Monitor deposit rate (should be relatively consistent)

2. **Webhook Monitoring:**
   - Set up external monitoring for webhook endpoints
   - Alert if no deposits received in 24 hours

3. **User Education:**
   - Clearly show which account number to use (Embedly vs 9PSB)
   - Provide clear instructions for bank transfers
   - Set up auto-reply for deposit complaints with diagnostic steps

4. **Reconciliation:**
   - Periodically run balance mismatch checks
   - Cross-reference with payment provider transaction logs

## Contact Information

If issues persist after following this guide:
1. Check payment provider status pages
2. Contact Embedly support with test signatures
3. Contact 9PSB support with test signatures
4. Review recent code changes to webhook handlers

## Files Modified

- `wallet/models.py` - Fixed deposit/withdraw balance refresh
- `wallet/management/commands/diagnose_webhook_issues.py` - NEW diagnostic tool
- `wallet/management/commands/test_webhook_signature.py` - NEW signature testing tool
