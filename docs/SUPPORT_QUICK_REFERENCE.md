# Customer Support Admin - Quick Reference

## Access URLs

- **Admin Panel**: `http://localhost:8000/internal-admin/`
- **Support Dashboard**: `http://localhost:8000/internal-admin/support-dashboard/`

---

## Support Levels

| Level | Permissions | Can Do | Cannot Do |
|-------|------------|---------|-----------|
| **Support Agent** | Read-only | View users, wallets, transactions, create notes | Modify accounts, reset PINs, view BVN/NIN |
| **Senior Support** | Limited actions | + Reset PINs, verify accounts, view BVN/NIN | Manage sessions, bulk operations |
| **Support Manager** | Full access | + Manage sessions, devices, bulk operations | Delete users |

---

## Quick Actions Reference

### User Management (`/internal-admin/account/usermodel/`)

| Action | Shortcut | Who Can Use | What It Does |
|--------|----------|-------------|--------------|
| Verify Users | ✅ | Senior+, Manager | Set users as verified |
| Unverify Users | ❌ | Senior+, Manager | Remove verification |
| Activate Users | 🟢 | Senior+, Manager | Enable user accounts |
| Deactivate Users | 🔴 | Senior+, Manager | Disable user accounts |
| Reset PINs | 🔑 | Senior+, Manager | Clear transaction PINs |
| Reset Passcodes | 🔐 | Senior+, Manager | Clear app passcodes |
| 24hr Restriction | ⏰ | Manager | Apply transaction limits |

### Session Management (`/internal-admin/account/usersession/`)

| Action | Who Can Use | What It Does |
|--------|-------------|--------------|
| Deactivate Sessions | Manager | Remote logout users |
| Activate Sessions | Manager | Re-enable sessions |

### Bank Accounts (`/internal-admin/account/userbankaccount/`)

| Action | Who Can Use | What It Does |
|--------|-------------|--------------|
| Verify Accounts | Senior+, Manager | Mark bank accounts as verified |
| Set as Default | Senior+, Manager | Set primary withdrawal account |

### Customer Notes (`/internal-admin/account/customernote/`)

| Action | Who Can Use | What It Does |
|--------|-------------|--------------|
| Mark as Resolved | All | Close resolved issues |
| Mark as Closed | All | Archive completed notes |
| Flag Notes | All | Escalate for attention |

---

## Common Tasks

### 1. Handle "I Forgot My PIN"

1. Go to **Users** admin
2. Find user by email/phone
3. Select user → Actions → **🔑 Reset transaction PINs**
4. Create customer note documenting the reset
5. Inform user to set new PIN on login

### 2. Verify User KYC

**Requirements**: Senior Support or Manager

1. Go to **Users** admin
2. Find and open user profile
3. Expand **BVN Info** or **NIN Info** section
4. Verify details match
5. Select user → Actions → **✅ Verify selected users**
6. Create customer note documenting verification

### 3. Handle Failed Withdrawal

1. Go to **Withdrawal Requests** (`/internal-admin/wallet/withdrawalrequest/`)
2. Filter by Status = **Failed**
3. Click on the failed withdrawal
4. Check **error_message** field
5. Common issues:
   - Insufficient balance → Check wallet
   - Invalid account → Verify bank details
   - Provider error → Check provider logs
6. Create customer note with resolution

### 4. Remote Logout (Security Issue)

**Requirements**: Manager only

1. Go to **User Sessions** (`/internal-admin/account/usersession/`)
2. Search for user email
3. Select all active sessions
4. Actions → **🔴 Deactivate selected sessions**
5. Create customer note flagged as **Security Concern**

### 5. Check User Balance

1. Go to **Users** admin
2. Find and open user
3. Click **View Wallet** link in Related Data section
4. See current balance and account details

### 6. Create Support Ticket

1. Go to **Customer Notes** admin
2. Click **Add Customer Note**
3. Fill in:
   - User: [select customer]
   - Category: [choose appropriate]
   - Priority: [low/medium/high/urgent]
   - Subject: Brief description
   - Note: Detailed information
4. Check **Flagged** if urgent
5. Click **Save**

---

## Customer Note Categories

| Category | Use For |
|----------|---------|
| General Inquiry | Basic questions, info requests |
| Account Issue | Login problems, profile updates |
| Wallet/Transaction | Missing funds, transaction errors |
| Withdrawal Issue | Failed payouts, slow withdrawals |
| Savings Goal | Savings features, interest |
| Verification/KYC | Identity verification, BVN/NIN |
| Security Concern | Suspicious activity, compromised accounts |
| Technical Issue | App bugs, errors |
| Complaint | Customer complaints |
| Feedback | Suggestions, praise |

