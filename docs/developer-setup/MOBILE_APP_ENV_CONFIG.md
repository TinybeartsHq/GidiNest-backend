# Mobile App Environment Configuration

**Last Updated:** November 6, 2025  
**Purpose:** Environment variables and configuration needed for mobile app (iOS & Android)

---

## Required Environment Variables

### 1. API Configuration

#### Base URLs

```javascript
// Development
API_BASE_URL = "http://localhost:8000/api/v2"
// or
API_BASE_URL = "http://127.0.0.1:8000/api/v2"

// Staging (if available)
API_BASE_URL = "https://staging-api.gidinest.com/api/v2"

// Production
API_BASE_URL = "https://api.gidinest.com/api/v2"
```

#### API Endpoints Structure

```
Base: {API_BASE_URL}

Authentication:
- POST {API_BASE_URL}/auth/signup
- POST {API_BASE_URL}/auth/signin
- POST {API_BASE_URL}/auth/refresh
- POST {API_BASE_URL}/auth/logout

Passcode:
- POST {API_BASE_URL}/auth/passcode/setup
- POST {API_BASE_URL}/auth/passcode/verify
- POST {API_BASE_URL}/auth/passcode/change

PIN:
- POST {API_BASE_URL}/auth/pin/setup
- POST {API_BASE_URL}/auth/pin/verify
- POST {API_BASE_URL}/auth/pin/change
- GET  {API_BASE_URL}/auth/pin/status

Profile:
- GET  {API_BASE_URL}/profile
- PUT  {API_BASE_URL}/profile

Dashboard:
- GET  {API_BASE_URL}/dashboard

Wallet:
- GET  {API_BASE_URL}/wallet
- POST {API_BASE_URL}/wallet/deposit
- POST {API_BASE_URL}/wallet/withdraw

Transactions:
- GET  {API_BASE_URL}/transactions
- GET  {API_BASE_URL}/transactions/{id}

Savings:
- GET  {API_BASE_URL}/savings/goals
- POST {API_BASE_URL}/savings/goals

Community:
- GET  {API_BASE_URL}/community/posts
- POST {API_BASE_URL}/community/posts

Notifications:
- GET  {API_BASE_URL}/notifications
```

---

### 2. Authentication Configuration

#### JWT Token Settings

```javascript
// Access Token Configuration
ACCESS_TOKEN_EXPIRY = 3600  // 1 hour in seconds
REFRESH_TOKEN_EXPIRY = 2592000  // 30 days in seconds

// Token Storage Keys (for secure storage)
ACCESS_TOKEN_KEY = "gidinest_access_token"
REFRESH_TOKEN_KEY = "gidinest_refresh_token"
USER_DATA_KEY = "gidinest_user_data"
```

#### Token Refresh Strategy

```javascript
// Auto-refresh access token when it has less than X seconds remaining
TOKEN_REFRESH_THRESHOLD = 300  // 5 minutes before expiry

// Retry failed requests with refreshed token
MAX_TOKEN_REFRESH_RETRIES = 3
```

---

### 3. OAuth Configuration (When Implemented)

#### Google Sign In

```javascript
// iOS (Info.plist)
GOOGLE_CLIENT_ID_IOS = "YOUR_GOOGLE_CLIENT_ID_IOS.apps.googleusercontent.com"

// Android (google-services.json)
GOOGLE_CLIENT_ID_ANDROID = "YOUR_GOOGLE_CLIENT_ID_ANDROID.apps.googleusercontent.com"
```

#### Apple Sign In

```javascript
// iOS (Info.plist)
APPLE_CLIENT_ID = "YOUR_APPLE_CLIENT_ID"
APPLE_TEAM_ID = "YOUR_APPLE_TEAM_ID"
APPLE_KEY_ID = "YOUR_APPLE_KEY_ID"
```

**Note:** OAuth endpoints are currently placeholders (501 Not Implemented)

---

### 4. Device & Session Configuration

#### Device Information

```javascript
// Required for signup/signin
DEVICE_ID = "unique-device-identifier"  // UUID or device-specific ID
DEVICE_NAME = "iPhone 14 Pro"  // or "Samsung Galaxy S23"
DEVICE_TYPE = "ios"  // or "android", "web", "unknown"
```

