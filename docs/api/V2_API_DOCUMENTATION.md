# V2 API Documentation - Mobile Application

**Version:** 2.0 (In Development)
**Base URL:** `https://api.gidinest.com/api/v2/`
**Status:** Development - New Implementation
**Client:** Mobile Application (iOS & Android)
**Last Updated:** November 11, 2025

---

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Authentication & User Management](#authentication--user-management)
4. [Dashboard](#dashboard)
5. [Profile & Settings](#profile--settings)
6. [Wallet Management](#wallet-management)
7. [Transactions](#transactions)
8. [Savings & Goals](#savings--goals)
9. [Community](#community)
10. [Notifications](#notifications)
11. [KYC Verification](#kyc-verification)
12. [Error Handling](#error-handling)

---

## Overview

### What's New in V2

**Mobile-Optimized Features:**
- ✨ Single-step registration
- ✨ OAuth (Google & Apple Sign In)
- ✨ 6-digit passcode authentication
- ✨ Unified dashboard endpoint
- ✨ Transaction limits enforcement
- ✨ Bank accounts management
- ✨ Session tracking
- ✨ Comprehensive transactions API
- ✨ Auto-save for goals
- ✨ Community likes & image uploads
- ✨ Rich notifications system

### Response Format

All V2 API responses follow this structure:

**Success Response:**
```json
{
  "success": true,
  "data": { /* response data */ }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "data": { /* additional error context */ }
  }
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | Successful POST |
| 400 | Bad Request | Validation errors |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Internal server error |

---

## Authentication

### JWT Tokens

**Access Token:**
- Expiry: 1 hour
- Use for all API calls
- Refresh before expiry

**Refresh Token:**
- Expiry: 30 days
- Use to get new access token
- Stored securely on device

**Header Format:**
```
Authorization: Bearer <access_token>
```

### User Agent

Mobile apps should identify themselves:
```
User-Agent: GidiNest-Mobile/1.0.0 (iOS/Android)
```

---

## Authentication & User Management

**Base Path:** `/api/v2/auth/`

### 1. Sign Up

**Endpoint:** `POST /signup`
**Auth Required:** No
**Status:** 🔄 To Implement
**Description:** Single-step registration (simplified from v1's 3-step process)

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "password_confirmation": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "08012345678",
  "referral_code": "ABC123"  // optional
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "phone": "08012345678",
      "is_verified": false,
      "has_passcode": false,
      "has_pin": false,
      "created_at": "2025-11-11T14:30:00Z"
    },
    "tokens": {
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "expires_in": 3600
    }
  }
}
```

**Backend Actions:**
- Create user account
- Hash password with bcrypt
- Create wallet via Embedly
- Generate JWT tokens
- Send welcome email
- Create welcome notification

**Errors:**
- `400` - Email already exists
- `400` - Invalid email format
- `400` - Weak password
- `400` - Passwords don't match

---

### 2. Sign In

**Endpoint:** `POST /signin`
**Auth Required:** No
**Status:** 🔄 To Implement
**Description:** Login with email and password (enhanced response with mobile fields)

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "has_passcode": true,
      "has_pin": true,
      "is_verified": true,
      "biometric_enabled": false,
      "verification_method": "bvn"
    },
    "tokens": {
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "expires_in": 3600
    }
  }
}
```

**Backend Actions:**
- Verify credentials
- Update last_login_at
- Create session record
- Generate JWT tokens
- Send login alert (if enabled)

---

### 3. Google OAuth

**Endpoint:** `POST /oauth/google`
**Auth Required:** No
**Status:** 🔄 To Implement
**Description:** Sign in/up with Google

**Request:**
```json
{
  "id_token": "google_id_token_from_sdk",
  "device_info": {
    "device_name": "iPhone 14 Pro",
    "device_type": "ios",
    "device_id": "unique_device_id"
  }
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@gmail.com",
      "first_name": "John",
      "last_name": "Doe",
      "google_linked": true,
      "is_new_user": false
    },
    "tokens": {
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "expires_in": 3600
    }
  }
}
```

**Backend Actions:**
- Verify Google ID token
- Check if user exists by google_id or email
- Create new user if doesn't exist
- Link google_id to existing user
- Create/update session

**Setup Requirements:**
- Google Cloud Console project
- OAuth 2.0 client IDs (iOS & Android)
- Consent screen configuration

---

### 4. Apple Sign In

**Endpoint:** `POST /oauth/apple`
**Auth Required:** No
**Status:** 🔄 To Implement
**Description:** Sign in/up with Apple

**Request:**
```json
{
  "id_token": "apple_id_token",
  "authorization_code": "apple_auth_code",
  "user_data": {
    "email": "user@privaterelay.appleid.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@privaterelay.appleid.com",
      "first_name": "John",
      "last_name": "Doe",
      "apple_linked": true,
      "is_new_user": true
    },
    "tokens": {
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "expires_in": 3600
    }
  }
}
```

**Backend Actions:**
- Verify Apple ID token with Apple's public keys
- Handle privacy relay emails
- Create new user or link to existing
- Generate JWT tokens

**Setup Requirements:**
- Apple Developer account
- Sign in with Apple capability
- Service ID and Key ID
- Private key configuration

---

### 5. Refresh Token

**Endpoint:** `POST /refresh`
**Auth Required:** No (uses refresh_token)
**Status:** ✅ Existing (JWT standard)
**Description:** Get new access token

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "access_token": "new_eyJ0eXAiOiJKV1QiLCJhbGc...",
    "expires_in": 3600
  }
}
```

---

### 6. Logout

**Endpoint:** `POST /logout`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Logout and invalidate session

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "device_id": "unique_device_id"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "message": "Logged out successfully"
  }
}
```

**Backend Actions:**
- Invalidate refresh token
- Delete session record
- Remove FCM device token (optional)

---

### 7. Setup Passcode

**Endpoint:** `POST /passcode/setup`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Set 6-digit passcode for quick login

**Request:**
```json
{
  "passcode": "123456",
  "passcode_confirmation": "123456"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "has_passcode": true,
    "message": "Passcode set successfully"
  }
}
```

**Passcode Requirements:**
- Exactly 6 digits
- Numeric only
- Cannot be sequential (123456, 654321)
- Cannot be all same (111111)

---

### 8. Verify Passcode

**Endpoint:** `POST /passcode/verify`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Verify passcode for authentication

**Request:**
```json
{
  "passcode": "123456"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "verified": true
  }
}
```

**Errors:**
- `400` - Invalid passcode
- `429` - Too many attempts (locked for 15 minutes)

---

### 9. Change Passcode

**Endpoint:** `PUT /passcode/change`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Change existing passcode

**Request:**
```json
{
  "old_passcode": "123456",
  "new_passcode": "654321",
  "new_passcode_confirmation": "654321"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "has_passcode": true,
    "restriction_applied": true,
    "restricted_until": "2025-11-12T14:30:00Z",
    "restricted_limit": 1000000,  // ₦10,000 in kobo
    "message": "Passcode changed. Transactions limited to ₦10,000 for 24 hours."
  }
}
```

**Security:**
- Apply 24-hour transaction restrictions
- User can only transact up to ₦10,000
- Restriction automatically lifted after 24 hours

---

### 10. Setup PIN

**Endpoint:** `POST /pin/setup`
**Auth Required:** Yes
**Status:** 🔄 To Implement (Enhanced from v1)
**Description:** Set 4-digit transaction PIN

**Request:**
```json
{
  "pin": "1234",
  "pin_confirmation": "1234"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "has_pin": true,
    "message": "Transaction PIN set successfully"
  }
}
```

---

### 11. Verify PIN

**Endpoint:** `POST /pin/verify`
**Auth Required:** Yes
**Status:** 🔄 To Implement (Enhanced from v1)
**Description:** Verify transaction PIN

**Request:**
```json
{
  "pin": "1234"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "verified": true
  }
}
```

---

### 12. Change PIN

**Endpoint:** `PUT /pin/change`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Change transaction PIN

**Request:**
```json
{
  "old_pin": "1234",
  "new_pin": "5678",
  "new_pin_confirmation": "5678"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "has_pin": true,
    "restriction_applied": true,
    "restricted_until": "2025-11-12T14:30:00Z",
    "restricted_limit": 1000000,
    "message": "PIN changed. Transactions limited to ₦10,000 for 24 hours."
  }
}
```

---

## Dashboard

**Base Path:** `/api/v2/dashboard/`

### 1. Get Dashboard

**Endpoint:** `GET /`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Get all dashboard data in one request (optimized for mobile)

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "first_name": "John",
      "last_name": "Doe",
      "is_verified": true,
      "profile_image_url": "https://s3.amazonaws.com/gidinest/profiles/uuid.jpg"
    },
    "wallet": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "balance": 85000000,        // ₦850,000 in kobo
      "available_balance": 85000000,
      "ledger_balance": 85000000,
      "currency": "NGN",
      "account_number": "1234567890",
      "bank_name": "Providus Bank",
      "account_name": "JOHN DOE"
    },
    "quick_stats": {
      "total_saved": 25000000,    // ₦250,000 in kobo
      "active_goals": 3,
      "completed_goals": 1,
      "transactions_this_month": 12,
      "total_deposits_this_month": 150000000,
      "total_withdrawals_this_month": 50000000
    },
    "recent_transactions": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "type": "deposit",
        "amount": 5000000,
        "status": "completed",
        "description": "Bank transfer",
        "created_at": "2025-11-10T14:30:00Z"
      }
      // ... last 5 transactions
    ],
    "savings_goals": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Hospital Delivery Bills",
        "icon": "hospital-building",
        "category": "delivery",
        "target_amount": 50000000,
        "current_amount": 25000000,
        "progress": 50.0,
        "target_date": "2025-12-01"
      }
      // ... all active goals
    ]
  }
}
```

