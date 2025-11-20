# Staff User Creation Guide

## Overview

This guide explains how to create staff users for GidiNest admin access **without requiring customer fields** like BVN, NIN, phone verification, etc.

---

## 🚀 Quick Methods

### Method 1: Via Admin Panel (Easiest)

1. **Login to Admin**: `/internal-admin/`
2. **Navigate to Users**: Click "Users" in the sidebar
3. **Click "Add User"** button (top right)
4. **Fill Required Fields**:
   - **Email**: `staff@gidinest.com`
   - **Password**: Set a strong password
   - **Password confirmation**: Repeat password
5. **Optional Fields**:
   - **First name**: Staff member's first name
   - **Last name**: Staff member's last name
6. **Set Permissions**:
   - ✅ **Active**: Check (allows login)
   - ✅ **Staff status**: Check (grants admin access)
   - ☐ **Superuser status**: Check only for full admin rights
7. **Click "Save"**

**That's it!** The system automatically:
- Sets `is_verified = True`
- Sets `email_verified = True`
- Sets `account_tier = 'Staff'`
- Fills optional fields with defaults
- Skips BVN/NIN requirements

---

### Method 2: Management Command (CLI)

#### Interactive Mode
```bash
python manage.py createstaff
```

You'll be prompted for:
- Email address
- Password (hidden input)
- Password confirmation
- First name (optional)
- Last name (optional)
- Admin/Superuser status (y/N)

**Example**:
```
$ python manage.py createstaff
Email address: john.doe@gidinest.com
Password: ********
Password (again): ********
First name (optional): John
Last name (optional): Doe
Make this user an admin (superuser)? [y/N]: N

✓ Staff user created successfully!

  Email: john.doe@gidinest.com
  Name: John Doe
  Role: Staff
  Status: Active

  They can now login at: /internal-admin/
```

#### Non-Interactive Mode (Scripts/Automation)
```bash
python manage.py createstaff \
  --email="staff@gidinest.com" \
  --password="SecurePassword123!" \
  --first-name="John" \
  --last-name="Doe" \
  --non-interactive
```

**For Admin/Superuser**:
```bash
python manage.py createstaff \
  --email="admin@gidinest.com" \
  --password="SuperSecurePass456!" \
  --first-name="Admin" \
  --last-name="User" \
  --admin \
  --non-interactive
```

---

### Method 3: Django Shell

```python
python manage.py shell
```

Then:

```python
from account.models.users import UserModel

# Create basic staff user
staff = UserModel.objects.create(
    email='staff@gidinest.com',
    first_name='Staff',
    last_name='Member',
    username='staff',
    is_staff=True,
    is_active=True,
    is_verified=True,
    email_verified=True,
    account_tier='Staff',
    phone='',  # Not required for staff
)
staff.set_password('YourSecurePassword')
staff.save()

print(f"✓ Staff user created: {staff.email}")
```

**For Admin/Superuser**:

```python
admin = UserModel.objects.create(
    email='admin@gidinest.com',
    first_name='Admin',
    last_name='User',
    username='admin',
    is_staff=True,
    is_superuser=True,  # Full admin rights
    is_active=True,
    is_verified=True,
    email_verified=True,
    account_tier='Staff',
    phone='',
)
admin.set_password('SuperSecurePassword')
admin.save()

print(f"✓ Admin user created: {admin.email}")
```

---

## 📋 Staff vs Customer Users

| Field | Customer User | Staff User |
|-------|---------------|------------|
| **Email** | ✅ Required | ✅ Required |
| **Password** | ✅ Required | ✅ Required |
| **Phone** | ✅ Required + Verified | ❌ Optional (empty OK) |
| **BVN** | ✅ Required for T2/T3 | ❌ Not required |
| **NIN** | ✅ Required for T3 | ❌ Not required |
| **Email Verification** | ✅ Required | ✅ Auto-verified |
| **Phone Verification** | ✅ Required | ❌ Not required |
| **Account Tier** | Tier 1/2/3 | "Staff" |
| **First/Last Name** | ✅ Required | ⚠️ Optional but recommended |
| **Address** | Optional | ❌ Not required |
| **DOB** | Optional | ❌ Not required |
| **Virtual Wallet** | ✅ Created | ❌ Not created |

---

## 🔐 Permission Levels

### Staff User (`is_staff=True, is_superuser=False`)

**Can Access**:
- ✅ Admin panel at `/internal-admin/`
- ✅ View all models (read-only by default)
- ✅ Support dashboard
- ✅ Customer notes

**Cannot Do** (unless specifically granted):
- ❌ Add/Edit/Delete users
- ❌ Change permissions
- ❌ Delete critical data
- ❌ Access Django settings

**Use Case**: Customer support staff, view-only admins

### Admin/Superuser (`is_staff=True, is_superuser=True`)

**Can Access**:
- ✅ Full admin panel access
- ✅ All CRUD operations
- ✅ User management
- ✅ Permission management
- ✅ Django admin settings
- ✅ All models and data

**Use Case**: System administrators, senior staff

---

## 🎯 Best Practices

### 1. **Use Strong Passwords**
```bash
# Good
SecureP@ssw0rd2025!

# Bad
password123
```

### 2. **Set Real Names**
Helps identify staff in audit logs:
```python
first_name='John'  # Good
first_name=''      # Works but not ideal
```

### 3. **Start with Basic Staff**
Grant `is_staff=True` first, then upgrade to `is_superuser` if needed.

### 4. **Use Company Email**
```bash
staff@gidinest.com      # Good
personalmail@gmail.com  # Not recommended
```

