# Authentication Flows API Documentation

This document provides comprehensive documentation for the email verification and password reset flows in the Veyu platform.

## Table of Contents
- [Email Verification Flow](#email-verification-flow)
- [Password Reset Flow](#password-reset-flow)
- [API Endpoints](#api-endpoints)
- [Frontend Integration Guide](#frontend-integration-guide)
- [Testing](#testing)

---

## Email Verification Flow

### Overview
When a user signs up, they receive a verification code via email that they must enter to verify their email address. This ensures that the email address provided is valid and belongs to the user.

### Flow Diagram
```
1. User signs up → Account created with verified_email=False
2. System generates verification code (6-digit OTP)
3. Verification email sent to user
4. User receives email with verification code
5. User enters code in app
6. System validates code
7. Account marked as verified (verified_email=True)
```

### Implementation Details

#### 1. Signup Process
When a user creates an account, the system automatically:
- Creates the user account
- Sets `verified_email` to `False`
- Generates a 6-digit verification code
- Sends a verification email with the code
- Sends a welcome email

**Endpoint:** `POST /api/v1/accounts/signup/`

**Request Body:**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "SecurePass123!",
  "confirm_password": "SecurePass123!",
  "user_type": "customer",
  "provider": "veyu",
  "phone_number": "+2348123456789"
}
```

**Response (201 Created):**
```json
{
  "token": "abc123...",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "user_type": "customer",
  "verified_email": false,
  "verification_sent": true,
  "welcome_email_sent": true
}
```

#### 2. Email Verification
Users verify their email by submitting the code they received.

**Endpoint:** `POST /api/v1/accounts/verify-email/`

**Headers:**
```
Authorization: Token <user_token>
```

**Request Body (Request Code):**
```json
{
  "action": "request-code"
}
```

**Response (200 OK):**
```json
{
  "error": false,
  "message": "OTP sent to your inbox"
}
```

**Request Body (Confirm Code):**
```json
{
  "action": "confirm-code",
  "code": "123456"
}
```

**Response (200 OK):**
```json
{
  "error": false,
  "message": "Successfully verified your email"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": true,
  "message": "Invalid OTP"
}
```

---

## Password Reset Flow

### Overview
Users who forget their password can request a password reset link via email. The link contains a secure token that allows them to set a new password.

### Flow Diagram
```
1. User clicks "Forgot Password"
2. User enters email address
3. System generates secure JWT token
4. Password reset email sent with reset link
5. User clicks link in email
6. User enters new password
7. System validates token and updates password
8. User can now login with new password
```

### Implementation Details

#### 1. Request Password Reset

**Endpoint:** `POST /api/v1/accounts/password/reset/`

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Password reset link has been sent to your email."
}
```

**Notes:**
- For security reasons, the same response is returned whether the email exists or not
- This prevents email enumeration attacks
- The reset link is valid for 24 hours

#### 2. Confirm Password Reset

**Endpoint:** `POST /api/v1/accounts/password/reset/confirm/`

**Request Body:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "password": "NewSecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Password has been reset successfully."
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": true,
  "message": "Invalid or expired token. Please request a new password reset."
}
```

---

## API Endpoints

### Authentication Endpoints Summary

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/v1/accounts/signup/` | POST | No | Create new account |
| `/api/v1/accounts/login/` | POST | No | Login to account |
| `/api/v1/accounts/verify-email/` | POST | Yes | Verify email with OTP |
| `/api/v1/accounts/password/reset/` | POST | No | Request password reset |
| `/api/v1/accounts/password/reset/confirm/` | POST | No | Confirm password reset |

### Email Templates

The system uses the following email templates:

1. **Verification Email** (`utils/templates/verification_email.html`)
   - Sent during signup
   - Contains 6-digit verification code
   - Code expires in 30 minutes

2. **Welcome Email** (`utils/templates/welcome_email.html`)
   - Sent after successful signup
   - Introduces user to platform features

3. **Password Reset Email** (`utils/templates/password_reset.html`)
   - Sent when user requests password reset
   - Contains secure reset link
   - Link expires in 24 hours

---

## Frontend Integration Guide

### 1. Signup Flow

```javascript
// Step 1: Create account
const signupResponse = await fetch('https://api.veyu.com/api/v1/accounts/signup/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'user@example.com',
    first_name: 'John',
    last_name: 'Doe',
    password: 'SecurePass123!',
    confirm_password: 'SecurePass123!',
    user_type: 'customer',
    provider: 'veyu',
    phone_number: '+2348123456789'
  })
});

const userData = await signupResponse.json();
// Store token for authenticated requests
localStorage.setItem('authToken', userData.token);

// Step 2: Show verification prompt
// User receives email with code
// Prompt user to enter the 6-digit code

// Step 3: Verify email
const verifyResponse = await fetch('https://api.veyu.com/api/v1/accounts/verify-email/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Token ${userData.token}`
  },
  body: JSON.stringify({
    action: 'confirm-code',
    code: '123456' // Code entered by user
  })
});

