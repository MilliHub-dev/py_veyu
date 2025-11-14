# Environment Variables Guide

This document provides comprehensive guidance on configuring environment variables for the Veyu platform deployment on Vercel.

## Quick Start

1. **Copy the template:**
   ```bash
   cp .env.example .env
   ```

2. **Generate a secret key:**
   ```bash
   python scripts/validate_env.py --generate-secret-key
   ```

3. **Edit `.env` with your values**

4. **Validate configuration:**
   ```bash
   python scripts/validate_env.py
   ```

## Critical Variables (Required)

These variables MUST be set for the application to function:

### `DJANGO_SECRET_KEY`
- **Purpose:** Django cryptographic signing key
- **Format:** 50+ character random string
- **Generate:** `python scripts/validate_env.py --generate-secret-key`
- **Example:** `DJANGO_SECRET_KEY=your-50-character-secret-key-here`

### `DATABASE_URL`
- **Purpose:** PostgreSQL database connection string
- **Format:** `postgresql://username:password@host:port/database?sslmode=require`
- **Providers:** Neon, Supabase, Railway, PlanetScale
- **Example:** `DATABASE_URL=postgresql://user:pass@ep-example.us-east-1.aws.neon.tech/dbname?sslmode=require`

### `EMAIL_HOST_USER` & `EMAIL_HOST_PASSWORD`
- **Purpose:** SMTP authentication for email sending
- **Providers:** Brevo (recommended), Gmail, SendGrid
- **Brevo Example:**
  ```
  EMAIL_HOST_USER=your-email@example.com
  EMAIL_HOST_PASSWORD=your-brevo-smtp-key
  ```

### `CLOUDINARY_URL`
- **Purpose:** Media file storage and CDN
- **Format:** `cloudinary://api_key:api_secret@cloud_name`
- **Get from:** [Cloudinary Console](https://cloudinary.com/console)
- **Example:** `CLOUDINARY_URL=cloudinary://123456789:abcdefghijklmnop@your-cloud-name`

### `AFRICAS_TALKING_API_KEY`
- **Purpose:** SMS/OTP functionality
- **Get from:** [Africa's Talking](https://account.africastalking.com/)
- **Example:** `AFRICAS_TALKING_API_KEY=your-api-key-here`

## Optional Variables

### Security & Performance
```bash
DEBUG=False                    # Always False in production
FRONTEND_URL=https://veyu.cc   # For email verification links
SENTRY_DSN=your-sentry-dsn     # Error tracking (recommended)
```

### Email Configuration
```bash
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@veyu.cc
EMAIL_TIMEOUT=60
```

### CORS & Security
```bash
CORS_ALLOWED_ORIGINS=https://veyu.cc,https://dev.veyu.cc
CSRF_TRUSTED_ORIGINS=https://*.vercel.app,https://*.veyu.cc
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## Service Setup Guides

### Database (PostgreSQL)

**Recommended: Neon**
1. Sign up at [neon.tech](https://neon.tech)
2. Create a new project
3. Copy the connection string
4. Set `DATABASE_URL=postgresql://...`

**Alternative: Supabase**
1. Sign up at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to Settings > Database
4. Copy the connection string
5. Set `DATABASE_URL=postgresql://...`

### Email (SMTP)

**Recommended: Brevo**
1. Sign up at [brevo.com](https://brevo.com)
2. Go to SMTP & API > SMTP
3. Create SMTP key
4. Set:
   ```
   EMAIL_HOST_USER=your-login-email
   EMAIL_HOST_PASSWORD=your-smtp-key
   ```

**Alternative: Gmail**
1. Enable 2FA on your Google account
2. Generate an App Password
3. Set:
   ```
   EMAIL_HOST=smtp.gmail.com
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   ```

### Media Storage (Cloudinary)

1. Sign up at [cloudinary.com](https://cloudinary.com)
2. Go to Dashboard
3. Copy the "Environment variable" value
4. Set `CLOUDINARY_URL=cloudinary://...`

### SMS (Africa's Talking)

1. Sign up at [africastalking.com](https://africastalking.com)
2. Go to Apps > Sandbox/Live
3. Copy the API Key
4. Set `AFRICAS_TALKING_API_KEY=your-key`

## Vercel Deployment

### Using Vercel CLI
```bash
vercel env add DJANGO_SECRET_KEY
vercel env add DATABASE_URL
vercel env add EMAIL_HOST_USER
vercel env add EMAIL_HOST_PASSWORD
vercel env add CLOUDINARY_URL
vercel env add AFRICAS_TALKING_API_KEY
```

### Using Vercel Dashboard
1. Go to your project settings
2. Navigate to Environment Variables
3. Add each variable with appropriate values
4. Set environment scope (Production, Preview, Development)

## Validation & Troubleshooting

### Validate Configuration
```bash
# Check all variables
python scripts/validate_env.py

# Generate secret key
python scripts/validate_env.py --generate-secret-key

# Setup helper
python scripts/setup_env.py
```

### Common Issues

**Database Connection Fails**
- Ensure SSL mode is set: `?sslmode=require`
- Check firewall settings
- Verify credentials

**Email Not Sending**
- Check SMTP credentials
- Verify TLS/SSL settings
- Test with a simple email client

**Media Uploads Fail**
- Verify Cloudinary URL format
- Check API key permissions
- Ensure CORS settings are correct

**SMS/OTP Not Working**
- Verify Africa's Talking API key
- Check account balance
- Ensure phone number format is correct

## Security Best Practices

1. **Never commit secrets to version control**
2. **Use different values for different environments**
3. **Rotate secrets regularly**
4. **Use strong, unique passwords**
5. **Enable 2FA on all service accounts**
6. **Monitor for unauthorized access**

## Environment-Specific Configuration

### Development
```bash
DEBUG=True
DATABASE_URL=sqlite:///local.db.sqlite3
USE_CONSOLE_EMAIL=True
```

### Staging
```bash
DEBUG=False
DATABASE_URL=postgresql://staging-db-url
FRONTEND_URL=https://staging.veyu.cc
```

### Production
```bash
DEBUG=False
DATABASE_URL=postgresql://production-db-url
FRONTEND_URL=https://veyu.cc
SENTRY_DSN=your-production-sentry-dsn
```

## Support

If you encounter issues:
1. Run the validation script: `python scripts/validate_env.py`
2. Check the logs for specific error messages
3. Refer to service provider documentation
4. Contact the development team with validation output