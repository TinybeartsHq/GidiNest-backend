# Remaining Backend Work for Mobile App

**Date:** November 12, 2025
**Frontend Status:** ✅ 98% Complete (79/81 tasks done)
**Backend Status:** 🔄 V2 APIs Need Implementation

---

## 📊 Current Situation

### ✅ What's Working (Production Ready)
- **V2 Authentication** - All auth endpoints fully implemented
- **V1 Wallet** - Balance, history, withdrawal, banks, PIN management
- **V1 KYC** - BVN/NIN verification, tier info, profile management
- **V1 Account** - Profile CRUD, verification status

### 🔄 What Needs Backend Implementation

Mobile app is **98% complete** but blocked on these V2 backend APIs:

---

## 🚨 HIGH PRIORITY - Mobile Blockers

### 1. Dashboard API (V2) - ⚠️ CRITICAL
**Current Status:** 🔄 Placeholder returns stub data
**File:** `dashboard/views.py:11-42`
**Mobile Impact:** Dashboard screen can't display real unified data

**Required Implementation:**
```python
GET /api/v2/dashboard/

Response should include:
{
  "user": {
    "id": "uuid",
    "first_name": "John",
    "last_name": "Doe",
    "email": "user@example.com",
    "account_tier": "Tier 2",
    "has_passcode": true,
    "has_pin": true
  },
  "wallet": {
    "balance": "50000.00",  // NGN
    "account_number": "1234567890",
    "bank_name": "Embedly Virtual Bank"
  },
  "quick_stats": {
    "total_savings": "25000.00",
    "active_goals": 3,
    "this_month_contributions": "5000.00"
  },
  "recent_transactions": [
    // Last 5 transactions
    {
      "id": "uuid",
      "type": "deposit",
      "amount": "10000.00",
      "description": "Wallet funding",
      "created_at": "2025-11-12T10:30:00Z",
      "status": "completed"
    }
  ],
  "savings_goals": [
    // Active savings goals
    {
      "id": "uuid",
      "name": "Emergency Fund",
      "target_amount": "100000.00",
      "current_amount": "50000.00",
      "progress_percentage": 50,
      "due_date": "2025-12-31"
    }
  ],
  "restrictions": {
    "is_restricted": false,
    "restricted_until": null,
    "restricted_limit": null
  }
}
```

**TODO:**
- [ ] Query user profile
- [ ] Get wallet balance from V1 wallet API or Embedly
- [ ] Calculate savings totals from savings goals
- [ ] Get recent transactions (last 5) from wallet history
- [ ] Get active savings goals
- [ ] Check restriction status
- [ ] Add Redis caching (30 seconds TTL)
- [ ] Error handling for missing wallet (404)

**Estimated Effort:** 2-3 hours

---

### 2. Transactions API (V2) - ⚠️ CRITICAL
**Current Status:** 🔄 Placeholder returns stub data
**File:** `transactions/views.py:11-76`
**Mobile Impact:** Transaction screens can't filter/paginate properly

**Required Implementation:**

#### Endpoint 1: List Transactions
```python
GET /api/v2/transactions/
Query Params:
  - type: "deposit" | "withdrawal" | "goal_funding" | "goal_withdrawal"
  - status: "pending" | "completed" | "failed"
  - start_date: "2025-11-01"
  - end_date: "2025-11-30"
  - page: 1
  - page_size: 20

Response:
{
  "count": 150,
  "next": "https://api.gidinest.com/api/v2/transactions/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "type": "deposit",
      "amount": "10000.00",
      "description": "Wallet funding via NIP",
      "status": "completed",
      "created_at": "2025-11-12T10:30:00Z",
      "metadata": {
        "bank_name": "GTBank",
        "account_number": "0123456789",
        "transaction_ref": "NIP202511121030"
      }
    }
  ],
  "summary": {
    "total_deposits": "50000.00",
    "total_withdrawals": "20000.00",
    "total_fees": "100.00",
    "net_change": "29900.00"
  }
}
```

#### Endpoint 2: Transaction Detail
```python
GET /api/v2/transactions/<uuid>

Response:
{
  "id": "uuid",
  "type": "withdrawal",
  "amount": "5000.00",
  "fee": "50.00",
  "total_amount": "5050.00",
  "description": "Withdrawal to GTBank",
  "status": "completed",
  "created_at": "2025-11-12T10:30:00Z",
  "completed_at": "2025-11-12T10:31:00Z",
  "metadata": {
    "bank_name": "GTBank",
    "account_number": "0123456789",
    "account_name": "John Doe",
    "transaction_ref": "WD202511121030",
    "embedly_ref": "EMBL123456"
  },
  "timeline": [
    {
      "status": "initiated",
      "timestamp": "2025-11-12T10:30:00Z",
      "note": "Withdrawal request received"
    },
    {
      "status": "processing",
      "timestamp": "2025-11-12T10:30:30Z",
      "note": "Processing via Embedly"
    },
    {
      "status": "completed",
      "timestamp": "2025-11-12T10:31:00Z",
      "note": "Transfer successful"
    }
  ]
}
```