const verifyResult = await verifyResponse.json();
if (!verifyResult.error) {
  // Email verified successfully
  // Redirect to dashboard
}
```

### 2. Resend Verification Code

```javascript
const resendResponse = await fetch('https://api.veyu.com/api/v1/accounts/verify-email/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Token ${authToken}`
  },
  body: JSON.stringify({
    action: 'request-code'
  })
});
```

### 3. Password Reset Flow

```javascript
// Step 1: Request password reset
const resetRequest = await fetch('https://api.veyu.com/api/v1/accounts/password/reset/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'user@example.com'
  })
});

// User receives email with reset link
// Link format: https://dev.veyu.cc/reset-password?token=<JWT_TOKEN>

// Step 2: User clicks link and enters new password
// Extract token from URL query parameter
const urlParams = new URLSearchParams(window.location.search);
const token = urlParams.get('token');

// Submit new password
const resetConfirm = await fetch('https://api.veyu.com/api/v1/accounts/password/reset/confirm/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    token: token,
    password: 'NewSecurePass123!'
  })
});

const result = await resetConfirm.json();
if (result.success) {
  // Password reset successful
  // Redirect to login page
}
```

### 4. UI/UX Recommendations

#### Signup Page
- Show clear message after signup: "Please check your email for a verification code"
- Provide "Resend Code" button (disabled for 60 seconds after each send)
- Show countdown timer for code expiration
- Allow user to continue to dashboard but show verification banner

#### Email Verification Page
- 6-digit code input with auto-focus
- Auto-submit when all digits entered
- Clear error messages for invalid codes
- "Didn't receive code?" with resend option

#### Password Reset Request Page
- Simple email input form
- Clear success message (don't reveal if email exists)
- Link to support if user doesn't receive email

#### Password Reset Confirmation Page
- Password strength indicator
- Confirm password field
- Clear validation messages
- Redirect to login after successful reset

---

## Testing

### Test Scenarios

#### Email Verification
1. ✅ User signs up and receives verification email
2. ✅ User enters correct code and email is verified
3. ✅ User enters incorrect code and receives error
4. ✅ User requests new code and receives it
5. ✅ Verification code expires after 30 minutes
6. ✅ Already verified user cannot verify again

#### Password Reset
1. ✅ User requests password reset with valid email
2. ✅ User requests password reset with invalid email (same response)
3. ✅ User clicks reset link and successfully resets password
4. ✅ User tries to use expired token (>24 hours)
5. ✅ User tries to use invalid token
6. ✅ User can login with new password after reset

### Manual Testing

#### Test Email Verification
```bash
# 1. Create account
curl -X POST https://api.veyu.com/api/v1/accounts/signup/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "password": "TestPass123!",
    "confirm_password": "TestPass123!",
    "user_type": "customer",
    "provider": "veyu"
  }'

# 2. Check email for verification code

# 3. Verify email
curl -X POST https://api.veyu.com/api/v1/accounts/verify-email/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <your_token>" \
  -d '{
    "action": "confirm-code",
    "code": "123456"
  }'
```

#### Test Password Reset
```bash
# 1. Request password reset
curl -X POST https://api.veyu.com/api/v1/accounts/password/reset/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com"
  }'

# 2. Check email for reset link

# 3. Reset password
curl -X POST https://api.veyu.com/api/v1/accounts/password/reset/confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "token": "<token_from_email>",
    "password": "NewTestPass123!"
  }'
```

---

## Security Considerations

### Email Verification
- Verification codes are 6 digits (1 million combinations)
- Codes expire after 30 minutes
- Codes are single-use
- Rate limiting should be implemented to prevent brute force

### Password Reset
- Reset tokens are JWT-based with user ID embedded
- Tokens expire after 24 hours
- Tokens are invalidated after use
- Email enumeration is prevented (same response for valid/invalid emails)
- All existing sessions should be invalidated after password reset

### Best Practices
1. Use HTTPS for all API calls
2. Implement rate limiting on authentication endpoints
3. Log all authentication attempts
4. Send security alerts for password changes
5. Consider implementing 2FA for sensitive accounts

---

## Troubleshooting

### Common Issues

**Issue: Verification email not received**
- Check spam/junk folder
- Verify email configuration in settings
- Check email logs in `sent_emails/` directory (dev mode)
- Verify SMTP credentials

**Issue: "Invalid OTP" error**
- Code may have expired (30 minute limit)
- User may have entered wrong code
- Request new code

**Issue: Password reset link not working**
- Token may have expired (24 hour limit)
- Token may have been used already
- Request new reset link

**Issue: "Invalid or expired token" on password reset**
- Token has expired (>24 hours)
- Token format is incorrect
- User ID in token doesn't exist
- Request new password reset

---

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Frontend URL for email links
FRONTEND_URL=https://dev.veyu.cc

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=info.veyu@gmail.com
EMAIL_HOST_PASSWORD=your_password_here
DEFAULT_FROM_EMAIL="Veyu <info.veyu@gmail.com>"
```

### Django Settings

The following settings are configured in `veyu/settings.py`:

```python
# Frontend URL for email verification and password reset links
FRONTEND_URL = env.get_value('FRONTEND_URL', 'https://dev.veyu.cc')

# Email configuration (see settings.py for full config)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env.get_value('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = env.get_value('EMAIL_PORT', 587)
EMAIL_USE_TLS = env.get_value('EMAIL_USE_TLS', True)
```

---

## Support

For issues or questions:
- Email: support@veyu.cc
- Documentation: https://docs.veyu.cc
- API Status: https://status.veyu.cc
