# Pre-Deployment Checklist

**Date:** November 6, 2025  
**Status:** ⚠️ **DO NOT DEPLOY YET** - Fix 500 error first

---

## 🚨 Critical Issues to Fix Before Deployment

### 1. **500 Error on Registration** ⚠️ HIGH PRIORITY
- **Issue:** `POST /api/v1/onboarding/register/complete` returns 500 error
- **Status:** Error handling added, but root cause needs investigation
- **Action Required:** 
  - [ ] Test registration locally and capture actual error
  - [ ] Fix the root cause
  - [ ] Verify registration works end-to-end

### 2. **Database Migrations** ✅ DONE
- **Status:** Migrations created and applied locally
- **Migration:** `0023_v2_mobile_schema_updates.py`
- **Action Required:**
  - [x] Migrations created
  - [x] Migrations applied locally
  - [ ] Test migrations on staging/dev database
  - [ ] Backup production database before applying migrations

---

## ✅ Pre-Deployment Checklist

### Code Changes
- [x] V2 authentication endpoints implemented
- [x] PUT method support added for passcode/PIN change
- [x] Serializer field name compatibility (old_passcode/current_passcode)
- [x] Error handling improved in RegisterCompleteView
- [ ] **500 error fixed** ⚠️ BLOCKING
- [ ] All tests passing locally

### Database
- [x] Migrations created (`0023_v2_mobile_schema_updates.py`)
- [x] Migrations applied locally
- [ ] Migrations tested on staging/dev database
- [ ] Database backup created (before production migration)
- [ ] Rollback plan prepared

### Testing
- [ ] V2 authentication endpoints tested
- [ ] V1 registration flow tested (currently failing)
- [ ] Passcode/PIN change tested
- [ ] Token refresh tested
- [ ] Error responses verified

### Documentation
- [x] V2 API checklist created
- [x] Mobile app env config created
- [x] Implementation review completed
- [ ] API documentation updated

---

## 📋 Deployment Order

### Step 1: Fix Critical Issues (DO THIS FIRST)
```bash
# 1. Test registration locally
# 2. Check server logs for actual error
# 3. Fix the 500 error
# 4. Test again to confirm fix
```

### Step 2: Test on Staging/Dev (If Available)
```bash
# 1. Deploy to staging environment
# 2. Run migrations: python manage.py migrate
# 3. Test all endpoints
# 4. Verify no regressions
```

### Step 3: Prepare Production Deployment
```bash
# 1. Backup production database
# 2. Review all code changes
# 3. Ensure environment variables are set
# 4. Prepare rollback plan
```

### Step 4: Deploy to Production
```bash
# 1. Deploy code (without migrations first if zero-downtime)
# 2. Run migrations: python manage.py migrate
# 3. Restart application
# 4. Verify health check endpoint
# 5. Test critical endpoints
```

---

## 🔍 Current Status

### ✅ Ready for Deployment
- V2 authentication endpoints (fully implemented)
- Database migrations (created and tested locally)
- Error handling improvements
- PUT method support

### ⚠️ Blocking Deployment
- **500 error on V1 registration** - MUST FIX FIRST
- Need to verify error is fixed before deploying

### 📝 Recommended Actions

**Before Deploying:**

1. **Fix the 500 error:**
   ```bash
   # Test registration locally
   # Check error logs
   # Fix the issue
   # Test again
   ```

2. **Verify migrations work:**
   ```bash
   # On staging/dev database
   python manage.py migrate account
   # Verify no errors
   ```

3. **Test critical flows:**
   - [ ] V1 registration (currently broken)
   - [ ] V2 signup
   - [ ] V2 signin
   - [ ] Passcode setup/change
   - [ ] PIN setup/change

---

## 🚀 Deployment Steps (When Ready)

### Option A: Zero-Downtime Deployment

1. **Deploy code first** (new code is backward compatible)
2. **Run migrations** (adds new columns, doesn't break existing)
3. **Restart application**
4. **Verify endpoints**

### Option B: Standard Deployment

1. **Backup database**
2. **Deploy code + run migrations together**
3. **Restart application**
4. **Verify endpoints**

---

## ⚠️ Important Notes

1. **V1 APIs are FROZEN** - Don't break existing web app functionality
2. **V2 APIs are NEW** - Safe to deploy, but test first
3. **Migrations add new columns** - Should be safe, but test first
4. **500 error must be fixed** - Don't deploy broken code

---

## 📞 If Deployment Fails

### Rollback Plan

1. **Revert code** (git revert or redeploy previous version)
2. **If migrations were applied:**
   ```bash
   # Rollback migration (if needed)
   python manage.py migrate account 0022
   ```
3. **Restore database backup** (if data corruption occurred)
4. **Restart application**

---

## ✅ Final Checklist Before Deploying

- [ ] 500 error fixed and tested
- [ ] All migrations tested on staging/dev
- [ ] V1 endpoints still work
- [ ] V2 endpoints tested
- [ ] Database backup created
- [ ] Environment variables configured
- [ ] Error monitoring setup (Sentry, etc.)
- [ ] Rollback plan prepared
- [ ] Team notified of deployment

---

## 🎯 Recommendation

**DO NOT DEPLOY YET**

1. ✅ Fix the 500 error first
2. ✅ Test locally
3. ✅ Test on staging/dev (if available)
4. ✅ Then deploy to production

**Current Priority:** Fix the registration 500 error before deploying.

---

**Last Updated:** November 6, 2025  
**Next Review:** After 500 error is fixed


