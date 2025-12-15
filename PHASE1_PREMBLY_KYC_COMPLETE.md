# Phase 1 Complete: Prembly KYC Integration

**Completed:** 2025-12-15
**Status:** ✅ Ready for Testing
**Provider:** Prembly Identitypass API

---

## 🎉 What Was Implemented

### 1. ✅ Prembly Helper Functions
**File:** `providers/helpers/prembly.py`

- **`verify_bvn(bvn: str)`** - Line 6
  - Endpoint: `https://api.prembly.com/identitypass/verification/bvn`
  - Returns BVN details from Prembly

- **`verify_nin(nin, first_name, last_name, dob)`** - Line 62
  - Endpoint: `https://api.prembly.com/verification/vnin`
  - Returns NIN details from Prembly

### 2. ✅ V2 KYC Serializers
**File:** `account/serializers.py` (Lines 142-252)

- `V2BVNVerifySerializer` - Validates BVN input
- `V2BVNConfirmSerializer` - Validates BVN confirmation
- `V2NINVerifySerializer` - Validates NIN input
- `V2NINConfirmSerializer` - Validates NIN confirmation

### 3. ✅ V2 KYC Views (Prembly Integration)
**File:** `account/views_v2_kyc.py` (NEW)

- **`V2BVNVerifyView`** - Step 1: Verify BVN
  - Calls Prembly API
  - Caches result for 10 minutes
  - Returns BVN details for user review

- **`V2BVNConfirmView`** - Step 2: Confirm BVN
  - Saves BVN data to database
  - Updates account tier
  - Returns verification status

- **`V2NINVerifyView`** - Step 1: Verify NIN
  - Calls Prembly API
  - Caches result for 10 minutes
  - Returns NIN details for user review

- **`V2NINConfirmView`** - Step 2: Confirm NIN
  - Saves NIN data to database
  - Updates account tier
  - Returns verification status

### 4. ✅ Updated V2 URLs
**File:** `account/urls_v2_kyc.py`

- `POST /api/v2/kyc/bvn/verify` → V2BVNVerifyView
- `POST /api/v2/kyc/bvn/confirm` → V2BVNConfirmView
- `POST /api/v2/kyc/nin/verify` → V2NINVerifyView
- `POST /api/v2/kyc/nin/confirm` → V2NINConfirmView

---

## 📋 API Endpoints Reference

### BVN Verification Flow

#### Step 1: Verify BVN
**Endpoint:** `POST /api/v2/kyc/bvn/verify`

**Auth:** Required (Bearer token)

**Request:**
```json
{
  "bvn": "12345678901"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "details": {
      "first_name": "John",
      "last_name": "Doe",
      "middle_name": "William",
      "date_of_birth": "15-Jan-1990",
      "phone_number": "08012345678",
      "email": "john.doe@example.com",
      "gender": "Male",
      "state_of_residence": "Lagos",
      "enrollment_bank": "Access Bank",
      "watch_listed": "false"
    }
  }
}
```

**Error Response (400):**
```json
{
  "success": false,
  "error": {
    "code": "KYC_BVN_INVALID",
    "message": "Invalid BVN or BVN verification failed",
    "data": { /* additional error details */ }
  }
}
```

#### Step 2: Confirm BVN
**Endpoint:** `POST /api/v2/kyc/bvn/confirm`
**Auth:** Required (Bearer token)

**Request:**
```json
{
  "bvn": "12345678901",
  "confirmed": true
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "is_verified": true,
    "verification_method": "bvn",
    "verification_status": "verified",
    "account_tier": "Tier 1",
    "message": "BVN verified successfully! You now have Tier 1 access",
    "limits": {
      "daily_limit": 50000000,
      "per_transaction_limit": 20000000,
      "monthly_limit": 500000000
    }
  }
}
```

---

### NIN Verification Flow

#### Step 1: Verify NIN
**Endpoint:** `POST /api/v2/kyc/nin/verify`
**Auth:** Required (Bearer token)

