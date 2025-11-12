# V1 API Documentation - Web Application

**Version:** 1.0
**Base URL:** `https://api.gidinest.com/api/v1/`
**Status:** Production - FROZEN (No modifications allowed)
**Client:** Web Application
**Last Updated:** November 11, 2025

---

## Table of Contents
1. [Authentication](#authentication)
2. [Overview](#overview)
3. [Authentication & Onboarding](#authentication--onboarding)
4. [Account & Profile](#account--profile)
5. [Wallet Management](#wallet-management)
6. [Savings & Goals](#savings--goals)
7. [Community](#community)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)

---

## Authentication

All endpoints (except registration and login) require JWT authentication.

**Header Format:**
```
Authorization: Bearer <access_token>
```

**Token Expiry:**
- Access Token: 14 days (current - will be changed to 1 hour in future)
- Refresh Token: 30 days

---

## Overview

### Response Format

All API responses follow this structure:

**Success Response:**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { /* response data */ }
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Error message",
  "errors": { /* validation errors */ }
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

## Authentication & Onboarding

**Base Path:** `/api/v1/onboarding/`

### 1. Register - Initiate

**Endpoint:** `POST /register/initiate`
**Auth Required:** No
**Description:** Start the registration process by sending email and receiving OTP

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "OTP sent to your email",
  "data": {
    "email": "user@example.com",
    "otp_expires_at": "2025-11-11T14:35:00Z"
  }
}
```

**Errors:**
- `400` - Email already exists
- `400` - Invalid email format

---

### 2. Register - Verify OTP

**Endpoint:** `POST /register/verify-otp`
**Auth Required:** No
**Description:** Verify the OTP sent to email

**Request:**
```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "OTP verified successfully",
  "data": {
    "email": "user@example.com",
    "verified": true
  }
}
```

**Errors:**
- `400` - Invalid OTP
- `400` - OTP expired
- `400` - Email not found

---

### 3. Register - Complete

**Endpoint:** `POST /register/complete`
**Auth Required:** No
**Description:** Complete registration with user details and password

**Request:**
```json
{
  "email": "user@example.com",
  "otp": "123456",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "08012345678",
  "password": "SecurePassword123!",
  "password_confirmation": "SecurePassword123!"
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Registration completed successfully",
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "phone": "08012345678",
      "is_verified": false,
      "created_at": "2025-11-11T14:30:00Z"
    },
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**Errors:**
- `400` - Passwords don't match
- `400` - OTP not verified
- `400` - Weak password

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number

---

### 4. Email Activation

**Endpoint:** `POST /register/email/activation`
**Auth Required:** Yes
**Description:** Activate email via activation link

**Request:**
```json
{
  "token": "activation_token_from_email"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Email activated successfully",
  "data": {
    "email_verified": true
  }
}
```

---

### 5. Login

**Endpoint:** `POST /login`
**Auth Required:** No
**Description:** Login with email and password

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
  "message": "Login successful",
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "is_verified": false,
      "has_bvn": false,
      "account_tier": "Tier 1"
    },
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**Errors:**
- `401` - Invalid credentials
- `401` - Account inactive

---

### 6. Request Password Reset OTP

**Endpoint:** `POST /request-otp`
**Auth Required:** No
**Description:** Request OTP for password reset

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "OTP sent to your email",
  "data": {
    "email": "user@example.com",
    "otp_expires_at": "2025-11-11T14:35:00Z"
  }
}
```

---

### 7. Verify Password Reset OTP

**Endpoint:** `POST /verify-otp`
**Auth Required:** No
**Description:** Verify OTP for password reset

**Request:**
```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "OTP verified",
  "data": {
    "verified": true,
    "reset_token": "temp_reset_token"
  }
}
```

---

### 8. Reset Password

**Endpoint:** `POST /reset-password`
**Auth Required:** No
**Description:** Reset password with verified OTP

**Request:**
```json
{
  "email": "user@example.com",
  "otp": "123456",
  "new_password": "NewPassword123!",
  "new_password_confirmation": "NewPassword123!"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Password reset successful"
}
```

---

### 9. Register FCM Device Token

**Endpoint:** `POST /device-fcm-token`
**Auth Required:** Yes
**Description:** Register device for push notifications

**Request:**
```json
{
  "fcm_token": "firebase_cloud_messaging_token",
  "device_name": "John's iPhone",
  "device_type": "ios"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Device registered successfully"
}
```

---

## Account & Profile

**Base Path:** `/api/v1/account/`

### 1. Get Profile

**Endpoint:** `GET /profile`
**Auth Required:** Yes
**Description:** Get current user's profile information

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "phone": "08012345678",
    "first_name": "John",
    "last_name": "Doe",
    "dob": "1990-01-15",
    "address": "123 Main Street, Lagos",
    "country": "Nigeria",
    "state": "Lagos",
    "image": "https://s3.amazonaws.com/...",
    "is_verified": false,
    "has_bvn": false,
    "has_nin": false,
    "account_tier": "Tier 1",
    "email_verified": false,
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

---

### 2. Update Profile

**Endpoint:** `PUT /profile`
**Auth Required:** Yes
**Description:** Update user profile information

**Request:**
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "phone": "08087654321",
  "dob": "1990-01-15",
  "address": "456 New Street, Lagos",
  "state": "Lagos",
  "country": "Nigeria"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Smith",
    // ... updated fields
  }
}
```

---

### 3. Update BVN

**Endpoint:** `POST /bvn-update`
**Auth Required:** Yes
**Description:** Verify and update user's BVN

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
  "message": "BVN verified successfully",
  "data": {
    "has_bvn": true,
    "bvn_first_name": "John",
    "bvn_last_name": "Doe",
    "bvn_dob": "15-Jan-1990",
    "bvn_phone": "08012345678",
    "is_verified": true,
    "account_tier": "Tier 2"
  }
}
```

**Errors:**
- `400` - Invalid BVN format (must be 11 digits)
- `400` - BVN verification failed
- `400` - Name mismatch

---

### 4. Update NIN

**Endpoint:** `POST /nin-update`
**Auth Required:** Yes
**Description:** Verify and update user's NIN

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
  "message": "NIN verified successfully",
  "data": {
    "has_nin": true,
    "nin_first_name": "John",
    "nin_last_name": "Doe",
    "nin_dob": "15-Jan-1990",
    "is_verified": true,
    "account_tier": "Tier 2"
  }
}
```

---

### 5. Get Account Tier Info

**Endpoint:** `GET /tier-info`
**Auth Required:** Yes
**Description:** Get information about current account tier and limits

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "current_tier": "Tier 1",
    "tiers": {
      "tier_1": {
        "name": "Tier 1",
        "verification_required": "None",
        "transaction_limit": "₦50,000",
        "features": ["Basic savings", "Limited withdrawals"]
      },
      "tier_2": {
        "name": "Tier 2",
        "verification_required": "BVN or NIN",
        "transaction_limit": "₦1,000,000",
        "features": ["All Tier 1 features", "Higher limits", "Community access"]
      },
      "tier_3": {
        "name": "Tier 3",
        "verification_required": "BVN + NIN",
        "transaction_limit": "₦10,000,000",
        "features": ["All Tier 2 features", "Priority support", "Investment options"]
      }
    }
  }
}
```

---

### 6. Get Verification Status

**Endpoint:** `GET /verification-status`
**Auth Required:** Yes
**Description:** Check user's verification status

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "is_verified": false,
    "has_bvn": false,
    "has_nin": false,
    "email_verified": false,
    "phone_verified": false,
    "account_tier": "Tier 1",
    "next_steps": [
      "Verify your BVN to upgrade to Tier 2",
      "Verify your email address"
    ]
  }
}
```

