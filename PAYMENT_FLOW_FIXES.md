# Payment Flow Fixes - Final

## Issues Fixed

### Issue 1: Wrong Field Name in Transaction Query
**Error**: `Cannot resolve keyword 'created_at' into field`

**Fix**: Changed `created_at` to `date_created` in Transaction model query
```python
# Before
created_at__gte=timezone.now() - timedelta(minutes=5)

# After  
date_created__gte=timezone.now() - timedelta(minutes=5)
```

### Issue 2: Webhook Failing When Inspection Doesn't Exist
**Error**: `VehicleInspection matching query does not exist`

**Fix**: Added try-except to handle missing inspection gracefully
```python
try:
    inspection = VehicleInspection.objects.get(id=related_id)
    # Process inspection payment
except VehicleInspection.DoesNotExist:
    # Create generic transaction, checkout will handle inspection creation
    transaction = Transaction.objects.create(...)
```

## How Payment Flow Works Now

### Scenario 1: Frontend Sends Payment Reference (Recommended)
```
1. User pays via Paystack
2. Paystack webhook → Backend creates transaction
3. Frontend calls checkout with payment_reference
4. Backend verifies payment with Paystack
5. Backend creates inspection record
6. Backend creates order
✅ Success!
```

### Scenario 2: Frontend Doesn't Send Reference (Fallback)
```
1. User pays via Paystack
2. Paystack webhook → Backend creates transaction
3. Frontend calls checkout without reference
4. Backend looks for recent transactions (last 5 min)
5. Backend finds transaction and creates inspection
6. Backend creates order
✅ Success!
```

### Scenario 3: Webhook with Metadata but No Inspection
```
1. User pays via Paystack with metadata
2. Webhook receives payment with inspection_id
3. Inspection doesn't exist yet (not created)
4. Webhook creates generic transaction (no error)
5. Frontend calls checkout
6. Backend finds transaction and creates inspection
7. Backend creates order
✅ Success!
```

## Frontend Integration

### Minimum Required Change
```javascript
// In onSuccess callback after Paystack payment
const onSuccess = async (response) => {
  await api.post(`/listings/checkout/${listing.uuid}/`, {
    payment_option: 'pay-after-inspection',
    payment_reference: response.reference  // ← Add this
  });
};
```

### Optional: Add Metadata (Better tracking)
```javascript
const paystackConfig = {
  reference: `INSP-${Date.now()}`,
  email: user.email,
  amount: inspectionFee * 100,
  publicKey: PAYSTACK_PUBLIC_KEY,
  metadata: {
    purpose: 'inspection',
    user_id: user.id,
    vehicle_id: listing.vehicle.id,
    listing_id: listing.uuid
  }
};
```

## Testing Checklist

- [ ] Payment succeeds in Paystack
- [ ] Webhook receives payment (check logs)
- [ ] Checkout creates order (no 402 error)
- [ ] Inspection record is created
- [ ] Transaction record is created
- [ ] Order status is correct
- [ ] No 500 errors in logs

## Files Modified
- `listings/api/views.py` - Fixed field name `created_at` → `date_created`
- `utils/views.py` - Added graceful handling for missing inspection

## Next Steps
1. Deploy backend changes
2. Update frontend to send `payment_reference`
3. Test payment flow end-to-end
4. Monitor logs for any issues
