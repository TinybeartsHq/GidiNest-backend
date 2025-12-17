# Admin Wallet Fix API

Admin-only endpoint for fixing wallet issues for users.

## Authentication

Requires staff/admin authentication. Add your admin JWT token to requests:

```
Authorization: Bearer {admin_token}
```

## Endpoints

### 1. List Users with Wallet Issues

**GET** `/api/internal-admin/wallet/fix`

Lists all users who have wallet data but the `has_virtual_wallet` flag is not set correctly.

**Example Request:**
```bash
curl -X GET "https://api.gidinest.com/api/internal-admin/wallet/fix?operation=list" \
  -H "Authorization: Bearer {admin_token}"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "users_with_flag_issue": [
      {
        "id": 123,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "wallet__account_number": "1100072011",
        "wallet__account_name": "GIDINEST/DOE JOHN",
        "wallet__bank": "9PSB",
        "has_bvn": true
      }
    ],
    "users_with_bvn_no_wallet": [
      {
        "id": 456,
        "email": "another@example.com",
        "first_name": "Jane",
        "last_name": "Smith",
        "has_bvn": true
      }
    ],
    "summary": {
      "flag_issue_count": 1,
      "bvn_no_wallet_count": 1
    }
  }
}
```

### 2. Fix All Users (Bulk Fix)

**POST** `/api/internal-admin/wallet/fix`

Fixes the `has_virtual_wallet` flag for ALL users who have wallet data.

**Example Request:**
```bash
curl -X POST "https://api.gidinest.com/api/internal-admin/wallet/fix" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "fix_flags"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "operation": "fix_flags",
    "users_fixed": 15,
    "message": "Successfully updated has_virtual_wallet flag for 15 users"
  }
}
```

### 3. Fix Single User

**POST** `/api/internal-admin/wallet/fix`

Fixes the `has_virtual_wallet` flag for a specific user.

**Example Request:**
```bash
curl -X POST "https://api.gidinest.com/api/internal-admin/wallet/fix" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "fix_single_user",
    "user_id": 123
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "operation": "fix_single_user",
    "user_id": 123,
    "user_email": "user@example.com",
    "wallet_account": "1100072011",
    "message": "Successfully updated has_virtual_wallet flag"
  }
}
```

## Usage Flow

1. **Check affected users:**
   ```bash
   GET /api/internal-admin/wallet/fix?operation=list
   ```

2. **Fix all users at once:**
   ```bash
   POST /api/internal-admin/wallet/fix
   Body: {"operation": "fix_flags"}
   ```

3. **Or fix one user at a time:**
   ```bash
   POST /api/internal-admin/wallet/fix
   Body: {"operation": "fix_single_user", "user_id": 123}
   ```

## Security

- Only staff/superuser accounts can access these endpoints
- All operations are logged with admin email for audit trail
- Uses Django's `IsAdminUser` permission class

## Common Issues

### Issue: Users have BVN but no wallet
**Solution:** These users need to call `/api/v2/kyc/wallet/retry` to create their wallet

### Issue: Wallet exists but no account details
**Solution:** Check 9PSB API logs to see why wallet creation failed, then use retry endpoint

### Issue: Wallet has account details but flag not set
**Solution:** Use this admin API to fix the flag (`fix_flags` operation)