#### Session Management

```javascript
// Session tracking
TRACK_SESSIONS = true
SESSION_SYNC_INTERVAL = 300  // Sync every 5 minutes
MAX_ACTIVE_SESSIONS = 5  // Maximum concurrent sessions
```

---

### 5. Security Configuration

#### Passcode Settings

```javascript
// Passcode requirements
PASSCODE_LENGTH = 6
PASSCODE_ALLOW_SEQUENTIAL = false  // Reject 123456, 654321
PASSCODE_ALLOW_REPETITIVE = false  // Reject 111111, 222222

// Biometric settings
BIOMETRIC_ENABLED = true  // Enable Face ID / Touch ID / Fingerprint
BIOMETRIC_FALLBACK_TO_PASSCODE = true
```

#### PIN Settings

```javascript
// Transaction PIN requirements
PIN_MIN_LENGTH = 4
PIN_MAX_LENGTH = 6
PIN_REQUIRED_FOR_WITHDRAWAL = true
```

#### Security Restrictions

```javascript
// 24-hour restriction after PIN/passcode change
RESTRICTION_DURATION_HOURS = 24
RESTRICTED_LIMIT_NGN = 10000  // ₦10,000 during restriction
```

---

### 6. Transaction Limits

#### Default Limits (in NGN)

```javascript
// Per-transaction limit
DEFAULT_PER_TRANSACTION_LIMIT = 50000  // ₦50,000

// Daily limit
DEFAULT_DAILY_LIMIT = 100000  // ₦100,000

// Monthly limit
DEFAULT_MONTHLY_LIMIT = 1000000  // ₦1,000,000

// Restricted limit (after PIN/passcode change)
RESTRICTED_LIMIT = 10000  // ₦10,000
```

---

### 7. API Request Configuration

#### Headers

```javascript
// Required headers for all requests
HEADERS = {
  "Content-Type": "application/json",
  "Accept": "application/json",
  "User-Agent": "GidiNest-Mobile/{VERSION} ({PLATFORM})"
}

// Authenticated requests
AUTH_HEADER = "Authorization: Bearer {ACCESS_TOKEN}"
```

#### Timeouts

```javascript
// Request timeouts
CONNECTION_TIMEOUT = 30  // seconds
READ_TIMEOUT = 30  // seconds
```

#### Retry Configuration

```javascript
// Retry failed requests
MAX_RETRIES = 3
RETRY_DELAY = 1000  // milliseconds
RETRY_ON_STATUS = [500, 502, 503, 504]  // Retry on these status codes
```

---

### 8. Error Handling

#### Error Response Format

```javascript
// Standard error response structure
{
  "status": false,
  "message": "Error message",
  "detail": "Detailed error message",
  "errors": {
    // Field-specific errors
  }
}

// HTTP Status Codes
STATUS_CODES = {
  SUCCESS: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  TOO_MANY_REQUESTS: 429,
  SERVER_ERROR: 500
}
```

---

### 9. Feature Flags

```javascript
// Enable/disable features
FEATURES = {
  OAUTH_GOOGLE: false,  // Currently not implemented
  OAUTH_APPLE: false,  // Currently not implemented
  BIOMETRIC_AUTH: true,
  PASSCODE_AUTH: true,
  SESSION_MANAGEMENT: true,
  TRANSACTION_LIMITS: true,
  BANK_ACCOUNTS: true,
  AUTO_SAVE: true,
  COMMUNITY: true,
  NOTIFICATIONS: true
}
```

---

### 10. Logging & Debugging

```javascript
// Logging configuration
LOG_LEVEL = "DEBUG"  // DEBUG, INFO, WARN, ERROR
LOG_API_REQUESTS = true
LOG_API_RESPONSES = false  // Don't log sensitive data in production
LOG_TO_CONSOLE = true
LOG_TO_FILE = false

// Debug mode
DEBUG_MODE = false  // Set to false in production
SHOW_ERROR_DETAILS = false  // Don't show stack traces in production
```

---

## Environment-Specific Configurations

### Development

