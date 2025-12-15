# Phase 2 Complete: 9PSB Wallet Integration

**Completed:** 2025-12-15
**Status:** ✅ Ready for Testing
**Provider:** 9 Payment Service Bank (9PSB)

---

## 🎉 What Was Implemented

### 1. ✅ 9PSB API Client Helper
**File:** `providers/helpers/psb9.py`

Complete client for 9PSB Wallet-as-a-Service API with the following methods:

- **`authenticate()`** - Get bearer token (auto-cached for 50 minutes)
- **`open_wallet(customer_data)`** - Create new wallet account
- **`get_wallet_balance(account_number)`** - Query wallet balance
- **`get_transaction_history(account_number, ...)`** - Retrieve transactions
- **`initiate_transfer(from_account, to_account, ...)`** - Send money to bank
- **`verify_account(account_number, bank_code)`** - Verify recipient details
- **`upgrade_account_tier(account_number, tier, kyc_data)`** - Upgrade to Tier 2/3
- **`get_wallet_status(account_number)`** - Get wallet information

**Authentication:** Automatic token management with Django cache

### 2. ✅ 9PSB Configuration
**File:** `gidinest_backend/settings.py` (Lines 191-195)

Environment variables added:
```python
PSB9_API_KEY = os.getenv('PSB9_API_KEY', config('PSB9_API_KEY', default=''))
PSB9_API_SECRET = os.getenv('PSB9_API_SECRET', config('PSB9_API_SECRET', default=''))
PSB9_BASE_URL = os.getenv('PSB9_BASE_URL', config('PSB9_BASE_URL', default='https://api.9psb.com.ng'))
PSB9_MERCHANT_ID = os.getenv('PSB9_MERCHANT_ID', config('PSB9_MERCHANT_ID', default=''))
```

### 3. ✅ Wallet Model Updates
**File:** `wallet/models.py` (Lines 62-87)

New fields added for dual-mode operation (V1 + V2):

**Dual-Mode Support:**
- `provider_version` - Indicates if wallet uses Embedly (v1) or 9PSB (v2)

**9PSB-Specific Fields:**
- `psb9_customer_id` - 9PSB customer identifier
- `psb9_account_number` - 10-digit account number (unique)
- `psb9_wallet_id` - 9PSB wallet identifier

### 4. ✅ Integrated Wallet Creation
**File:** `account/views_v2_kyc.py` (Lines 221-269)

**V2BVNConfirmView** now automatically:
1. Creates 9PSB customer account after BVN verification
2. Opens virtual wallet with 9PSB
3. Stores account details in wallet model
4. Returns wallet info in response

**Response Enhancement:**
```json
{
  "success": true,
  "data": {
    "is_verified": true,
    "verification_method": "bvn",
    "account_tier": "Tier 1",
    "message": "BVN verified successfully! You now have Tier 1 access",
    "limits": { ... },
    "wallet": {
      "created": true,
      "account_number": "0123456789",
      "bank": "9PSB",
      "message": "Virtual wallet created successfully! You can now receive deposits."
    }
  }
}
```

### 5. ✅ 9PSB Webhook Handler
**File:** `wallet/views_v2.py` (Lines 408-625)

**PSB9WebhookView** handles deposit notifications:

**Features:**
- HMAC-SHA256 signature verification
- Duplicate transaction detection
- Automatic wallet crediting
- Transaction record creation
- Push notifications
- In-app notifications
- Comprehensive logging

**Endpoint:** `POST /api/wallet/9psb/webhook`

**Expected Payload:**
```json
{
  "event": "transfer.credit",
  "data": {
    "reference": "PSB9_TXN_123456",
    "accountNumber": "0123456789",
    "accountName": "John Doe",
    "amount": 10000.00,
    "narration": "Transfer from GTBank",
    "senderName": "Jane Smith",
    "senderAccount": "9876543210",
    "transactionDate": "2025-12-15T10:30:00Z"
  }
}
```

**Security:** Webhook signature header `X-9PSB-Signature` or `X-Webhook-Signature`

### 6. ✅ URL Configuration
**File:** `wallet/urls.py` (Line 42)

New webhook route:
```python
path('9psb/webhook', PSB9WebhookView.as_view(), name='9psb-webhook'),
```

---

