# Frontend Developer Quick Start Guide

**API Version:** V1  
**Base URL:** `https://api.gidinest.com/api/v1/`  
**Platform:** Web Application

---

## 🎯 Overview

This guide will help you integrate the GidiNest V1 API into your web application. The V1 API is **production-ready and frozen** - meaning it's stable and won't have breaking changes.

---

## 📋 Prerequisites

- Web application (React, Vue, Angular, or any framework)
- HTTP client library (axios, fetch, etc.)
- Understanding of REST APIs and JWT authentication

---

## 🚀 Quick Start

### 1. Base URL Configuration

```javascript
// config.js or constants.js
const API_BASE_URL = 'https://api.gidinest.com/api/v1';
// For local development: 'http://localhost:8000/api/v1'
```

### 2. Authentication Setup

#### Step 1: Register/Login
```javascript
// Register a new user
const register = async (userData) => {
  const response = await fetch(`${API_BASE_URL}/onboarding/register/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  });
  return response.json();
};

// Login
const login = async (email, password) => {
  const response = await fetch(`${API_BASE_URL}/onboarding/login/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
  const data = await response.json();
  
  // Store tokens
  localStorage.setItem('access_token', data.data.access);
  localStorage.setItem('refresh_token', data.data.refresh);
  
  return data;
};
```

#### Step 2: Create API Client with Auth
```javascript
// apiClient.js
const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };
};

const apiClient = {
  get: async (endpoint) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: getAuthHeaders(),
    });
    return response.json();
  },
  
  post: async (endpoint, data) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return response.json();
  },
  
  // Add PUT, DELETE, etc.
};
```

#### Step 3: Handle Token Refresh
```javascript
// tokenRefresh.js
const refreshToken = async () => {
  const refresh = localStorage.getItem('refresh_token');
  const response = await fetch(`${API_BASE_URL}/onboarding/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });
  const data = await response.json();
  localStorage.setItem('access_token', data.data.access);
  return data.data.access;
};

// Intercept 401 errors and refresh token
const apiCallWithRefresh = async (apiCall) => {
  try {
    return await apiCall();
  } catch (error) {
    if (error.status === 401) {
      await refreshToken();
      return await apiCall(); // Retry with new token
    }
    throw error;
  }
};
```

---

## 📚 Available Endpoints

### Authentication & Onboarding
- `POST /onboarding/register/` - Register new user
- `POST /onboarding/login/` - Login user
- `POST /onboarding/token/refresh/` - Refresh access token
- `POST /onboarding/logout/` - Logout user

### Account Management
- `GET /account/profile/` - Get user profile
- `PUT /account/profile/` - Update user profile
- `GET /account/bank-accounts/` - List bank accounts
- `POST /account/bank-accounts/` - Add bank account

### Wallet Operations
- `GET /wallet/` - Get wallet balance
- `GET /wallet/transactions/` - List transactions
- `POST /wallet/deposit/` - Deposit funds
- `POST /wallet/withdraw/` - Withdraw funds

### Savings Goals
- `GET /savings/goals/` - List savings goals
- `POST /savings/goals/` - Create savings goal
- `GET /savings/goals/{id}/` - Get goal details
- `POST /savings/goals/{id}/deposit/` - Add to savings goal

### Community
- `GET /community/posts/` - List community posts
- `POST /community/posts/` - Create post
- `GET /community/posts/{id}/` - Get post details

---

## 💡 Example: Complete User Flow

```javascript
// Example: Complete user registration and profile setup
async function completeRegistration(userData) {
  try {
    // 1. Register
    const registerResponse = await register(userData);
    if (!registerResponse.success) {
      throw new Error(registerResponse.message);
    }
    
    // 2. Login
    const loginResponse = await login(userData.email, userData.password);
    if (!loginResponse.success) {
      throw new Error(loginResponse.message);
    }
    
    // 3. Get profile
    const profile = await apiClient.get('/account/profile/');
    console.log('User profile:', profile.data);
    
    // 4. Create savings goal
    const goal = await apiClient.post('/savings/goals/', {
      name: 'Emergency Fund',
      target_amount: 100000,
      deadline: '2025-12-31',
    });
    console.log('Created goal:', goal.data);
    
    return { success: true, profile, goal };
  } catch (error) {
    console.error('Registration failed:', error);
    return { success: false, error: error.message };
  }
}
```

---

## 🔍 Testing with Swagger

1. **Start your backend server:**
   ```bash
   python manage.py runserver
   ```

2. **Open Swagger UI:**
   - Navigate to: http://localhost:8000/api/docs/
   - Filter by "V1" tags to see only web API endpoints

3. **Test Authentication:**
   - Click "Authorize" button
   - Use `/onboarding/login/` to get a token
   - Copy the access token
   - Paste it in the Authorization field: `Bearer <token>`

4. **Test Endpoints:**
   - Try out endpoints directly in Swagger
   - See request/response examples
   - Copy code examples

---

## ⚠️ Important Notes

### V1 API is FROZEN
- ✅ Stable and production-ready
- ✅ No breaking changes will be made
- ❌ No new features will be added
- 💡 For new features, consider V2 API

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
```javascript
const handleApiError = (response) => {
  if (!response.success) {
    // Handle error
    console.error(response.message);
    if (response.errors) {
      // Field-specific errors
      Object.keys(response.errors).forEach(field => {
        console.error(`${field}: ${response.errors[field]}`);
      });
    }
  }
};
```

---

## 📖 Full Documentation

- **[Complete V1 API Reference](../api/V1_API_DOCUMENTATION.md)**
- **[Swagger UI - V1 Only](http://localhost:8000/api/docs/?tags=V1)**
- **[Swagger Setup Guide](../SWAGGER_SETUP.md)**

---

## 🆘 Troubleshooting

### Common Issues

**401 Unauthorized**
- Check if token is expired
- Implement token refresh logic
- Verify Authorization header format: `Bearer <token>`

**CORS Errors**
- Ensure backend CORS settings include your domain
- Check preflight requests are handled

**Network Errors**
- Verify API_BASE_URL is correct
- Check if backend server is running
- Verify network connectivity

---

**Need Help?** Check the [main API guide](../API_GUIDE.md) or contact the development team.