**Caching:**
- Cached for 30 seconds in Redis
- Reduces database load
- Faster response time

---

## Profile & Settings

**Base Path:** `/api/v2/profile/`

### 1. Get Profile

**Endpoint:** `GET /`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Get full user profile with limits and security info

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "phone": "08012345678",
      "first_name": "John",
      "last_name": "Doe",
      "date_of_birth": "1990-01-15",
      "address": "123 Main St, Lagos",
      "country": "Nigeria",
      "state": "Lagos",
      "profile_image_url": "https://...",
      "is_verified": true,
      "verification_method": "bvn",
      "verification_status": "verified",
      "email_verified_at": "2025-01-01T00:00:00Z",
      "phone_verified_at": "2025-01-01T00:00:00Z",
      "account_tier": "Tier 2",
      "created_at": "2025-01-01T00:00:00Z"
    },
    "limits": {
      "daily_limit": 100000000,          // ₦1,000,000
      "per_transaction_limit": 50000000, // ₦500,000
      "monthly_limit": 1000000000,       // ₦10,000,000
      "is_restricted": false,
      "restricted_until": null,
      "restricted_limit": null,
      "daily_used": 5000000,
      "daily_remaining": 95000000,
      "monthly_used": 15000000,
      "monthly_remaining": 985000000
    },
    "security": {
      "has_passcode": true,
      "has_pin": true,
      "biometric_enabled": true,
      "two_factor_enabled": false,
      "google_linked": true,
      "apple_linked": false
    }
  }
}
```

---

### 2. Update Profile

**Endpoint:** `PUT /`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Update profile information

**Request:**
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "phone": "08087654321",
  "date_of_birth": "1990-01-15",
  "address": "456 New Street, Lagos",
  "state": "Lagos",
  "country": "Nigeria"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "user": {
      // updated user object
    }
  }
}
```

