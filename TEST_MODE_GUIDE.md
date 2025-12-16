# Test Mode: Duplicate BVN/NIN Testing

**Last Updated:** 2025-12-15

---

## ✅ Test Mode Enabled

I've added a **test mode** that allows duplicate BVNs and NINs in **DEBUG mode only**.

This lets you test the complete flow multiple times with the same BVN without database resets!

---

## 🔧 How It Works

### When `DEBUG = True` (Development):
- ✅ **Duplicate BVNs allowed** - Same BVN can be used for multiple accounts
- ✅ **Duplicate NINs allowed** - Same NIN can be used for multiple accounts
- ⚠️ **Warning logged** - Each duplicate use is logged for visibility

### When `DEBUG = False` (Production):
- ❌ **Duplicate BVNs blocked** - One BVN per account (secure)
- ❌ **Duplicate NINs blocked** - One NIN per account (secure)
- 🔒 **Error returned** - "This BVN/NIN has already been used for another account"

---

## 🧪 Testing Now

### 1. Ensure DEBUG Mode is On

Check your settings:

```python
# settings.py or .env
DEBUG = True  # ✅ Test mode enabled
```

Or check in Django shell:
```python
from django.conf import settings
print(f"DEBUG: {settings.DEBUG}")  # Should be True
```

### 2. Test with Same BVN Multiple Times

**You can now:**
```javascript
// Test User 1
POST /api/v2/kyc/bvn/verify
{ "bvn": "22222222222" }
✅ Works!

// Test User 2 (same BVN!)
POST /api/v2/kyc/bvn/verify
{ "bvn": "22222222222" }
✅ Also works! (TEST MODE)
```

### 3. Check Logs

You'll see warning messages:
```
⚠️ TEST MODE: Allowing duplicate BVN 22222222222 for user test2@example.com
```

This reminds you that in production, this would be blocked.

---

## 📋 Complete Test Flow

Now you can test multiple times without resetting:

```javascript
// Test #1
register('user1@test.com')
verifyBVN('22222222222')
confirmBVN('22222222222')
✅ Wallet created!

// Test #2 (same BVN!)
register('user2@test.com')
verifyBVN('22222222222')  // ✅ Works in TEST MODE
confirmBVN('22222222222')
✅ Wallet created!

// Test #3 (same BVN!)
register('user3@test.com')
verifyBVN('22222222222')  // ✅ Still works!
confirmBVN('22222222222')
✅ Wallet created!
```

**No more "BVN already used" errors during testing!** 🎉

---

## 🔐 Security: Production Behavior

### Before Deployment to Production:

**CRITICAL:** Set `DEBUG = False`

```python
# settings.py or .env
DEBUG = False  # 🔒 Production mode
```

**What happens:**
```javascript
// Production: User 1
register('user1@example.com')
verifyBVN('22222222222')
confirmBVN('22222222222')
✅ Works!

// Production: User 2 (tries same BVN)
register('user2@example.com')
verifyBVN('22222222222')
❌ ERROR: "This BVN has already been used for another account"
```

This protects against:
- Identity fraud
- Account duplication
- BVN sharing

---

## 📊 What's Changed

### BVN Verify View (`account/views_v2_kyc.py`)

**Before:**
```python
# Always check for duplicates
if UserModel.objects.filter(bvn=bvn).exclude(id=user.id).exists():
    return error("BVN already used")
```

**After:**
```python
# Skip duplicate check in DEBUG mode
if not settings.DEBUG:
    if UserModel.objects.filter(bvn=bvn).exclude(id=user.id).exists():
        return error("BVN already used")
else:
    # In DEBUG mode, allow duplicates but log warning
    if UserModel.objects.filter(bvn=bvn).exclude(id=user.id).exists():
        logger.warning(f"⚠️ TEST MODE: Allowing duplicate BVN")
```

Same changes applied to NIN verification!

---

## 🎯 Testing Scenarios

### Scenario 1: Test Same User Multiple Times

```javascript
// First test
user = register('test@example.com')
verifyBVN('22222222222')
confirmBVN('22222222222')
✅ Tier 1, Wallet created

// Want to test again? No problem!
// Just delete and re-register:
deleteUser('test@example.com')
user = register('test@example.com')
verifyBVN('22222222222')  // ✅ Works again!
confirmBVN('22222222222')
✅ Tier 1, Wallet created
```

### Scenario 2: Test Multiple Users Same BVN

```javascript
// User 1
register('user1@test.com')
verifyBVN('22222222222')
confirmBVN('22222222222')
✅ Success

// User 2 (same BVN - TEST MODE only)
register('user2@test.com')
verifyBVN('22222222222')  // ✅ Allowed in TEST MODE
confirmBVN('22222222222')
✅ Success

// User 3 (same BVN)
register('user3@test.com')
verifyBVN('22222222222')  // ✅ Still allowed
confirmBVN('22222222222')
✅ Success
```

### Scenario 3: Test Edge Cases

```javascript
// Test wallet creation failure recovery
register('test@example.com')
verifyBVN('22222222222')
// Simulate 9PSB failure
confirmBVN('22222222222')
// Wallet fails but BVN saved

// Retry same user
verifyBVN('22222222222')  // ❌ "Already verified" (still blocked)

// But can test with new user + same BVN!
register('test2@example.com')
verifyBVN('22222222222')  // ✅ Works in TEST MODE
```

---

## ⚠️ Important Reminders

### For Development:
1. ✅ `DEBUG = True` - Test mode enabled
2. ✅ Use same BVN/NIN multiple times
3. ✅ Test with multiple users
4. ✅ Check logs for warnings

### For Production:
1. 🔒 `DEBUG = False` - Security enabled
2. 🔒 Duplicate BVN/NIN blocked
3. 🔒 One identity per account
4. 🔒 Check logs for blocked attempts

### Always Remember:
- **Test Mode** = Convenient testing
- **Production Mode** = Security first
- **Never deploy with DEBUG=True**

---

## 🚀 Start Testing Now!

**Your current setup:**
```bash
# Check if test mode is enabled
python manage.py shell
>>> from django.conf import settings
>>> print(f"DEBUG: {settings.DEBUG}")
True  # ✅ Test mode enabled!
```

**Test multiple times:**
```javascript
// Now you can test as many times as you want!
for (let i = 0; i < 10; i++) {
  const user = await register(`test${i}@example.com`);
  await verifyBVN('22222222222');  // Same BVN each time!
  await confirmBVN('22222222222');
  console.log(`✅ Test ${i + 1} complete!`);
}
```

**No more database resets needed!** 🎉

---

## 📝 Summary

**What you can do now:**
- ✅ Test BVN flow multiple times
- ✅ Use same BVN for multiple test users
- ✅ No more "BVN already used" errors
- ✅ No database resets needed
- ✅ Faster testing iteration

**What's protected:**
- 🔒 Production will still enforce uniqueness
- 🔒 Real users can't share BVNs
- 🔒 Security maintained when DEBUG=False
- 🔒 Test mode clearly logged

---

**Happy Testing!** 🧪✨

Remember to set `DEBUG=False` before deploying to production!
