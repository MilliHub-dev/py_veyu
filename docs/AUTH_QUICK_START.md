# Authentication Quick Start Guide

Quick reference for implementing email verification and password reset in your frontend application.

## Base URL
```
Production: https://api.veyu.com
Development: http://localhost:8000
```

## Quick Reference

### 1. User Signup with Email Verification

```javascript
// POST /api/v1/accounts/signup/
const response = await fetch(`${API_BASE}/api/v1/accounts/signup/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: "user@example.com",
    first_name: "John",
    last_name: "Doe",
    password: "SecurePass123!",
    confirm_password: "SecurePass123!",
    user_type: "customer",  // customer | mechanic | dealer
    provider: "veyu",       // veyu | google | apple | facebook
    phone_number: "+2348123456789"  // optional
  })
});

// Response
{
  "token": "abc123...",
  "email": "user@example.com",
  "verified_email": false,
  "verification_sent": true
}
```

### 2. Verify Email with OTP

```javascript
// POST /api/v1/accounts/verify-email/
const response = await fetch(`${API_BASE}/api/v1/accounts/verify-email/`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Token ${userToken}`
  },
  body: JSON.stringify({
    action: "confirm-code",
    code: "123456"  // 6-digit code from email
  })
});

// Response
{
  "error": false,
  "message": "Successfully verified your email"
}
```

### 3. Resend Verification Code

```javascript
// POST /api/v1/accounts/verify-email/
const response = await fetch(`${API_BASE}/api/v1/accounts/verify-email/`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Token ${userToken}`
  },
  body: JSON.stringify({
    action: "request-code"
  })
});

// Response
{
  "error": false,
  "message": "OTP sent to your inbox"
}
```

### 4. Request Password Reset

```javascript
// POST /api/v1/accounts/password/reset/
const response = await fetch(`${API_BASE}/api/v1/accounts/password/reset/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: "user@example.com"
  })
});

// Response (always 200, even if email doesn't exist)
{
  "success": true,
  "message": "Password reset link has been sent to your email."
}
```

### 5. Reset Password

```javascript
// POST /api/v1/accounts/password/reset/confirm/
const response = await fetch(`${API_BASE}/api/v1/accounts/password/reset/confirm/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    token: "eyJ0eXAiOiJKV1QiLCJhbGc...",  // from email link
    password: "NewSecurePass123!"
  })
});

// Response
{
  "success": true,
  "message": "Password has been reset successfully."
}
```

## React Example Components

### Signup Component

```jsx
import { useState } from 'react';

