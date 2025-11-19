# GidiNest API Guide

**Welcome to the GidiNest API Documentation!** This guide will help you choose the right API version for your platform.

---

## 🎯 Quick Start

### **Building a Web Application?**
👉 Use **[V1 API - Web Application](api/V1_API_DOCUMENTATION.md)**  
- Base URL: `https://api.gidinest.com/api/v1/`
- Status: **Production - FROZEN** (stable, no breaking changes)
- Interactive Docs: [Swagger UI - Filter by "V1" tags](/api/docs/)

### **Building a Mobile Application (iOS/Android)?**
👉 Use **[V2 API - Mobile Application](api/V2_API_DOCUMENTATION.md)**  
- Base URL: `https://api.gidinest.com/api/v2/`
- Status: **Development** (actively being enhanced)
- Interactive Docs: [Swagger UI - Filter by "V2" tags](/api/docs/)

---

## 📱 Platform-Specific Guides

### For Frontend Developers (Web)
- **[Frontend Developer Guide](frontend/QUICK_START.md)** - Complete setup guide
- **[V1 API Reference](api/V1_API_DOCUMENTATION.md)** - Full API documentation
- **[Swagger UI - V1 Only](http://localhost:8000/api/docs/?tags=V1)** - Interactive API explorer

### For Mobile Developers (iOS/Android)
- **[Mobile Developer Guide](mobile/QUICK_START.md)** - Complete setup guide
- **[V2 API Reference](api/V2_API_DOCUMENTATION.md)** - Full API documentation
- **[Swagger UI - V2 Only](http://localhost:8000/api/docs/?tags=V2)** - Interactive API explorer

---

## 🔄 API Versions Overview

### V1 API - Web Application
- **Purpose:** Web dashboard and admin portal
- **Status:** Production, FROZEN (no new features)
- **Endpoints:** `/api/v1/*`
- **Authentication:** JWT tokens
- **Documentation:** [V1 API Docs](api/V1_API_DOCUMENTATION.md)

**Available Modules:**
- Authentication & Onboarding
- Account & Profile Management
- Wallet Operations
- Savings Goals
- Community Posts

### V2 API - Mobile Application
- **Purpose:** Native mobile apps (iOS & Android)
- **Status:** Active Development
- **Endpoints:** `/api/v2/*`
- **Authentication:** JWT tokens (short-lived access tokens)
- **Documentation:** [V2 API Docs](api/V2_API_DOCUMENTATION.md)

**Available Modules:**
- Authentication & User Management
- Dashboard & Overview
- Profile & Settings
- Wallet Management
- Transactions
- Savings Goals
- Community
- Notifications
- KYC Verification

---

## 🔗 Interactive Documentation

### Swagger UI (Recommended)
- **Full API:** http://localhost:8000/api/docs/
- **V1 Only:** http://localhost:8000/api/docs/?tags=V1
- **V2 Only:** http://localhost:8000/api/docs/?tags=V2

### ReDoc (Alternative View)
- **Full API:** http://localhost:8000/api/redoc/

### OpenAPI Schema
- **JSON:** http://localhost:8000/api/schema/
- **YAML:** http://localhost:8000/api/schema/?format=openapi

---

## 🔐 Authentication

Both V1 and V2 use JWT (JSON Web Tokens) for authentication.

### Getting Started
1. Register/Login to get access and refresh tokens
2. Include token in Authorization header: `Bearer <access_token>`
3. Refresh token when access token expires

### Differences
- **V1:** Longer-lived tokens (suitable for web sessions)
- **V2:** Shorter-lived tokens (1 hour) with refresh mechanism (better for mobile security)

---

## 📊 Response Format

All APIs follow a standard response structure:

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    // Response data here
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Error description",
  "errors": {
    // Field-specific errors
  }
}
```

---

## 🚀 Getting Started

### 1. Choose Your Platform
- **Web App** → Use V1 API
- **Mobile App** → Use V2 API

### 2. Read Platform-Specific Guide
- **Frontend:** [docs/frontend/QUICK_START.md](frontend/QUICK_START.md)
- **Mobile:** [docs/mobile/QUICK_START.md](mobile/QUICK_START.md)

### 3. Explore Interactive Docs
- Open Swagger UI and filter by your API version
- Test endpoints directly from the browser

### 4. Start Building!
- Use the API reference documentation
- Follow the examples in Swagger UI

---

## ❓ Need Help?

- **API Issues:** Check the [Troubleshooting Guide](troubleshooting.md)
- **Swagger Help:** See [Swagger Setup Guide](SWAGGER_SETUP.md)
- **General Questions:** Contact the development team

---

## 📝 Notes

- **V1 is FROZEN:** No new features will be added. Use V2 for new functionality.
- **V2 is Active:** New features and improvements are being added regularly.
- **Both versions share the same database:** Data is consistent across platforms.
- **Swagger is always up-to-date:** Auto-generated from code, so it's the most current reference.

---

**Last Updated:** November 2025  
**Maintained By:** GidiNest Development Team