**TODO:**
- [ ] Query all transaction types (WalletTransaction, GoalTransaction models)
- [ ] Apply filters (type, status, date range)
- [ ] Implement pagination (20 per page)
- [ ] Calculate summary statistics
- [ ] Transaction detail with timeline
- [ ] Add metadata field mapping
- [ ] Handle missing transactions (404)

**Estimated Effort:** 3-4 hours

---

## 🔄 MEDIUM PRIORITY - Nice to Have

### 3. Savings Goals API (V2) - Optional Enhancement
**Current Status:** ✅ V1 savings endpoints work, but not unified with V2
**Mobile Impact:** Savings screens work but could benefit from V2 standardization

**Current V1 Endpoints Working:**
- `GET /api/v1/savings/goals/` - List goals
- `POST /api/v1/savings/goals/` - Create goal
- `GET /api/v1/savings/goals/<id>/` - Goal detail
- `POST /api/v1/savings/goals/<id>/fund/` - Add funds
- `POST /api/v1/savings/goals/<id>/withdraw/` - Withdraw funds

**Potential V2 Improvements:**
- Unified response format with V2 auth
- Better progress tracking
- Milestones and achievements
- Social sharing features

**Priority:** LOW - V1 works fine
**Estimated Effort:** 4-6 hours (if needed)

---

### 4. Notifications API (V2) - Optional
**Current Status:** 🔄 Placeholder exists
**Mobile Impact:** Mobile app can function without this (using local notifications)

**Potential Implementation:**
```python
GET /api/v2/notifications/
POST /api/v2/notifications/<id>/read
POST /api/v2/notifications/mark-all-read
DELETE /api/v2/notifications/<id>
```

**Priority:** LOW - Not blocking mobile app
**Estimated Effort:** 2-3 hours

---

## 📋 FUTURE ENHANCEMENTS

### 5. OAuth Implementation (Google & Apple Sign In)
**Current Status:** 🔄 Placeholder returns 501
**Files:** `onboarding/views/auth_v2.py:425-479`

**Required:**
- [ ] Google OAuth integration (google-auth library)
- [ ] Apple Sign In integration (apple-signin library)
- [ ] Social account linking
- [ ] Email verification bypass for OAuth users

**Priority:** MEDIUM - Nice UX improvement
**Estimated Effort:** 6-8 hours

---

### 6. Wallet V2 Migration
**Current Status:** ✅ V1 fully functional, V2 placeholders exist
**Recommendation:** KEEP USING V1 - No need to migrate

**Reason:** V1 wallet APIs are production-ready and working perfectly:
- Balance, history, withdrawal all functional
- Embedly integration working
- PIN management complete
- Mobile app already integrated

**Priority:** VERY LOW - Don't migrate unless necessary
**Estimated Effort:** 8-10 hours (not recommended)

---

### 7. KYC V2 Migration
**Current Status:** ✅ V1 fully functional, V2 placeholders exist
**Recommendation:** KEEP USING V1 - No need to migrate

**Reason:** V1 KYC APIs are production-ready:
- BVN/NIN verification working with Embedly
- Tier system implemented
- Profile management complete
- Mobile app already integrated

**Priority:** VERY LOW - Don't migrate unless necessary
**Estimated Effort:** 6-8 hours (not recommended)

---

## 🎯 Recommended Implementation Order

### Week 1 (Highest Priority)
1. **Dashboard API** - Unblock dashboard screen
   - Aggregate data from multiple sources
   - Add caching
   - Handle edge cases (no wallet, no transactions)

2. **Transactions API** - Unblock transaction filtering
   - List with pagination
   - Detail view with timeline
   - Summary statistics

### Week 2 (Medium Priority)
3. **OAuth Integration** - Improve user experience
   - Google Sign In
   - Apple Sign In

4. **Notifications API** - Enhanced user engagement
   - Basic CRUD
   - Push notification integration

### Future (Low Priority)
5. **Provider Abstraction** - Prepare for Embedly migration
   - Create KYC provider interface
   - Implement new provider
   - Data migration strategy

---

## 📊 Work Breakdown

### Backend Work Required:
| Task | Priority | Effort | Status | Blockers |
|------|----------|--------|--------|----------|
| Dashboard API | 🔴 HIGH | 2-3h | 🔄 TODO | Mobile blocked |
| Transactions API | 🔴 HIGH | 3-4h | 🔄 TODO | Mobile blocked |
| OAuth (Google/Apple) | 🟡 MEDIUM | 6-8h | 🔄 TODO | None |
| Notifications API | 🟢 LOW | 2-3h | 🔄 TODO | None |
| Savings V2 | 🟢 LOW | 4-6h | ⏭️ SKIP | V1 works |
| Wallet V2 | 🟢 LOW | 8-10h | ⏭️ SKIP | V1 works |
| KYC V2 | 🟢 LOW | 6-8h | ⏭️ SKIP | V1 works |

