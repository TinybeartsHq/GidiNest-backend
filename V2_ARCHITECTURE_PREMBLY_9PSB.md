# V2 Architecture: Prembly + 9PSB Integration Plan

**Created:** 2025-12-15
**Status:** Planning Phase
**Goal:** Migrate from Embedly to Prembly (KYC) + 9PSB (Banking)

---

## 🎯 Overview

### Current State (V1)
- **KYC Provider:** Embedly
- **Wallet Provider:** Embedly
- **Status:** Production (Stable)
- **API Version:** V1

### Target State (V2)
- **KYC Provider:** Prembly (BVN + NIN verification)
- **Wallet Provider:** 9PSB (9 Payment Service Bank)
- **Status:** To be implemented
- **API Version:** V2

### Strategy
- **V1:** Keep running with Embedly (no changes)
- **V2:** New mobile app uses Prembly + 9PSB
- **Migration:** Gradual transition, dual operation during testing

---

## 📊 Architecture Comparison

| Component | V1 (Current) | V2 (Target) | Status |
|-----------|-------------|-------------|--------|
| **BVN Verification** | Embedly `upgrade_kyc()` | Prembly `verify_bvn()` | ✅ Helper ready |
| **NIN Verification** | Embedly `upgrade_kyc_nin()` | Prembly `verify_nin()` | ✅ Helper ready |
| **Wallet Creation** | Embedly `create_wallet()` | 9PSB API | ❌ Not started |
| **Deposits** | Embedly webhook | 9PSB webhook | ❌ Not started |
| **Withdrawals** | Embedly API | 9PSB API | ❌ Not started |
| **Balance Check** | Embedly API | 9PSB API | ❌ Not started |
| **Transaction History** | Embedly API | 9PSB API | ❌ Not started |

---

## 🏗️ V2 Implementation Roadmap

### Phase 1: Prembly KYC Integration ✅ (Partially Complete)

**Status:** Helper functions ready, views not implemented

#### Completed:
- ✅ `verify_bvn()` function in `providers/helpers/prembly.py`
- ✅ `verify_nin()` function in `providers/helpers/prembly.py`
- ✅ Database fields for BVN/NIN data
- ✅ `PREMBLY_API_KEY` configuration

#### TODO:
- ❌ Create V2 KYC view classes
- ❌ Implement BVN verify + confirm endpoints
- ❌ Implement NIN verify + confirm endpoints
- ❌ Add session/cache for two-step verification
- ❌ Error handling and validation
- ❌ Testing (unit + integration)

**Estimated Effort:** 2-3 days

---

### Phase 2: 9PSB Banking Integration ❌ (Not Started)

**Status:** No code exists, needs full implementation

#### What's Needed:

**1. 9PSB API Client** (`providers/helpers/psb9.py`)
```python
class PSB9Client:
    """Client for 9 Payment Service Bank API"""

    def create_customer(self, customer_data):
        """Create customer account with 9PSB"""
        pass

    def create_wallet(self, customer_id):
        """Create virtual account/wallet"""
        pass

    def get_balance(self, account_number):
        """Get wallet balance"""
        pass

    def get_transaction_history(self, account_number, start_date, end_date):
        """Get transaction history"""
        pass

    def initiate_transfer(self, from_account, to_account, amount):
        """Initiate bank transfer/withdrawal"""
        pass

    def verify_account(self, bank_code, account_number):
        """Verify recipient bank account"""
        pass
```

**2. 9PSB Configuration** (settings.py)
```python
# 9PSB Configuration
PSB9_API_KEY = os.getenv('PSB9_API_KEY', config('PSB9_API_KEY'))
PSB9_API_SECRET = os.getenv('PSB9_API_SECRET', config('PSB9_API_SECRET'))
PSB9_BASE_URL = os.getenv('PSB9_BASE_URL', 'https://api.9psb.com.ng/v1')
PSB9_MERCHANT_ID = os.getenv('PSB9_MERCHANT_ID', config('PSB9_MERCHANT_ID'))
```

**3. 9PSB Webhook Handler** (`wallet/views_v2.py`)
```python
class PSB9WebhookView(APIView):
    """Handle deposit/credit webhooks from 9PSB"""

    def post(self, request):
        # Verify webhook signature
        # Process deposit
        # Credit user wallet
        # Send notifications
        pass
```

**4. V2 Wallet Views**
- `POST /api/v2/wallet/create` - Create wallet with 9PSB
- `GET /api/v2/wallet/balance` - Get balance from 9PSB
- `POST /api/v2/wallet/withdraw` - Initiate withdrawal via 9PSB
- `GET /api/v2/wallet/transactions` - Get transaction history from 9PSB

**Estimated Effort:** 5-7 days

---

### Phase 3: V2 User Onboarding Flow

**Complete user journey with new providers:**

```
1. User registers (OAuth or email)
   ↓
2. User completes profile
   ↓
3. BVN Verification (Prembly)
   - POST /api/v2/kyc/bvn/verify → Returns BVN details
   - POST /api/v2/kyc/bvn/confirm → Saves to DB, creates 9PSB customer
   ↓
4. Wallet Creation (9PSB)
   - Automatically create wallet after BVN confirmation
   - Store 9PSB customer ID and account number
   ↓
5. Optional: NIN Verification (Prembly)
   - POST /api/v2/kyc/nin/verify
   - POST /api/v2/kyc/nin/confirm
   - Upgrade to Tier 2
```

**Estimated Effort:** 3-4 days