---

### 7. Sync Embedly Verification

**Endpoint:** `POST /sync-embedly`
**Auth Required:** Yes
**Description:** Sync verification status with Embedly payment provider

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Sync completed",
  "data": {
    "embedly_customer_id": "embedly_cust_123",
    "kyc_tier": "tier_2",
    "is_verified": true
  }
}
```

---

### 8. Create Wallet

**Endpoint:** `POST /create-wallet`
**Auth Required:** Yes
**Description:** Create virtual wallet for user (called during onboarding)

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Wallet created successfully",
  "data": {
    "wallet_id": "550e8400-e29b-41d4-a716-446655440000",
    "account_number": "1234567890",
    "bank_name": "Providus Bank",
    "account_name": "JOHN DOE",
    "balance": 0
  }
}
```

---

## Wallet Management

**Base Path:** `/api/v1/wallet/`

### 1. Get Wallet Balance

**Endpoint:** `GET /balance`
**Auth Required:** Yes
**Description:** Get current wallet balance and account details

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "balance": 850000.00,
    "currency": "NGN",
    "account_number": "1234567890",
    "bank": "Providus Bank",
    "bank_code": "001",
    "account_name": "JOHN DOE",
    "embedly_wallet_id": "embedly_wallet_123"
  }
}
```

---

### 2. Get Transaction History

**Endpoint:** `GET /history`
**Auth Required:** Yes
**Description:** Get wallet transaction history

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "transaction_type": "credit",
        "amount": 50000.00,
        "description": "Bank transfer deposit",
        "sender_name": "John Doe",
        "sender_account": "0123456789",
        "external_reference": "NIP_REF_123",
        "created_at": "2025-11-10T14:30:00Z"
      },
      {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "transaction_type": "debit",
        "amount": 10000.00,
        "description": "Savings contribution",
        "created_at": "2025-11-09T10:15:00Z"
      }
    ],
    "count": 45,
    "next": "https://api.gidinest.com/api/v1/wallet/history?page=2",
    "previous": null
  }
}
```

