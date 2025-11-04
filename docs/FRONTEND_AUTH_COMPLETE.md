# Complete Frontend Authentication Guide

Comprehensive authentication implementation guide for Veyu platform frontend developers.

## 📋 Table of Contents
- [Quick Reference](#quick-reference)
- [Setup](#setup)
- [Authentication Flows](#authentication-flows)
- [API Endpoints](#api-endpoints)
- [React Examples](#react-examples)
- [Error Handling](#error-handling)

---

## Quick Reference

### Base Configuration
```javascript
// API Base URL
Production: https://api.veyu.com
Development: http://localhost:8000

// Authentication Header
Authorization: Token <your_token>

// User Types
- customer: Regular users
- mechanic: Mechanics
- dealer: Car dealers

// Providers
- veyu: Native authentication
- google: Google OAuth
- apple: Apple Sign In
- facebook: Facebook Login
```

### Key Endpoints
| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/v1/accounts/login/` | POST | No | Login |
| `/api/v1/accounts/verify-email/` | POST | Yes | Email verification |
| `/api/v1/accounts/verify-phone/` | POST | Yes | Phone verification |
| `/api/v1/accounts/password/reset/` | POST | No | Request password reset |
| `/api/v1/accounts/password/reset/confirm/` | POST | No | Confirm password reset |
| `/api/v1/accounts/token/refresh/` | POST | No | Refresh JWT token |

---

## Setup

### 1. Environment Variables
```bash
REACT_APP_API_BASE_URL=https://api.veyu.com
REACT_APP_FRONTEND_URL=https://dev.veyu.cc
```

### 2. API Client
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

---

## Authentication Flows

### 1. Signup (Note: Check endpoint availability)

**Endpoint:** `POST /api/v1/accounts/auth/` or via dj-rest-auth

```javascript
const signup = async (userData) => {
  const response = await api.post('/api/v1/accounts/auth/', {
    email: userData.email,
    first_name: userData.firstName,
    last_name: userData.lastName,
    password: userData.password,
    confirm_password: userData.confirmPassword,
    user_type: userData.userType, // customer | mechanic | dealer
    provider: 'veyu',
    phone_number: userData.phone, // optional
    action: 'create-account'
  }, { skipAuth: true });
  
  // Store token
  localStorage.setItem('authToken', response.data.token);
  return response;
};
```

### 2. Login

**Endpoint:** `POST /api/v1/accounts/login/`

```javascript
const login = async (email, password) => {
  const response = await api.post('/api/v1/accounts/login/', {
    email,
    password,
    provider: 'veyu'
  }, { skipAuth: true });
  
  // Store auth data
  localStorage.setItem('authToken', response.token);
  localStorage.setItem('userId', response.id);
  localStorage.setItem('userType', response.user_type);
  
  // Store business data if applicable
  if (response.dealerId) {
    localStorage.setItem('dealerId', response.dealerId);
    localStorage.setItem('businessStatus', response.business_verification_status);
  }
  
  return response;
};
```

### 3. Email Verification

**Endpoint:** `POST /api/v1/accounts/verify-email/`

```javascript
// Request new code
const requestCode = async () => {
  return await api.post('/api/v1/accounts/verify-email/', {
    action: 'request-code'
  });
};

// Verify with code
const verifyEmail = async (code) => {
  return await api.post('/api/v1/accounts/verify-email/', {
    action: 'confirm-code',
    code: code // 6-digit code
  });
};
```

### 4. Password Reset

```javascript
// Step 1: Request reset
const requestReset = async (email) => {
  return await api.post('/api/v1/accounts/password/reset/', {
    email
  }, { skipAuth: true });
};

// Step 2: Confirm reset
const confirmReset = async (token, newPassword) => {
  return await api.post('/api/v1/accounts/password/reset/confirm/', {
    token,
    password: newPassword
  }, { skipAuth: true });
};
```

---

## React Examples

### Auth Context
```jsx
import { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api/client';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (token) {
      setUser({
        id: localStorage.getItem('userId'),
        email: localStorage.getItem('userEmail'),
        userType: localStorage.getItem('userType'),
        token
      });
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const response = await api.post('/api/v1/accounts/login/', {
      email, password, provider: 'veyu'
    }, { skipAuth: true });
    
    localStorage.setItem('authToken', response.token);
    localStorage.setItem('userId', response.id);
    localStorage.setItem('userEmail', response.email);
    localStorage.setItem('userType', response.user_type);
    
    setUser({
      id: response.id,
      email: response.email,
      userType: response.user_type,
      token: response.token
    });
    
    return response;
  };

  const logout = () => {
    localStorage.clear();
    setUser(null);
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {!loading && children}
    </AuthContext.Provider>
  );
}
```

### Login Component
```jsx
import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login(email, password);
      window.location.href = '/dashboard';
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && <div className="error">{error}</div>}
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      <button type="submit">Login</button>
    </form>
  );
}
```

### Email Verification Component
```jsx
import { useState } from 'react';
import { api } from '../api/client';

function EmailVerification() {
  const [code, setCode] = useState('');
  const [error, setError] = useState('');

  const handleVerify = async (e) => {
    e.preventDefault();
    try {
      await api.post('/api/v1/accounts/verify-email/', {
        action: 'confirm-code',
        code
      });
      alert('Email verified!');
      window.location.href = '/dashboard';
    } catch (err) {
      setError(err.message);
    }
  };

  const handleResend = async () => {
    try {
      await api.post('/api/v1/accounts/verify-email/', {
        action: 'request-code'
      });
      alert('Code sent!');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div>
      <h2>Verify Your Email</h2>
      {error && <div className="error">{error}</div>}
      <form onSubmit={handleVerify}>
        <input
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="000000"
          maxLength={6}
          required
        />
        <button type="submit">Verify</button>
      </form>
      <button onClick={handleResend}>Resend Code</button>
    </div>
  );
}
```

### Protected Route
```jsx
import { Navigate } from 'react-router-dom';

function ProtectedRoute({ children, requiredUserType }) {
  const token = localStorage.getItem('authToken');
  const userType = localStorage.getItem('userType');

  if (!token) return <Navigate to="/login" />;
  
  if (requiredUserType && userType !== requiredUserType) {
    return <Navigate to="/dashboard" />;
  }

  return children;
}

// Usage:
// <Route path="/dashboard" element={
//   <ProtectedRoute><Dashboard /></ProtectedRoute>
// } />
```

---

## Error Handling

### Common Errors
```javascript
// Account doesn't exist
{ error: true, message: "Account does not exist" }

// Provider mismatch
{ error: true, message: "Authentication failed: Provider mismatch" }

// Invalid credentials
{ error: true, message: "Invalid credentials" }

// Invalid OTP
{ error: true, message: "Invalid OTP" }

// Expired token
{ error: true, message: "Invalid or expired token. Please request a new password reset." }
```

### Error Handler
```javascript
const handleApiError = (error) => {
  if (error.message.includes('401')) {
    // Unauthorized - clear token and redirect
    localStorage.clear();
    window.location.href = '/login';
  } else if (error.message.includes('404')) {
    return 'Resource not found';
  } else if (error.message.includes('500')) {
    return 'Server error. Please try again later.';
  }
  return error.message || 'An error occurred';
};
```

---

## Important Notes

### Email Verification
- **Code Format:** 6 digits
- **Expiry:** 30 minutes
- **Can be resent:** Yes
- **Single-use:** Yes

### Password Reset
- **Token Type:** JWT
- **Expiry:** 24 hours
- **Single-use:** Yes
- **Link Format:** `https://dev.veyu.cc/reset-password?token=<JWT>`

### Authentication
- **Token Type:** Token-based (not JWT for regular auth)
- **Header Format:** `Authorization: Token <token>`
- **Storage:** localStorage recommended
- **Expiry:** Check with backend team

### Provider Matching
- **Critical:** Provider in login MUST match signup provider
- **veyu:** Requires password validation
- **google/apple/facebook:** Implement third-party token validation

### User Types & Responses
- **customer:** Basic user data only
- **dealer:** Includes `dealerId`, `verified_business`, `business_verification_status`
- **mechanic:** Includes `mechanicId`, `verified_business`, `business_verification_status`

### Business Verification Status
- `not_submitted`: No verification submitted
- `pending`: Awaiting admin review
- `verified`: Approved by admin
- `rejected`: Rejected (check rejection_reason)

---

## Testing

### Test Credentials (Development)
```
Email: test@veyu.com
Password: TestPass123!
```

### Manual Testing
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

## Additional Resources

- **Full API Documentation:** `/docs/AUTH_FLOWS_API.md`
- **Quick Start Guide:** `/docs/AUTH_QUICK_START.md`
- **Business Verification:** `/docs/BUSINESS_VERIFICATION_API.md`
- **Swagger UI:** `https://api.veyu.com/api/docs/`
- **Support:** support@veyu.cc

---

## Checklist for Frontend Implementation

- [ ] Set up environment variables
- [ ] Create API client with token authentication
- [ ] Implement Auth Context/Provider
- [ ] Create Login component
- [ ] Create Signup component (verify endpoint exists)
- [ ] Create Email Verification component
- [ ] Create Password Reset Request component
- [ ] Create Password Reset Confirm component
- [ ] Implement Protected Routes
- [ ] Add error handling
- [ ] Store user data in localStorage
- [ ] Handle token expiration
- [ ] Test all authentication flows
- [ ] Implement logout functionality
- [ ] Add loading states
- [ ] Handle provider-specific logic

---

**Last Updated:** November 2025  
**Version:** 1.0  
**Maintained by:** Veyu Development Team