---

### Phase 4: Data Migration Strategy

**Question:** What happens to existing V1 users?

#### Option A: Dual Mode (Recommended)
- V1 users continue using Embedly
- New V2 users use Prembly + 9PSB
- Add `provider_version` field to User model
- Wallet model stores both `embedly_wallet_id` and `psb9_account_number`

```python
# User model additions
provider_version = models.CharField(max_length=10, default='v1')  # 'v1' or 'v2'

# Wallet model additions
psb9_customer_id = models.CharField(max_length=255, null=True, blank=True)
psb9_account_number = models.CharField(max_length=20, null=True, blank=True)
```

#### Option B: Full Migration
- Migrate all users from Embedly to 9PSB
- Requires:
  - Balance reconciliation script
  - Transaction history migration
  - Coordinated cutover
  - Risk of data loss/issues

**Recommended:** Option A (Dual Mode)

**Estimated Effort:** 1-2 days

---

## 🔧 Technical Requirements

### Information Needed from 9PSB:

1. **API Documentation**
   - Base URL (sandbox + production)
   - Authentication method (API key, OAuth, etc.)
   - Available endpoints
   - Request/response formats

2. **Onboarding Requirements**
   - What data needed to create customer?
   - KYC requirements (do they accept BVN from Prembly?)
   - Account number format
   - Wallet limits

3. **Webhook Configuration**
   - Webhook URL format
   - Signature verification method
   - Payload structure for deposits
   - Retry policy

4. **Transaction Capabilities**
   - Supported banks for transfers
   - Transfer limits
   - Processing time
   - Fees structure

5. **Testing Environment**
   - Sandbox API access
   - Test credentials
   - Mock webhook functionality

---

## 📋 Implementation Checklist

### Prembly KYC (Phase 1)
- [x] Add BVN verification helper
- [x] Add NIN verification helper
- [x] Configure API key
- [ ] Create `BVNVerifyView`
- [ ] Create `BVNConfirmView`
- [ ] Create `NINVerifyView`
- [ ] Create `NINConfirmView`
- [ ] Add session management
- [ ] Write tests
- [ ] Update V2 API documentation

### 9PSB Banking (Phase 2)
- [ ] Obtain 9PSB API credentials (sandbox)
- [ ] Review 9PSB API documentation
- [ ] Create `PSB9Client` helper class
- [ ] Implement customer creation
- [ ] Implement wallet creation
- [ ] Implement balance check
- [ ] Implement transaction history
- [ ] Implement transfers/withdrawals
- [ ] Create webhook handler
- [ ] Test webhook signature verification
- [ ] Write tests
- [ ] Update V2 API documentation

### Integration (Phase 3)
- [ ] Update V2 registration flow
- [ ] Connect BVN confirmation → 9PSB customer creation
- [ ] Connect wallet creation to 9PSB
- [ ] Update V2 dashboard to use 9PSB data
- [ ] Update transaction endpoints
- [ ] End-to-end testing
- [ ] Performance testing

### Migration (Phase 4)
- [ ] Add `provider_version` field to models
- [ ] Add 9PSB fields to Wallet model
- [ ] Create migration scripts
- [ ] Test dual-mode operation
- [ ] Create rollback plan
- [ ] Document migration process

---

## ⚠️ Critical Questions to Answer

Before proceeding, we need to clarify:

1. **9PSB API Access:**
   - Do you have 9PSB API credentials?
   - Do you have access to their API documentation?
   - Is there a sandbox/test environment?

2. **Integration Approach:**
   - Does 9PSB accept KYC from Prembly directly?
   - Or do we need to pass BVN data to 9PSB for their own verification?

3. **Migration Timeline:**
   - When do you want to launch V2?
   - Will V1 continue to operate indefinitely?
   - Or is there a cutoff date to migrate all users?

4. **Existing Users:**
   - Keep them on Embedly (V1)?
   - Migrate them to 9PSB?
   - Allow them to choose?

5. **Feature Parity:**
   - Does 9PSB support all features Embedly has?
   - Are there any Embedly features we need to drop?
   - Are there new 9PSB features to add?

---

## 🎯 Recommended Next Steps

### Immediate (This Week)
1. ✅ Complete Prembly helper functions (DONE)
2. 📝 Get 9PSB API documentation and credentials
3. 📝 Review 9PSB capabilities and requirements
4. 📝 Decide on migration strategy (dual-mode vs full migration)

### Short-term (Next 2 Weeks)
1. Implement V2 KYC views with Prembly
2. Create basic 9PSB client with core functions
3. Test KYC flow end-to-end
4. Test wallet creation with 9PSB

### Medium-term (Next Month)
1. Implement all 9PSB wallet operations
2. Set up webhook handling
3. Complete V2 API endpoints
4. Comprehensive testing
5. Deploy to staging

### Long-term (Next Quarter)
1. Beta testing with select users
2. Monitor performance and errors
3. Gradual rollout to production
4. Plan Embedly deprecation (if applicable)

---

## 📞 Action Items

**For you to provide:**
1. 9PSB API documentation or access
2. 9PSB credentials (sandbox + production)
3. Clarification on migration strategy
4. Timeline for V2 launch

**For development:**
1. Implement V2 KYC views (can start now)
2. Create 9PSB client (needs API docs)
3. Build V2 wallet endpoints (needs 9PSB client)
4. Testing and deployment

---

**Ready to proceed?** Let me know if you have the 9PSB API documentation, and I can start implementing the integration!
