# Gmail SMTP Setup Guide

This guide explains how to configure Gmail SMTP for the Veyu platform.

## Prerequisites

1. A Gmail account
2. Two-factor authentication (2FA) enabled on your Gmail account

## Step 1: Enable 2FA on Gmail

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under "Signing in to Google", click on "2-Step Verification"
3. Follow the setup process to enable 2FA

## Step 2: Generate App Password

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under "Signing in to Google", click on "App passwords"
3. Select "Mail" as the app
4. Select "Other (Custom name)" as the device
5. Enter "Veyu Platform" as the custom name
6. Click "Generate"
7. Copy the 16-character app password (it will look like: `abcd efgh ijkl mnop`)

## Step 3: Update Environment Variables

Update your `.env` file with the following Gmail configuration:

```bash
# Email Configuration (Gmail)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
SERVER_EMAIL=your-email@gmail.com

# Email Settings
EMAIL_BACKEND=utils.email_backends.ReliableSMTPBackend
EMAIL_SSL_VERIFY=True
EMAIL_TIMEOUT=15
EMAIL_MAX_RETRIES=3
EMAIL_RETRY_DELAY=2
EMAIL_FALLBACK_ENABLED=True
EMAIL_FALLBACK_BACKEND=django.core.mail.backends.console.EmailBackend
```

## Step 4: Test the Configuration

Run the email test command to verify everything is working:

```bash
# Test configuration and connection
python manage.py test_email --check-only --health-check

# Send a test email
python manage.py test_email --to your-test@email.com
```

## Important Notes

1. **Use App Passwords**: Never use your regular Gmail password. Always use the 16-character app password.

2. **Security**: App passwords bypass 2FA, so keep them secure and don't share them.

3. **Rate Limits**: Gmail has sending limits:
   - 500 emails per day for free accounts
   - 2000 emails per day for Google Workspace accounts

4. **From Address**: The `DEFAULT_FROM_EMAIL` should match your Gmail address to avoid authentication issues.

5. **SSL Verification**: Gmail requires proper SSL certificate verification, so keep `EMAIL_SSL_VERIFY=True`.

## Troubleshooting

### "Username and password not accepted" Error

1. Verify 2FA is enabled on your Gmail account
2. Make sure you're using the app password, not your regular password
3. Check that the email address is correct

### "SSL Certificate Verification Failed" Error

1. Ensure `EMAIL_SSL_VERIFY=True` in your `.env` file
2. Check your system's SSL certificates are up to date

### Rate Limiting Issues

1. Monitor your daily sending limits
2. Consider upgrading to Google Workspace for higher limits
3. Implement email queuing for high-volume applications

## Alternative: Google Workspace

For production applications, consider using Google Workspace which offers:
- Higher sending limits (2000 emails/day)
- Better deliverability
- Professional email addresses (@yourdomain.com)
- Enhanced security features

## Security Best Practices

1. **Rotate App Passwords**: Regularly generate new app passwords and revoke old ones
2. **Monitor Usage**: Keep track of email sending patterns
3. **Use Environment Variables**: Never commit email credentials to version control
4. **Enable Logging**: Monitor email delivery success/failure rates
5. **Implement Fallbacks**: Always have a backup email method configured