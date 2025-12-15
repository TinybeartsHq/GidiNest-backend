# 9PSB Integration Testing Guide

**Last Updated:** 2025-12-15
**Environment:** Test/Sandbox

---

## 🚀 Quick Start

### 1. Configure Environment Variables

Add these to your `.env` file:

```bash
# 9PSB Test Credentials
PSB9_USERNAME=gidinest
PSB9_PASSWORD=RN7aXaCxGjCF3bj3L3ocNxWwQ6jvFGsWF9AG5CY2cg3aQyGagl
PSB9_CLIENT_ID=waas
PSB9_CLIENT_SECRET=cRAwnWElcNMUZpALdnlve6PubUkCPOQR
PSB9_BASE_URL=http://102.216.128.75:9090

# Prembly (if not already set)
PREMBLY_API_KEY=your_prembly_key
```

### 2. Run Database Migration

```bash
python manage.py makemigrations wallet
python manage.py migrate
```

### 3. Start Django Server

```bash
python manage.py runserver
```

---

## 🧪 Test Authentication

### Test 9PSB Authentication Directly

```bash
curl -X POST http://102.216.128.75:9090/bank9ja/api/v2/k1/authenticate \
  -H "Content-Type: application/json" \
  -d '{
    "username": "gidinest",
    "password": "RN7aXaCxGjCF3bj3L3ocNxWwQ6jvFGsWF9AG5CY2cg3aQyGagl",
    "clientId": "waas",
    "clientSecret": "cRAwnWElcNMUZpALdnlve6PubUkCPOQR"
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 3600
  }
}
```

### Test Authentication via Django

Open Django shell:
```bash
python manage.py shell
```

Run:
```python
from providers.helpers.psb9 import psb9_client

# Test authentication
token = psb9_client.authenticate()
print(f"Token: {token[:50]}..." if token else "Authentication failed")

# Check credentials
print(f"Username: {psb9_client.username}")
print(f"Client ID: {psb9_client.client_id}")
print(f"Base URL: {psb9_client.base_url}")
```

---

## 🔐 Test Complete KYC + Wallet Creation Flow

### Step 1: Register User (if needed)

```bash
curl -X POST http://localhost:8000/api/v2/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User",
    "phone": "08012345678"
  }'
```

Save the `access_token` from the response.

### Step 2: Verify BVN with Prembly

```bash
curl -X POST http://localhost:8000/api/v2/kyc/bvn/verify \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bvn": "22222222222"
  }'
```

**Expected:** BVN details returned from Prembly

### Step 3: Confirm BVN (Creates 9PSB Wallet)

```bash
curl -X POST http://localhost:8000/api/v2/kyc/bvn/confirm \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bvn": "22222222222",
    "confirmed": true
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "is_verified": true,
    "verification_method": "bvn",
    "account_tier": "Tier 1",
    "message": "BVN verified successfully! You now have Tier 1 access",
    "limits": {
      "daily_limit": 50000000,
      "per_transaction_limit": 20000000,
      "monthly_limit": 500000000
    },
    "wallet": {
      "created": true,
      "account_number": "0123456789",
      "bank": "9PSB",
      "message": "Virtual wallet created successfully! You can now receive deposits."
    }
  }
}
```

**What Happens:**
1. ✅ BVN saved to user model
2. ✅ Account tier upgraded to Tier 1
3. ✅ 9PSB authenticates with credentials
4. ✅ 9PSB wallet created for user
5. ✅ Wallet details saved to database

### Step 4: Verify Wallet Creation

Check Django shell:
```python
from wallet.models import Wallet
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(email='testuser@example.com')

# Check user verification
print(f"Has BVN: {user.has_bvn}")
print(f"Account Tier: {user.account_tier}")

# Check wallet
wallet = user.wallet
print(f"Provider: {wallet.provider_version}")
print(f"9PSB Account: {wallet.psb9_account_number}")
print(f"9PSB Customer ID: {wallet.psb9_customer_id}")
print(f"Balance: {wallet.balance}")
```

---

## 💰 Test Deposit via Webhook

### Option 1: Manual Webhook Call

Generate signature:
```bash
SECRET="cRAwnWElcNMUZpALdnlve6PubUkCPOQR"
PAYLOAD='{"event":"transfer.credit","data":{"reference":"TEST_001","accountNumber":"0123456789","amount":10000.00,"narration":"Test deposit","senderName":"Test Sender"}}'
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" -hex | awk '{print $2}')

curl -X POST http://localhost:8000/api/wallet/9psb/webhook \
  -H "Content-Type: application/json" \
  -H "X-9PSB-Signature: $SIGNATURE" \
  -d "$PAYLOAD"
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Deposit processed successfully",
  "data": {
    "reference": "TEST_001",
    "account_number": "0123456789",
    "amount": "10000.00",
    "new_balance": "10000.00",
    "transaction_id": "uuid",
    "status": "success"
  }
}
```

### Option 2: Python Script

