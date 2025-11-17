# Mobile Developer Quick Start Guide

**API Version:** V2  
**Base URL:** `https://api.gidinest.com/api/v2/`  
**Platform:** Mobile Application (iOS & Android)

---

## 🎯 Overview

This guide will help you integrate the GidiNest V2 API into your mobile application. The V2 API is **actively developed** and optimized for mobile use with features like short-lived tokens, refresh mechanisms, and mobile-specific endpoints.

---

## 📋 Prerequisites

- Mobile app project (iOS Swift/Kotlin, Android Kotlin/Java, React Native, Flutter, etc.)
- HTTP client library (Alamofire, Retrofit, axios, http, etc.)
- Understanding of REST APIs and JWT authentication

---

## 🚀 Quick Start

### 1. Base URL Configuration

```swift
// iOS - Constants.swift
struct API {
    static let baseURL = "https://api.gidinest.com/api/v2"
    // For local development: "http://localhost:8000/api/v2"
}
```

```kotlin
// Android - ApiConstants.kt
object ApiConstants {
    const val BASE_URL = "https://api.gidinest.com/api/v2"
    // For local development: "http://10.0.2.2:8000/api/v2" (Android emulator)
}
```

```dart
// Flutter - config.dart
class ApiConfig {
  static const String baseUrl = 'https://api.gidinest.com/api/v2';
  // For local development: 'http://localhost:8000/api/v2'
}
```

### 2. Authentication Setup

#### Step 1: Register/Login
```swift
// iOS Example
func login(email: String, password: String) async throws -> AuthResponse {
    let url = URL(string: "\(API.baseURL)/auth/login/")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    
    let body = ["email": email, "password": password]
    request.httpBody = try JSONSerialization.data(withJSONObject: body)
    
    let (data, _) = try await URLSession.shared.data(for: request)
    let response = try JSONDecoder().decode(AuthResponse.self, from: data)
    
    // Store tokens securely
    KeychainHelper.save(accessToken: response.data.access, refreshToken: response.data.refresh)
    
    return response
}
```

```kotlin
// Android Example
suspend fun login(email: String, password: String): AuthResponse {
    val request = LoginRequest(email, password)
    val response = apiService.login(request)
    
    // Store tokens securely
    tokenManager.saveTokens(response.data.access, response.data.refresh)
    
    return response
}
```

#### Step 2: API Client with Auto-Refresh
```swift
// iOS - ApiClient.swift
class ApiClient {
    static let shared = ApiClient()
    
    func request<T: Decodable>(_ endpoint: String, method: HTTPMethod = .get, body: Data? = nil) async throws -> T {
        var request = URLRequest(url: URL(string: "\(API.baseURL)\(endpoint)")!)
        request.httpMethod = method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // Add auth token
        if let token = KeychainHelper.getAccessToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        if let body = body {
            request.httpBody = body
        }
        
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            
            // Handle 401 - Token expired
            if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 401 {
                try await refreshToken()
                // Retry request with new token
                return try await request(endpoint, method: method, body: body)
            }
            
            return try JSONDecoder().decode(T.self, from: data)
        } catch {
            throw error
        }
    }
    
    private func refreshToken() async throws {
        guard let refreshToken = KeychainHelper.getRefreshToken() else {
            throw AuthError.noRefreshToken
        }
        
        // Call refresh endpoint
        // Update stored tokens
    }
}
```

### 3. Secure Token Storage

**iOS (Keychain):**
```swift
import Security

class KeychainHelper {
    static func save(accessToken: String, refreshToken: String) {
        // Save to Keychain
        let accessData = accessToken.data(using: .utf8)!
        let refreshData = refreshToken.data(using: .utf8)!
        
        // Use Keychain Services API
        SecItemAdd([kSecClass: kSecClassGenericPassword, 
                   kSecAttrAccount: "access_token",
                   kSecValueData: accessData] as CFDictionary, nil)
    }
    
    static func getAccessToken() -> String? {
        // Retrieve from Keychain
        // ...
    }
}
```

**Android (EncryptedSharedPreferences):**
```kotlin
class TokenManager(context: Context) {
    private val prefs = EncryptedSharedPreferences.create(
        "token_prefs",
        MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build(),
        context,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )
    
    fun saveTokens(accessToken: String, refreshToken: String) {
        prefs.edit()
            .putString("access_token", accessToken)
            .putString("refresh_token", refreshToken)
            .apply()
    }
}
```

---

## 📚 Available Endpoints

### Authentication
- `POST /auth/register/` - Register new user
- `POST /auth/login/` - Login user
- `POST /auth/refresh/` - Refresh access token
- `POST /auth/logout/` - Logout user
- `POST /auth/verify-otp/` - Verify OTP

### Dashboard
- `GET /dashboard/` - Get dashboard overview
- `GET /dashboard/stats/` - Get statistics