**Request:**
```json
{
  "nin": "12345678901",
  "first_name": "John",
  "last_name": "Doe",
  "dob": "1990-01-15"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "details": {
      "first_name": "John",
      "last_name": "Doe",
      "middle_name": "William",
      "date_of_birth": "15-Jan-1990",
      "gender": "Male",
      "state_of_origin": "Lagos",
      "lga": "Ikeja",
      "address": "123 Main Street, Ikeja, Lagos",
      "phone": "08012345678"
    }
  }
}
```

#### Step 2: Confirm NIN
**Endpoint:** `POST /api/v2/kyc/nin/confirm`
**Auth:** Required (Bearer token)

**Request:**
```json
{
  "nin": "12345678901",
  "confirmed": true
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "is_verified": true,
    "verification_method": "nin",
    "verification_status": "verified",
    "account_tier": "Tier 2",
    "message": "Both BVN and NIN verified! You now have Tier 2 access",
    "limits": {
      "daily_limit": 100000000,
      "per_transaction_limit": 50000000,
      "monthly_limit": 1000000000
    }
  }
}
```

---

## 🔒 Error Codes

| Code | HTTP | Description | Action |
|------|------|-------------|--------|
| `VALIDATION_ERROR` | 400 | Invalid input data | Check request format |
| `KYC_BVN_INVALID` | 400 | Invalid BVN | Verify BVN is correct |
| `KYC_NIN_INVALID` | 400 | Invalid NIN | Verify NIN is correct |
| `KYC_BVN_ALREADY_VERIFIED` | 400 | BVN already verified | No action needed |
| `KYC_NIN_ALREADY_VERIFIED` | 400 | NIN already verified | No action needed |
| `KYC_BVN_DUPLICATE` | 400 | BVN used on another account | Use different BVN |
| `KYC_NIN_DUPLICATE` | 400 | NIN used on another account | Use different NIN |
| `KYC_SESSION_EXPIRED` | 400 | Verification session expired | Re-verify |
| `KYC_BVN_MISMATCH` | 400 | BVN doesn't match session | Re-verify |
| `KYC_NIN_MISMATCH` | 400 | NIN doesn't match session | Re-verify |
| `SERVER_ERROR` | 500 | Server error | Retry later |

---

## 🧪 Testing Guide

### Prerequisites
1. **Prembly API Key** configured in environment:
   ```bash
   PREMBLY_API_KEY=your_prembly_api_key
   ```

2. **Django cache** configured (default or Redis)

3. **Test user account** with JWT authentication

### Manual Testing Steps

#### Test BVN Verification

**Step 1: Verify BVN**
```bash
curl -X POST http://localhost:8000/api/v2/kyc/bvn/verify \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bvn": "12345678901"
  }'
```

**Expected:**
- 200 OK with BVN details
- Data cached for 10 minutes

**Step 2: Confirm BVN**
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
- Account tier updated
- BVN data saved to database

#### Test NIN Verification

**Step 1: Verify NIN**
```bash
curl -X POST http://localhost:8000/api/v2/kyc/nin/verify \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nin": "12345678901",
    "first_name": "John",
    "last_name": "Doe",
    "dob": "1990-01-15"
  }'
```

**Step 2: Confirm NIN**
```bash
curl -X POST http://localhost:8000/api/v2/kyc/nin/confirm \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nin": "12345678901",
    "confirmed": true
  }'
```

### Edge Cases to Test

1. **Session Expiration**
   - Verify BVN
   - Wait 11 minutes
   - Try to confirm → Should get `KYC_SESSION_EXPIRED`

2. **Duplicate BVN/NIN**
   - Verify and confirm BVN for User A
   - Try to verify same BVN for User B → Should get `KYC_BVN_DUPLICATE`

3. **Already Verified**
   - Verify and confirm BVN
   - Try to verify again → Should get `KYC_BVN_ALREADY_VERIFIED`

4. **Invalid BVN/NIN**
   - Use test BVN: "00000000000"
   - Should get error from Prembly

5. **Mismatched BVN in Confirm**
   - Verify with BVN "12345678901"
   - Confirm with BVN "98765432109" → Should get `KYC_BVN_MISMATCH`

---

## 🔍 Implementation Details

