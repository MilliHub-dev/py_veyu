# Frontend Integration Guide - Veyu Platform

Welcome! This guide helps you integrate your frontend with the Veyu backend authentication system.

## 📚 Documentation Structure

We've organized the documentation to help you get started quickly:

### 1. **FRONTEND_AUTH_COMPLETE.md** ⭐ START HERE
Complete implementation guide with:
- Quick reference for all endpoints
- Setup instructions
- Full authentication flows
- React component examples
- Error handling
- Testing guide

### 2. **AUTH_QUICK_START.md**
Condensed quick-start guide with:
- Minimal code examples
- API endpoint reference
- Common patterns

### 3. **AUTH_FLOWS_API.md**
Detailed API documentation covering:
- Email verification flow
- Password reset flow
- Request/response examples
- Security considerations
- Troubleshooting

### 4. **BUSINESS_VERIFICATION_API.md**
For dealers and mechanics:
- Business verification submission
- Document upload requirements
- Status checking
- Admin approval process

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Configure Your Environment
```bash
# .env
REACT_APP_API_BASE_URL=https://api.veyu.com
REACT_APP_FRONTEND_URL=https://dev.veyu.cc
```

### Step 2: Set Up API Client
```javascript
// src/api/client.js
const API_BASE = process.env.REACT_APP_API_BASE_URL;

export const api = {
  async call(endpoint, options = {}) {
    const token = localStorage.getItem('authToken');
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    
    if (token && !options.skipAuth) {
      headers['Authorization'] = `Token ${token}`;
    }
    
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Request failed');
    }
    
    return response.json();
  },
  
  post(endpoint, data, options) {
    return this.call(endpoint, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};
```

### Step 3: Implement Login
```javascript
const login = async (email, password) => {
  const response = await api.post('/api/v1/accounts/login/', {
    email,
    password,
    provider: 'veyu'
  }, { skipAuth: true });
  
  localStorage.setItem('authToken', response.token);
  localStorage.setItem('userType', response.user_type);
  
  return response;
};
```

### Step 4: Add Authentication Header
All authenticated requests automatically include:
```
Authorization: Token <your_token>
```

---

## 🔑 Key Endpoints

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/v1/accounts/signup/` | POST | No | Create account |
| `/api/v1/accounts/login/` | POST | No | Login |
| `/api/v1/accounts/verify-email/` | POST | Yes | Email verification |
| `/api/v1/accounts/password/reset/` | POST | No | Request password reset |
| `/api/v1/accounts/password/reset/confirm/` | POST | No | Confirm password reset |

---

## 📋 Implementation Checklist

### Core Authentication
- [ ] Set up environment variables
- [ ] Create API client with token authentication
- [ ] Implement signup flow
- [ ] Implement login flow
- [ ] Implement logout functionality
- [ ] Store auth token in localStorage
- [ ] Add authentication header to requests

### Email Verification
- [ ] Create email verification component
- [ ] Implement code input (6 digits)
- [ ] Add resend code functionality
- [ ] Handle verification success/error

### Password Reset
- [ ] Create forgot password form
- [ ] Implement reset request
- [ ] Create reset confirmation page
- [ ] Extract token from URL
- [ ] Handle password update

### User Experience
- [ ] Add loading states
- [ ] Implement error handling
- [ ] Create protected routes
- [ ] Handle token expiration
- [ ] Add success messages
- [ ] Implement form validation

### Testing
- [ ] Test signup flow
- [ ] Test login flow
- [ ] Test email verification
- [ ] Test password reset
- [ ] Test error scenarios
- [ ] Test protected routes

---

## 🎯 User Types & Features

### Customer
- Basic authentication
- Email verification
- Password reset
- Profile management

### Dealer
Additional features:
- Business profile setup
- Business verification submission
- Listing management
- Order management

### Mechanic
Additional features:
- Business profile setup
- Business verification submission
- Service booking management
- Schedule management

---

## 🔐 Authentication Flow

```
1. User Signs Up
   ↓
2. Account Created (verified_email: false)
   ↓
3. Verification Email Sent (6-digit code)
   ↓