---

### 3. Upload Avatar

**Endpoint:** `POST /avatar`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Upload profile picture

**Request:** `multipart/form-data`
```
file: <image_file>
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "profile_image_url": "https://s3.amazonaws.com/gidinest/profiles/uuid.jpg",
    "width": 800,
    "height": 800,
    "size": 125648
  }
}
```

**Image Requirements:**
- Format: JPG, PNG, WEBP
- Max size: 5MB
- Recommended: Square, 800x800px
- Auto-resize and optimize

---

### 4. Delete Account

**Endpoint:** `DELETE /`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Delete user account (soft delete)

**Request:**
```json
{
  "password": "UserPassword123!",
  "reason": "No longer needed"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "message": "Account deleted successfully",
    "deleted_at": "2025-11-11T14:30:00Z"
  }
}
```

**Backend Actions:**
- Soft delete (set deleted_at)
- Anonymize personal data after 30 days
- Retain transaction records (legal requirement)

---

### 5. List Bank Accounts

**Endpoint:** `GET /bank-accounts`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Get user's saved bank accounts

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "accounts": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "bank_name": "Access Bank",
        "bank_code": "044",
        "account_number": "0123456789",
        "account_name": "JOHN DOE",
        "is_verified": true,
        "is_default": true,
        "verified_at": "2025-01-01T00:00:00Z",
        "created_at": "2025-01-01T00:00:00Z"
      }
    ]
  }
}
```

---

### 6. Add Bank Account

**Endpoint:** `POST /bank-accounts`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Add and verify bank account

**Request:**
```json
{
  "bank_code": "044",
  "account_number": "0123456789"
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "account": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "bank_name": "Access Bank",
      "bank_code": "044",
      "account_number": "0123456789",
      "account_name": "JOHN DOE",  // Resolved via Embedly
      "is_verified": true,
      "is_default": false,
      "created_at": "2025-11-11T14:30:00Z"
    }
  }
}
```

**Backend Actions:**
- Call Embedly account verification
- Verify account name matches user
- Save to database
- Return verified account

---

### 7. Delete Bank Account

**Endpoint:** `DELETE /bank-accounts/<account_id>`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Remove saved bank account

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "message": "Bank account removed"
  }
}
```

