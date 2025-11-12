# Mobile App API Endpoints - Complete Reference

**Last Updated:** November 11, 2025
**Base URL:** `https://api.gidinest.com`
**Status:** Ready for Mobile Integration

This document lists all API endpoints available for the mobile application, using a hybrid V1/V2 approach for optimal functionality.

---

## 🔐 Authentication APIs (V2)

**Base URL:** `/api/v2/auth/`
**Status:** ✅ All endpoints fully implemented and ready

### Sign Up
```http
POST /api/v2/auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "password_confirmation": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "08012345678",
  "referral_code": "ABC123",        // optional
  "device_id": "unique_device_id",  // optional
  "device_name": "iPhone 14 Pro",   // optional
  "device_type": "ios",             // optional: ios, android, web
  "location": "Lagos, Nigeria"      // optional
}

Response: 201 Created
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "phone": "08012345678",
      "has_passcode": false,
      "has_pin": false,
      "is_verified": false,
      "verification_status": "pending",
      "account_tier": "Tier 1"
    },
    "tokens": {
      "access_token": "eyJ...",
      "refresh_token": "eyJ...",
      "expires_in": 3600
    }
  }
}
```

### Sign In (Email/Password)
```http
POST /api/v2/auth/signin
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "device_id": "unique_device_id",  // optional
  "device_name": "iPhone 14 Pro",   // optional
  "device_type": "ios",             // optional
  "location": "Lagos, Nigeria"      // optional
}

Response: 200 OK
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "has_passcode": true,
      "has_pin": true,
      "is_verified": true,
      "biometric_enabled": false,
      "verification_method": "bvn",
      "is_restricted": false
    },
    "tokens": {
      "access_token": "eyJ...",
      "refresh_token": "eyJ...",
      "expires_in": 3600
    }
  }
}
```

### Sign In (Passcode)
```http
POST /api/v2/auth/signin
Content-Type: application/json

{
  "email": "user@example.com",
  "passcode": "123456",
  "device_id": "unique_device_id",  // optional
  "device_name": "iPhone 14 Pro",   // optional
  "device_type": "ios",             // optional
  "location": "Lagos, Nigeria"      // optional
}

Response: 200 OK (same as above)
```

### Refresh Token
```http
POST /api/v2/auth/refresh
Content-Type: application/json

{
  "refresh": "eyJ..."
}

Response: 200 OK
{
  "access": "new_eyJ...",
  "refresh": "new_refresh_eyJ..."
}
```

### Logout
```http
POST /api/v2/auth/logout
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "refresh_token": "eyJ...",        // optional
  "device_id": "unique_device_id"   // optional
}

Response: 200 OK
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

## 🔑 Passcode Management (V2)

**Base URL:** `/api/v2/auth/passcode/`
**Status:** ✅ Fully implemented

### Setup Passcode
```http
POST /api/v2/auth/passcode/setup
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "passcode": "123456",
  "passcode_confirmation": "123456"
}

Response: 200 OK
{
  "success": true,
  "message": "Passcode set successfully",
  "data": {
    "has_passcode": true
  }
}
```

### Verify Passcode
```http
POST /api/v2/auth/passcode/verify
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "passcode": "123456"
}

Response: 200 OK
{
  "success": true,
  "data": {
    "verified": true
  }
}
```

### Change Passcode
```http
PUT /api/v2/auth/passcode/change
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "old_passcode": "123456",
  "new_passcode": "654987",
  "new_passcode_confirmation": "654987"
}

Response: 200 OK
{
  "success": true,
  "message": "Passcode changed successfully. Transaction limit restricted to ₦10,000 for 24 hours.",
  "data": {
    "has_passcode": true,
    "restriction_applied": true,
    "restricted_until": "2025-11-12T14:30:00Z",
    "restricted_limit": 1000000
  }
}
```

---

## 🔢 Transaction PIN Management (V2)

**Base URL:** `/api/v2/auth/pin/`
**Status:** ✅ Fully implemented

### Setup PIN
```http
POST /api/v2/auth/pin/setup
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "pin": "1234",
  "pin_confirmation": "1234"
}

Response: 200 OK
{
  "success": true,
  "message": "Transaction PIN set successfully",
  "data": {
    "has_pin": true
  }
}
```

### Verify PIN
```http
POST /api/v2/auth/pin/verify
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "pin": "1234"
}

