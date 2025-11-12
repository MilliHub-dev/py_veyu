# Email Timeout Fix Guide

## Problem
Emails are timing out during signup, causing slow API responses and poor user experience.

**Error:** `Email send error: timed out`

## Solution

### 1. ✅ Increased Timeout (Already Applied)
Changed `EMAIL_TIMEOUT` from 30 to 60 seconds in `veyu/settings.py`

### 2. 🚀 Use Async Email Sending (Recommended)

Instead of blocking the signup process, send emails in the background.

#### Before (Blocking):
```python
# In accounts/api/views.py signup view
from accounts.utils.email_notifications import send_verification_email, send_welcome_email

# This blocks the API response
send_verification_email(user, verification_code)
send_welcome_email(user)
```

#### After (Non-blocking):
```python
# In accounts/api/views.py signup view
from utils.async_email import send_verification_email_async, send_welcome_email_async

# This returns immediately, emails sent in background
send_verification_email_async(user, verification_code)
send_welcome_email_async(user)
```

### 3. 📝 Update Your Signup View

Find your signup view in `accounts/api/views.py` and replace:

```python
# OLD CODE (remove this)
send_verification_email(user, verification_code)
send_welcome_email(user)

# NEW CODE (use this)
from utils.async_email import send_verification_email_async, send_welcome_email_async
send_verification_email_async(user, verification_code)
send_welcome_email_async(user)
```

### 4. 🔍 Available Async Email Functions

All in `utils/async_email.py`:

- `send_verification_email_async(user, verification_code)`
- `send_welcome_email_async(user)`
- `send_otp_email_async(user, otp_code, validity_minutes=30)`
- `send_password_reset_email_async(user, reset_url, reset_token=None)`
- `send_wallet_transaction_async(user, transaction_details)`
- `send_order_confirmation_async(user, order_details)`
- `send_booking_confirmation_async(user, booking_details)`

### 5. ✨ Benefits

- **Faster API responses** - User gets immediate response
- **Better UX** - No waiting for email to send
- **No timeouts** - Email sends in background
- **Same reliability** - Emails still get sent, just asynchronously

### 6. 🧪 Testing

Test that emails still work:

```bash
python test_simple_email.py
```

### 7. 📊 Monitoring

Check logs to see async email status:
- `Email queued for async sending` - Email started
- `Async email sent successfully` - Email delivered
- `Async email failed` - Email had issues

### 8. 🔧 Alternative: Use Celery (Advanced)

For production, consider using Celery for proper task queuing:

```python
# tasks.py
from celery import shared_task

@shared_task
def send_verification_email_task(user_id, verification_code):
    user = User.objects.get(id=user_id)
    send_verification_email(user, verification_code)
```

But the threading approach in `async_email.py` works well for most cases!

---

## Quick Fix Summary

1. ✅ Timeout increased to 60 seconds
2. 🚀 Use `send_verification_email_async()` instead of `send_verification_email()`
3. 📝 Update signup view to use async functions
4. 🎉 Enjoy fast API responses!