**Total Critical Work:** 5-7 hours (Dashboard + Transactions)
**Total Medium Priority:** 6-8 hours (OAuth)
**Total Low Priority:** 6-9 hours (Notifications + others if needed)

---

## 🚀 Quick Start Guide for Backend Implementation

### 1. Dashboard API Implementation

**File:** `dashboard/views.py`

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from wallet.views import WalletBalanceAPIView
from savings.models import SavingsGoal
from wallet.models import WalletTransaction

class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Try cache first
        cache_key = f'dashboard_{request.user.id}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        user = request.user

        # Get wallet balance
        try:
            wallet = user.wallet
            wallet_data = {
                "balance": str(wallet.balance),
                "account_number": wallet.account_number,
                "bank_name": wallet.bank_name or "Embedly Virtual Bank"
            }
        except ObjectDoesNotExist:
            wallet_data = None

        # Get savings goals
        goals = SavingsGoal.objects.filter(user=user, is_active=True)
        total_savings = sum(goal.current_amount for goal in goals)
        this_month_contributions = calculate_month_contributions(goals)

        # Get recent transactions
        recent_transactions = WalletTransaction.objects.filter(
            user=user
        ).order_by('-created_at')[:5]

        # Build response
        data = {
            "user": {
                "id": str(user.id),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "account_tier": user.account_tier,
                "has_passcode": user.passcode_set,
                "has_pin": user.transaction_pin_set
            },
            "wallet": wallet_data,
            "quick_stats": {
                "total_savings": str(total_savings),
                "active_goals": goals.count(),
                "this_month_contributions": str(this_month_contributions)
            },
            "recent_transactions": serialize_transactions(recent_transactions),
            "savings_goals": serialize_goals(goals),
            "restrictions": {
                "is_restricted": user.is_restricted(),
                "restricted_until": user.limit_restricted_until,
                "restricted_limit": user.restricted_limit
            }
        }

        # Cache for 30 seconds
        cache.set(cache_key, data, 30)

        return Response({"success": True, "data": data})
```

### 2. Transactions API Implementation

**File:** `transactions/views.py`

```python
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Sum
from wallet.models import WalletTransaction
from savings.models import GoalTransaction

class TransactionListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Get query params
        transaction_type = request.query_params.get('type')
        status = request.query_params.get('status')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Query wallet transactions
        wallet_txns = WalletTransaction.objects.filter(user=user)

        # Apply filters
        if transaction_type:
            wallet_txns = wallet_txns.filter(transaction_type=transaction_type)
        if status:
            wallet_txns = wallet_txns.filter(status=status)
        if start_date:
            wallet_txns = wallet_txns.filter(created_at__gte=start_date)
        if end_date:
            wallet_txns = wallet_txns.filter(created_at__lte=end_date)

        # Order by most recent
        wallet_txns = wallet_txns.order_by('-created_at')

        # Paginate
        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(wallet_txns, request)

        # Serialize
        transactions = serialize_transactions(result_page)

        # Calculate summary
        summary = calculate_summary(wallet_txns)

        return paginator.get_paginated_response({
            "success": True,
            "data": transactions,
            "summary": summary
        })
```

---

## 📝 Notes

### Why Not Migrate to V2 for Everything?

**V1 APIs that should stay V1:**
1. **Wallet** - Production-ready, Embedly integrated, working perfectly
2. **KYC** - Embedly integrated, tier system working, no benefit to migrate
3. **Account** - Profile management working fine

**V2 APIs that need implementation:**
1. **Dashboard** - New unified endpoint, mobile needs this
2. **Transactions** - Enhanced filtering and pagination, mobile needs this

### Current Mobile App Strategy:
- ✅ Use V2 for Authentication (already implemented)
- ✅ Use V1 for Wallet, KYC, Profile (production-ready)
- 🔄 Need V2 Dashboard and Transactions (must implement)

---

## 🎉 Summary

### Critical Path to Launch:
1. Implement Dashboard API (2-3 hours)
2. Implement Transactions API (3-4 hours)
3. Test with mobile app
4. Deploy to production

**Total Time to Unblock Mobile:** 5-7 hours of backend work

### Everything Else:
- OAuth, Notifications, and other features can be added post-launch
- V1 APIs are production-ready and working well
- No need to migrate V1 to V2 unless there's a specific benefit

---

**Last Updated:** November 12, 2025
**Status:** 🔄 2 Critical APIs Needed, 5-7 hours of work
**Mobile App Status:** ✅ 98% Complete, waiting on backend