Response: 200 OK
{
  "success": true,
  "data": {
    "verified": true
  }
}
```

### Change PIN
```http
PUT /api/v2/auth/pin/change
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "old_pin": "1234",
  "new_pin": "5678",
  "new_pin_confirmation": "5678"
}

Response: 200 OK
{
  "success": true,
  "message": "PIN changed successfully. Transaction limit restricted to ₦10,000 for 24 hours.",
  "data": {
    "has_pin": true,
    "restriction_applied": true,
    "restricted_until": "2025-11-12T14:30:00Z",
    "restricted_limit": 1000000
  }
}
```

### Check PIN Status
```http
GET /api/v2/auth/pin/status
Authorization: Bearer {access_token}

Response: 200 OK
{
  "status": true,
  "transaction_pin_set": true,
  "detail": "Transaction PIN is set."
}
```

---

## 👤 Profile Management (V1)

**Base URL:** `/api/v1/account/`
**Status:** ✅ Fully implemented

### Get User Profile
```http
GET /api/v1/account/profile
Authorization: Bearer {access_token}

Response: 200 OK
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "08012345678",
  "account_tier": "Tier 2",
  "has_virtual_wallet": true,
  "has_bvn": true,
  "has_nin": true,
  "is_verified": true,
  "has_passcode": true,
  "has_pin": true,
  "dob": "1990-01-01",
  "address": "Lagos, Nigeria",
  "created_at": "2025-01-01T00:00:00Z"
}
```

### Update User Profile
```http
PUT /api/v1/account/profile
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "phone": "08012345678",
  "dob": "1990-01-01",
  "address": "123 Main St",
  "city": "Lagos",
  "state": "Lagos",
  "country": "Nigeria"
}

Response: 200 OK
{
  "message": "Profile updated successfully.",
  "data": { /* updated profile */ }
}
```

---

## 🎯 KYC Verification (V1)

**Base URL:** `/api/v1/account/`
**Status:** ✅ Fully implemented with Embedly

### Verify BVN
```http
POST /api/v1/account/bvn-update
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "bvn": "12345678901"
}

Response: 200 OK
{
  "success": true,
  "message": "BVN verified successfully! You now have Tier 1 access. Daily limit: ₦50K."
}
```

### Verify NIN
```http
POST /api/v1/account/nin-update
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "nin": "12345678901",
  "firstname": "John",
  "lastname": "Doe",
  "dob": "1990-01-01T00:00:00"
}

Response: 200 OK
{
  "success": true,
  "message": "Congratulations! You now have Tier 2 access with both BVN and NIN verified!"
}
```

### Get Verification Status
```http
GET /api/v1/account/verification-status
Authorization: Bearer {access_token}

Response: 200 OK
{
  "bvn": {
    "verified": true,
    "bvn_number": "12345678901",
    "verified_name": "John Doe",
    "dob": "1990-01-01"
  },
  "nin": {
    "verified": true,
    "nin_number": "12345678901",
    "verified_name": "John Doe",
    "dob": "1990-01-01"
  },
  "account_info": {
    "account_tier": "Tier 2",
    "has_virtual_wallet": true,
    "profile_name": "John Doe",
    "profile_dob": "1990-01-01"
  }
}
```

### Get Account Tier Information
```http
GET /api/v1/account/tier-info
Authorization: Bearer {access_token}

Response: 200 OK
{
  "current_tier": {
    "name": "Tier 2",
    "daily_transaction_limit": 100000,
    "cumulative_transaction_limit": 500000,
    "wallet_balance_limit": 500000,
    "features": ["All Tier 1 features", "Community groups", "Higher limits"],
    "requirements": ["BVN and NIN verification"],
    "is_current": true,
    "can_upgrade": false
  },
  "all_tiers": { /* all tier information */ },
  "verification_status": {
    "has_bvn": true,
    "has_nin": true,
    "has_virtual_wallet": true
  },
  "upgrade_options": []
}
```

### Sync Verification with Embedly
```http
POST /api/v1/account/sync-embedly
Authorization: Bearer {access_token}

Response: 200 OK
{
  "success": true,
  "data": {
    "message": "Verification status synced successfully!",
    "updated": true,
    "changes": ["BVN verification updated", "Wallet created"],
    "current_status": {
      "account_tier": "Tier 1",
      "has_bvn": true,
      "has_nin": false,
      "has_virtual_wallet": true
    }
  }
}
```

### Create Wallet (Manual)
```http
POST /api/v1/account/create-wallet
Authorization: Bearer {access_token}