## 📋 Complete V2 User Journey

```
1. User registers (OAuth or email)
   ↓
2. User completes profile
   ↓
3. BVN Verification (Prembly)
   POST /api/v2/kyc/bvn/verify → Returns BVN details
   POST /api/v2/kyc/bvn/confirm → Saves to DB
   ↓
4. Wallet Creation (9PSB) ✅ AUTOMATIC
   - Wallet created immediately after BVN confirm
   - User receives account number
   - Ready to receive deposits
   ↓
5. Deposits (9PSB Webhook) ✅
   - User transfers to their account number
   - 9PSB sends webhook notification
   - Wallet automatically credited
   - User receives push notification
   ↓
6. Optional: NIN Verification (Tier 2 Upgrade)
   POST /api/v2/kyc/nin/verify
   POST /api/v2/kyc/nin/confirm
   - Upgrades to Tier 2 (higher limits)
```

---

## 🔧 9PSB API Endpoints Used

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `POST /waas/api/v1/authenticate` | Get bearer token | ✅ Implemented |
| `POST /waas/api/v1/open_wallet` | Create wallet | ✅ Implemented |
| `POST /waas/api/v1/wallet/enquiry` | Get balance | ✅ Implemented |
| `POST /waas/api/v1/wallet/transactions` | Transaction history | ✅ Implemented |
| `POST /waas/api/v1/wallet/transfer` | Initiate transfer | ✅ Implemented |
| `POST /waas/api/v1/verify_account` | Verify recipient | ✅ Implemented |
| `POST /waas/api/v1/upgrade_account` | Upgrade tier | ✅ Implemented |
| `POST /waas/api/v1/wallet/status` | Wallet status | ✅ Implemented |

**Webhook:** 9PSB sends POST requests to `/api/wallet/9psb/webhook`

---

## 🧪 Testing Guide

### Prerequisites

1. **9PSB Credentials** configured in environment:
   ```bash
   PSB9_API_KEY=your_9psb_api_key
   PSB9_API_SECRET=your_9psb_api_secret
   PSB9_BASE_URL=https://sandbox.9psb.com.ng  # or production URL
   PSB9_MERCHANT_ID=your_merchant_id
   ```

2. **Database migration** for new wallet fields:
   ```bash
   python manage.py makemigrations wallet
   python manage.py migrate
   ```

3. **Django cache** configured (default or Redis)

4. **Test user account** with JWT authentication

### Manual Testing Steps

#### Test Complete V2 Flow

**Step 1: Verify BVN (Prembly)**
```bash
curl -X POST http://localhost:8000/api/v2/kyc/bvn/verify \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"bvn": "12345678901"}'
```

**Expected:** 200 OK with BVN details

**Step 2: Confirm BVN (Creates 9PSB Wallet)**
```bash
curl -X POST http://localhost:8000/api/v2/kyc/bvn/confirm \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bvn": "12345678901",
    "confirmed": true
  }'
```

**Expected:**
- 200 OK with verification status
- User `has_bvn` = True
- Account tier = "Tier 1"
- Wallet created with 9PSB
- Response includes wallet account number

**Step 3: Test Deposit via Webhook**

Simulate 9PSB webhook (in production, 9PSB sends this automatically):

```bash
# Generate signature
SECRET="your_9psb_api_secret"
PAYLOAD='{"event":"transfer.credit","data":{"reference":"TEST_TXN_001","accountNumber":"0123456789","amount":10000.00,"narration":"Test deposit","senderName":"Test User"}}'
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" -hex | awk '{print $2}')

curl -X POST http://localhost:8000/api/wallet/9psb/webhook \
  -H "Content-Type: application/json" \
  -H "X-9PSB-Signature: $SIGNATURE" \
  -d "$PAYLOAD"
```

**Expected:**
- 200 OK
- Wallet credited with 10,000 NGN
- Transaction record created
- User receives notification