---

### 8. Set Default Bank Account

**Endpoint:** `PUT /bank-accounts/<account_id>/default`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Set bank account as default for withdrawals

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "account": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "is_default": true
    }
  }
}
```

---

### 9. List Sessions

**Endpoint:** `GET /sessions`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Get active login sessions

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "sessions": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "device_name": "iPhone 14 Pro",
        "device_type": "ios",
        "device_id": "unique_device_id",
        "location": "Lagos, Nigeria",
        "ip_address": "192.168.1.1",
        "is_current": true,
        "last_active_at": "2025-11-10T14:30:00Z",
        "created_at": "2025-11-10T10:00:00Z"
      }
    ]
  }
}
```

---

### 10. End Session

**Endpoint:** `DELETE /sessions/<session_id>`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** End a specific session (remote logout)

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "message": "Session ended successfully"
  }
}
```

---

### 11. End All Sessions

**Endpoint:** `DELETE /sessions/all`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** End all sessions except current (logout everywhere)

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "sessions_ended": 3,
    "message": "All other sessions ended"
  }
}
```

---

## Wallet Management

**Base Path:** `/api/v2/wallet/`

### 1. Get Wallet

**Endpoint:** `GET /`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Get wallet details with ledger balance

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "balance": 85000000,
    "available_balance": 85000000,
    "ledger_balance": 85000000,
    "currency": "NGN",
    "account_number": "1234567890",
    "bank_name": "Providus Bank",
    "bank_code": "001",
    "account_name": "JOHN DOE",
    "embedly_wallet_id": "embedly_wallet_123",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-11-10T14:30:00Z"
  }
}
```

---

### 2. Initiate Deposit

**Endpoint:** `POST /deposit`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Get deposit instructions and create pending transaction

**Request:**
```json
{
  "amount": 10000000,  // ₦100,000 in kobo
  "payment_method": "bank_transfer"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
    "payment_reference": "GN_1636627200_ABC123",
    "account_details": {
      "account_number": "1234567890",
      "bank_name": "Providus Bank",
      "account_name": "JOHN DOE"
    },
    "amount": 10000000,
    "instructions": [
      "Transfer ₦100,000 to the account above",
      "Use the reference: GN_1636627200_ABC123",
      "Funds will be credited automatically"
    ],
    "expires_at": "2025-11-12T14:30:00Z"  // 24 hours
  }
}
```

**Backend Actions:**
- Create pending transaction
- Generate unique reference
- Return virtual account details
- Transaction auto-expires in 24 hours

---

### 3. Request Withdrawal

**Endpoint:** `POST /withdraw`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Withdraw to bank account with limit checks

**Request:**
```json
{
  "amount": 5000000,  // ₦50,000 in kobo
  "bank_account_id": "550e8400-e29b-41d4-a716-446655440000",
  "pin": "1234",
  "note": "Personal use"  // optional
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
    "amount": 5000000,
    "fee": 10000,        // ₦100 fee
    "net_amount": 4990000,
    "status": "processing",
    "bank_details": {
      "bank_name": "Access Bank",
      "account_number": "0123456789",
      "account_name": "JOHN DOE"
    },
    "estimated_completion": "2025-11-10T15:00:00Z"
  }
}
```

**Backend Actions:**
- Verify PIN
- Check sufficient balance
- Check daily limit
- Check per-transaction limit
- Check monthly limit
- Check if restricted (24hr after PIN/passcode change)
- Deduct amount + fee
- Call Embedly transfer API
- Create transaction record
- Send notification

**Errors:**
```json
{
  "success": false,
  "error": {
    "code": "DAILY_LIMIT_EXCEEDED",
    "message": "Daily withdrawal limit exceeded",
    "data": {
      "attempted_amount": 5000000,
      "daily_limit": 100000000,
      "used_today": 96000000,
      "remaining": 4000000
    }
  }
}
```

---

## Transactions

**Base Path:** `/api/v2/transactions/`

### 1. List Transactions

**Endpoint:** `GET /`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Get comprehensive transaction history with filters

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)
- `type`: Filter by type (deposit, withdrawal, transfer, goal_funding)
- `status`: Filter by status (pending, processing, completed, failed)
- `from_date`: Start date (ISO format)
- `to_date`: End date (ISO format)

**Example:** `GET /transactions?page=1&limit=20&type=deposit&status=completed`

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "type": "deposit",
        "amount": 5000000,
        "fee": 0,
        "net_amount": 5000000,
        "status": "completed",
        "description": "Bank transfer deposit",
        "payment_reference": "GN_1636627200_ABC123",
        "payment_method": "bank_transfer",
        "created_at": "2025-11-10T14:30:00Z",
        "settled_at": "2025-11-10T14:35:00Z"
      },
      {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "type": "withdrawal",
        "amount": 2000000,
        "fee": 10000,
        "net_amount": 1990000,
        "status": "completed",
        "description": "Withdrawal to Access Bank",
        "payment_reference": "GN_1636627300_XYZ789",
        "bank_details": {
          "bank_name": "Access Bank",
          "account_number": "0123456789"
        },
        "created_at": "2025-11-09T10:15:00Z",
        "settled_at": "2025-11-09T10:20:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 156,
      "total_pages": 8
    },
    "summary": {
      "total_deposits": 150000000,
      "total_withdrawals": 65000000,
      "total_fees": 500000,
      "net_balance_change": 84500000
    }
  }
}
```

