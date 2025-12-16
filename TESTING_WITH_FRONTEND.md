# Testing V2 Flow with Frontend - Troubleshooting Guide

**Last Updated:** 2025-12-15

---

## 🐛 Issue: "BVN Already Used for Another Account"

This error is **working correctly** - the system prevents duplicate BVN usage across accounts.

### Solution: Test with Fresh Data

You have 3 options:

---

## ✅ Option 1: Create New Test User (Recommended)

### On Your Frontend:

**Register a new user with a different email:**
```javascript
const testUser = {
  email: `test${Date.now()}@example.com`,  // Unique email
  password: 'TestPass123!',
  first_name: 'Test',
  last_name: 'User',
  phone: '08098765432'
};

// Register → Login → Verify BVN → Confirm BVN → Wallet Created!
```

---

## ✅ Option 2: Reset BVN Association (Django Shell)

If you want to test with the same user:

```bash
python manage.py shell
```

Then run:
```python
from django.contrib.auth import get_user_model

User = get_user_model()

# Find the user
user = User.objects.get(email='iyoroebiperre@gmail.com')

# Reset BVN fields
user.bvn = None
user.has_bvn = False
user.bvn_first_name = None
user.bvn_last_name = None
user.bvn_dob = None
user.bvn_phone = None
user.account_tier = 'Tier 0'

user.save()

print(f"✅ BVN reset for {user.email}")

# Also delete wallet if exists
try:
    wallet = user.wallet
    wallet.delete()
    print("✅ Wallet deleted")
except:
    print("No wallet found")
```

Now you can test BVN verification again!

---

## ✅ Option 3: Test with Different BVN

If you have multiple test BVNs, use a different one:

```javascript
// Instead of the BVN that's already used
const bvn = '22222222222';  // Try different test BVN
```

---

## 🧪 Complete Testing Flow

### Step-by-Step Frontend Test

**1. Register New User**
```javascript
POST /api/v2/auth/register
{
  "email": "newtest@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "08012345678"
}
```

**2. Verify BVN (Step 1)**
```javascript
POST /api/v2/kyc/bvn/verify
Headers: { "Authorization": "Bearer YOUR_TOKEN" }
Body: { "bvn": "22222222222" }

// Expected: BVN details returned
```

**3. Confirm BVN (Step 2) - Creates Wallet!**
```javascript
POST /api/v2/kyc/bvn/confirm
Headers: { "Authorization": "Bearer YOUR_TOKEN" }
Body: { "bvn": "22222222222", "confirmed": true }

// Expected Response:
{
  "success": true,
  "data": {
    "is_verified": true,
    "account_tier": "Tier 1",
    "wallet": {
      "created": true,
      "account_number": "0123456789",
      "bank": "9PSB"
    }
  }
}
```

**4. Check Wallet**
```javascript
GET /api/v2/wallet/
Headers: { "Authorization": "Bearer YOUR_TOKEN" }

// Shows wallet with account number
```

---

## 📊 What You Should See in Logs (Success)

When everything works correctly, you'll see:

```
INFO Creating 9PSB wallet for user newtest@example.com
INFO Authenticating with 9PSB WAAS API
INFO 9PSB authentication successful
INFO Opening 9PSB wallet for newtest@example.com
INFO 9PSB wallet opened successfully: 0123456789
INFO BVN confirmed and saved for user newtest@example.com, tier: Tier 1
```

---

## ⚠️ What You're Currently Seeing (Error)

```
ERROR 9PSB authentication failed: {'accessToken': '...', 'message': 'successful', ...}
```

**This is now FIXED!** The code was looking for the wrong field in the response.

**Before Fix:**
- Code expected: `data.status == 'success'` and `data.data.token`
- 9PSB returns: `data.message == 'successful'` and `data.accessToken`

**After Fix:**
- Code now checks both formats ✅

---

## 🔄 Testing After Fix

### 1. Restart Django Server

```bash
# Stop current server (Ctrl+C)
# Start fresh
python manage.py runserver
```

### 2. Test with Fresh User

Either:
- Register new user on frontend, OR
- Reset existing user's BVN (see Option 2 above)

### 3. Go Through BVN Flow

**Frontend Flow:**
```
[BVN Input Screen]
Enter BVN: 22222222222
[Verify Button] ✅

↓

[Confirmation Screen]
Name: John Doe
DOB: 15-Jan-1990
[Confirm Button] ✅

↓

[Success Screen]
✅ Verification Complete!
🎉 Wallet Created!
Account: 0123456789
Bank: 9PSB
```