**Step 4: Check Wallet Balance**
```bash
curl -X GET http://localhost:8000/api/v2/wallet/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected:**
- Wallet balance shows deposited amount
- Account number displayed
- Bank = "9PSB"

### Edge Cases to Test

1. **Authentication Token Caching**
   - First 9PSB API call gets new token
   - Subsequent calls use cached token
   - Token refreshes after 50 minutes

2. **Duplicate Webhook**
   - Send same webhook twice
   - Second request should return "duplicate" status
   - Wallet not credited twice

3. **Invalid Webhook Signature**
   - Send webhook with wrong signature
   - Should return 401 Unauthorized

4. **Wallet Already Exists**
   - Verify BVN for user who already has wallet
   - Should not create duplicate wallet
   - Should update existing wallet to V2

5. **9PSB API Failure**
   - If 9PSB is down during wallet creation
   - BVN confirmation still succeeds
   - User can retry wallet creation later

---

## 🔒 Security Features

### Webhook Signature Verification

9PSB webhook handler verifies every request using HMAC-SHA256:

```python
expected_signature = hmac.new(
    PSB9_API_SECRET.encode('utf-8'),
    raw_body.encode('utf-8'),
    hashlib.sha256
).hexdigest()

if not hmac.compare_digest(expected_signature, signature_header):
    return 401 Unauthorized
```

### Authentication Token Management

- Tokens cached for 50 minutes
- Automatic refresh before expiry
- Secure storage in Django cache

### Transaction Safety

- Database transactions for atomic operations
- Duplicate detection by external reference
- Balance checks before withdrawals

---

## 📊 Database Schema Changes

### Wallet Model Additions

```sql
ALTER TABLE wallet ADD COLUMN provider_version VARCHAR(10) DEFAULT 'v1';
ALTER TABLE wallet ADD COLUMN psb9_customer_id VARCHAR(255) NULL;
ALTER TABLE wallet ADD COLUMN psb9_account_number VARCHAR(20) NULL UNIQUE;
ALTER TABLE wallet ADD COLUMN psb9_wallet_id VARCHAR(255) NULL;
```

**Migration:** Run `python manage.py migrate wallet` after deployment

---

## 🚀 Deployment Checklist

Before deploying to production:

### Environment Configuration
- [ ] Set `PSB9_API_KEY` in production environment
- [ ] Set `PSB9_API_SECRET` in production environment
- [ ] Set `PSB9_BASE_URL` to production URL
- [ ] Set `PSB9_MERCHANT_ID` in production environment

### Database
- [ ] Run wallet migrations (`python manage.py migrate wallet`)
- [ ] Verify new fields exist in database

### Testing
- [ ] Test BVN verification in staging
- [ ] Test wallet creation in staging
- [ ] Test webhook with 9PSB sandbox
- [ ] Verify webhook signature validation
- [ ] Test duplicate webhook handling
- [ ] Test deposit flow end-to-end

### 9PSB Configuration
- [ ] Register webhook URL with 9PSB: `https://yourdomain.com/api/wallet/9psb/webhook`
- [ ] Verify webhook signature header name
- [ ] Test webhook from 9PSB sandbox
- [ ] Configure 9PSB IP whitelist (if required)

### Monitoring
- [ ] Set up error monitoring for 9PSB API calls
- [ ] Configure alerts for webhook failures
- [ ] Monitor authentication token refresh
- [ ] Track wallet creation success rate

### Documentation
- [ ] Update V2 API documentation
- [ ] Document webhook endpoint for 9PSB
- [ ] Create troubleshooting guide
- [ ] Update mobile app integration guide

---

## 🔄 Dual-Mode Operation

The system now supports both V1 (Embedly) and V2 (9PSB) simultaneously:

### V1 Users (Existing)
- Continue using Embedly
- Wallet model: `provider_version = 'v1'`
- Embedly webhook: `/api/wallet/embedly/webhook/secure`
- No changes to existing functionality

### V2 Users (New)
- Use Prembly + 9PSB
- Wallet model: `provider_version = 'v2'`
- 9PSB webhook: `/api/wallet/9psb/webhook`
- Enhanced features and better limits

### Shared Features
- Same wallet balance model
- Same transaction history
- Same withdrawal flow
- Same frontend views

---

## 📈 Account Tier Limits

### Tier 0 (No Verification)
- Limited access
- Cannot create wallet

### Tier 1 (BVN or NIN Verified)
- Daily limit: NGN 50,000,000
- Per transaction: NGN 20,000,000
- Monthly limit: NGN 500,000,000
- **Wallet creation:** ✅ Automatic after BVN confirm