4. User Enters Code
   ↓
5. Email Verified (verified_email: true)
   ↓
6. User Can Access Full Platform
```

---

## 📱 Response Data Structure

### Login Response (Customer)
```json
{
  "id": 123,
  "email": "user@example.com",
  "token": "abc123token",
  "first_name": "John",
  "last_name": "Doe",
  "user_type": "customer",
  "provider": "veyu",
  "is_active": true
}
```

### Login Response (Dealer/Mechanic)
```json
{
  "id": 456,
  "email": "dealer@example.com",
  "token": "def456token",
  "first_name": "Jane",
  "last_name": "Smith",
  "user_type": "dealer",
  "provider": "veyu",
  "is_active": true,
  "dealerId": "550e8400-e29b-41d4-a716-446655440000",
  "verified_id": true,
  "verified_business": false,
  "business_verification_status": "pending"
}
```

---

## ⚠️ Important Notes

### Provider Matching
**CRITICAL:** The provider in login request MUST match the provider used during signup.
- `veyu` → Validates email/password
- `google/apple/facebook` → Implement third-party token validation

### Token Storage
- Store in `localStorage` for web apps
- Store in secure storage for mobile apps
- Never expose tokens in URLs or logs

### Email Verification
- Code: 6 digits
- Expiry: 30 minutes
- Can be resent
- Single-use only

### Password Reset
- Token: JWT-based
- Expiry: 24 hours
- Single-use only
- Link format: `https://dev.veyu.cc/reset-password?token=<JWT>`

### Business Verification Status
- `not_submitted`: No verification yet
- `pending`: Awaiting admin review
- `verified`: Approved
- `rejected`: Rejected (check rejection_reason)

---

## 🛠️ Development Tools

### API Documentation
- **Swagger UI:** `https://api.veyu.com/api/docs/`
- **ReDoc:** `https://api.veyu.com/redoc/`

### Test Credentials (Development Only)
```
Email: test@veyu.com
Password: TestPass123!
```

### Testing with cURL
```bash
# Login
curl -X POST http://localhost:8000/api/v1/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@veyu.com","password":"TestPass123!","provider":"veyu"}'

# Verify Email
curl -X POST http://localhost:8000/api/v1/accounts/verify-email/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <your_token>" \
  -d '{"action":"confirm-code","code":"123456"}'
```

---

## 🐛 Common Issues & Solutions

### Issue: "Account does not exist"
**Solution:** User hasn't signed up yet. Direct them to signup page.

### Issue: "Provider mismatch"
**Solution:** User is trying to login with wrong provider. Show message: "This account was created with [provider]. Please use [provider] to login."

### Issue: "Invalid OTP"
**Solution:** Code expired or incorrect. Allow user to request new code.

### Issue: "Invalid or expired token" (password reset)
**Solution:** Reset link expired. User must request new reset link.

### Issue: Token not working
**Solution:** Check header format: `Authorization: Token <token>` (note: "Token" not "Bearer")

---

## 📞 Support & Resources

### Documentation
- Complete Auth Guide: `FRONTEND_AUTH_COMPLETE.md`
- Quick Start: `AUTH_QUICK_START.md`
- API Details: `AUTH_FLOWS_API.md`
- Business Verification: `BUSINESS_VERIFICATION_API.md`

### Contact
- **Email:** support@veyu.cc
- **API Docs:** https://api.veyu.com/api/docs/
- **Status Page:** https://status.veyu.cc

---

## 🎓 Next Steps

1. ✅ Read `FRONTEND_AUTH_COMPLETE.md` for detailed implementation
2. ✅ Set up your development environment
3. ✅ Implement core authentication (signup, login, logout)
4. ✅ Add email verification flow
5. ✅ Implement password reset
6. ✅ Add protected routes
7. ✅ Test all flows thoroughly
8. ✅ Implement business verification (for dealers/mechanics)
9. ✅ Deploy to staging
10. ✅ Conduct user acceptance testing

---

**Version:** 1.0  
**Last Updated:** November 2025  
**Maintained by:** Veyu Development Team

Happy coding! 🚀
