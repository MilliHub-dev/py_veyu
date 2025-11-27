# Deployment Guide: Customer Profile Fix

## Overview

This deployment fixes the `AttributeError: 'Account' object has no attribute 'customer'` error that was causing 500 errors on checkout and inspection booking endpoints.

## Changes Made

### 1. Fixed Profile Access in Views
**File:** `listings/api/views.py`

Changed `request.user.customer` to `request.user.customer_profile` with proper error handling.

### 2. Added Auto-Profile Creation Signal
**File:** `accounts/signals.py`

Added a signal that automatically creates Customer, Dealership, or Mechanic profiles when new accounts are created.

### 3. Created Migration Script
**File:** `scripts/create_missing_profiles.py`

Script to create profiles for existing users who don't have them yet.

## Deployment Steps

### Step 1: Commit and Push Changes

```bash
# Check what files changed
git status

# Add the changed files
git add listings/api/views.py
git add accounts/signals.py
git add scripts/create_missing_profiles.py
git add CUSTOMER_PROFILE_FIX.md
git add DEPLOY_CUSTOMER_FIX.md

# Commit with descriptive message
git commit -m "Fix: Correct customer profile access and add auto-creation signal

- Fix AttributeError in checkout and inspection endpoints
- Change request.user.customer to request.user.customer_profile
- Add signal to auto-create profiles for new users
- Add script to create profiles for existing users
- Add proper error handling for missing profiles"

# Push to repository
git push origin main
```

### Step 2: Vercel Will Auto-Deploy

Vercel will automatically deploy when you push to your repository. Monitor the deployment:

1. Go to: https://vercel.com/dashboard
2. Click on your project
3. Go to "Deployments" tab
4. Watch the latest deployment progress

### Step 3: Create Profiles for Existing Users

After deployment completes, run the migration script to create profiles for existing users:

**Option A: Via Django Shell (Recommended)**

```bash
# SSH into your production server or use Vercel CLI
python manage.py shell

# Then run:
from scripts.create_missing_profiles import create_missing_profiles
create_missing_profiles()
```

**Option B: Via Management Command**

```bash
python manage.py shell < scripts/create_missing_profiles.py
```

**Option C: Manually via Admin**

If you can't run scripts on Vercel, you can create profiles manually:

1. Go to Django Admin: https://your-app.vercel.app/admin/
2. For each user without a profile:
   - Go to Accounts → Customers (or Dealerships/Mechanics)
   - Click "Add Customer"
   - Select the user
   - Save

### Step 4: Test the Fix

#### Test Checkout Endpoint

```bash
# Replace with your actual values
export JWT_TOKEN="your_jwt_token"
export LISTING_ID="c87678f6-c930-11f0-a5b2-cdce16ffe435"
export API_URL="https://your-app.vercel.app"

# Test checkout
curl -X POST "$API_URL/api/v1/listings/checkout/$LISTING_ID/" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_option": "card"
  }'
```

**Expected Response (Success):**
```json
{
  "order_id": "...",
  "status": "success",
  "message": "Order created successfully"
}
```

**Expected Response (No Profile - Should Not Happen After Migration):**
```json
{
  "error": "Customer profile not found. Please complete your profile first."
}
```

#### Test Inspection Booking

```bash
curl -X POST "$API_URL/api/v1/listings/inspection/schedule/" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "listing_id": "'"$LISTING_ID"'",
    "date": "2025-12-01",
    "time": "10:00"
  }'
```

### Step 5: Monitor Logs

Check Vercel function logs for any errors:

```bash
# Via Vercel CLI
vercel logs --follow

# Or in Vercel Dashboard:
# Deployments → Click deployment → Functions tab
```

Look for:
- ✅ No AttributeError exceptions
- ✅ "Created Customer profile for user..." log messages (for new users)
- ✅ Successful order creation logs

## Rollback Plan

If something goes wrong, you can quickly rollback:

### Option 1: Vercel Dashboard Rollback

1. Go to Vercel Dashboard → Deployments
2. Find the previous working deployment
3. Click the three dots (⋯)
4. Click "Promote to Production"

### Option 2: Git Revert

```bash
# Revert the commit
git revert HEAD

# Push to trigger new deployment
git push origin main
```

## Verification Checklist

After deployment, verify:

- [ ] Deployment completed successfully in Vercel
- [ ] No build errors in deployment logs
- [ ] Migration script ran successfully
- [ ] All existing users have profiles
- [ ] Checkout endpoint works (returns 200 or proper error)
- [ ] Inspection booking works (returns 200 or proper error)
- [ ] No AttributeError in function logs
- [ ] New user registrations auto-create profiles

## Expected Impact

### Before Fix
- ❌ 500 Internal Server Error on checkout
- ❌ 500 Internal Server Error on inspection booking
- ❌ AttributeError in logs
- ❌ Lost revenue from failed checkouts

### After Fix
- ✅ Checkout works correctly
- ✅ Inspection booking works correctly
- ✅ Proper error messages for edge cases
- ✅ Auto-creation of profiles for new users
- ✅ No more AttributeError exceptions

## Monitoring

### Key Metrics to Watch

1. **Error Rate**
   - Should drop to near zero for checkout/inspection endpoints
   - Monitor in Vercel Analytics

2. **Successful Checkouts**
   - Should increase after fix
   - Monitor in your analytics dashboard

3. **Profile Creation**
   - Check that new users get profiles automatically
   - Monitor logs for "Created Customer profile" messages

### Alerts to Set Up

Consider setting up alerts for:
- 500 errors on checkout endpoint
- AttributeError exceptions
- Failed profile creation

## Support

If you encounter issues:

1. **Check Logs**
   ```bash
   vercel logs --follow
   ```

2. **Check Profile Creation**
   ```bash
   python manage.py shell
   >>> from accounts.models import Account, Customer
   >>> users_without_profiles = Account.objects.filter(user_type='customer').exclude(customer_profile__isnull=False)
   >>> print(f"Users without profiles: {users_without_profiles.count()}")
   ```

3. **Manually Create Profile**
   ```bash
   python manage.py shell
   >>> from accounts.models import Account, Customer
   >>> user = Account.objects.get(email='user@example.com')
   >>> Customer.objects.create(user=user)
   ```

## Documentation Updates

After successful deployment, update:

1. **API Documentation** - Note that users need profiles
2. **Onboarding Flow** - Ensure profile creation is part of signup
3. **Error Handling Guide** - Document the new error messages

## Success Criteria

✅ Deployment is successful when:

1. No AttributeError in logs for 24 hours
2. Checkout endpoint returns proper responses
3. All existing users have profiles
4. New users automatically get profiles
5. Error rate drops significantly

---

**Deployment Date:** _[Fill in after deployment]_  
**Deployed By:** _[Your name]_  
**Status:** _[Success/Rollback/In Progress]_  
**Notes:** _[Any additional notes]_