---

### 3. Request Withdrawal

**Endpoint:** `POST /withdraw/request`
**Auth Required:** Yes
**Description:** Request withdrawal to bank account

**Request:**
```json
{
  "amount": 50000.00,
  "bank_name": "Access Bank",
  "bank_code": "044",
  "account_number": "0123456789",
  "account_name": "John Doe"
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Withdrawal request submitted",
  "data": {
    "withdrawal_id": 123,
    "amount": 50000.00,
    "fee": 100.00,
    "net_amount": 49900.00,
    "status": "pending",
    "bank_name": "Access Bank",
    "account_number": "0123456789",
    "created_at": "2025-11-11T14:30:00Z"
  }
}
```

**Errors:**
- `400` - Insufficient balance
- `400` - Invalid bank account
- `400` - Transaction PIN required

---

### 4. Check Withdrawal Status

**Endpoint:** `GET /withdraw/status/<withdrawal_id>`
**Auth Required:** Yes
**Description:** Check status of withdrawal request

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "withdrawal_id": 123,
    "amount": 50000.00,
    "status": "completed",
    "transaction_ref": "EMBEDLY_TXN_123",
    "bank_name": "Access Bank",
    "account_number": "0123456789",
    "created_at": "2025-11-11T14:30:00Z",
    "updated_at": "2025-11-11T14:35:00Z"
  }
}
```

**Statuses:**
- `pending` - Request received
- `processing` - Being processed
- `completed` - Successfully transferred
- `failed` - Transfer failed

---

### 5. Get Banks List

**Endpoint:** `GET /banks`
**Auth Required:** Yes
**Description:** Get list of supported Nigerian banks

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "banks": [
      {
        "bank_code": "044",
        "bank_name": "Access Bank"
      },
      {
        "bank_code": "063",
        "bank_name": "Diamond Bank"
      }
      // ... more banks
    ]
  }
}
```

---

### 6. Resolve Bank Account

**Endpoint:** `POST /resolve-bank-account`
**Auth Required:** Yes
**Description:** Verify bank account and get account name