### 4. Check Logs

You should now see:
```
✅ Authenticating with 9PSB WAAS API
✅ 9PSB authentication successful
✅ Creating 9PSB wallet
✅ 9PSB wallet opened successfully: 0123456789
```

---

## 🐞 If Still Getting Errors

### Check 9PSB Connectivity

```bash
# Test direct API call
curl -X POST http://102.216.128.75:9090/bank9ja/api/v2/k1/authenticate \
  -H "Content-Type: application/json" \
  -d '{
    "username": "gidinest",
    "password": "RN7aXaCxGjCF3bj3L3ocNxWwQ6jvFGsWF9AG5CY2cg3aQyGagl",
    "clientId": "waas",
    "clientSecret": "cRAwnWElcNMUZpALdnlve6PubUkCPOQR"
  }'
```

**Expected:**
```json
{
  "accessToken": "eyJ...",
  "message": "successful",
  "expiresIn": "7200"
}
```

### Check Environment Variables

```python
# In Django shell
from django.conf import settings

print(f"Username: {settings.PSB9_USERNAME}")
print(f"Client ID: {settings.PSB9_CLIENT_ID}")
print(f"Base URL: {settings.PSB9_BASE_URL}")

# Should print:
# Username: gidinest
# Client ID: waas
# Base URL: http://102.216.128.75:9090
```

### Check Wallet Opening Endpoint

The wallet opening might need a different endpoint. Check the logs for the full error response after the fix.

---

## 📱 Frontend Error Handling

Update your frontend to show better error messages:

```javascript
const handleBVNConfirm = async () => {
  try {
    const response = await confirmBVN(bvn, true);

    if (response.wallet?.created) {
      // Success! Wallet created
      navigation.navigate('WalletSuccess', {
        accountNumber: response.wallet.account_number,
        bank: response.wallet.bank
      });
    } else {
      // BVN confirmed but wallet creation may have failed
      Alert.alert(
        'Verification Complete',
        'Your BVN is verified! Wallet creation is in progress.',
        [{ text: 'OK', onPress: () => navigation.navigate('Dashboard') }]
      );
    }
  } catch (error) {
    if (error.message.includes('already been used')) {
      Alert.alert(
        'BVN Already Used',
        'This BVN is associated with another account. Please use a different BVN or contact support.',
        [{ text: 'OK' }]
      );
    } else if (error.message.includes('SESSION_EXPIRED')) {
      Alert.alert(
        'Session Expired',
        'Please verify your BVN again.',
        [{ text: 'OK', onPress: () => navigation.goBack() }]
      );
    } else {
      Alert.alert('Error', error.message);
    }
  }
};
```

---

## ✅ Quick Test Checklist

After restarting server with the fix:

- [ ] Server restarted
- [ ] Environment variables set
- [ ] New user registered (or existing user BVN reset)
- [ ] BVN verify succeeds
- [ ] BVN confirm succeeds
- [ ] Wallet created (check response)
- [ ] Account number returned
- [ ] Wallet visible in /api/v2/wallet/

---

## 🎯 Expected Success Flow

**Frontend:**
1. User enters BVN
2. Details displayed for confirmation
3. User confirms
4. Success screen with account number

**Backend:**
1. ✅ BVN verified via Prembly
2. ✅ BVN saved to database
3. ✅ 9PSB authentication (NEW: now working!)
4. ✅ 9PSB wallet created
5. ✅ Account number saved
6. ✅ Response with wallet details

**Logs:**
```
INFO Authenticating with 9PSB WAAS API
INFO 9PSB authentication successful
INFO Creating 9PSB wallet for user...
INFO 9PSB wallet opened successfully: 0123456789
```

---

## 💡 Pro Tips

1. **Use Unique Emails for Testing:**
   ```javascript
   const email = `test${Date.now()}@example.com`;
   ```

2. **Watch Django Logs in Real-Time:**
   ```bash
   tail -f path/to/django.log | grep "9PSB"
   ```

3. **Test with Django Shell First:**
   ```python
   from providers.helpers.psb9 import psb9_client
   token = psb9_client.authenticate()
   print(f"Token: {token[:20]}..." if token else "Failed")
   ```

4. **Keep Test BVNs Organized:**
   - BVN 1: For User A
   - BVN 2: For User B
   - Each BVN can only be used once!

---

**Now try again with a fresh user!** 🚀

The authentication fix should resolve the wallet creation issue. If you still see errors, check the new detailed logs for the wallet opening response.