```javascript
const DEV_CONFIG = {
  API_BASE_URL: "http://localhost:8000/api/v2",
  DEBUG_MODE: true,
  LOG_LEVEL: "DEBUG",
  LOG_API_RESPONSES: true,
  SHOW_ERROR_DETAILS: true,
}
```

### Staging

```javascript
const STAGING_CONFIG = {
  API_BASE_URL: "https://staging-api.gidinest.com/api/v2",
  DEBUG_MODE: true,
  LOG_LEVEL: "INFO",
  LOG_API_RESPONSES: false,
  SHOW_ERROR_DETAILS: false,
}
```

### Production

```javascript
const PROD_CONFIG = {
  API_BASE_URL: "https://api.gidinest.com/api/v2",
  DEBUG_MODE: false,
  LOG_LEVEL: "ERROR",
  LOG_API_RESPONSES: false,
  SHOW_ERROR_DETAILS: false,
}
```

---

## Implementation Examples

### iOS (Swift)

```swift
struct AppConfig {
    static let apiBaseURL = Bundle.main.object(forInfoDictionaryKey: "API_BASE_URL") as! String
    static let accessTokenExpiry: TimeInterval = 3600
    static let refreshTokenExpiry: TimeInterval = 2592000
}

// Usage
let url = "\(AppConfig.apiBaseURL)/auth/signin"
```

### Android (Kotlin)

```kotlin
object AppConfig {
    const val API_BASE_URL = BuildConfig.API_BASE_URL
    const val ACCESS_TOKEN_EXPIRY = 3600L
    const val REFRESH_TOKEN_EXPIRY = 2592000L
}

// Usage
val url = "${AppConfig.API_BASE_URL}/auth/signin"
```

### React Native / Flutter

```javascript
// config.js
export const API_BASE_URL = __DEV__ 
  ? "http://localhost:8000/api/v2"
  : "https://api.gidinest.com/api/v2";

export const ACCESS_TOKEN_EXPIRY = 3600;
export const REFRESH_TOKEN_EXPIRY = 2592000;
```

---

## Security Best Practices

1. **Never commit sensitive data** to version control
2. **Use secure storage** for tokens (Keychain on iOS, Keystore on Android)
3. **Validate SSL certificates** in production
4. **Implement certificate pinning** for production builds
5. **Encrypt sensitive data** at rest
6. **Use environment-specific configs** (dev/staging/prod)
7. **Rotate tokens** before expiry
8. **Handle token refresh** automatically
9. **Clear tokens** on logout
10. **Validate API responses** before using data

---

## Testing Configuration

### Mock Server (for testing)

```javascript
// Use mock server for unit tests
USE_MOCK_SERVER = true
MOCK_SERVER_URL = "http://localhost:3000/api/v2"

// Mock responses
MOCK_RESPONSES = {
  signup: { success: true, data: { /* mock user */ } },
  signin: { success: true, data: { /* mock tokens */ } },
}
```

---

## Summary

### Minimum Required Variables

1. ✅ `API_BASE_URL` - Base URL for API calls
2. ✅ `DEVICE_ID` - Unique device identifier
3. ✅ `DEVICE_TYPE` - "ios" or "android"
4. ✅ `ACCESS_TOKEN_KEY` - Storage key for access token
5. ✅ `REFRESH_TOKEN_KEY` - Storage key for refresh token

### Optional but Recommended

- `DEBUG_MODE` - Enable/disable debug features
- `LOG_LEVEL` - Logging verbosity
- `TOKEN_REFRESH_THRESHOLD` - When to refresh tokens
- `CONNECTION_TIMEOUT` - Request timeout settings
- `MAX_RETRIES` - Retry configuration

---

## Next Steps

1. ✅ Set up environment-specific configs (dev/staging/prod)
2. ✅ Implement secure token storage
3. ✅ Set up automatic token refresh
4. ✅ Configure error handling
5. ✅ Implement session management
6. 🔄 Configure OAuth (when backend is ready)
7. 🔄 Set up push notifications (FCM/APNS)
8. 🔄 Configure analytics (if needed)

---

**Note:** This configuration guide is based on the current V2 API implementation. Some features (like OAuth) are placeholders and will be updated when implemented.


