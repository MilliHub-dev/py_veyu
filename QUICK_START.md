# 🚀 Quick Start - Fix Your 500 Error Now

## ✅ Your Build is Working!

Good news: Your build completed successfully. The 500 error is just missing environment variables.

## 🎯 Fix in 3 Steps (5 minutes)

### Step 1: Go to Vercel Dashboard

Open: **https://vercel.com/dashboard**

Navigate to: **Your Project → Settings → Environment Variables**

### Step 2: Add These Variables

Click "Add New" for each variable below.

For each one:
- ✅ Check **Production**
- ✅ Check **Preview** 
- ✅ Check **Development**

```
Variable: DJANGO_SECRET_KEY
Value: [Generate using command below]

Variable: DATABASE_URL
Value: postgresql://neondb_owner:npg_vHyir23nxsRB@ep-plain-mouse-a4bqp0g3-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require

Variable: CLOUDINARY_URL
Value: cloudinary://214829223316295:TH5PRU0x-nBl0XvvRvxW0SFLTq0@dcnq4b1mo

Variable: EMAIL_HOST_USER
Value: 9b4e78001@smtp-brevo.com

Variable: EMAIL_HOST_PASSWORD
Value: xsmtpsib-f8430f6957c5e0272f0399b903ed8b58ff5a6a4fda60f90bb89c9b674a77f287-oEdguD5gZaC10W04

Variable: EMAIL_HOST
Value: smtp-relay.brevo.com

Variable: EMAIL_PORT
Value: 587

Variable: EMAIL_USE_TLS
Value: True

Variable: DEFAULT_FROM_EMAIL
Value: noreply@veyu.cc

Variable: FRONTEND_URL
Value: https://veyu.cc
```

**Generate DJANGO_SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Step 3: Redeploy

After adding all variables, redeploy:

**In Vercel Dashboard:**
- Go to **Deployments** tab
- Click **⋮** (three dots) on latest deployment
- Click **Redeploy**

**Or via CLI:**
```bash
vercel --prod
```

**Or via Git:**
```bash
git commit --allow-empty -m "Trigger redeploy"
git push
```

## ✅ Test Your Fix

After deployment completes (1-2 minutes):

```bash
# Should return: {"status": "healthy"}
curl https://your-app.vercel.app/health

# Should show database connection
curl https://your-app.vercel.app/api/health/django
```

## 🎉 Success!

If you see `{"status": "healthy"}`, you're done! Your API is now working.

## ❌ Still Getting 500?

1. **Did you redeploy?** Variables only work after redeployment
2. **Check all environments?** Must select Production, Preview, AND Development
3. **Check logs:** `vercel logs --follow`
4. **Read:** `check_deployment.md` for detailed troubleshooting

## 📞 Need Help?

- Run: `bash verify_vercel_env.sh` to check what's missing
- Read: `check_deployment.md` for detailed instructions
- Check: Vercel function logs for specific errors

---

**You're one redeploy away from success! 🚀**