### Tier 2 (BVN AND NIN Verified)
- Daily limit: NGN 100,000,000
- Per transaction: NGN 50,000,000
- Monthly limit: NGN 1,000,000,000
- **Account upgrade:** Can be done via 9PSB API

---

## 🔍 Implementation Details

### Wallet Creation Flow

**BVN Confirm View Logic:**

1. User confirms BVN details
2. Save BVN data to user model
3. Update account tier
4. **Check if wallet exists:**
   - If no wallet → Create new 9PSB wallet
   - If wallet exists but no 9PSB account → Create 9PSB wallet
   - If wallet exists with 9PSB account → Skip creation
5. Prepare customer data from BVN info
6. Call `psb9_client.open_wallet(customer_data)`
7. Store 9PSB account details in wallet model
8. Return response with wallet info

**Graceful Failure:**
- If 9PSB API fails, BVN confirmation still succeeds
- Wallet creation can be retried later
- User notified via logs and response

### Webhook Processing Flow

1. Receive POST request from 9PSB
2. Extract raw body and signature header
3. Verify HMAC-SHA256 signature
4. Parse webhook data
5. Check event type (only process `transfer.credit`)
6. Validate required fields
7. Check for duplicate transaction
8. Find wallet by 9PSB account number
9. Credit wallet atomically
10. Create transaction record
11. Send push notification
12. Create in-app notification
13. Return success response

---

## ⚠️ Known Limitations

1. **Withdrawal Processing:**
   - V2 withdrawals still use Embedly for now
   - Need to integrate 9PSB transfer API
   - Manual processing as fallback

2. **Transaction History:**
   - Can query 9PSB transaction history
   - Not yet displayed in mobile app
   - Requires frontend update

3. **Account Upgrades:**
   - Tier 2/3 upgrades to 9PSB not automated
   - NIN confirmation doesn't trigger 9PSB upgrade
   - Can be done manually via admin

---

## ✅ Phase 2 Complete!

**What's Working:**
- ✅ 9PSB API client with all methods
- ✅ Automatic wallet creation after BVN
- ✅ Webhook handling for deposits
- ✅ Push and in-app notifications
- ✅ Dual-mode operation (V1 + V2)
- ✅ Comprehensive error handling
- ✅ Signature verification
- ✅ Transaction safety

**What's Next (Phase 3 - Optional):**
- Integrate 9PSB transfers for V2 withdrawals
- Add transaction history from 9PSB
- Implement account upgrades to 9PSB
- Create admin dashboard for 9PSB operations
- Build reconciliation tools

**Ready for:**
- Staging deployment and testing
- 9PSB sandbox integration
- Mobile app integration
- Production deployment (after testing)

---

## 📞 Support

**Issues or Questions?**
- Check logs for detailed error messages
- Verify 9PSB credentials are valid
- Ensure webhook signature matches expected format
- Test with 9PSB sandbox first
- Check wallet model has new fields

**Common Issues:**

1. **"9PSB credentials missing"**
   - Solution: Set PSB9_API_KEY and PSB9_API_SECRET in environment

2. **"Invalid webhook signature"**
   - Solution: Verify 9PSB is using correct API secret
   - Check signature header name (X-9PSB-Signature or X-Webhook-Signature)

3. **"Wallet not found for account number"**
   - Solution: Ensure wallet was created successfully
   - Check psb9_account_number field is populated

4. **"Authentication failed"**
   - Solution: Verify API credentials are correct
   - Check base URL is correct (sandbox vs production)

---

## 📝 Migration Notes

### From Phase 1 to Phase 2

**Database Migration Required:** Yes
```bash
python manage.py makemigrations wallet
python manage.py migrate
```

**Environment Variables Added:**
- PSB9_API_KEY
- PSB9_API_SECRET
- PSB9_BASE_URL
- PSB9_MERCHANT_ID

**Backward Compatibility:** ✅ Yes
- V1 users unaffected
- Existing wallets continue working
- No breaking changes

**Rollback Plan:**
- Phase 2 changes are additive
- Can disable V2 by not confirming BVN
- V1 continues to work independently

---

**Phase 2 Status:** ✅ COMPLETE
**Phase 3 Status:** 📝 Optional Enhancements

**Last Updated:** 2025-12-15