**Request:**
```json
{
  "account_number": "0123456789",
  "bank_code": "044"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "account_number": "0123456789",
    "account_name": "JOHN DOE",
    "bank_code": "044",
    "bank_name": "Access Bank"
  }
}
```

**Errors:**
- `400` - Invalid account number
- `400` - Bank account not found

---

### 7. Set Transaction PIN

**Endpoint:** `POST /transaction-pin/set`
**Auth Required:** Yes
**Description:** Set 4-digit transaction PIN for withdrawals

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
  "message": "Transaction PIN set successfully",
  "data": {
    "transaction_pin_set": true
  }
}
```

**PIN Requirements:**
- Exactly 4 digits
- Numeric only
- Cannot be sequential (e.g., 1234, 4321)
- Cannot be repeated (e.g., 1111)

---

### 8. Verify Transaction PIN

**Endpoint:** `POST /transaction-pin/verify`
**Auth Required:** Yes
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
  "message": "PIN verified",
  "data": {
    "verified": true
  }
}
```

**Errors:**
- `400` - Invalid PIN
- `429` - Too many failed attempts (locked for 15 minutes)

---

### 9. Get Transaction PIN Status

**Endpoint:** `GET /transaction-pin/status`
**Auth Required:** Yes
**Description:** Check if user has set transaction PIN

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "transaction_pin_set": true
  }
}
```

---

### 10. Embedly Webhook (Deposits)

**Endpoint:** `POST /embedly/webhook/secure`
**Auth Required:** No (Signature verification)
**Description:** Receive deposit notifications from Embedly

**Headers:**
```
X-Auth-Signature: signature_from_embedly
```

**Request:**
```json
{
  "event": "nip",
  "data": {
    "amount": 50000,
    "accountNumber": "1234567890",
    "senderName": "John Doe",
    "senderAccount": "0123456789",
    "sessionId": "session_123",
    "transactionReference": "NIP_REF_123"
  }
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Webhook processed"
}
```

---

### 11. Payout Webhook

**Endpoint:** `POST /payout/webhook`
**Auth Required:** No (Signature verification)
**Description:** Receive payout status updates from Embedly

**Request:**
```json
{
  "event": "payout.completed",
  "data": {
    "transactionReference": "EMBEDLY_TXN_123",
    "status": "completed",
    "amount": 50000
  }
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Webhook processed"
}
```

---

## Savings & Goals

**Base Path:** `/api/v1/savings/`

### 1. List Savings Goals

**Endpoint:** `GET /goals`
**Auth Required:** Yes
**Description:** Get all user's savings goals

**Query Parameters:**
- `status`: Filter by status (active, completed, paused, cancelled)

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "goals": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Emergency Fund",
        "amount": 250000.00,
        "target_amount": 500000.00,
        "status": "active",
        "interest_rate": 10.0,
        "accrued_interest": 5000.00,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-11-10T14:30:00Z"
      }
    ]
  }
}
```

---

### 2. Create Savings Goal

**Endpoint:** `POST /goals`
**Auth Required:** Yes
**Description:** Create new savings goal

**Request:**
```json
{
  "name": "Emergency Fund",
  "target_amount": 500000.00
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Savings goal created",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Emergency Fund",
    "amount": 0.00,
    "target_amount": 500000.00,
    "status": "active",
    "interest_rate": 10.0,
    "accrued_interest": 0.00,
    "created_at": "2025-11-11T14:30:00Z"
  }
}
```

---

### 3. Delete Savings Goal

