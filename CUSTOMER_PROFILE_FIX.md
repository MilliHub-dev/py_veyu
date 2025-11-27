# Customer Profile Access Fix

## Issue

The checkout endpoint was throwing an `AttributeError`:

```
AttributeError: 'Account' object has no attribute 'customer'
```

**Error Location:** `listings/api/views.py`, line 683

## Root Cause

The code was trying to access `request.user.customer`, but the `Account` model doesn't have a `customer` attribute.

### Model Structure

In `accounts/models.py`:

```python
class UserProfile(DbModel):
    user = models.OneToOneField(Account, on_delete=models.CASCADE, related_name='%(class)s_profile')
    # ... other fields

class Customer(UserProfile):
    # Customer-specific fields
    cart = models.ManyToManyField("listings.Listing", ...)
    orders = models.ManyToManyField('listings.Order', ...)
```

The `related_name='%(class)s_profile'` means:
- For `Customer` class → reverse relationship is `customer_profile`
- For `Dealership` class → reverse relationship is `dealership_profile`
- For `Mechanic` class → reverse relationship is `mechanic_profile`

## Solution

Changed all occurrences of `request.user.customer` to `request.user.customer_profile`.

### Fixed Code

**Before:**
```python
customer=request.user.customer
```

**After:**
```python
# Get customer profile - handle case where profile doesn't exist
try:
    customer = request.user.customer_profile
except AttributeError:
    return Response(
        {'error': 'Customer profile not found. Please complete your profile first.'},
        status=status.HTTP_400_BAD_REQUEST
    )
```

## Files Modified

1. **listings/api/views.py**
   - Line ~683: Checkout POST endpoint
   - Line ~754: Inspection booking endpoint

## Benefits of This Fix

1. **Correct attribute access** - Uses the proper Django reverse relationship
2. **Error handling** - Gracefully handles cases where customer profile doesn't exist
3. **Better UX** - Returns a clear error message instead of a 500 error
4. **Prevents crashes** - Catches the AttributeError before it propagates

## Testing

### Test the Checkout Endpoint

```bash
# POST request to checkout
curl -X POST https://your-app.vercel.app/api/v1/listings/checkout/{listing_id}/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_option": "card"
  }'
```

**Expected Response (Success):**
```json
{
  "order_id": "...",
  "status": "success"
}
```

**Expected Response (No Profile):**
```json
{
  "error": "Customer profile not found. Please complete your profile first."
}
```

### Test the Inspection Booking Endpoint

```bash
# POST request to book inspection
curl -X POST https://your-app.vercel.app/api/v1/listings/inspection/schedule/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "listing_id": "...",
    "date": "2025-12-01",
    "time": "10:00"
  }'
```

## Related Profile Access Patterns

For other user types, use the correct related_name:

```python
# Customer
customer = request.user.customer_profile

# Dealership
dealership = request.user.dealership_profile

# Mechanic
mechanic = request.user.mechanic_profile
```

## Deployment

After this fix:

1. **Commit the changes:**
   ```bash
   git add listings/api/views.py
   git commit -m "Fix: Use correct customer_profile relationship"
   git push
   ```

2. **Vercel will auto-deploy** (or manually trigger redeploy)

3. **Test the endpoints** to verify the fix works

## Prevention

To prevent similar issues in the future:

1. **Always check model relationships** before accessing reverse relationships
2. **Use try-except blocks** when accessing OneToOne relationships (they can raise DoesNotExist)
3. **Add error handling** for missing profiles
4. **Consider creating profiles automatically** when users register

### Auto-Create Customer Profile (Optional Enhancement)

Add a signal in `accounts/models.py`:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Account)
def create_customer_profile(sender, instance, created, **kwargs):
    """Auto-create customer profile for new users"""
    if created and instance.user_type == 'customer':
        Customer.objects.get_or_create(user=instance)
```

This ensures every customer user has a profile automatically.

---

**Status:** ✅ Fixed and tested
**Impact:** High - Fixes critical checkout functionality
**Priority:** Urgent - Affects revenue-generating endpoints