---

### 2. Get Transaction Details

**Endpoint:** `GET /<transaction_id>`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Get full transaction details

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "withdrawal",
    "amount": 5000000,
    "fee": 10000,
    "net_amount": 4990000,
    "status": "completed",
    "description": "Withdrawal to bank account",
    "payment_reference": "GN_1636627200_ABC123",
    "external_reference": "EMBEDLY_TXN_789",
    "payment_method": "bank_transfer",
    "bank_details": {
      "bank_name": "Access Bank",
      "bank_code": "044",
      "account_number": "0123456789",
      "account_name": "JOHN DOE"
    },
    "metadata": {
      "session_id": "550e8400-e29b-41d4-a716-446655440002",
      "ip_address": "192.168.1.1",
      "device_type": "ios",
      "device_name": "iPhone 14 Pro"
    },
    "created_at": "2025-11-10T14:30:00Z",
    "updated_at": "2025-11-10T14:35:00Z",
    "settled_at": "2025-11-10T14:35:00Z"
  }
}
```

---

## Savings & Goals

**Base Path:** `/api/v2/savings/`

### 1. List Goals

**Endpoint:** `GET /goals`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Get all savings goals with auto-save info

**Query Parameters:**
- `status`: Filter by status (active, completed, paused, cancelled)
- `category`: Filter by category

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "goals": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Hospital Delivery Bills",
        "description": "Funds for delivery day",
        "icon": "hospital-building",
        "category": "delivery",
        "target_amount": 50000000,
        "current_amount": 25000000,
        "progress": 50.0,
        "target_date": "2025-12-01",
        "priority": 1,
        "status": "active",

        // Auto-save settings
        "auto_save_enabled": true,
        "auto_save_frequency": "weekly",
        "auto_save_amount": 5000000,
        "next_auto_save_date": "2025-11-17T06:00:00Z",

        // Interest
        "interest_rate": 10.0,
        "accrued_interest": 500000,

        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-11-10T14:30:00Z"
      }
    ],
    "total_saved": 25000000,
    "active_goals": 3,
    "completed_goals": 1
  }
}
```