---

## Priority Levels

| Priority | Response Time | Use For |
|----------|---------------|---------|
| **Urgent** | < 1 hour | Missing money, security breaches |
| **High** | < 4 hours | Failed withdrawals, login issues |
| **Medium** | < 24 hours | General issues, verification |
| **Low** | < 48 hours | Feature requests, feedback |

---

## Search Tips

### Find User by...

- **Email**: Just type in search box
- **Phone**: Use search box (searches phone field)
- **Name**: Search first_name or last_name
- **BVN**: Search in user admin
- **Wallet Account**: Go to Wallets admin, search account_number

### Find Transaction by...

- **Reference**: Search in Wallet Transactions
- **User**: Filter by user email
- **Amount**: Use admin filters
- **Date**: Use date range filters

---

## Dashboard Alerts

| Alert | Meaning | Action |
|-------|---------|--------|
| 🔴 Urgent notes | Customer notes marked urgent | Review immediately |
| ⚠️ Flagged notes | Notes requiring attention | Assign to senior support |
| ⚠️ Pending withdrawals | > 10 withdrawals pending | Check provider status |
| ⚠️ Failed withdrawals | > 5 failed in 24h | Investigate pattern |
| 🔴 System errors | > 50 errors in 24h | Notify tech team |
| ℹ️ Unverified users | > 20 with BVN waiting | Process verifications |

---

## Keyboard Shortcuts (Django Admin)

| Key | Action |
|-----|--------|
| `s` | Save |
| `Ctrl+S` | Save and continue editing |
| `Shift+Ctrl+S` | Save and add another |
| `/` | Focus search |

---

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "You don't have permission" | Not staff or no group | Check is_staff, assign group |
| "Refresh token invalid" | Session expired | User needs to re-login |
| "Transaction limit exceeded" | Daily/monthly limit hit | Check limits, apply restriction if needed |
| "BVN verification failed" | Mismatch in details | Check BVN fields, manual verify if correct |

---

## Useful Filters

### Users
- `is_verified=True/False` - Verification status
- `is_active=True/False` - Account status
- `account_tier=Tier 1/2/3` - User tier
- `has_bvn=True` - Users with BVN

### Customer Notes
- `status=open` - Open tickets
- `priority=urgent` - Urgent issues
- `flagged=True` - Flagged for attention
- `category=security` - Security issues

### Sessions
- `is_active=True` - Active logins
- `device_type=ios/android` - By platform

---

## Contact & Escalation

### Escalation Path
1. **Support Agent** → Cannot resolve
2. **Senior Support** → Technical/security issue
3. **Support Manager** → System-wide issue
4. **Tech Team** → Critical bug/outage

### When to Escalate
- Security breach suspected
- System-wide outages
- Multiple failed withdrawals
- Data inconsistencies
- Bug in production

---

## Daily Checklist

### Morning (Start of Shift)
- [ ] Check Support Dashboard alerts
- [ ] Review urgent customer notes
- [ ] Check pending withdrawals (if > 10, investigate)
- [ ] Review flagged notes from previous shift

### During Shift
- [ ] Respond to new customer notes within SLA
- [ ] Update note status as you work
- [ ] Create notes for all significant interactions
- [ ] Flag issues that need escalation

### End of Shift
- [ ] Update all in-progress notes
- [ ] Flag unresolved urgent issues
- [ ] Close resolved notes
- [ ] Brief next shift on pending issues

---

## Tips & Best Practices

### Documentation
- ✅ Always create a customer note
- ✅ Use clear, descriptive subjects
- ✅ Document what you did, not just the issue
- ✅ Update status as you work

### Communication
- ✅ Be professional and empathetic
- ✅ Explain technical issues simply
- ✅ Set expectations on resolution time
- ✅ Follow up on escalated issues

### Security
- ✅ Verify user identity before sharing info
- ✅ Never share passwords or PINs
- ✅ Use "internal_only" for sensitive notes
- ✅ Log out when leaving workstation

### Efficiency
- ✅ Use bulk actions for similar issues
- ✅ Create templates for common responses
- ✅ Learn keyboard shortcuts
- ✅ Use filters to find issues quickly

---

## Need Help?

1. **Check**: Audit logs (`/internal-admin/account/adminauditlog/`)
2. **Check**: Server logs (`/internal-admin/core/serverlog/`)
3. **Check**: Full guide (`docs/CUSTOMER_SUPPORT_ADMIN_GUIDE.md`)
4. **Escalate**: Contact your supervisor

---

**Last Updated**: 2024-11-19