### 5. **Document Staff Accounts**
Keep a record of who has access:
- Email
- Name
- Role (Staff/Admin)
- Date created
- Purpose

---

## 🔧 Modifying Staff Users

### Grant Superuser Status

**Via Admin Panel**:
1. Go to Users list
2. Click on the staff user
3. Scroll to "Permissions"
4. Check "Superuser status"
5. Save

**Via Shell**:
```python
from account.models.users import UserModel

user = UserModel.objects.get(email='staff@gidinest.com')
user.is_superuser = True
user.save()

print(f"✓ {user.email} is now a superuser")
```

**Via Management Command**:
```bash
python manage.py shell -c "
from account.models.users import UserModel
user = UserModel.objects.get(email='staff@gidinest.com')
user.is_superuser = True
user.save()
print('Done')
"
```

### Remove Admin Access

**Deactivate (Recommended)**:
```python
user = UserModel.objects.get(email='staff@gidinest.com')
user.is_active = False
user.save()
```

**Remove Staff Status**:
```python
user = UserModel.objects.get(email='staff@gidinest.com')
user.is_staff = False
user.is_superuser = False
user.save()
```

**Delete (Use with caution)**:
```python
user = UserModel.objects.get(email='staff@gidinest.com')
user.delete()
```

---

## 🐛 Troubleshooting

### Error: "User with this email already exists"
**Solution**: Use a different email or delete the existing user first.

```python
# Check if user exists
UserModel.objects.filter(email='staff@gidinest.com').exists()

# Delete if needed
UserModel.objects.filter(email='staff@gidinest.com').delete()
```

### Error: "NOT NULL constraint failed: users.phone"
**Solution**: Already fixed! The system now automatically sets `phone=''` for staff users.

### Staff Can't Login
**Check**:
1. `is_active = True`
2. `is_staff = True`
3. Password is correct
4. Email is correct

```python
user = UserModel.objects.get(email='staff@gidinest.com')
print(f"Active: {user.is_active}")
print(f"Staff: {user.is_staff}")
print(f"Can login: {user.is_active and user.is_staff}")
```

### Staff Can't See Admin Panel
**Solution**: Ensure `is_staff=True`

```python
user = UserModel.objects.get(email='staff@gidinest.com')
user.is_staff = True
user.save()
```

### Staff Can't Edit/Delete
**Expected Behavior**: Basic staff (`is_superuser=False`) have read-only access by default.

**Solution**: Either:
1. Grant specific permissions via Django admin Groups
2. Make them a superuser: `user.is_superuser = True`

---

## 📊 Bulk Staff Creation

### Create Multiple Staff from CSV

**1. Create CSV file** (`staff.csv`):
```csv
email,first_name,last_name,is_admin
john@gidinest.com,John,Doe,False
jane@gidinest.com,Jane,Smith,True
support@gidinest.com,Support,Team,False
```

**2. Run Python script**:
```python
import csv
from account.models.users import UserModel

with open('staff.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        user = UserModel.objects.create(
            email=row['email'],
            first_name=row['first_name'],
            last_name=row['last_name'],
            username=row['email'].split('@')[0],
            is_staff=True,
            is_superuser=(row['is_admin'].lower() == 'true'),
            is_active=True,
            is_verified=True,
            email_verified=True,
            account_tier='Staff',
            phone='',
        )
        # Set default password (they should change it)
        user.set_password('ChangeMe2025!')
        user.save()
        print(f"✓ Created: {user.email}")
```

---

## 🔒 Security Considerations

### 1. **Password Policy**
- Minimum 12 characters
- Mix of upper/lower/numbers/symbols
- Not based on personal info
- Changed regularly

### 2. **Access Levels**
- Grant minimum necessary permissions
- Use staff for support, admin for management only
- Review permissions regularly

### 3. **Audit Logging**
All admin actions are logged in `AdminAuditLog`:
```python
from account.models import AdminAuditLog

# View recent staff actions
logs = AdminAuditLog.objects.filter(
    user__account_tier='Staff'
).order_by('-timestamp')[:20]

for log in logs:
    print(f"{log.timestamp}: {log.user.email} - {log.action_description}")
```

### 4. **Session Management**
- Sessions expire after inactivity
- Staff can be logged out remotely via UserSession admin

### 5. **Deactivation**
Deactivate (don't delete) when staff leave:
```python
user.is_active = False
user.save()
```

---

## 📝 Summary

### Quick Reference

| Task | Command |
|------|---------|
| **Create Staff via Admin** | Add User button → Fill form → Check "Staff status" |
| **Create Staff via CLI** | `python manage.py createstaff` |
| **Create Admin via CLI** | `python manage.py createstaff --admin` |
| **Grant Superuser** | Admin panel → User → Check "Superuser" |
| **Deactivate** | Admin panel → User → Uncheck "Active" |
| **View Audit Log** | Admin panel → Admin Audit Logs |

### Key Points

✅ **No Customer Fields Required** - BVN, NIN, phone verification not needed
✅ **Auto-Verified** - Email verification automatic for staff
✅ **Simple Process** - Just email, password, and permission level
✅ **Multiple Methods** - Admin panel, CLI command, or Python shell
✅ **Audit Logged** - All admin actions tracked automatically
✅ **Flexible Permissions** - Staff (read) or Admin (full access)

---

## 🆘 Need Help?

1. **Check this guide** for common solutions
2. **Review audit logs** for what changed
3. **Test in Django shell** to verify user properties
4. **Check Django logs** for error messages

---

**🎉 You're all set! Staff users can now be created easily without customer verification requirements.**