### Profile Management
- `GET /profile/` - Get user profile
- `PUT /profile/` - Update profile
- `POST /profile/upload-photo/` - Upload profile photo

### Wallet Operations
- `GET /wallet/` - Get wallet balance
- `GET /wallet/transactions/` - List transactions
- `POST /wallet/deposit/` - Initiate deposit
- `POST /wallet/withdraw/` - Request withdrawal

### Transactions
- `GET /transactions/` - List all transactions
- `GET /transactions/{id}/` - Get transaction details
- `GET /transactions/filter/` - Filter transactions

### Savings Goals
- `GET /savings/goals/` - List savings goals
- `POST /savings/goals/` - Create savings goal
- `GET /savings/goals/{id}/` - Get goal details
- `POST /savings/goals/{id}/deposit/` - Add to goal

### Community
- `GET /community/posts/` - List posts
- `POST /community/posts/` - Create post
- `GET /community/posts/{id}/` - Get post details

### Notifications
- `GET /notifications/` - List notifications
- `PUT /notifications/{id}/read/` - Mark as read
- `GET /notifications/unread-count/` - Get unread count

### KYC Verification
- `POST /kyc/verify/` - Submit KYC documents
- `GET /kyc/status/` - Check verification status

---

## 💡 Example: Complete Mobile Flow

```swift
// iOS Example: Complete user onboarding
class OnboardingService {
    func completeOnboarding(userData: UserRegistrationData) async throws {
        // 1. Register
        let registerResponse = try await apiClient.register(userData)
        
        // 2. Verify OTP
        let otpResponse = try await apiClient.verifyOTP(
            phone: userData.phone,
            otp: userData.otp
        )
        
        // 3. Login
        let loginResponse = try await apiClient.login(
            email: userData.email,
            password: userData.password
        )
        
        // 4. Get dashboard
        let dashboard = try await apiClient.getDashboard()
        
        // 5. Create initial savings goal
        let goal = try await apiClient.createSavingsGoal(
            name: "Emergency Fund",
            targetAmount: 100000,
            deadline: Date().addingTimeInterval(365 * 24 * 3600)
        )
        
        return OnboardingResult(
            user: loginResponse.data.user,
            dashboard: dashboard.data,
            goal: goal.data
        )
    }
}
```

---

## 🔍 Testing with Swagger

1. **Start your backend server:**
   ```bash
   python manage.py runserver
   ```

2. **For iOS Simulator:**
   - Use: `http://localhost:8000/api/docs/`

3. **For Android Emulator:**
   - Use: `http://10.0.2.2:8000/api/docs/`

4. **For Physical Device:**
   - Find your computer's IP: `ifconfig` (Mac) or `ipconfig` (Windows)
   - Use: `http://YOUR_IP:8000/api/docs/`
   - Filter by "V2" tags to see only mobile endpoints

---

## ⚠️ Important Notes

### V2 API Features
- ✅ **Short-lived tokens** (1 hour) for better security
- ✅ **Refresh token mechanism** for seamless UX
- ✅ **Mobile-optimized endpoints** (dashboard, notifications)
- ✅ **Active development** - new features added regularly

### Token Management
- **Access Token:** 1 hour lifetime
- **Refresh Token:** Longer lifetime (store securely)
- **Auto-refresh:** Implement automatic token refresh before expiry

### Response Format
All responses follow this structure:
```json
{
  "success": true|false,
  "message": "Human-readable message",
  "data": { /* Response data */ }
}
```

### Error Handling
```swift
enum ApiError: Error {
    case networkError
    case unauthorized
    case tokenExpired
    case serverError(String)
}

func handleApiError(_ error: Error) {
    if let apiError = error as? ApiError {
        switch apiError {
        case .tokenExpired:
            // Refresh token and retry
            refreshTokenAndRetry()
        case .unauthorized:
            // Redirect to login
            navigateToLogin()
        default:
            // Show error message
            showError(apiError.localizedDescription)
        }
    }
}
```

---

## 📖 Full Documentation

- **[Complete V2 API Reference](../api/V2_API_DOCUMENTATION.md)**
- **[Swagger UI - V2 Only](http://localhost:8000/api/docs/?tags=V2)**
- **[Swagger Setup Guide](../SWAGGER_SETUP.md)**

---

## 🆘 Troubleshooting

### Common Issues

**401 Unauthorized / Token Expired**
- Implement automatic token refresh
- Check token storage is working
- Verify token format: `Bearer <token>`

**Network Timeout**
- Check device connectivity
- Verify API base URL (use IP for physical devices)
- Check backend server is running

**CORS Errors (if using web view)**
- Backend CORS settings should allow your domain
- Use native HTTP clients instead of web views when possible

---

**Need Help?** Check the [main API guide](../API_GUIDE.md) or contact the development team.




