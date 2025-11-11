# Brevo SMTP Setup Guide

## Why Brevo?
- **Free tier**: 300 emails/day
- **Reliable delivery**: Better than Gmail for production
- **No firewall issues**: Works in most server environments
- **Easy setup**: Simple SMTP configuration
- **Email tracking**: Built-in analytics and tracking

## Setup Steps

### 1. Create Brevo Account
1. Go to https://www.brevo.com/
2. Sign up for a free account
3. Verify your email address

### 2. Get SMTP Credentials
1. Log in to your Brevo dashboard
2. Go to **Settings** → **SMTP & API**
3. Click on **SMTP** tab
4. You'll see your SMTP credentials:
   - **SMTP Server**: `smtp-relay.brevo.com`
   - **Port**: `587` (recommended) or `465` (SSL)
   - **Login**: Your Brevo account email
   - **SMTP Key**: Click "Generate a new SMTP key" if you don't have one

### 3. Verify Sender Email
1. Go to **Senders** → **Domains & Addresses**
2. Add your sender email (e.g., `noreply@veyu.cc`)
3. Verify the email by clicking the link sent to that address
4. **Important**: You can only send from verified email addresses

### 4. Update Environment Variables

Update your `.env` file with your Brevo credentials:

```bash
# Email - Brevo SMTP Configuration
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_brevo_account_email@example.com
EMAIL_HOST_PASSWORD=your_brevo_smtp_key_here
DEFAULT_FROM_EMAIL=noreply@veyu.cc
```

**Replace:**
- `your_brevo_account_email@example.com` - Your Brevo login email
- `your_brevo_smtp_key_here` - The SMTP key from step 2
- `noreply@veyu.cc` - Your verified sender email

### 5. Test Email Delivery

Run the test script to verify configuration:

```bash
python manage.py shell < test_email_delivery.py
```

Or test with Django shell:

```python
from django.core.mail import send_mail

send_mail(
    subject='Test Email from Veyu',
    message='This is a test email.',
    from_email='noreply@veyu.cc',  # Must be verified in Brevo
    recipient_list=['your-email@example.com'],
    fail_silently=False,
)
```

### 6. Monitor Email Delivery

1. Go to **Statistics** in Brevo dashboard
2. View email delivery rates, opens, clicks, etc.
3. Check **Logs** for detailed delivery information

## Brevo Free Tier Limits

- **300 emails/day** (9,000/month)
- Unlimited contacts
- Email templates
- Real-time statistics
- SMTP and API access

## Upgrade Options

If you need more than 300 emails/day:
- **Lite Plan**: $25/month - 10,000 emails/month
- **Premium Plan**: $65/month - 20,000 emails/month
- **Enterprise**: Custom pricing

## Troubleshooting

### "Authentication failed"
- Verify your SMTP key is correct
- Make sure you're using your Brevo account email as EMAIL_HOST_USER
- Generate a new SMTP key if needed

### "Sender not verified"
- Add and verify your sender email in Brevo dashboard
- You can only send from verified addresses

### "Daily limit exceeded"
- You've sent more than 300 emails today
- Upgrade your plan or wait until tomorrow
- Check your Brevo dashboard for usage stats

### Emails going to spam
- Verify your domain with SPF and DKIM records
- Go to **Senders** → **Domains** in Brevo
- Follow the DNS configuration instructions

## Best Practices

1. **Use a dedicated sender email**: `noreply@veyu.cc` or `notifications@veyu.cc`
2. **Verify your domain**: Set up SPF and DKIM for better deliverability
3. **Monitor your stats**: Check Brevo dashboard regularly
4. **Handle bounces**: Set up webhook to handle bounce notifications
5. **Rate limiting**: Don't send too many emails at once

## Alternative SMTP Ports

If port 587 doesn't work:

```bash
# Try port 465 with SSL
EMAIL_PORT=465
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True
```

Or port 2525:

```bash
# Alternative port
EMAIL_PORT=2525
EMAIL_USE_TLS=True
```

## Support

- Brevo Documentation: https://developers.brevo.com/
- Brevo Support: https://help.brevo.com/
- Email: support@brevo.com

---

**Note**: After updating your `.env` file, restart your Django application for changes to take effect.
