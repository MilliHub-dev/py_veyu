# Authentication Endpoints Reference

Quick reference for all authentication endpoints, request/response payloads, and examples.

---

## Base URL
```
Production: https://api.veyu.com
Development: http://localhost:8000
```

## Authentication Header
```
Authorization: Token <your_token>
```

---

## 1. Signup

**Endpoint:** `POST /api/v1/accounts/signup/`  
**Authentication:** Not required

### Request Payload
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "SecurePass123!",
  "confirm_password": "SecurePass123!",
  "user_type": "customer",
  "provider": "veyu",
  "phone_number": "+2348123456789",
  "action": "create-account"
}
```

**Note:** `phone_number` is optional and only stored for customer accounts.

### Request Fields
| Field | Type | Required | Options | Description |
|-------|------|----------|---------|-------------|
| `email` | string | Yes | - | User's email address |
| `first_name` | string | Yes | - | User's first name |
| `last_name` | string | Yes | - | User's last name |
| `password` | string | Yes* | - | Password (required for provider=veyu) |
| `confirm_password` | string | Yes* | - | Password confirmation |
| `user_type` | string | Yes | `customer`, `mechanic`, `dealer` | Type of user account |
| `provider` | string | Yes | `veyu`, `google` | Authentication provider |
| `phone_number` | string | No** | - | Phone number with country code |
| `action` | string | Yes | `create-account` | Action type |

*Required only when `provider=veyu`  
**Optional - only stored for customer accounts

### Response (201 Created)
```json
{
  "error": false,
  "message": "Account created successfully. Please check your email to verify your account.",
  "data": {
    "token": "abc123token456...",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "user_type": "customer",
    "email_verified": false,
    "verification_sent": true,
    "welcome_email_sent": true
  }
}
```

### Error Response (400/500)
```json
{
  "error": true,
  "message": "User with this email already exists"
}
```

---

## 2. Login

**Endpoint:** `POST /api/v1/accounts/login/`  
**Authentication:** Not required

### Request Payload
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "provider": "veyu"
}
```

### Request Fields
| Field | Type | Required | Options | Description |
|-------|------|----------|---------|-------------|
| `email` | string | Yes | - | User's email address |
| `password` | string | Yes* | - | User's password |
| `provider` | string | Yes | `veyu`, `google`, `apple`, `facebook` | Must match signup provider |

*Required only when `provider=veyu`

### Response - Customer (200 OK)
```json
{
  "id": 123,
  "email": "user@example.com",
  "token": "abc123token456...",
  "first_name": "John",
  "last_name": "Doe",
  "user_type": "customer",
  "provider": "veyu",
  "is_active": true
}
```

### Response - Dealer (200 OK)
```json
{
  "id": 456,
  "email": "dealer@example.com",
  "token": "def456token789...",
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

### Response - Mechanic (200 OK)
```json
{
  "id": 789,
  "email": "mechanic@example.com",
  "token": "ghi789token012...",
  "first_name": "Mike",
  "last_name": "Johnson",
  "user_type": "mechanic",
  "provider": "veyu",
  "is_active": true,
  "mechanicId": "660e8400-e29b-41d4-a716-446655440001",
  "verified_id": true,
  "verified_business": true,
  "business_verification_status": "verified"
}
```

### Error Responses
```json
// 404 - Account doesn't exist
{
  "error": true,
  "message": "Account does not exist"
}

// 401 - Provider mismatch
{
  "error": true,
  "message": "Authentication failed: Provider mismatch"
}