Create `test_webhook.py`:
```python
import requests
import json
import hmac
import hashlib

BASE_URL = "http://localhost:8000"
CLIENT_SECRET = "cRAwnWElcNMUZpALdnlve6PubUkCPOQR"

payload = {
    "event": "transfer.credit",
    "data": {
        "reference": "TEST_WEBHOOK_001",
        "accountNumber": "0123456789",  # Replace with actual account number
        "accountName": "Test User",
        "amount": 5000.00,
        "narration": "Test deposit via script",
        "senderName": "John Doe",
        "senderAccount": "9876543210",
        "senderBank": "GTBank",
        "transactionDate": "2025-12-15T10:30:00Z"
    }
}

# Generate signature
payload_str = json.dumps(payload, separators=(',', ':'))
signature = hmac.new(
    CLIENT_SECRET.encode('utf-8'),
    payload_str.encode('utf-8'),
    hashlib.sha256
).hexdigest()

# Send webhook
response = requests.post(
    f"{BASE_URL}/api/wallet/9psb/webhook",
    json=payload,
    headers={
        "Content-Type": "application/json",
        "X-9PSB-Signature": signature
    }
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

Run:
```bash
python test_webhook.py
```

### Option 3: Using 9PSB Test Account

Transfer money to your virtual account number from the test debit account:
- **Test Debit Account:** `1100011303`
- **Your Account:** (from wallet creation response)

9PSB should automatically send a webhook to your endpoint when the transfer completes.

---

## 🔍 Verify Deposit

### Check Wallet Balance

```bash
curl -X GET http://localhost:8000/api/v2/wallet/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected:**
```json
{
  "success": true,
  "data": {
    "wallet": {
      "balance": "10000.00",
      "account_number": "0123456789",
      "bank": "9PSB",
      "currency": "NGN"
    },
    "savings_goals": [],
    "transaction_pin_set": false
  }
}
```

### Check Transaction History

Django shell:
```python
from wallet.models import WalletTransaction

# Get recent transactions
transactions = WalletTransaction.objects.filter(
    wallet__user__email='testuser@example.com'
).order_by('-created_at')

for txn in transactions:
    print(f"{txn.transaction_type}: {txn.amount} - {txn.description}")
    print(f"Reference: {txn.external_reference}")
    print(f"Date: {txn.created_at}")
    print("---")
```

---

## ⚠️ Troubleshooting

### Authentication Fails

**Error:** "9PSB credentials missing"

**Solution:**
1. Check `.env` file has all 4 credentials:
   - PSB9_USERNAME
   - PSB9_PASSWORD
   - PSB9_CLIENT_ID
   - PSB9_CLIENT_SECRET

2. Restart Django server after updating `.env`

3. Verify credentials in Django shell:
   ```python
   from django.conf import settings
   print(settings.PSB9_USERNAME)
   print(settings.PSB9_CLIENT_ID)
   print(settings.PSB9_BASE_URL)
   ```

### Wallet Creation Fails

**Error:** "Failed to create 9PSB wallet"

**Possible Causes:**
1. 9PSB server unreachable (check IP: `102.216.128.75:9090`)
2. Authentication failed (check credentials)
3. Invalid customer data (missing required fields)

**Debug:**
```python
from providers.helpers.psb9 import psb9_client

# Test authentication
token = psb9_client.authenticate()
if not token:
    print("Authentication failed!")
else:
    print(f"Token received: {token[:20]}...")

    # Test wallet creation
    customer_data = {
        "firstName": "Test",
        "lastName": "User",
        "phoneNumber": "08012345678",
        "email": "test@example.com",
        "bvn": "12345678901",
        "gender": "M",
        "dateOfBirth": "1990-01-15",
        "address": "123 Test Street, Lagos"
    }

    result = psb9_client.open_wallet(customer_data)
    print(result)
```

### Webhook Signature Invalid

**Error:** "Invalid webhook signature"

**Possible Causes:**
1. Using wrong secret (should be `PSB9_CLIENT_SECRET`)
2. Payload modified after signing
3. Different JSON formatting

**Debug:**
```python
import hmac
import hashlib
import json

CLIENT_SECRET = "cRAwnWElcNMUZpALdnlve6PubUkCPOQR"

# Your payload
payload = {"event": "transfer.credit", "data": {...}}

# Generate signature (exact format matters!)
payload_str = json.dumps(payload, separators=(',', ':'))
signature = hmac.new(
    CLIENT_SECRET.encode('utf-8'),
    payload_str.encode('utf-8'),
    hashlib.sha256
).hexdigest()

print(f"Signature: {signature}")
```

### Network Issues

**Error:** Connection timeout to `102.216.128.75:9090`

**Solution:**
1. Check your server can access the IP:
   ```bash
   curl http://102.216.128.75:9090/bank9ja/api/v2/k1/authenticate
   ```

2. May need to whitelist your IP with 9PSB

3. Check firewall rules

---

## 📊 Monitor Logs

Watch Django logs for 9PSB activity:

```bash
# In Django settings, ensure logging is configured
# Then watch logs:
tail -f /path/to/django.log | grep "9PSB"
```

Key log messages:
- ✅ "Authenticating with 9PSB WAAS API"
- ✅ "9PSB authentication successful"
- ✅ "Creating 9PSB wallet for user {email}"
- ✅ "9PSB wallet created successfully"
- ✅ "9PSB webhook: Signature verified successfully"
- ✅ "9PSB webhook: Deposit processed successfully"

---

## ✅ Success Checklist

- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] Can authenticate with 9PSB directly
- [ ] BVN verification works (Prembly)
- [ ] Wallet created after BVN confirm
- [ ] Wallet has 9PSB account number
- [ ] Webhook signature verified
- [ ] Test deposit credited wallet
- [ ] Transaction record created
- [ ] User received notification
- [ ] Balance updated correctly

---

## 🚀 Ready for Production

Once all tests pass:

1. **Get Production Credentials** from 9PSB
2. **Update Environment:**
   ```bash
   PSB9_USERNAME=production_username
   PSB9_PASSWORD=production_password
   PSB9_CLIENT_ID=production_client_id
   PSB9_CLIENT_SECRET=production_client_secret
   PSB9_BASE_URL=https://production.9psb.com.ng  # Update with actual production URL
   ```

3. **Register Webhook** with 9PSB:
   - URL: `https://yourdomain.com/api/wallet/9psb/webhook`
   - Method: POST
   - Signature: HMAC-SHA256 via `X-9PSB-Signature` header

4. **Test in Staging** first with production credentials

5. **Deploy to Production**

---

**Happy Testing!** 🎉