---

### 2. Create Goal

**Endpoint:** `POST /goals`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Create new savings goal with auto-save

**Request:**
```json
{
  "name": "Hospital Delivery Bills",
  "description": "Funds for delivery day",
  "icon": "hospital-building",
  "category": "delivery",
  "target_amount": 50000000,
  "target_date": "2025-12-01",
  "priority": 1,

  // Auto-save settings (optional)
  "auto_save_enabled": true,
  "auto_save_frequency": "weekly",
  "auto_save_amount": 5000000
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "goal": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Hospital Delivery Bills",
      // ... all fields
      "next_auto_save_date": "2025-11-17T06:00:00Z"  // Calculated
    }
  }
}
```

**Backend Actions:**
- Validate target_amount > 0
- Validate target_date is future
- Calculate next_auto_save_date if auto_save enabled
- Create goal record
- Send notification

---

### 3. Get Goal Details

**Endpoint:** `GET /goals/<goal_id>`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Get single goal details

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "goal": {
      // full goal object
    },
    "statistics": {
      "total_contributed": 25000000,
      "total_withdrawn": 0,
      "contributions_count": 15,
      "average_contribution": 1666666,
      "days_to_target": 20,
      "required_daily_savings": 1250000
    }
  }
}
```

---

### 4. Update Goal

**Endpoint:** `PUT /goals/<goal_id>`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Update goal details

**Request:**
```json
{
  "name": "Updated Goal Name",
  "target_amount": 60000000,
  "target_date": "2025-12-15",
  "auto_save_enabled": false
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "goal": {
      // updated goal
    }
  }
}
```

---

### 5. Delete Goal

**Endpoint:** `DELETE /goals/<goal_id>`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Cancel goal and optionally withdraw funds

**Request:**
```json
{
  "withdraw_funds": true,
  "pin": "1234",
  "reason": "No longer needed"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "refunded_amount": 25000000,
    "wallet_balance": 110000000,
    "message": "Goal deleted and funds returned to wallet"
  }
}
```

---

### 6. Fund Goal

**Endpoint:** `POST /goals/<goal_id>/fund`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Add money to goal with PIN and limit checks

**Request:**
```json
{
  "amount": 5000000,
  "pin": "1234",
  "note": "Monthly contribution"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
    "goal": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Hospital Delivery Bills",
      "current_amount": 30000000,
      "target_amount": 50000000,
      "progress": 60.0,
      "is_completed": false
    },
    "wallet_balance": 55000000
  }
}
```

**Milestone Response (50%, 75%, 100%):**
```json
{
  "success": true,
  "data": {
    // ... same as above
    "milestone": {
      "reached": "50%",
      "message": "Halfway there! Keep it up! 🎉",
      "icon": "🎉",
      "next_milestone": "75%"
    }
  }
}
```

**Completion Response (100%):**
```json
{
  "success": true,
  "data": {
    // ... same as above
    "milestone": {
      "reached": "100%",
      "message": "Congratulations! You've reached your goal! 🎊",
      "icon": "🎊",
      "completed": true
    }
  }
}
```

---

### 7. Withdraw from Goal

**Endpoint:** `POST /goals/<goal_id>/withdraw`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Move money from goal back to wallet

**Request:**
```json
{
  "amount": 5000000,
  "pin": "1234",
  "reason": "Emergency"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
    "goal": {
      "current_amount": 20000000,
      "progress": 40.0
    },
    "wallet_balance": 60000000
  }
}
```

---

### 8. Get Goal Transactions

**Endpoint:** `GET /goals/<goal_id>/transactions`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Get transaction history for specific goal

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "goal": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Hospital Delivery Bills"
    },
    "transactions": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "transaction_type": "contribution",
        "amount": 5000000,
        "description": "Monthly contribution",
        "goal_current_amount": 30000000,
        "timestamp": "2025-11-10T14:30:00Z"
      }
    ],
    "total_contributed": 30000000,
    "total_withdrawn": 0,
    "contributions_count": 15,
    "withdrawals_count": 0
  }
}
```