Response: 200 OK
{
  "success": true,
  "data": {
    "message": "Wallet created successfully!",
    "wallet": {
      "account_name": "John Doe",
      "account_number": "1234567890",
      "bank": "Providus Bank",
      "bank_code": "101",
      "balance": 0.0,
      "currency": "NGN"
    }
  }
}
```

---

## 💰 Wallet Operations (V1)

**Base URL:** `/api/v1/wallet/`
**Status:** ✅ Fully implemented

### Get Wallet Balance
```http
GET /api/v1/wallet/balance
Authorization: Bearer {access_token}

Response: 200 OK
{
  "success": true,
  "data": {
    "wallet": {
      "id": "uuid",
      "account_name": "John Doe",
      "account_number": "1234567890",
      "bank": "Providus Bank",
      "bank_code": "101",
      "balance": 50000.00,
      "currency": "NGN",
      "created_at": "2025-01-01T00:00:00Z"
    },
    "user_goals": [
      {
        "id": "uuid",
        "name": "Emergency Fund",
        "target_amount": 100000.00,
        "current_amount": 25000.00,
        "deadline": "2025-12-31"
      }
    ],
    "transaction_pin_set": true
  }
}
```

### Get Transaction History
```http
GET /api/v1/wallet/history
Authorization: Bearer {access_token}

Response: 200 OK
{
  "success": true,
  "data": {
    "transactions": [
      {
        "id": "uuid",
        "transaction_type": "credit",
        "amount": 10000.00,
        "description": "Transfer from John",
        "sender_name": "John Smith",
        "sender_account": "0123456789",
        "external_reference": "REF123",
        "created_at": "2025-11-10T10:30:00Z"
      },
      {
        "id": "uuid",
        "transaction_type": "debit",
        "amount": 5000.00,
        "description": "Withdrawal to GTBank",
        "external_reference": "WD123",
        "created_at": "2025-11-09T14:20:00Z"
      }
    ]
  }
}
```

### Get Bank List
```http
GET /api/v1/wallet/banks
Authorization: Bearer {access_token}

Response: 200 OK
{
  "success": true,
  "data": {
    "banks": [
      {
        "bankCode": "000010",
        "bankName": "Sterling Bank"
      },
      {
        "bankCode": "000011",
        "bankName": "First Bank of Nigeria"
      }
    ]
  }
}
```

### Resolve Bank Account (Name Enquiry)
```http
POST /api/v1/wallet/resolve-bank-account
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "account_number": "0123456789",
  "bank_code": "000013"
}

Response: 200 OK
{
  "status": true,
  "detail": "Account resolved successfully.",
  "data": {
    "account_number": "0123456789",
    "account_name": "JOHN DOE",
    "bank_code": "000013"
  }
}
```

**Validation Rules:**
- Account number must be exactly 10 digits
- Account number must be numeric only
- Both fields are required

**Error Responses:**

400 Bad Request (Missing fields):
```json
{
  "status": false,
  "detail": "Both account_number and bank_code are required."
}
```

400 Bad Request (Invalid format):
```json
{
  "status": false,
  "detail": "Account number must be exactly 10 digits."
}
```

400 Bad Request (Account not found or invalid):
```json
{
  "status": false,
  "detail": "Unable to validate account details"
}
```

**Successful Verification Response:**
```json
{
  "status": true,
  "detail": "Account resolved successfully.",
  "data": {
    "account_number": "0123456789",
    "account_name": "JOHN DOE",
    "bank_code": "000013",
    "verified": true
  }
}
```

**Graceful Degradation Response (When Embedly Unavailable):**
```json
{
  "status": true,
  "detail": "Account verification service temporarily unavailable. Please verify account details carefully.",
  "data": {
    "account_number": "0123456789",
    "account_name": null,
    "bank_code": "000013",
    "verified": false,
    "warning": "Unable to verify account name. Please double-check account details before proceeding."
  }
}
```

**Implementation Notes:**
- Uses Embedly's `Payout/name-enquiry` endpoint
- Call this BEFORE withdrawal to verify account holder name
- Display returned name to user for confirmation
- Prevents sending money to wrong accounts

**Mobile App MUST Handle `verified: false`:**
```typescript
if (!response.data.verified || response.data.account_name === null) {
  // Show warning dialog
  Alert.alert(
    "⚠️ Account Verification Unavailable",
    response.data.warning || "We cannot verify the account name. Please ensure your account details are correct.",
    [
      { text: "Cancel", style: "cancel" },
      { text: "I've Verified - Proceed", style: "destructive", onPress: () => proceed() }
    ]
  );
} else {
  // Show confirmation with verified name
  Alert.alert(
    "Confirm Withdrawal",
    `Send to ${response.data.account_name}?`,
    [
      { text: "Cancel", style: "cancel" },
      { text: "Confirm", onPress: () => proceed() }
    ]
  );
}
```

### Initiate Withdrawal
```http
POST /api/v1/wallet/withdraw/request
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "bank_name": "Sterling Bank",
  "bank_code": "000010",
  "account_number": "0123456789",
  "account_name": "JOHN DOE",
  "amount": 10000,
  "transaction_pin": "1234"
}