// 401 - Invalid credentials
{
  "error": true,
  "message": "Invalid credentials"
}
```

---

## 3. Email Verification - Request Code

**Endpoint:** `POST /api/v1/accounts/verify-email/`  
**Authentication:** Required (Token)

### Request Payload
```json
{
  "action": "request-code"
}
```

### Request Fields
| Field | Type | Required | Options | Description |
|-------|------|----------|---------|-------------|
| `action` | string | Yes | `request-code` | Request new verification code |

### Response (200 OK)
```json
{
  "error": false,
  "message": "OTP sent to your inbox"
}
```

---

## 4. Email Verification - Confirm Code

**Endpoint:** `POST /api/v1/accounts/verify-email/`  
**Authentication:** Required (Token)

### Request Payload
```json
{
  "action": "confirm-code",
  "code": "123456"
}
```

### Request Fields
| Field | Type | Required | Options | Description |
|-------|------|----------|---------|-------------|
| `action` | string | Yes | `confirm-code` | Verify email with code |
| `code` | string | Yes | - | 6-digit verification code |

### Response (200 OK)
```json
{
  "error": false,
  "message": "Successfully verified your email"
}
```

### Error Response (400)
```json
{
  "error": true,
  "message": "Invalid OTP"
}
```

**Note:** Code expires in 30 minutes and is single-use only.

---


---

## 5. Password Reset - Request

**Endpoint:** `POST /api/v1/accounts/password/reset/`  
**Authentication:** Not required

### Request Payload
```json
{
  "email": "user@example.com"
}
```

### Request Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | User's email address |

### Response (200 OK)
```json
{
  "success": true,
  "message": "Password reset link has been sent to your email."
}
```

**Note:** Always returns success for security (prevents email enumeration). Reset link expires in 24 hours.

---

## 6. Password Reset - Confirm

**Endpoint:** `POST /api/v1/accounts/password/reset/confirm/`  
**Authentication:** Not required

### Request Payload
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "password": "NewSecurePass123!"
}
```

### Request Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `token` | string | Yes | JWT token from reset email link |
| `password` | string | Yes | New password (min 8 characters) |

### Response (200 OK)
```json
{
  "success": true,
  "message": "Password has been reset successfully."
}
```

### Error Response (400)
```json
{
  "error": true,
  "message": "Invalid or expired token. Please request a new password reset."
}
```

**Note:** Token expires in 24 hours and is single-use only.

---

## 7. Token Refresh

**Endpoint:** `POST /api/v1/accounts/token/refresh/`  
**Authentication:** Not required

### Request Payload
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Request Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `refresh` | string | Yes | JWT refresh token |

### Response (200 OK)
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

## Quick Examples

### JavaScript/Fetch
```javascript
// Signup
const signup = await fetch('https://dev.veyu.cc/api/v1/accounts/signup/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    first_name: 'John',
    last_name: 'Doe',
    password: 'SecurePass123!',
    confirm_password: 'SecurePass123!',
    user_type: 'customer',
    provider: 'veyu',
    action: 'create-account'
  })
});

// Login
const login = await fetch('https://dev.veyu.cc/api/v1/accounts/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SecurePass123!',
    provider: 'veyu'
  })
});

// Verify Email (with token)
const verify = await fetch('https://dev.veyu.cc/api/v1/accounts/verify-email/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Token abc123token456...'
  },
  body: JSON.stringify({
    action: 'confirm-code',
    code: '123456'
  })
});
```

### cURL
```bash
# Signup
curl -X POST https://dev.veyu.cc/api/v1/accounts/signup/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!",
    "user_type": "customer",
    "provider": "veyu",
    "action": "create-account"
  }'

# Login
curl -X POST https://dev.veyu.cc/api/v1/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "provider": "veyu"
  }'

# Verify Email
curl -X POST https://dev.veyu.cc/api/v1/accounts/verify-email/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token abc123token456..." \
  -d '{
    "action": "confirm-code",
    "code": "123456"
  }'
```

---

## Important Notes

### Provider Matching
- Provider in login **MUST** match the provider used during signup
- `veyu`: Validates email and password
- `google`: Third-party authentication

### Token Format
- **Header:** `Authorization: Token <token>`
- **NOT** `Bearer <token>`

### Verification Codes
- **Format:** 6 digits
- **Expiry:** 30 minutes
- **Single-use:** Yes
- **Can be resent:** Yes

### Password Reset Tokens
- **Format:** JWT
- **Expiry:** 24 hours
- **Single-use:** Yes

### Business Verification Status
- `not_submitted`: No verification submitted
- `pending`: Awaiting admin review
- `verified`: Approved by admin
- `rejected`: Rejected by admin

---

**Last Updated:** November 2025  
**Version:** 1.0
