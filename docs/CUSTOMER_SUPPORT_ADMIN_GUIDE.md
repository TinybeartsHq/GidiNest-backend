# Customer Support Admin System - Complete Guide

## Overview

This guide covers the complete customer support admin system for GidiNest. The system provides a comprehensive admin interface for support staff to handle customer inquiries, manage user accounts, and monitor platform health.

## Table of Contents

1. [Features](#features)
2. [Support Levels & Permissions](#support-levels--permissions)
3. [Setup Instructions](#setup-instructions)
4. [Admin Interfaces](#admin-interfaces)
5. [Custom Actions](#custom-actions)
6. [Support Dashboard](#support-dashboard)
7. [Customer Notes System](#customer-notes-system)
8. [Audit Logging](#audit-logging)
9. [Creating Support Staff Users](#creating-support-staff-users)
10. [Best Practices](#best-practices)

---

## Features

### ✅ What's Included

- **3-Tier Support System**: Support Agent, Senior Support, Support Manager
- **Customer Notes**: Track all support interactions with customers
- **Audit Logging**: Complete audit trail of all admin actions
- **Support Dashboard**: Real-time metrics and alerts
- **Enhanced User Management**: Custom actions for common support tasks
- **Session Management**: View and remotely logout users
- **Bank Account Management**: View and verify customer bank accounts
- **Quick Actions**: Reset PINs, verify accounts, bulk operations

### 🆕 New Admin Interfaces

1. **UserSession Admin** - View active sessions, remote logout
2. **UserBankAccount Admin** - Manage customer bank accounts
3. **CustomerNote Admin** - Document support interactions
4. **AdminAuditLog Admin** - Track all admin actions
5. **Support Dashboard** - Centralized support metrics

---

## Support Levels & Permissions

### Level 1: Support Agent (Read-Only)

**Purpose**: First-line support, answer basic queries

**Permissions**:
- ✅ View user profiles (no BVN/NIN access)
- ✅ View wallets and transactions
- ✅ View withdrawal requests
- ✅ View savings goals
- ✅ View payment links
- ✅ Create and manage customer notes
- ✅ View server logs for debugging
- ❌ Cannot modify user accounts
- ❌ Cannot reset PINs or passwords
- ❌ Cannot view sensitive data (BVN/NIN)

**Use Cases**:
- Answer balance inquiries
- Check transaction status
- Create customer notes
- Escalate complex issues

---

### Level 2: Senior Support (Limited Actions)

**Purpose**: Handle escalated issues, perform account actions

**Inherits**: All Level 1 permissions

**Additional Permissions**:
- ✅ View BVN/NIN data
- ✅ Modify user accounts (verify, activate/deactivate)
- ✅ Reset transaction PINs
- ✅ Reset passcodes
- ✅ View user sessions
- ✅ Manage bank accounts (verify, set as default)
- ✅ Delete customer notes

**Use Cases**:
- Verify user KYC
- Reset forgotten PINs
- Handle account issues
- Verify bank account information

---

### Level 3: Support Manager (Full Support Access)

**Purpose**: Full support operations, system monitoring

**Inherits**: All Level 2 permissions

**Additional Permissions**:
- ✅ Manage user sessions (remote logout)
- ✅ Manage devices (view, edit, delete)
- ✅ Add/delete bank accounts
- ✅ Modify withdrawal requests
- ✅ Modify payment links
- ✅ Modify savings goals
- ✅ Apply 24-hour transaction restrictions

**Use Cases**:
- Handle security incidents
- Manage compromised accounts
- Override system restrictions
- Bulk operations
- System monitoring

---

## Setup Instructions

### 1. Run Database Migrations

```bash
# Activate virtual environment
source venv/bin/activate

# Run migrations
python manage.py migrate account
```

### 2. Set Up Support Groups

```bash
# Run the setup command
python manage.py setup_support_groups
```

This creates three groups:
- Support Agent (14 permissions)
- Senior Support (19 permissions)
- Support Manager (28 permissions)

### 3. Access Points

- **Admin Panel**: `http://localhost:8000/internal-admin/`
- **Support Dashboard**: `http://localhost:8000/internal-admin/support-dashboard/`

---

## Admin Interfaces

### Enhanced User Admin

**Location**: `/internal-admin/account/usermodel/`

**New Features**:
- Support notes count column
- Links to related data (wallet, sessions, bank accounts, notes)
- Custom actions (verify, reset PIN, etc.)
- Collapsible BVN/NIN sections
- Security settings section

**Custom Actions**:
- ✅ Verify selected users
- ❌ Unverify selected users
- 🟢 Activate selected users
- 🔴 Deactivate selected users
- 🔑 Reset transaction PINs
- 🔐 Reset passcodes
- ⏰ Apply 24-hour restriction

### UserSession Admin

**Location**: `/internal-admin/account/usersession/`

**Features**:
- View all active sessions
- Filter by device type, status
- Search by user email, IP address
- Remote logout (deactivate sessions)

**Use Cases**:
- Security monitoring
- Handle compromised accounts
- View session history

### UserBankAccount Admin

**Location**: `/internal-admin/account/userbankaccount/`

**Features**:
- View saved bank accounts
- Verify accounts
- Set default account
- Search by account number, bank name

**Custom Actions**:
- ✅ Verify selected bank accounts
- ❌ Unverify selected bank accounts
- ⭐ Set as default account

### CustomerNote Admin

**Location**: `/internal-admin/account/customernote/`

**Features**:
- Track all support interactions
- 10 categories (account, wallet, security, etc.)
- 4 priority levels (low, medium, high, urgent)
- 4 status levels (open, in_progress, resolved, closed)
- Flag for escalation
- Internal-only notes
- Auto-resolution timestamps

**Custom Actions**:
- ✅ Mark as Resolved
- 🔒 Mark as Closed
- 🚩 Flag notes for attention
- Remove flag

**Best Practices**:
- Always create a note for significant interactions
- Use appropriate categories and priorities
- Flag urgent issues for manager attention
- Use internal_only for sensitive information

### AdminAuditLog Admin

**Location**: `/internal-admin/account/adminauditlog/`

**Features**:
- Read-only audit trail
- Tracks who did what and when
- IP address and user agent tracking
- Field-level change tracking (JSON)
- Color-coded action types

**Cannot**:
- ❌ Create manual entries
- ❌ Edit existing entries
- ❌ Delete (except superusers)

---

## Support Dashboard

**Location**: `/internal-admin/support-dashboard/`

### Metrics Displayed

**User Metrics**:
- Total users
- Verified vs unverified
- Active users
- New users (24h, 7d)

**Wallet & Transactions**:
- Total wallets
- Total balance
- Transactions (24h)
- Pending withdrawals
- Failed withdrawals (24h)

**Support Metrics**:
- Open customer notes
- In progress notes
- Urgent notes
- Flagged notes
- Notes created/resolved (24h)

**System Health**:
- Active sessions
- Errors (24h)
- Active savings goals

### Alerts

The dashboard shows automatic alerts for:
- ⚠️ Urgent customer notes
- ⚠️ Flagged notes
- ⚠️ High pending withdrawals
- ⚠️ Failed withdrawals spike
- ⚠️ System errors spike

### Quick Links

Direct access to:
- Manage Users
- Customer Notes
- Withdrawals
- Transactions
- Sessions
- Server Logs

---

## Customer Notes System

### Creating a Note

1. Go to **Customer Notes** admin
2. Click **Add Customer Note**
3. Fill in:
   - **User**: Select the customer
   - **Category**: Choose appropriate category
   - **Priority**: low/medium/high/urgent
   - **Subject**: Brief description
   - **Note**: Detailed information
   - **Internal Only**: Check if sensitive

4. Click **Save**

### Managing Notes

**Filter Options**:
- Status (open, in_progress, resolved, closed)
- Priority
- Category
- Flagged
- Date created

**Bulk Actions**:
- Mark as Resolved
- Mark as Closed
- Flag/Unflag

### Note Categories

1. **General Inquiry** - Basic questions
2. **Account Issue** - Login, profile problems
3. **Wallet/Transaction Issue** - Money problems
4. **Withdrawal Issue** - Payout problems
5. **Savings Goal Issue** - Savings features
6. **Verification/KYC Issue** - Identity verification
7. **Security Concern** - Suspicious activity
8. **Technical Issue** - App bugs
9. **Complaint** - Customer complaints
10. **Feedback** - Suggestions, praise

---

## Audit Logging

### What Gets Logged

The system automatically logs:
- Customer note creation/updates
- (Future: All admin actions)

### Viewing Audit Logs

1. Go to **Admin Audit Logs**
2. Filter by:
   - Action type (create, update, delete)
   - Date range
   - Admin user
   - Content type (model)

3. Click on any entry to see:
   - Who performed the action
   - What was changed (JSON diff)
   - IP address
   - User agent (browser)
   - Timestamp

### Searching Logs

Search by:
- Admin user email
- Action description
- Object representation
- IP address

---

## Creating Support Staff Users

### Method 1: Django Admin (Recommended)

1. **Create User**:
   - Go to `/internal-admin/account/usermodel/`
   - Click **Add User**
   - Enter email and password
   - Set **Staff status** = ✅ (REQUIRED)
   - Leave **Superuser status** = ❌ (unless needed)
   - Click **Save**

2. **Assign Support Group**:
   - Edit the user
   - Scroll to **Permissions** section
   - Under **Groups**, select appropriate level:
     - Support Agent (read-only)
     - Senior Support (limited actions)
     - Support Manager (full access)
   - Click **Save**

3. **Test Access**:
   - Have the user log in at `/internal-admin/`
   - Verify they can only access permitted sections

### Method 2: Django Shell

```python
from account.models import UserModel
from django.contrib.auth.models import Group

# Create user
user = UserModel.objects.create_user(
    email='support@gidinest.com',
    password='secure_password_here',
    first_name='John',
    last_name='Doe',
    is_staff=True,  # REQUIRED for admin access
    is_superuser=False
)

# Assign to group
support_agent = Group.objects.get(name='Support Agent')
user.groups.add(support_agent)

print(f"Created support user: {user.email}")
```

### Important Notes

- ✅ **is_staff=True** is REQUIRED for admin access
- ❌ **is_superuser=True** should ONLY be for admins
- 👥 Assign to appropriate support group
- 🔐 Use strong passwords
- 📝 Create a customer note documenting the new staff member

---

## Custom Actions

### Verify Users

**Who Can Use**: Senior Support, Support Manager

**How**:
1. Select users in the user list
2. Choose **Actions** → **✅ Verify selected users**
3. Click **Go**

**What Happens**:
- Sets `is_verified=True`
- Sets `verification_status='verified'`

### Reset Transaction PINs

**Who Can Use**: Senior Support, Support Manager

**How**:
1. Select users
2. Choose **Actions** → **🔑 Reset transaction PINs**
3. Click **Go**

**What Happens**:
- Clears `transaction_pin`
- Sets `transaction_pin_set=False`
- User must set new PIN on next login

### Reset Passcodes

**Who Can Use**: Senior Support, Support Manager

**How**:
1. Select users
2. Choose **Actions** → **🔐 Reset passcodes**
3. Click **Go**

**What Happens**:
- Clears `passcode_hash`
- Sets `passcode_set=False`
- User must set new passcode

### Apply 24-Hour Restriction

**Who Can Use**: Support Manager

**How**:
1. Select users
2. Choose **Actions** → **⏰ Apply 24-hour restriction**
3. Click **Go**

**What Happens**:
- Applies lower transaction limits for 24 hours
- Used after PIN changes or security incidents

### Remote Logout (Deactivate Sessions)

**Who Can Use**: Support Manager

**Where**: UserSession admin

**How**:
1. Select sessions
2. Choose **Actions** → **🔴 Deactivate selected sessions**
3. Click **Go**

**What Happens**:
- Sets `is_active=False`
- User is logged out immediately
- Must login again

---

## Best Practices

### Security

1. **Never Share Credentials**
   - Each support staff has their own account
   - Never share passwords

2. **Use Appropriate Permissions**
   - Start new staff as Support Agent
   - Promote based on experience

3. **Audit Regular Reviews**
   - Review audit logs weekly
   - Check for unusual activity

4. **Customer Note Everything**
   - Document all significant interactions
   - Use internal_only for sensitive info

### Customer Service

1. **Response Times**
   - Urgent: < 1 hour
   - High: < 4 hours
   - Medium: < 24 hours
   - Low: < 48 hours

2. **Escalation Path**
   - Agent → Senior Support → Manager
   - Flag urgent issues immediately

3. **Privacy**
   - Only access what's needed
   - Don't share customer data externally
   - Use internal_only notes for sensitive info

### Data Management

1. **Customer Notes**
   - Create notes for all interactions
   - Use clear subjects
   - Update status regularly
   - Close resolved issues

2. **Verification**
   - Verify BVN/NIN carefully
   - Check for mismatches
   - Document verification in notes

3. **Withdrawals**
   - Monitor pending withdrawals
   - Investigate failed withdrawals
   - Communicate status to users

---

## Troubleshooting

### Can't Access Admin

**Problem**: User gets "You don't have permission" error

**Solution**:
1. Verify `is_staff=True`
2. Check group assignment
3. Run `python manage.py setup_support_groups` again

### Missing Permissions

**Problem**: Support staff can't perform expected actions

**Solution**:
1. Check their group assignment
2. Verify group has correct permissions
3. Re-run setup command if needed

### Dashboard Not Loading

**Problem**: Support dashboard shows errors

**Solution**:
1. Check database migrations: `python manage.py migrate`
2. Verify templates exist
3. Check server logs: `/internal-admin/core/serverlog/`

---

## API Reference

### Support Dashboard URL

```
GET /internal-admin/support-dashboard/
```

**Requires**: `@staff_member_required`

**Returns**: HTML dashboard with metrics

### Management Commands

```bash
# Set up support groups
python manage.py setup_support_groups

# Create support user (example)
python manage.py createsuperuser
```

---

## File Locations

### Models
- `account/models/customer_notes.py` - CustomerNote model
- `account/models/admin_audit_log.py` - AdminAuditLog model

### Admin
- `account/admin.py` - All admin interfaces
- `account/admin_views.py` - Support dashboard view

### Templates
- `templates/admin/support_dashboard.html` - Dashboard template

### Management Commands
- `account/management/commands/setup_support_groups.py`

### URLs
- `gidinest_backend/urls.py` - Dashboard URL registration

---

## Support Contact

For issues with the support system:
1. Check server logs: `/internal-admin/core/serverlog/`
2. Check audit logs: `/internal-admin/account/adminauditlog/`
3. Contact system administrator

---

## Changelog

### Version 1.0 (2024-11-19)

**New Features**:
- ✅ 3-tier support system
- ✅ Customer notes tracking
- ✅ Admin audit logging
- ✅ Support dashboard
- ✅ Enhanced user admin with custom actions
- ✅ UserSession admin
- ✅ UserBankAccount admin

**Migrations**:
- `account/migrations/0025_customernote_adminauditlog.py`

---

## License

Internal use only - GidiNest Platform
