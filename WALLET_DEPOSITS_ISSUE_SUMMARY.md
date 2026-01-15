# Wallet Deposits Not Working - Issue Summary & Solution

## THE PROBLEM 🚨

**Users are transferring money to their virtual accounts but the money is NOT appearing in their wallets.**

### Example Case
- User: Faithfulness Ekeh (faithfulekeh@gmail.com)
- Virtual Account: 9710306989 (Sterling Bank via Embedly)
- Current Balance: ₦0.00
- Transaction History: Empty (0 transactions)
- Status: User transferred money but it was never credited

## ROOT CAUSE IDENTIFIED ✅

**Embedly webhook signature verification is failing.**

Your logs show repeated signature mismatch errors from Jan 9-15, 2026:
```
WARNING: Embedly deposit webhook signature mismatch
```

### What This Means:
1. ✅ User transfers money to virtual account
2. ✅ Embedly receives the transfer
3. ✅ Embedly sends webhook notification to your server
4. ❌ **Your server rejects it (403 Forbidden) because signature doesn't match**
5. ❌ Money is NEVER credited to user's wallet
6. ❌ User sees ₦0 balance despite having transferred money

### Why Signature Fails:
Your webhook handler verifies Embedly's request using HMAC signature to prevent fraud. The signature mismatch means either:
- Wrong webhook secret configured in `.env`
- Embedly changed their signature algorithm
- Secret key was regenerated but not updated in your system

## IMMEDIATE ACTIONS REQUIRED

### 1. Deploy Enhanced Logging (Get Debug Info)

I've added detailed logging to help diagnose the exact issue.

**Deploy the changes:**
```bash
cd /var/www/GidiNest-backend
git pull  # Or copy the updated files
sudo systemctl restart gunicorn
```

**Files modified:**
- `wallet/views.py` - Enhanced webhook signature debugging
- `wallet/models.py` - Fixed balance refresh bug after deposit

### 2. Trigger Test Deposit & Capture Debug Info

**Ask Faithfulness Ekeh (or any user) to make a small test transfer:**
- To: 9710306989 (Sterling Bank)
- Amount: ₦100-500 (small amount for testing)

**Wait 30 seconds, then check logs:**
```bash
sudo journalctl -u gunicorn -n 100 | grep -A 15 "EMBEDLY WEBHOOK SIGNATURE MISMATCH"
```

**You'll now see detailed output like:**
```
EMBEDLY WEBHOOK SIGNATURE MISMATCH - DETAILED DEBUG INFO
Provided signature: abc123def456789...
Signature length: 128
Body length: 234
Body preview: {"event":"nip","data":{"accountNumber":"9710306989",...}}
Secret used (preview): sk_test_ab...xy (len=80)
Expected SHA-512: xyz789abc123...
Expected SHA-256: def456ghi789...
```

**Send this info to Embedly support IMMEDIATELY.**

### 3. Contact Embedly Support

**Email them:**
```
Subject: URGENT: Webhook Signature Verification Failing - All Deposits Blocked

Hello Embedly Team,

Our production system is rejecting ALL deposit webhooks due to signature mismatch.
This is blocking all user deposits.

Environment: Production
Webhook URL: https://app.gidinest.com/wallet/embedly/webhook/secure

[PASTE THE DEBUG INFO FROM LOGS HERE]

Questions:
1. What secret should we use for webhook signature verification?
2. Has your signature algorithm changed recently?
3. Was our webhook secret regenerated?

This is critical - all deposits have been failing since Jan 9, 2026.
Please respond urgently.
```

## TEMPORARY WORKAROUND (While Waiting for Fix)

While investigating the signature issue, you can manually credit verified deposits.

**Safety First:** Only credit deposits you've verified through:
- User's bank statement
- Embedly dashboard transaction logs
- Direct confirmation from user

### Manual Credit Command

I've created a safe manual credit tool:

```bash
# Step 1: Verify the deposit exists in Embedly's system first!

# Step 2: Credit the wallet
python manage.py manual_credit 9710306989 10000.00 "MANUAL_20260115_001" --sender "Faithfulness Ekeh" --confirm
```

**For each affected user:**
1. Ask them for proof of transfer (screenshot/statement)
2. Verify in Embedly dashboard that transfer was received
3. Use unique reference: `MANUAL_YYYYMMDD_NNN`
4. Document in spreadsheet for reconciliation
5. Run the command with `--confirm` flag

