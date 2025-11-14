# Deploy to Vercel - Quick Guide

## Prerequisites

1. **Vercel CLI installed:**
   ```bash
   npm install -g vercel
   ```

2. **Environment variables ready** (get these from your services):
   - `DJANGO_SECRET_KEY` - Generate with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
   - `DATABASE_URL` - PostgreSQL connection string (Neon, Supabase, etc.)
   - `CLOUDINARY_URL` - From Cloudinary dashboard
   - `EMAIL_HOST_USER` & `EMAIL_HOST_PASSWORD` - SMTP credentials
   - `AFRICAS_TALKING_API_KEY` - SMS API key

## Deploy Steps

### 1. Login to Vercel
```bash
vercel login
```

### 2. Set Environment Variables
```bash
vercel env add DJANGO_SECRET_KEY
vercel env add DATABASE_URL
vercel env add CLOUDINARY_URL
vercel env add EMAIL_HOST_USER
vercel env add EMAIL_HOST_PASSWORD
vercel env add AFRICAS_TALKING_API_KEY
```

### 3. Deploy
```bash
vercel --prod
```

That's it! 🚀

## Files That Make It Work

- **`vercel.json`** - Vercel configuration (routes, builds, settings)
- **`build_files.sh`** - Build script (installs deps, collects static files)
- **`vercel_app.py`** - WSGI entry point for serverless
- **`veyu/vercel_settings.py`** - Django settings optimized for Vercel

## Troubleshooting

**Build fails?**
- Check environment variables are set
- Verify `requirements.txt` is complete
- Check build logs in Vercel dashboard

**App doesn't start?**
- Check function logs in Vercel dashboard
- Verify database connection string
- Ensure all required environment variables are set

**Static files not loading?**
- Check if `collectstatic` ran successfully in build logs
- Verify static file routes in `vercel.json`

## Quick Commands

```bash
# Deploy to preview
vercel

# Deploy to production
vercel --prod

# Check deployment status
vercel ls

# View logs
vercel logs
```