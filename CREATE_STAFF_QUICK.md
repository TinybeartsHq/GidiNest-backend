# Create Staff User - Quick Guide

## 🚀 Fastest Method: Admin Panel

1. Login: `/internal-admin/`
2. Click **"Users"** → **"Add User"**
3. Fill:
   - Email: `staff@gidinest.com`
   - Password: `SecurePass123!`
   - Password (again): `SecurePass123!`
   - First name: `John` (optional)
   - Last name: `Doe` (optional)
4. Check:
   - ✅ **Active**
   - ✅ **Staff status**
   - ☐ **Superuser** (only for full admin)
5. Click **"Save"**

**Done!** Staff can login immediately.

---

## ⚡ Via Command Line

```bash
python manage.py createstaff
```

Follow prompts to enter:
- Email
- Password
- Name (optional)
- Admin status (y/N)

---

## 🤖 Automated (Scripts)

```bash
python manage.py createstaff \
  --email="staff@gidinest.com" \
  --password="SecurePass123!" \
  --first-name="John" \
  --last-name="Doe" \
  --non-interactive
```

For superuser, add `--admin`:
```bash
python manage.py createstaff \
  --email="admin@gidinest.com" \
  --password="AdminPass456!" \
  --admin \
  --non-interactive
```

---

## 🐍 Python Shell

```python
python manage.py shell
```

```python
from account.models.users import UserModel

staff = UserModel.objects.create(
    email='staff@gidinest.com',
    first_name='John',
    last_name='Doe',
    username='staff',
    is_staff=True,
    is_active=True,
    is_verified=True,
    email_verified=True,
    account_tier='Staff',
    phone='',
)
staff.set_password('SecurePass123!')
staff.save()

print(f"✓ Created: {staff.email}")
```

---

## ✅ What Happens Automatically

When you create a staff user, the system **automatically**:
- ✅ Sets `is_verified = True`
- ✅ Sets `email_verified = True`
- ✅ Sets `account_tier = 'Staff'`
- ✅ Fills `phone = ''` (no phone required)
- ✅ Fills `username` from email if empty
- ✅ **Skips BVN/NIN requirements**
- ✅ **No phone verification needed**

---

## 🔐 Permission Levels

### Staff (`is_staff=True`, `is_superuser=False`)
- ✅ Can access admin panel
- ✅ Can view all data
- ❌ Can't edit/delete (read-only)
- **Use for**: Customer support

### Admin (`is_staff=True`, `is_superuser=True`)
- ✅ Full admin panel access
- ✅ Can edit/delete everything
- ✅ Can manage permissions
- **Use for**: System administrators

---

## 🛠️ Common Tasks

### Make Existing User Staff
```python
from account.models.users import UserModel

user = UserModel.objects.get(email='user@example.com')
user.is_staff = True
user.is_verified = True
user.email_verified = True
user.account_tier = 'Staff'
user.save()
```

### Upgrade Staff to Admin
```python
user = UserModel.objects.get(email='staff@gidinest.com')
user.is_superuser = True
user.save()
```

### Deactivate Staff
```python
user = UserModel.objects.get(email='staff@gidinest.com')
user.is_active = False
user.save()
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Email already exists" | Use different email or delete existing user |
| Can't login | Check: `is_active=True`, `is_staff=True` |
| Can't see admin | Check: `is_staff=True` |
| Can't edit data | Expected for staff. Grant `is_superuser=True` for editing |

---

## 📚 Full Documentation

For detailed information, see: [`STAFF_USER_CREATION_GUIDE.md`](./STAFF_USER_CREATION_GUIDE.md)

---

**🎉 That's it! You can now create staff users without any customer verification requirements!**
