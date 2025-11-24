# ✅ Build Successful - Now Fix Runtime Error

## Good News
Your build completed successfully! The 500 error is now a **runtime issue**, not a build issue.

## Most Likely Cause
**Missing environment variables in Vercel**

## Fix Now (5 minutes)

### Step 1: Set Environment Variables in Vercel

1. Go to: https://vercel.com/dashboard
2. Select your project
3. Go to: **Settings** → **Environment Variables**
4. Add these variables for **Production**, **Preview**, and **Development**:

```bash
DJANGO_SECRET_KEY=<generate-below>
DATABASE_URL=postgresql://neondb_owner:npg_vHyir23nxsRB@ep-plain-mouse-a4bqp0g3-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require
CLOUDINARY_URL=cloudinary://214829223316295:TH5PRU0x-nBl0XvvRvxW0SFLTq0@dcnq4b1mo
EMAIL_HOST_USER=9b4e78001@smtp-brevo.com
EMAIL_HOST_PASSWORD=xsmtpsib-f8430f6957c5e0272f0399b903ed8b58ff5a6a4fda60f90bb89c9b674a77f287-oEdguD5gZaC10W04
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@veyu.cc
FRONTEND_URL=https://veyu.cc
```

### Step 2: Generate DJANGO_SECRET_KEY

Run this command locally:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and use it as your `DJANGO_SECRET_KEY` value.

### Step 3: Redeploy

After adding all environment variables:

**Option A - Vercel Dashboard:**
1. Go to Deployments tab
2. Click the three dots on latest deployment
3. Click "Redeploy"

**Option B - CLI:**
```bash
vercel --prod
```

**Option C - Git Push:**
```bash
git commit --allow-empty -m "Trigger redeploy"
git push
```

### Step 4: Test

After redeployment completes (1-2 minutes):

```bash
# Test basic health
curl https://your-app.vercel.app/health

# Test Django health (includes database check)
curl https://your-app.vercel.app/api/health/django
```

## How to Add Environment Variables in Vercel

### Via Dashboard (Recommended):

1. **Navigate**: Vercel Dashboard → Your Project → Settings → Environment Variables

2. **For each variable**:
   - Click "Add New"
   - Enter variable name (e.g., `DJANGO_SECRET_KEY`)
   - Enter value
   - Select environments: ✅ Production ✅ Preview ✅ Development
   - Click "Save"

3. **Repeat** for all variables listed above

### Via CLI (Alternative):

```bash
# Add a variable
vercel env add DJANGO_SECRET_KEY

# When prompted:
# - Enter the value
# - Select: Production, Preview, Development (use spacebar to select)
# - Press Enter

# Repeat for each variable
```

## Verify Environment Variables

After adding variables, verify they're set:

```bash
# List all environment variables
vercel env ls

# Should show:
# DJANGO_SECRET_KEY (Production, Preview, Development)
# DATABASE_URL (Production, Preview, Development)
# CLOUDINARY_URL (Production, Preview, Development)
# EMAIL_HOST_USER (Production, Preview, Development)
# EMAIL_HOST_PASSWORD (Production, Preview, Development)
# ... etc
```

## Check Logs After Redeploy

```bash
# View real-time logs
vercel logs --follow

# Or in dashboard:
# Vercel Dashboard → Deployments → Click deployment → Functions tab
```

Look for:
- ✅ "Django WSGI application initialized successfully"
- ✅ No "KeyError" or "environment variable not set" errors
- ✅ Database connection successful

## Expected Results

### Before Setting Variables:
```
❌ 500 Internal Server Error
❌ Logs show: "DJANGO_SECRET_KEY must be set"
❌ Logs show: "DATABASE_URL must be set"
```

### After Setting Variables:
```
✅ 200 OK responses
✅ /health returns: {"status": "healthy"}
✅ /api/health/django returns database connection info
✅ API endpoints work correctly
```

## Troubleshooting

### If still getting 500 after setting variables:

1. **Check you redeployed** - Variables only take effect after redeploy
2. **Check variable names** - Must match exactly (case-sensitive)
3. **Check all environments** - Set for Production, Preview, AND Development
4. **Check logs** - Look for specific error messages

### Common Mistakes:

- ❌ Forgot to redeploy after adding variables
- ❌ Only set variables for Production (need all 3 environments)
- ❌ Typo in variable name (e.g., `DJANGO_SECERT_KEY`)
- ❌ Missing `?sslmode=require` in DATABASE_URL
- ❌ Extra spaces or quotes in variable values

## Quick Checklist

- [ ] Generated new DJANGO_SECRET_KEY
- [ ] Added all 9+ environment variables in Vercel
- [ ] Set variables for Production, Preview, AND Development
- [ ] Verified DATABASE_URL includes `?sslmode=require`
- [ ] Redeployed after adding variables
- [ ] Waited for deployment to complete
- [ ] Tested /health endpoint
- [ ] Checked function logs for errors

## Next Steps

1. ✅ Build successful (DONE)
2. ⏳ Set environment variables (DO THIS NOW)
3. ⏳ Redeploy
4. ⏳ Test endpoints
5. ⏳ Monitor logs

---

**You're almost there! Just need to set those environment variables and redeploy.**