**Endpoint:** `DELETE /goals/<goal_id>/`
**Auth Required:** Yes
**Description:** Delete a savings goal (funds returned to wallet)

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Goal deleted successfully",
  "data": {
    "refunded_amount": 250000.00,
    "wallet_balance": 1100000.00
  }
}
```

---

### 4. Contribute or Withdraw from Goal

**Endpoint:** `POST /goals/contribute-withdraw`
**Auth Required:** Yes
**Description:** Add money to or withdraw from a savings goal

**Request (Contribute):**
```json
{
  "goal_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": 50000.00,
  "transaction_type": "contribution"
}
```

**Request (Withdraw):**
```json
{
  "goal_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": 10000.00,
  "transaction_type": "withdrawal"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Transaction successful",
  "data": {
    "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
    "goal": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Emergency Fund",
      "amount": 300000.00,
      "target_amount": 500000.00
    },
    "wallet_balance": 550000.00
  }
}
```

**Errors:**
- `400` - Insufficient wallet balance (for contribution)
- `400` - Insufficient goal balance (for withdrawal)

---

### 5. Get All Savings History

**Endpoint:** `GET /history/all`
**Auth Required:** Yes
**Description:** Get all savings transactions across all goals

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "goal": {
          "id": "550e8400-e29b-41d4-a716-446655440001",
          "name": "Emergency Fund"
        },
        "transaction_type": "contribution",
        "amount": 50000.00,
        "goal_current_amount": 300000.00,
        "timestamp": "2025-11-10T14:30:00Z"
      }
    ]
  }
}
```

---

### 6. Get Goal-Specific History

**Endpoint:** `GET /history/<goal_id>`
**Auth Required:** Yes
**Description:** Get transaction history for specific goal

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "goal": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Emergency Fund"
    },
    "transactions": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "transaction_type": "contribution",
        "amount": 50000.00,
        "description": "Monthly contribution",
        "goal_current_amount": 300000.00,
        "timestamp": "2025-11-10T14:30:00Z"
      }
    ],
    "total_contributed": 300000.00,
    "total_withdrawn": 0.00
  }
}
```

---

### 7. Get Savings Dashboard Analytics

**Endpoint:** `GET /dashboard-analytics`
**Auth Required:** Yes
**Description:** Get savings analytics and statistics

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "total_saved": 550000.00,
    "total_interest_earned": 15000.00,
    "active_goals": 3,
    "completed_goals": 1,
    "total_goals": 4,
    "this_month_contributions": 150000.00,
    "average_monthly_savings": 125000.00,
    "goals_breakdown": [
      {
        "name": "Emergency Fund",
        "amount": 300000.00,
        "percentage": 54.5
      },
      {
        "name": "Vacation Fund",
        "amount": 250000.00,
        "percentage": 45.5
      }
    ]
  }
}
```

---

## Community

**Base Path:** `/api/v1/community/`

### 1. List Posts

**Endpoint:** `GET /posts`
**Auth Required:** Yes
**Description:** Get community posts feed

**Query Parameters:**
- `page`: Page number
- `limit`: Items per page
- `search`: Search in title and content

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "count": 234,
    "next": "https://api.gidinest.com/api/v1/community/posts?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "author": {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "first_name": "Jane",
          "last_name": "Doe"
        },
        "title": "My Savings Journey",
        "content": "Just reached my first goal!",
        "likes_count": 45,
        "views_count": 320,
        "created_at": "2025-11-10T14:30:00Z",
        "updated_at": "2025-11-10T14:30:00Z"
      }
    ]
  }
}
```

---

### 2. Create Post

**Endpoint:** `POST /posts`
**Auth Required:** Yes
**Description:** Create new community post

**Request:**
```json
{
  "title": "My Savings Journey",
  "content": "Just reached my first savings goal of ₦500,000! Here's how I did it..."
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Post created successfully",
  "data": {
    "id": 1,
    "author": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "first_name": "Jane",
      "last_name": "Doe"
    },
    "title": "My Savings Journey",
    "content": "Just reached my first savings goal...",
    "likes_count": 0,
    "views_count": 0,
    "created_at": "2025-11-11T14:30:00Z"
  }
}
```

---

### 3. Get Post Details

**Endpoint:** `GET /posts/<post_id>`
**Auth Required:** Yes
**Description:** Get single post with full details

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": 1,
    "author": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "first_name": "Jane",
      "last_name": "Doe"
    },
    "title": "My Savings Journey",
    "content": "Just reached my first savings goal...",
    "likes_count": 45,
    "views_count": 320,
    "created_at": "2025-11-10T14:30:00Z",
    "updated_at": "2025-11-10T14:30:00Z"
  }
}
```

