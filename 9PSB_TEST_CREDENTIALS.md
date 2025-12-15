# 9PSB Test Credentials (Wallet As A Service)

**Environment:** Test/Sandbox
**Provider:** 9 Payment Service Bank (9PSB)

---

## Authentication Credentials

```json
{
    "username": "gidinest",
    "password": "RN7aXaCxGjCF3bj3L3ocNxWwQ6jvFGsWF9AG5CY2cg3aQyGagl",
    "clientId": "waas",
    "clientSecret": "cRAwnWElcNMUZpALdnlve6PubUkCPOQR"
}
```

---

## API Endpoints

### Authentication Endpoints

**VAS (Value Added Services) Auth:**
```
POST http://102.216.128.75:9090/identity/api/v1/authenticate
```

**WAAS (Wallet As A Service) Auth:**
```
POST http://102.216.128.75:9090/bank9ja/api/v2/k1/authenticate
```

### Base URLs

**VAS & WAAS Base URL:**
```
http://102.216.128.75:9090
```

---

## Test Account

**Test Debit Account:** `1100011303` (or WAAS Wallet)

---

## Environment Variables for Testing

Add these to your `.env` file or environment:

```bash
# 9PSB Test Credentials
PSB9_USERNAME=gidinest
PSB9_PASSWORD=RN7aXaCxGjCF3bj3L3ocNxWwQ6jvFGsWF9AG5CY2cg3aQyGagl
PSB9_CLIENT_ID=waas
PSB9_CLIENT_SECRET=cRAwnWElcNMUZpALdnlve6PubUkCPOQR
PSB9_BASE_URL=http://102.216.128.75:9090
```

---

## Authentication Payload Structure

### WAAS Authentication

**Endpoint:** `POST http://102.216.128.75:9090/bank9ja/api/v2/k1/authenticate`

**Request Body:**
```json
{
    "username": "gidinest",
    "password": "RN7aXaCxGjCF3bj3L3ocNxWwQ6jvFGsWF9AG5CY2cg3aQyGagl",
    "clientId": "waas",
    "clientSecret": "cRAwnWElcNMUZpALdnlve6PubUkCPOQR"
}
```

**Expected Response:**
```json
{
    "status": "success",
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "expiresIn": 3600
    }
}
```

---

## Quick Test with cURL

### Test Authentication

```bash
curl -X POST http://102.216.128.75:9090/bank9ja/api/v2/k1/authenticate \
  -H "Content-Type: application/json" \
  -d '{
    "username": "gidinest",
    "password": "RN7aXaCxGjCF3bj3L3ocNxWwQ6jvFGsWF9AG5CY2cg3aQyGagl",
    "clientId": "waas",
    "clientSecret": "cRAwnWElcNMUZpALdnlve6PubUkCPOQR"
  }'
```

---

## Important Notes

1. **Test Environment Only**
   - These credentials are for testing/sandbox only
   - Do NOT use in production

2. **IP Address Access**
   - Ensure your server can access `102.216.128.75:9090`
   - May need to whitelist your IP address
   - Check firewall rules if connection fails

3. **Authentication Method**
   - Uses username/password + clientId/clientSecret
   - NOT API key/secret as initially assumed
   - Token-based authentication (JWT)

4. **Token Expiry**
   - Tokens expire after 1 hour (3600 seconds)
   - Implement automatic refresh in client

5. **WAAS vs VAS**
   - WAAS: Wallet As A Service (wallet operations)
   - VAS: Value Added Services (additional services)
   - Use WAAS auth for wallet operations

---

## Next Steps

1. Update 9PSB client helper to use correct authentication structure
2. Update settings.py with correct environment variables
3. Test authentication with provided credentials
4. Test wallet creation with test account
5. Configure webhook endpoint with 9PSB

---

**Last Updated:** 2025-12-15