Response: 200 OK
{
  "status": true,
  "detail": "Withdrawal initiated successfully. Funds will be transferred shortly.",
  "withdrawal_request": {
    "id": 123,
    "amount": 10000.00,
    "bank_name": "Sterling Bank",
    "account_number": "0123456789",
    "bank_account_name": "JOHN DOE",
    "status": "processing"
  }
}
```

### Check Withdrawal Status
```http
GET /api/v1/wallet/withdraw/status/123
Authorization: Bearer {access_token}

Response: 200 OK
{
  "status": true,
  "detail": "Withdrawal completed successfully",
  "data": {
    "id": 123,
    "amount": 10000.00,
    "bank_name": "Sterling Bank",
    "account_number": "0123456789",
    "status": "completed",
    "created_at": "2025-11-11T10:00:00Z",
    "completed_at": "2025-11-11T10:05:00Z"
  }
}
```

### Set Transaction PIN (Legacy - Use V2)
```http
POST /api/v1/wallet/transaction-pin/set
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "pin": "1234",
  "old_pin": "5678"  // required if updating
}

Response: 200 OK
{
  "status": true,
  "detail": "Transaction PIN set successfully.",
  "transaction_pin_set": true
}
```

### Verify Transaction PIN (Legacy - Use V2)
```http
POST /api/v1/wallet/transaction-pin/verify
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "pin": "1234"
}

Response: 200 OK
{
  "status": true,
  "valid": true,
  "detail": "PIN is valid."
}
```

### Check PIN Status (Legacy - Use V2)
```http
GET /api/v1/wallet/transaction-pin/status
Authorization: Bearer {access_token}

Response: 200 OK
{
  "status": true,
  "transaction_pin_set": true,
  "detail": "Transaction PIN is set."
}
```

---

## 📊 Account Tiers & Limits

### Tier Structure

| Tier | Requirements | Daily Limit | Cumulative Limit | Wallet Balance |
|------|--------------|-------------|------------------|----------------|
| **Tier 1** | BVN **OR** NIN | ₦50,000 | ₦300,000 | ₦300,000 |
| **Tier 2** | BVN **AND** NIN | ₦100,000 | ₦500,000 | ₦500,000 |
| **Tier 3** | BVN + NIN + Address + Proof | Unlimited | Unlimited | Unlimited |

### Features by Tier

**Tier 1:**
- Basic wallet
- Send money
- Receive money
- Savings goals

**Tier 2:**
- All Tier 1 features
- Community groups
- Higher transaction limits

**Tier 3 (Coming Soon):**
- All Tier 2 features
- Unlimited transactions
- Unlimited balance
- Premium support
- Priority processing

---

## 🚫 24-Hour Security Restriction

When user changes **Passcode** or **Transaction PIN**, a 24-hour restriction is automatically applied:

- **Restriction Duration:** 24 hours
- **Transaction Limit:** ₦10,000 (1,000,000 kobo)
- **Applies to:** Withdrawals and transfers
- **Auto-expires:** After 24 hours

**Response Fields:**
```json
{
  "restriction_applied": true,
  "restricted_until": "2025-11-12T14:30:00Z",
  "restricted_limit": 1000000  // in kobo (₦10,000)
}
```

**Checking Restriction Status:**
Include in user profile response:
- `is_restricted`: boolean
- `limit_restricted_until`: timestamp
- `restricted_limit`: amount in kobo

---

## 🔄 OAuth (Coming Soon)

**Base URL:** `/api/v2/auth/oauth/`
**Status:** 🔄 Placeholder (Returns 501)

### Google Sign In
```http
POST /api/v2/auth/oauth/google
Content-Type: application/json