function SignupForm() {
  const [formData, setFormData] = useState({
    email: '',
    first_name: '',
    last_name: '',
    password: '',
    confirm_password: '',
    user_type: 'customer',
    provider: 'veyu'
  });
  const [showVerification, setShowVerification] = useState(false);
  const [userToken, setUserToken] = useState('');

  const handleSignup = async (e) => {
    e.preventDefault();
    
    const response = await fetch('https://dev.veyu.cc/api/v1/accounts/signup/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    });
    
    const data = await response.json();
    
    if (response.ok) {
      setUserToken(data.token);
      setShowVerification(true);
      alert('Check your email for verification code!');
    }
  };

  return (
    <div>
      {!showVerification ? (
        <form onSubmit={handleSignup}>
          <input
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            required
          />
          <input
            type="text"
            placeholder="First Name"
            value={formData.first_name}
            onChange={(e) => setFormData({...formData, first_name: e.target.value})}
            required
          />
          <input
            type="text"
            placeholder="Last Name"
            value={formData.last_name}
            onChange={(e) => setFormData({...formData, last_name: e.target.value})}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={formData.password}
            onChange={(e) => setFormData({...formData, password: e.target.value})}
            required
          />
          <input
            type="password"
            placeholder="Confirm Password"
            value={formData.confirm_password}
            onChange={(e) => setFormData({...formData, confirm_password: e.target.value})}
            required
          />
          <button type="submit">Sign Up</button>
        </form>
      ) : (
        <VerificationForm token={userToken} />
      )}
    </div>
  );
}
```

### Email Verification Component

```jsx
function VerificationForm({ token }) {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);

  const handleVerify = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    const response = await fetch('https://dev.veyu.cc/api/v1/accounts/verify-email/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${token}`
      },
      body: JSON.stringify({
        action: 'confirm-code',
        code: code
      })
    });
    
    const data = await response.json();
    setLoading(false);
    
    if (!data.error) {
      alert('Email verified successfully!');
      // Redirect to dashboard
      window.location.href = '/dashboard';
    } else {
      alert(data.message);
    }
  };

  const handleResend = async () => {
    const response = await fetch('https://dev.veyu.cc/api/v1/accounts/verify-email/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${token}`
      },
      body: JSON.stringify({
        action: 'request-code'
      })
    });
    
    const data = await response.json();
    alert(data.message);
  };

  return (
    <form onSubmit={handleVerify}>
      <h2>Verify Your Email</h2>
      <p>Enter the 6-digit code sent to your email</p>
      <input
        type="text"
        placeholder="123456"
        value={code}
        onChange={(e) => setCode(e.target.value)}
        maxLength={6}
        pattern="[0-9]{6}"
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Verifying...' : 'Verify Email'}
      </button>
      <button type="button" onClick={handleResend}>
        Resend Code
      </button>
    </form>
  );
}
```

### Password Reset Request Component

```jsx
function ForgotPasswordForm() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const response = await fetch('https://dev.veyu.cc/api/v1/accounts/password/reset/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    
    if (response.ok) {
      setSubmitted(true);
    }
  };

  if (submitted) {
    return (
      <div>
        <h2>Check Your Email</h2>
        <p>If an account exists with {email}, you will receive a password reset link.</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit}>
      <h2>Forgot Password?</h2>
      <input
        type="email"
        placeholder="Enter your email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <button type="submit">Send Reset Link</button>
    </form>
  );
}
```

### Password Reset Confirm Component

```jsx
import { useSearchParams } from 'react-router-dom';

function ResetPasswordForm() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      alert('Passwords do not match!');
      return;
    }
    
    const response = await fetch('https://dev.veyu.cc/api/v1/accounts/password/reset/confirm/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, password })
    });
    
    const data = await response.json();
    
    if (data.success) {
      setSuccess(true);
      setTimeout(() => {
        window.location.href = '/login';
      }, 2000);
    } else {
      alert(data.message);
    }
  };

  if (success) {
    return (
      <div>
        <h2>Password Reset Successful!</h2>
        <p>Redirecting to login...</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit}>
      <h2>Reset Your Password</h2>
      <input
        type="password"
        placeholder="New Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        minLength={8}
        required
      />
      <input
        type="password"
        placeholder="Confirm New Password"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
        required
      />
      <button type="submit">Reset Password</button>
    </form>
  );
}
```

## Error Handling

### Common Error Responses

```javascript
// 400 Bad Request - Validation Error
{
  "error": true,
  "message": "Passwords do not match."
}

// 400 Bad Request - Invalid OTP
{
  "error": true,
  "message": "Invalid OTP"
}

// 400 Bad Request - Invalid Token
{
  "error": true,
  "message": "Invalid or expired token. Please request a new password reset."
}

// 401 Unauthorized - Authentication Required
{
  "detail": "Authentication credentials were not provided."
}

// 500 Internal Server Error
{
  "error": true,
  "message": "Failed to send password reset email. Please try again."
}
```

## Important Notes

1. **Email Verification Code**
   - 6 digits
   - Expires in 30 minutes
   - Can be resent

2. **Password Reset Token**
   - JWT-based
   - Expires in 24 hours
   - Single-use

3. **Authentication**
   - Use `Token` authentication for API calls
   - Include in header: `Authorization: Token <token>`

4. **User Types**
   - `customer` - Regular users
   - `mechanic` - Mechanics
   - `dealer` - Car dealers

5. **Providers**
   - `veyu` - Native authentication (requires password)
   - `google` - Google OAuth
   - `apple` - Apple Sign In
   - `facebook` - Facebook Login

## Testing

Use these test credentials in development:

```
Email: test@veyu.com
Password: TestPass123!
```

## Need Help?

- Full Documentation: `docs/AUTH_FLOWS_API.md`
- API Documentation: https://dev.veyu.cc/swagger/
- Support: support@veyu.cc