---

### 4. Update Post

**Endpoint:** `PUT /posts/<post_id>`
**Auth Required:** Yes
**Description:** Update own post

**Request:**
```json
{
  "title": "Updated Title",
  "content": "Updated content..."
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Post updated successfully",
  "data": {
    // updated post
  }
}
```

**Errors:**
- `403` - Not the post author

---

### 5. Delete Post

**Endpoint:** `DELETE /posts/<post_id>`
**Auth Required:** Yes
**Description:** Delete own post

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Post deleted successfully"
}
```

**Errors:**
- `403` - Not the post author

---

### 6. List Post Comments

**Endpoint:** `GET /posts/<post_id>/comments`
**Auth Required:** Yes
**Description:** Get comments for a post

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": 1,
        "post_id": 1,
        "author": {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "first_name": "John",
          "last_name": "Doe"
        },
        "content": "Congratulations!",
        "created_at": "2025-11-10T15:00:00Z"
      }
    ]
  }
}
```

---

### 7. Add Comment

**Endpoint:** `POST /posts/<post_id>/comments`
**Auth Required:** Yes
**Description:** Add comment to a post

**Request:**
```json
{
  "content": "Congratulations on reaching your goal!"
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "Comment added",
  "data": {
    "id": 1,
    "post_id": 1,
    "author": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "first_name": "John",
      "last_name": "Doe"
    },
    "content": "Congratulations!",
    "created_at": "2025-11-11T14:30:00Z"
  }
}
```

---

### 8. Get Comment

**Endpoint:** `GET /comments/<comment_id>`
**Auth Required:** Yes
**Description:** Get single comment details

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": 1,
    "post_id": 1,
    "author": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "first_name": "John"
    },
    "content": "Congratulations!",
    "created_at": "2025-11-10T15:00:00Z"
  }
}
```

---

### 9. Update Comment

**Endpoint:** `PUT /comments/<comment_id>`
**Auth Required:** Yes
**Description:** Update own comment

**Request:**
```json
{
  "content": "Updated comment text"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Comment updated"
}
```

---

### 10. Delete Comment

**Endpoint:** `DELETE /comments/<comment_id>`
**Auth Required:** Yes
**Description:** Delete own comment

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Comment deleted"
}
```

---

## Error Handling

### Standard Error Response

```json
{
  "success": false,
  "message": "Error description",
  "errors": {
    "field_name": ["Error message for this field"]
  }
}
```

### Common Error Codes

| Code | Message | Cause |
|------|---------|-------|
| `AUTH_001` | Invalid credentials | Wrong email/password |
| `AUTH_002` | Token expired | JWT token has expired |
| `AUTH_003` | Token invalid | Malformed JWT token |
| `WALLET_001` | Insufficient balance | Not enough funds |
| `WALLET_002` | Invalid amount | Amount <= 0 |
| `PIN_001` | Invalid PIN | Wrong PIN entered |
| `PIN_002` | PIN locked | Too many failed attempts |
| `KYC_001` | BVN verification failed | Invalid BVN |
| `KYC_002` | Name mismatch | BVN name doesn't match profile |

---

## Rate Limiting

Current rate limits (subject to change):

| Endpoint Type | Limit |
|---------------|-------|
| Authentication | 5 requests per minute |
| General API | 60 requests per minute |
| Webhooks | No limit |

**Rate Limit Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1636627200
```

**Rate Limit Exceeded Response:**
```json
{
  "success": false,
  "message": "Rate limit exceeded. Try again in 42 seconds.",
  "retry_after": 42
}
```

---

## Change Log

### Version 1.0 (Current - Production)
- Initial API version
- All endpoints stable and in production
- Used by web application
- **Status:** FROZEN - No breaking changes allowed

---

## Support

For API support:
- Email: dev@gidinest.com
- Documentation: https://docs.gidinest.com
- Status Page: https://status.gidinest.com

---

**Document End**