{
  "id_token": "google_id_token"
}

Response: 501 Not Implemented
{
  "success": false,
  "message": "Google Sign In not yet implemented"
}
```

### Apple Sign In
```http
POST /api/v2/auth/oauth/apple
Content-Type: application/json

{
  "id_token": "apple_id_token",
  "authorization_code": "apple_auth_code"
}

Response: 501 Not Implemented
{
  "success": false,
  "message": "Apple Sign In not yet implemented"
}
```

---

## 🎯 Recommended Mobile Implementation

### Phase 1: Current Implementation (Use Now)

```
✅ Authentication      → /api/v2/auth/*
✅ Passcode           → /api/v2/auth/passcode/*
✅ Transaction PIN    → /api/v2/auth/pin/*
✅ Profile            → /api/v1/account/profile
✅ KYC Verification   → /api/v1/account/bvn-update, nin-update
✅ Wallet Operations  → /api/v1/wallet/*
✅ Transaction History → /api/v1/wallet/history
```

### Dashboard Data (Aggregate Multiple Endpoints)

Since `/api/v2/dashboard/` is not implemented, aggregate these:

1. **User Info:** `GET /api/v1/account/profile`
2. **Wallet Balance:** `GET /api/v1/wallet/balance`
3. **Recent Transactions:** `GET /api/v1/wallet/history` (limit to 5)
4. **Account Tier:** `GET /api/v1/account/tier-info`
5. **Verification Status:** `GET /api/v1/account/verification-status`

---

## 🔒 Authentication Flow

### Standard Flow
1. **Sign Up** → `/api/v2/auth/signup`
2. **Set Passcode** → `/api/v2/auth/passcode/setup`
3. **Verify BVN/NIN** → `/api/v1/account/bvn-update` or `nin-update`
4. **Set Transaction PIN** → `/api/v2/auth/pin/setup`
5. **Start Using App** ✅

### Quick Login Flow
1. **Sign In with Passcode** → `/api/v2/auth/signin` (with passcode)
2. **Or Biometric** → Local biometric → Sign in with stored passcode
3. **Access App** ✅

### Session Management
- **Access Token:** Expires in 1 hour
- **Refresh Token:** Expires in 30 days
- **Refresh** → `/api/v2/auth/refresh` when access token expires

---

## 📝 Error Response Format

All endpoints follow this error format:

```json
{
  "success": false,
  "detail": "Error message here",
  "status": false  // for some V1 endpoints
}
```

Common HTTP Status Codes:
- `200 OK` - Success
- `201 Created` - Resource created (signup)
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Invalid/expired token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error
- `501 Not Implemented` - Feature not available yet

---

## 🎨 Mobile App Checklist

Based on your completed tasks, here's what's ready:

### ✅ Completed
- [x] Sign Up with V2 API
- [x] Sign In with Email/Password
- [x] Sign In with Passcode
- [x] Biometric Authentication
- [x] Logout
- [x] Passcode Management
- [x] Transaction PIN Management
- [x] Security Settings
- [x] Restriction Banner
- [x] Account Tier Badge

### 🔄 Recommended Next Steps
1. **Implement KYC Verification Screens**
   - BVN verification screen
   - NIN verification screen
   - Tier upgrade prompts

2. **Wallet & Transactions**
   - Withdrawal flow with PIN verification
   - Transaction history with filters
   - Bank account resolution

3. **Dashboard**
   - Aggregate data from multiple endpoints
   - Show wallet balance
   - Recent transactions
   - Savings goals

4. **Profile Management**
   - Edit profile screen
   - View verification status
   - Check account tier

---

## 📚 Additional Resources

- **Swagger UI:** `https://api.gidinest.com/api/docs/`
- **ReDoc:** `https://api.gidinest.com/api/redoc/`
- **OpenAPI Schema:** `https://api.gidinest.com/api/schema/`
- **V2 API Documentation:** `V2_API_DOCUMENTATION.md`
- **V2 API Availability:** `V2_API_AVAILABILITY.md`

---

**Document Version:** 1.0
**Last Updated:** November 11, 2025
**Maintained By:** Backend Team