### Caching Strategy
- **Cache Key:** `bvn_verification_{user.id}` or `nin_verification_{user.id}`
- **Timeout:** 10 minutes (600 seconds)
- **Data Stored:**
  ```python
  {
    "bvn": "12345678901",
    "verification_data": { /* Prembly response */ },
    "timestamp": "2025-12-15T10:30:00"
  }
  ```

### Account Tier Logic
- **Tier 0 (Default):** No verification
- **Tier 1:** BVN **OR** NIN verified
  - Daily: NGN 50M
  - Per transaction: NGN 20M
  - Monthly: NGN 500M

- **Tier 2:** BVN **AND** NIN verified
  - Daily: NGN 100M
  - Per transaction: NGN 50M
  - Monthly: NGN 1B

### Database Fields Updated

**BVN Confirmation:**
- `bvn`
- `bvn_first_name`
- `bvn_last_name`
- `bvn_dob`
- `bvn_gender`
- `bvn_phone`
- `bvn_marital_status`
- `bvn_nationality`
- `bvn_residential_address`
- `bvn_state_of_residence`
- `bvn_watch_listed`
- `bvn_enrollment_bank`
- `has_bvn` = True
- `account_tier`
- `image` (if not already set)

**NIN Confirmation:**
- `nin`
- `nin_first_name`
- `nin_last_name`
- `nin_dob`
- `nin_gender`
- `nin_phone`
- `nin_marital_status`
- `nin_nationality`
- `nin_residential_address`
- `nin_state_of_residence`
- `has_nin` = True
- `account_tier`

---

## 🚀 Deployment Checklist

Before deploying to production:

- [ ] Set `PREMBLY_API_KEY` in production environment
- [ ] Test all 4 endpoints in staging
- [ ] Verify cache is working (Redis recommended for production)
- [ ] Test with real Prembly credentials
- [ ] Update V2 API documentation
- [ ] Set up error monitoring for Prembly API calls
- [ ] Configure rate limiting for KYC endpoints
- [ ] Test mobile app integration
- [ ] Verify account tier logic
- [ ] Test session expiration
- [ ] Load test with multiple concurrent verifications

---

## 📊 Monitoring & Logging

All views log important events:

**Info Logs:**
- `Verifying BVN for user {email} via Prembly`
- `BVN verification successful for {email}, data cached`
- `BVN confirmed and saved for user {email}, tier: {tier}`

**Error Logs:**
- `Prembly BVN verification failed for {email}: {error}`
- `Error saving BVN for user {email}: {error}`

**Monitor these in production:**
- Prembly API response times
- Verification success/failure rates
- Cache hit/miss rates
- Session expiration occurrences

---

## 🔧 Configuration Required

**Environment Variables:**
```bash
# Prembly API Key
PREMBLY_API_KEY=your_prembly_api_key

# Cache (Redis recommended for production)
REDIS_URL=redis://localhost:6379/0
```

**Django Settings:**
```python
# Cache configuration (in settings.py)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    }
}
```

---

## ✅ Phase 1 Complete!

**What's Working:**
- ✅ BVN verification with Prembly
- ✅ NIN verification with Prembly
- ✅ Two-step verification flow
- ✅ Session management with cache
- ✅ Account tier upgrades
- ✅ Duplicate checking
- ✅ Error handling
- ✅ Comprehensive logging

**What's Next (Phase 2):**
- ❌ 9PSB integration for wallet creation
- ❌ 9PSB deposit handling
- ❌ 9PSB withdrawal functionality
- ❌ 9PSB transaction history

**Ready for:**
- Mobile app integration
- Staging testing
- Production deployment (after 9PSB Phase 2)

---

## 📞 Support

**Issues or Questions?**
- Check logs for detailed error messages
- Verify Prembly API key is valid
- Ensure cache is configured correctly
- Test with Prembly sandbox first

**Next Steps:**
- Await 9PSB API documentation for Phase 2
- Begin mobile app integration testing
- Set up staging environment testing

---

**Phase 1 Status:** ✅ COMPLETE
**Phase 2 Status:** ⏳ Awaiting 9PSB documentation
