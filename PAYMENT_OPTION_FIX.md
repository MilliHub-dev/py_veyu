# Payment Option Field Fix

## Issue
The checkout endpoint was failing with a database constraint violation:
```
django.db.utils.IntegrityError: null value in column "payment_option" of relation "listings_order" violates not-null constraint
```

## Root Cause
The `Order` model's `payment_option` field had `default="Not Available"`, but "Not Available" was not in the valid `PAYMENT_OPTION` choices. When the client didn't send a `payment_option` value, Django tried to use the invalid default, resulting in a null value being inserted into the database.

## Solution
1. **Updated Model Default**: Changed the default value from `"Not Available"` to `'pay-after-inspection'` (a valid choice)
2. **Added View Validation**: Modified the checkout view to explicitly default to `'pay-after-inspection'` when no payment option is provided
3. **Created Migration**: Generated and applied migration `0006_fix_payment_option_default.py` to update the database schema

## Files Changed
- `listings/models.py` - Updated `payment_option` field default
- `listings/api/views.py` - Added explicit default handling in checkout view
- `listings/migrations/0006_fix_payment_option_default.py` - New migration

## Testing
After deploying, test the checkout endpoint:
```bash
POST /api/v1/listings/checkout/{listing_id}/
```

Both with and without the `payment_option` field in the request body to ensure it works correctly.