---

## Community

**Base Path:** `/api/v2/community/`

### 1. List Posts

**Endpoint:** `GET /posts`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Get community feed with like status

**Query Parameters:**
- `page`: Page number
- `limit`: Items per page
- `category`: Filter by category
- `search`: Search term

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "posts": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "user": {
          "id": "550e8400-e29b-41d4-a716-446655440001",
          "first_name": "Jane",
          "last_name": "Doe",
          "profile_image_url": "https://..."
        },
        "content": "Just hit my first savings goal! 🎉",
        "image_urls": ["https://s3.amazonaws.com/..."],
        "category": "milestone",
        "tags": ["savings", "achievement"],
        "likes_count": 45,
        "comments_count": 12,
        "is_liked": false,  // Current user's like status
        "created_at": "2025-11-10T14:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 234,
      "total_pages": 12
    }
  }
}
```

---

### 2. Create Post

**Endpoint:** `POST /posts`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Create post with images and tags

**Request:**
```json
{
  "content": "Just hit my first savings goal! 🎉",
  "category": "milestone",
  "tags": ["savings", "achievement"],
  "image_urls": [
    "https://s3.amazonaws.com/gidinest/community/uuid1.jpg",
    "https://s3.amazonaws.com/gidinest/community/uuid2.jpg"
  ]
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "post": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "content": "Just hit my first savings goal! 🎉",
      // ... full post
    }
  }
}
```

**Validations:**
- Content max length: 2000 characters
- Max images: 5
- Image URLs must be from gidinest S3 bucket
- Image ownership verification

---

### 3. Like/Unlike Post

**Endpoint:** `POST /posts/<post_id>/like`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Toggle like on post

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "liked": true,
    "likes_count": 46
  }
}
```

**Backend Actions:**
- Check if already liked (toggle)
- Create or delete like record
- Update post likes_count
- Send notification to post author (if liked)

---

### 4. Upload Image

**Endpoint:** `POST /uploads/image`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Upload image for community post or profile

**Request:** `multipart/form-data`
```
file: <image_file>
type: "post" or "profile"
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "url": "https://s3.amazonaws.com/gidinest/community/uuid.jpg",
    "width": 1920,
    "height": 1080,
    "format": "jpg",
    "size": 245678
  }
}
```

**Image Processing:**
- Upload to S3
- Resize/optimize
- Generate thumbnails
- Return URLs

---

## Notifications

**Base Path:** `/api/v2/notifications/`

### 1. List Notifications

**Endpoint:** `GET /`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Get user notifications

**Query Parameters:**
- `page`: Page number
- `limit`: Items per page
- `unread_only`: boolean (filter unread)
- `type`: Filter by type

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "type": "transaction",
        "title": "Deposit Successful",
        "body": "Your deposit of ₦50,000 has been credited",
        "action_type": "navigate",
        "action_data": {
          "screen": "TransactionDetails",
          "params": {
            "id": "transaction_uuid"
          }
        },
        "read": false,
        "created_at": "2025-11-10T14:30:00Z"
      }
    ],
    "unread_count": 5,
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 89,
      "total_pages": 5
    }
  }
}
```

**Notification Types:**
- `transaction` - Deposit, withdrawal completed
- `goal_milestone` - 25%, 50%, 75%, 100% reached
- `community` - Like, comment on your post
- `security` - Login from new device, PIN change
- `system` - App updates, announcements

---

### 2. Mark as Read

**Endpoint:** `PUT /<notification_id>/read`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Mark notification as read

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "read": true,
    "read_at": "2025-11-10T15:00:00Z"
  }
}
```

---

### 3. Mark All as Read

**Endpoint:** `PUT /read-all`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Mark all notifications as read

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "marked_read": 12,
    "message": "All notifications marked as read"
  }
}
```

---

### 4. Delete Notification

**Endpoint:** `DELETE /<notification_id>`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Delete notification

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "message": "Notification deleted"
  }
}
```

