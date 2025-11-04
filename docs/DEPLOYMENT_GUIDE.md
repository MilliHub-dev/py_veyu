# Veyu Backend Deployment Guide

## ✅ Fixed Issues

### 1. ASGI Configuration Error (FIXED)
**Problem:** `ImproperlyConfigured: Requested setting REST_FRAMEWORK, but settings are not configured`

**Root Cause:** The `chat.routing` module was imported before `django.setup()` was called in `veyu/asgi.py`, causing Django settings to be accessed before configuration.

**Solution:** Moved the import of `chat.routing` and `chat.middleware` to **after** `django.setup()` call.

**File Changed:** `veyu/asgi.py`

```python
# BEFORE (INCORRECT)
from chat.routing import urlpatterns as chat_urlpatterns  # ❌ Too early
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

# AFTER (CORRECT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()
# Import after Django setup to avoid settings configuration errors
from chat.routing import urlpatterns as chat_urlpatterns  # ✅ After setup
from chat.middleware import ApiTokenAuthMiddleware
```

---

## 🚀 Render Deployment Checklist

### Environment Variables to Set on Render

Make sure all these environment variables are configured in your Render dashboard:

#### Django Core
```bash
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-app.onrender.com
DJANGO_SETTINGS_MODULE=veyu.settings
```

#### Database
```bash
DATABASE_URL=postgresql://user:password@host:port/database
```

#### Cloudinary
```bash
CLOUDINARY_URL=cloudinary://your-cloudinary-url
```

#### Email Configuration
```bash
EMAIL_HOST_USER=info.veyu@gmail.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=info.veyu@gmail.com
SERVER_EMAIL=info.veyu@gmail.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True

# ZeptoMail (Alternative)
ZEPTOMAIL_API_KEY=your-zeptomail-key
ZEPTOMAIL_SENDER_EMAIL=admin@veyu.cc
```

#### Frontend URL
```bash
FRONTEND_URL=https://dev.veyu.cc
```

#### Payment Gateways
```bash
# Paystack
PAYSTACK_LIVE_PUBLIC_KEY=your-live-public-key
PAYSTACK_LIVE_SECRET_KEY=your-live-secret-key
PAYSTACK_TEST_PUBLIC_KEY=pk_test_...
PAYSTACK_TEST_SECRET_KEY=sk_test_...

# Flutterwave
FLW_SECRET_KEY=your-flutterwave-key
```

#### Other Services
```bash
AFRICAS_TALKING_API_KEY=your-api-key
```

---

## 📦 Build Configuration

### Build Command
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

### Start Command
```bash
daphne -b 0.0.0.0 -p $PORT veyu.asgi:application
```

---

## 🔧 Common Deployment Issues & Solutions

### Issue 1: Module Not Found Errors
**Symptom:** `ModuleNotFoundError: No module named 'xyz'`

**Solution:** Ensure all dependencies are in `requirements.txt`:
```bash
pip freeze > requirements.txt
```

Common missing packages:
- `whitenoise` - For static files
- `daphne` - ASGI server
- `channels` - WebSocket support
- `channels-redis` - Redis channel layer
- `psycopg2-binary` - PostgreSQL adapter
- `reportlab` - PDF generation

### Issue 2: Static Files Not Loading
**Symptom:** CSS/JS files return 404

**Solution:** 
1. Ensure `whitenoise` is installed
2. Run `python manage.py collectstatic` during build
3. Check `STATIC_ROOT` and `STATIC_URL` in settings

### Issue 3: Database Connection Errors
**Symptom:** `OperationalError: could not connect to server`

**Solution:**
1. Verify `DATABASE_URL` environment variable is set
2. Ensure PostgreSQL addon is attached to your Render service
3. Check database credentials

### Issue 4: WebSocket Connection Fails
**Symptom:** WebSocket connections fail or timeout

**Solution:**
1. Ensure Redis is configured and running
2. Check `CHANNEL_LAYERS` configuration in settings
3. Verify Render allows WebSocket connections

### Issue 5: CORS Errors
**Symptom:** Frontend can't connect to API

**Solution:**
1. Add frontend domain to `ALLOWED_HOSTS`
2. Configure `CORS_ALLOWED_ORIGINS` in settings
3. Ensure `corsheaders` middleware is enabled

---

## 🔍 Debugging Deployment

### View Logs on Render
1. Go to your service dashboard
2. Click on "Logs" tab
3. Look for error messages

### Test ASGI Application Locally
```bash
# Test if ASGI loads without errors
python -c "import veyu.asgi"

# Run with Daphne locally
daphne -b 127.0.0.1 -p 8000 veyu.asgi:application
```

### Check Environment Variables
```bash
# In Render shell
echo $DJANGO_SETTINGS_MODULE
echo $DATABASE_URL
```

---

## 📋 Pre-Deployment Checklist

- [ ] All environment variables configured on Render
- [ ] `requirements.txt` is up to date
- [ ] Database migrations are ready
- [ ] Static files configuration is correct
- [ ] ASGI configuration is fixed (imports after django.setup())
- [ ] `DEBUG=False` for production
- [ ] `ALLOWED_HOSTS` includes your Render domain
- [ ] Redis is configured for channels
- [ ] CORS settings allow your frontend domain

---

## 🎯 Post-Deployment Steps

1. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

2. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

3. **Collect Static Files** (if not done in build)
   ```bash
   python manage.py collectstatic --noinput
   ```

4. **Test Key Endpoints**
   - `/api/docs/` - Swagger documentation
   - `/admin/` - Admin panel
   - `/api/v1/accounts/login/` - Authentication

5. **Monitor Logs**
   - Check for any errors
   - Monitor performance
   - Watch for memory/CPU usage

---

## 🔐 Security Recommendations

1. **Never commit secrets** to version control
2. Use **strong SECRET_KEY** in production
3. Set **DEBUG=False** in production
4. Configure **ALLOWED_HOSTS** properly
5. Use **HTTPS** only (Render provides this)
6. Enable **CSRF protection**
7. Configure **CORS** restrictively
8. Use **environment variables** for all secrets

---

## 📞 Support

If deployment issues persist:
1. Check Render's troubleshooting guide: https://render.com/docs/troubleshooting-deploys
2. Review Django deployment checklist: https://docs.djangoproject.com/en/stable/howto/deployment/checklist/
3. Check Daphne documentation: https://github.com/django/daphne

---

## 🎉 Success Indicators

Your deployment is successful when:
- ✅ Build completes without errors
- ✅ Service starts and stays running
- ✅ API documentation loads at `/api/docs/`
- ✅ Admin panel accessible at `/admin/`
- ✅ Database connections work
- ✅ WebSocket connections establish
- ✅ Static files load correctly
- ✅ Email sending works
- ✅ Payment webhooks receive events

---

**Last Updated:** November 4, 2025
**Status:** ASGI configuration fixed ✅
