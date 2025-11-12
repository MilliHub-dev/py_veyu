# Render Email Setup - Final Steps

## ✅ What's Been Done

1. ✅ Brevo API integration created
2. ✅ Async email system implemented  
3. ✅ SMTP fallback added (if API key missing)
4. ✅ Code committed and pushed to GitHub
5. ✅ Render will auto-deploy the changes

## 🔧 What You Need to Do in Render Dashboard

### Step 1: Add Environment Variable

1. Go to https://dashboard.render.com
2. Select your **py_veyu** web service
3. Click on **Environment** in the left sidebar
4. Click **Add Environment Variable**
5. Add:
   - **Key**: `BREVO_API_KEY`
   - **Value**: `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`
6. Click **Save Changes**

Render will automatically restart your service.

### Step 2: Wait for Deployment

- Render will pull the latest code from GitHub
- It will rebuild and redeploy automatically
- This takes about 2-5 minutes

### Step 3: Test Signup

Try signing up with a new email. You should see in the logs:

**With API Key (Fast):**
```
✅ Email sent via Brevo API to [...], Message ID: <...>
📧 Email queued for async sending
✅ Async email sent successfully
```

**Without API Key (Fallback to SMTP):**
```
⚠️ BREVO_API_KEY not set, falling back to SMTP
Email send error: timed out
```

## 🎯 Expected Results

### With BREVO_API_KEY Set:
- ✅ Emails send in 2-3 seconds
- ✅ No timeouts
- ✅ Instant signup response
- ✅ Users receive emails immediately

### Without BREVO_API_KEY:
- ⚠️ Falls back to SMTP
- ⚠️ May timeout (current issue)
- ⚠️ Slow response times

## 📊 How to Verify

### Check Render Logs:
```bash
# In Render dashboard, go to Logs tab
# Look for these messages after signup:
✅ Email sent via Brevo API
📧 Email queued for async sending
```

### Check Your Email:
- Signup with a test email
- Email should arrive within 5 seconds

## 🐛 Troubleshooting

### If Still Timing Out:

1. **Verify API Key is Set:**
   - Go to Render Dashboard → Environment
   - Check `BREVO_API_KEY` exists
   - Value should start with `xkeysib-`

2. **Check Deployment Status:**
   - Go to Render Dashboard → Events
   - Latest deploy should be successful
   - Should show commit: "Add Brevo API fallback to SMTP"

3. **Check Logs:**
   - Look for `⚠️ BREVO_API_KEY not set` - means env var missing
   - Look for `✅ Email sent via Brevo API` - means it's working!

## 📝 Summary

**Current Status:**
- ✅ Code is ready and deployed
- ⏳ Waiting for `BREVO_API_KEY` to be added in Render dashboard
- ⏳ Waiting for Render to restart with new environment variable

**Next Step:**
Add the `BREVO_API_KEY` environment variable in Render dashboard and wait for auto-restart!

---

**Need Help?**
If you're still having issues after adding the API key, share the latest logs and I'll help debug!