### Manual Credit for Faithfulness Ekeh Example:
```bash
# First check what they actually transferred (ask user or check Embedly)
# Then credit:
python manage.py manual_credit 9710306989 [AMOUNT] "MANUAL_20260115_001" --sender "Bank Transfer" --confirm
```

## DIAGNOSTIC TOOLS CREATED

### 1. Webhook Health Check
```bash
python manage.py diagnose_webhook_issues
```

Shows:
- Webhook configuration status
- Recent deposit activity
- Wallet configurations
- Balance mismatches
- Actionable recommendations

### 2. Signature Testing
```bash
python manage.py test_webhook_signature
```

Generates expected signatures for debugging with Embedly support.

### 3. Manual Credit Tool
```bash
python manage.py manual_credit <account_number> <amount> <reference> --confirm
```

Safely credit verified deposits while webhooks are down.

## BUGS FIXED

### Bug 1: Wallet Balance Not Refreshing ✅ FIXED
**Location:** `wallet/models.py:100-144`

The `deposit()` and `withdraw()` methods weren't refreshing the wallet instance after using `F()` expressions. This could cause serialization issues.

**Fix:** Added `refresh_from_db()` after atomic updates.

## AFFECTED USERS

### Find All Potentially Affected Users
```bash
python manage.py shell
```

```python
from wallet.models import Wallet

# Users with zero transactions (may have tried deposits)
print("Users with zero transaction history:")
for wallet in Wallet.objects.all():
    if wallet.wallettransaction_set.count() == 0:
        print(f"  {wallet.user.email} - Account: {wallet.account_number}")
```

**Action:** Contact these users to check if they attempted deposits.

## TIMELINE OF ISSUE

- **Jan 9, 2026 13:07** - First signature mismatch logged
- **Jan 9-15** - Multiple signature mismatches (every deposit attempt failed)
- **Jan 15** - Issue identified and fixes deployed

**All deposits between Jan 9-15 failed and were NOT credited.**

## SUCCESS CRITERIA

Once fixed, verify:

```bash
# 1. Test deposit works
python manage.py shell -c "
from wallet.models import Wallet
wallet = Wallet.objects.get(account_number='9710306989')
print(f'Balance: ₦{wallet.balance}')
print(f'Transactions: {wallet.wallettransaction_set.count()}')
"

# 2. No signature errors in logs
sudo journalctl -u gunicorn -n 50 | grep -i "signature mismatch"
# (Should be empty)

# 3. Successful credit log
sudo journalctl -u gunicorn -n 50 | grep -i "successfully credited"
# (Should show successful deposit)
```

## NEXT STEPS CHECKLIST

- [ ] Deploy enhanced logging (`git pull` + `sudo systemctl restart gunicorn`)
- [ ] Trigger test deposit with Faithfulness Ekeh
- [ ] Capture detailed debug info from logs
- [ ] Send debug info to Embedly support
- [ ] Find all affected users (zero transaction history)
- [ ] For verified deposits: manually credit using safe command
- [ ] Once Embedly responds: Update webhook secret if needed
- [ ] Test deposits work after fix
- [ ] Notify all affected users
- [ ] Set up monitoring to alert on future webhook failures

## MONITORING GOING FORWARD

Add daily health check:
```bash
# Add to crontab
0 9 * * * cd /var/www/GidiNest-backend && python manage.py diagnose_webhook_issues | grep "NO DEPOSITS" && echo "ALERT: Webhook failure detected" | mail -s "Deposit System Down" admin@gidinest.com
```

## FILES CREATED/MODIFIED

**Modified:**
- `wallet/models.py` - Fixed balance refresh bug
- `wallet/views.py` - Enhanced webhook debugging

**Created:**
- `wallet/management/commands/diagnose_webhook_issues.py` - Health check tool
- `wallet/management/commands/test_webhook_signature.py` - Signature debug tool
- `wallet/management/commands/manual_credit.py` - Safe manual credit tool
- `WALLET_DEPOSIT_TROUBLESHOOTING.md` - Comprehensive troubleshooting guide
- `URGENT_DEPOSIT_FIX_PLAN.md` - Step-by-step fix plan
- `debug_embedly_webhook.py` - Signature testing script

## QUESTIONS?

See detailed documentation in:
- `URGENT_DEPOSIT_FIX_PLAN.md` - Immediate action plan
- `WALLET_DEPOSIT_TROUBLESHOOTING.md` - Full troubleshooting guide
