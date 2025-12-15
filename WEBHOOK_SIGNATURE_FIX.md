# Fixing Embedly Webhook Signature Mismatch

## Problem
The Embedly deposit webhook is failing with a **"signature mismatch"** error. This happens because the webhook secret is not properly configured.

## Root Cause
The `EMBEDLY_WEBHOOK_SECRET` environment variable was missing from the configuration. Without this secret, the webhook handler cannot properly verify that incoming webhooks are genuinely from Embedly.

## Solution

### 1. Get Your Webhook Secret from Embedly

Contact Embedly support or check your Embedly dashboard to get:
- **Webhook Secret** (also called "Webhook Signing Secret" or "API Secret")
- This is different from your API Key

The webhook secret is used by Embedly to sign webhook payloads. You need this to verify webhook authenticity.

### 2. Add the Secret to Your Environment Variables

Add the following to your `.env` file (create one if it doesn't exist):

```bash
EMBEDLY_WEBHOOK_SECRET=your_webhook_secret_here
```

**Alternative locations to check:**
- Some Embedly implementations use the API key as the webhook secret
- Some use the organization ID
- Check with Embedly support to confirm which value to use

### 3. Restart Your Application

After adding the environment variable:

```bash
# Stop your Django server
# Restart it to load the new environment variable
python manage.py runserver
```

For production (using gunicorn/uwsgi):
```bash
# Restart your application server
sudo systemctl restart gunicorn  # or your process manager
```

### 4. Verify Configuration

Run the webhook configuration checker:

```bash
python manage.py check_webhook_config
```

This will show you which secrets are configured and provide guidance.

### 5. Test the Webhook

Test the webhook endpoint locally:

```bash
python manage.py test_webhook_endpoint
```

This will:
- Generate a test webhook payload
- Create a proper signature
- Send it to your webhook endpoint
- Show you the response

## How It Works

### Webhook Signature Verification

When Embedly sends a webhook:

1. **Embedly creates a signature** using HMAC-SHA256 (or SHA512):
   ```
   signature = HMAC-SHA256(webhook_secret, request_body)
   ```

2. **Embedly sends the signature in a header**:
   - Usually: `X-Auth-Signature`
   - Sometimes: `x-embedly-signature`

3. **Your server verifies the signature**:
   - Computes the signature using your stored webhook secret
   - Compares it with the signature Embedly sent
   - If they match, the webhook is authentic

### Current Implementation

The webhook handler (in `wallet/views.py:885-1078`) tries multiple secrets in order:

1. `EMBEDLY_WEBHOOK_SECRET` ← **Primary (add this!)**
2. `EMBEDLY_WEBHOOK_KEY` ← Alternative
3. `EMBEDLY_API_KEY_PRODUCTION` ← Fallback
4. `EMBEDLY_ORGANIZATION_ID_PRODUCTION` ← Fallback

It also tries both SHA256 and SHA512 algorithms for compatibility.

## Enhanced Debugging

The webhook handler now logs detailed information when signatures fail:

- Which signature header was used
- Signature length and preview
- Which secrets were tried
- All HTTP headers received
- Request body preview

Check your logs to see exactly what's failing:

```bash
# View recent webhook errors
tail -f /var/log/django/error.log | grep "signature mismatch"
```

## Common Issues

### Issue 1: Wrong Secret
**Symptom:** Signature always fails
**Solution:** Verify you're using the correct webhook secret from Embedly (not the API key)

### Issue 2: Wrong Header
**Symptom:** "Missing signature" error
**Solution:** Check logs to see which header Embedly is using, update code if needed

### Issue 3: Wrong Algorithm
**Symptom:** Signature fails even with correct secret
**Solution:** Current code tries both SHA256 and SHA512. If Embedly uses a different algorithm, contact support.

### Issue 4: Body Encoding
**Symptom:** Signature fails intermittently
**Solution:** Ensure webhook body is read as UTF-8 (already implemented in `wallet/views.py:734`)

## Testing Checklist

- [ ] `EMBEDLY_WEBHOOK_SECRET` added to `.env`
- [ ] Application restarted
- [ ] `python manage.py check_webhook_config` shows secret is configured
- [ ] `python manage.py test_webhook_endpoint` returns 200 OK
- [ ] Test deposit from Embedly dashboard works
- [ ] Webhook logs show successful verification

## Support

If you're still experiencing issues:

1. **Check the enhanced logs** - they now show exactly which secrets were tried
2. **Contact Embedly support** - ask for:
   - The correct webhook secret to use
   - Which signature header they send (`X-Auth-Signature`, `x-embedly-signature`, etc.)
   - Which hashing algorithm they use (SHA256, SHA512, etc.)
3. **Verify webhook URL** in Embedly dashboard:
   - Should be: `https://app.gidinest.com/api/v1/wallet/embedly/webhook/secure`

## Files Modified

- ✅ `gidinest_backend/settings.py:417` - Added `EMBEDLY_WEBHOOK_SECRET` configuration
- ✅ `wallet/views.py:944-980` - Enhanced error logging for signature mismatches

## Next Steps

After fixing the webhook signature issue:

1. Monitor webhook logs to ensure deposits are processing correctly
2. Test a real deposit to verify end-to-end flow
3. Consider setting up webhook monitoring/alerting for production
