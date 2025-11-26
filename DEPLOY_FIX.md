# Deploying the Platform Fees Fix to Vercel

## What Was Fixed
The `listings_platformfeesettings` table was missing from the production database, causing 500 errors on the checkout endpoint.

## Changes Made

### 1. Database Migrations
- Fixed migration conflicts (renumbered to 0004 and 0005)
- Applied migrations to production database ✓
- Created default platform fee settings ✓

### 2. Build Process Update
- Updated `build.py` to run migrations during Vercel deployment
- This ensures future deployments automatically apply new migrations

## Deployment Steps

### Option 1: Automatic Deployment (Recommended)
If you have automatic deployments enabled on Vercel:

1. **Commit and push the changes:**
   ```bash
   git add .
   git commit -m "Fix: Add PlatformFeeSettings migration and update build process"
   git push origin main
   ```

2. **Vercel will automatically:**
   - Detect the push
   - Run the build process
   - Apply migrations
   - Deploy the updated code

3. **Monitor the deployment:**
   - Go to https://vercel.com/dashboard
   - Check the deployment logs
   - Look for "✅ Database migrations completed successfully"

### Option 2: Manual Deployment
If automatic deployments are disabled:

1. **Commit the changes:**
   ```bash
   git add .
   git commit -m "Fix: Add PlatformFeeSettings migration and update build process"
   ```

2. **Deploy via Vercel CLI:**
   ```bash
   vercel --prod
   ```

3. **Or trigger deployment from Vercel dashboard:**
   - Go to your project settings
   - Click "Deployments"
   - Click "Deploy" button

## Verification

After deployment, test the endpoint:

```bash
curl -X GET "https://veyu.cc/api/v1/listings/checkout/c87678f6-c930-11f0-a5b2-cdce16ffe435/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Expected: 200 OK response with checkout details (or 404 if listing doesn't exist)

## What's Already Done

✅ Migrations applied to production database
✅ Default platform fee settings created
✅ Build script updated to run migrations
✅ All local verifications passed

## Next Steps

1. Deploy the code changes to Vercel
2. Test the checkout endpoint
3. Monitor for any errors in Vercel logs

## Rollback Plan

If issues occur after deployment:

1. **Revert the deployment** in Vercel dashboard
2. **Or revert the commit:**
   ```bash
   git revert HEAD
   git push origin main
   ```

The database changes are backward compatible and won't cause issues.