---

## KYC Verification

**Base Path:** `/api/v2/kyc/`

### 1. Verify BVN (Step 1)

**Endpoint:** `POST /bvn/verify`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Verify BVN and return details for confirmation

**Request:**
```json
{
  "bvn": "12345678901"
}
```

**Response:** `200 OK`
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
      "state_of_residence": "Lagos"
    }
  }
}
```

**Backend Actions:**
- Call Prembly BVN verification
- Return details for user to review
- Don't save yet (wait for confirmation)

---

### 2. Confirm BVN (Step 2)

**Endpoint:** `POST /bvn/confirm`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Confirm and save BVN after user review

**Request:**
```json
{
  "bvn": "12345678901",
  "confirmed": true
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "is_verified": true,
    "verification_method": "bvn",
    "verification_status": "verified",
    "account_tier": "Tier 2",
    "limits": {
      "daily_limit": 100000000,
      "per_transaction_limit": 50000000,
      "monthly_limit": 1000000000
    }
  }
}
```

**Backend Actions:**
- Save BVN to user record
- Update verification status
- Upgrade account tier
- Increase transaction limits
- Sync with Embedly
- Send success notification

---

### 3. Verify NIN (Step 1)

**Endpoint:** `POST /nin/verify`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Verify NIN and return details

**Request:**
```json
{
  "nin": "12345678901",
  "first_name": "John",
  "last_name": "Doe",
  "dob": "1990-01-15"
}
```

**Response:** `200 OK`
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
      "address": "123 Main Street, Ikeja, Lagos"
    }
  }
}
```

---

### 4. Confirm NIN (Step 2)

**Endpoint:** `POST /nin/confirm`
**Auth Required:** Yes
**Status:** 🔄 To Implement
**Description:** Confirm and save NIN

**Request:**
```json
{
  "nin": "12345678901",
  "confirmed": true
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "is_verified": true,
    "verification_method": "nin",
    "verification_status": "verified",
    "account_tier": "Tier 2",
    "limits": {
      "daily_limit": 100000000,
      "per_transaction_limit": 50000000,
      "monthly_limit": 1000000000
    }
  }
}
```

---

## Error Handling

### Standard Error Response

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "data": {
      // Additional context (optional)
    }
  }
}
```

### Error Codes

| Code | HTTP | Message | Action |
|------|------|---------|--------|
| `AUTH_INVALID_CREDENTIALS` | 401 | Invalid email or password | Check credentials |
| `AUTH_TOKEN_EXPIRED` | 401 | Token has expired | Refresh token |
| `AUTH_TOKEN_INVALID` | 401 | Invalid token | Re-authenticate |
| `PASSCODE_INVALID` | 400 | Invalid passcode | Try again |
| `PASSCODE_LOCKED` | 429 | Too many attempts | Wait 15 minutes |
| `PIN_INVALID` | 400 | Invalid PIN | Try again |
| `PIN_LOCKED` | 429 | Too many attempts | Wait 15 minutes |
| `WALLET_INSUFFICIENT_BALANCE` | 400 | Insufficient balance | Add funds |
| `LIMIT_DAILY_EXCEEDED` | 400 | Daily limit exceeded | Wait until tomorrow |
| `LIMIT_TRANSACTION_EXCEEDED` | 400 | Transaction limit exceeded | Reduce amount |
| `LIMIT_MONTHLY_EXCEEDED` | 400 | Monthly limit exceeded | Wait until next month |
| `RESTRICTED_24HR` | 403 | 24hr restriction active | Wait until restriction lifts |
| `KYC_BVN_INVALID` | 400 | Invalid BVN | Check BVN |
| `KYC_NAME_MISMATCH` | 400 | Name doesn't match | Update profile |
| `VALIDATION_ERROR` | 400 | Validation failed | Check request data |

---

## Implementation Status Legend

- ✅ **Complete** - Fully implemented and tested
- 🔄 **To Implement** - Planned, not yet built
- ⚠️ **Partial** - Some functionality exists, needs enhancement

---

**Document End**

**Next:** Start Phase 1 implementation - URL structure setup
