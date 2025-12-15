# Embedly Webhook Signature Fix - Quick Summary

## ✅ What Was Fixed

### Problem
Embedly deposit webhooks were failing with **"signature mismatch"** errors because the webhook secret was not configured.

### Solution
Added the missing `EMBEDLY_WEBHOOK_SECRET` configuration and improved error logging.

---

## 🔧 Changes Made

### 1. Settings Configuration (gidinest_backend/settings.py:417)
```python
EMBEDLY_WEBHOOK_SECRET=os.getenv('EMBEDLY_WEBHOOK_SECRET', config('EMBEDLY_WEBHOOK_SECRET', default=''))
```

### 2. Enhanced Error Logging (wallet/views.py:944-980)
- Shows which signature header Embedly sent
- Displays which secrets were tried
- Includes request body preview
- Helps diagnose future issues

### 3. Diagnostic Tools
- Created `diagnose_webhook_signature` management command
- Created comprehensive fix guide (WEBHOOK_SIGNATURE_FIX.md)

---

## 📋 What You Need to Do

### Step 1: Get Your Webhook Secret
Contact Embedly support or check your Embedly dashboard to get your webhook secret.

### Step 2: Add to Environment
Add this line to your `.env` file:
```bash
EMBEDLY_WEBHOOK_SECRET=your_actual_webhook_secret_here
```

### Step 3: Restart Application
```bash
# Development
python manage.py runserver

# Production
sudo systemctl restart gunicorn  # or your process manager
```

### Step 4: Test (Optional)
```bash
# Check configuration
python manage.py check_webhook_config

# Run diagnostics
python manage.py diagnose_webhook_signature

# Test webhook endpoint
python manage.py test_webhook_endpoint
```

---

## 🔍 Important Notes

**The webhook secret might be:**
- A dedicated webhook signing secret from Embedly
- Your API key (if Embedly uses it for signing)
- Your organization ID (less common)

**Ask Embedly support which value to use!**

---

## 📊 How to Verify It's Working

### Before Fix
```
ERROR: Embedly deposit webhook signature mismatch
```

### After Fix
```
INFO: Successfully credited 1000 to wallet 1234567890 for user user@example.com
```

### Check Logs
```bash
# Look for successful webhook processing
tail -f /var/log/django/app.log | grep "Successfully credited"

# Or check for remaining signature errors
tail -f /var/log/django/error.log | grep "signature mismatch"
```

---

## 🆘 Still Having Issues?

### 1. Run Diagnostics
```bash
python manage.py diagnose_webhook_signature
```

### 2. Check Enhanced Logs
The webhook now logs detailed information including:
- Which signature header was received
- Which secrets were tried
- Request headers and body preview

### 3. Contact Embedly Support
Ask them for:
- The correct webhook secret
- Which HTTP header they use for signatures (`X-Auth-Signature`, `x-embedly-signature`, etc.)
- Which algorithm they use (SHA256, SHA512, etc.)

### 4. Verify Webhook URL
Ensure this URL is configured in Embedly dashboard:
```
https://app.gidinest.com/api/v1/wallet/embedly/webhook/secure
```

---

## 📁 Files Modified

| File | Change |
|------|--------|
| `gidinest_backend/settings.py` | Added `EMBEDLY_WEBHOOK_SECRET` config |
| `wallet/views.py` | Enhanced signature error logging |
| `wallet/management/commands/diagnose_webhook_signature.py` | New diagnostic tool |
| `WEBHOOK_SIGNATURE_FIX.md` | Comprehensive troubleshooting guide |

---

## ⏭️ Next Steps After Fix

1. ✅ Add `EMBEDLY_WEBHOOK_SECRET` to `.env`
2. ✅ Restart application
3. ✅ Test webhook with a deposit
4. ✅ Monitor logs for successful deposits
5. ✅ Set up alerting for webhook failures (optional)

---

**For detailed troubleshooting, see:** `WEBHOOK_SIGNATURE_FIX.md`
