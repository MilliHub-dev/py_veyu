# Brevo API Setup Guide

## Problem
SMTP emails are timing out on your server due to network/firewall issues.

## Solution: Use Brevo HTTP API Instead

The HTTP API is much faster and more reliable than SMTP.

---

## Step 1: Get Your Brevo API Key

1. Go to https://app.brevo.com/
2. Log in to your Brevo account
3. Click on your name (top right) → **SMTP & API**
4. Under **API Keys** section, click **Create a new API key**
5. Give it a name like "Veyu Production"
6. Copy the API key (starts with `xkeysib-...`)

---

## Step 2: Add API Key to Environment

### On Your Server:

Add this to your `.env` file or environment variables:

```bash
BREVO_API_KEY=xkeysib-your-actual-api-key-here
```

### Locally (for testing):

Add to your `.env` file:

```bash
BREVO_API_KEY=xkeysib-your-actual-api-key-here
```

---

## Step 3: Test the API

```bash
python test_brevo_api.py
```

You should see:
```
✅ Simple email sent! Message ID: <some-id>
✅ Template email sent!
✅ Verification email sent!
```

---

## Step 4: Deploy

Once you've added the `BREVO_API_KEY` to your server's environment variables:

1. Restart your application
2. Test signup - emails should now send instantly!

---

## Benefits of API vs SMTP

| Feature | SMTP | HTTP API |
|---------|------|----------|
| Speed | Slow (30-60s) | Fast (<2s) |
| Reliability | Blocked by firewalls | Works everywhere |
| Timeout Issues | Common | Rare |
| Setup | Complex | Simple |

---

## Current Status

✅ Code is ready - just need to add `BREVO_API_KEY`  
✅ Async email system configured  
✅ All templates working  
⏳ Waiting for API key to be added

---

## Fallback

If you can't get the API key right now, the system will fall back to SMTP automatically. But API is **highly recommended** for production!

---

## Questions?

Check Brevo documentation: https://developers.brevo.com/docs
