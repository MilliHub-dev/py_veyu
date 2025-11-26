# Checkout Endpoint - Quick Reference

## Endpoint
```
GET /api/v1/listings/checkout/{listingId}/
```

## What It Returns

```json
{
  "error": false,
  "listing_price": 5000000.00,
  "fees": {
    "tax": 375000.00,           // 7.5% VAT
    "inspection_fee": 100000.00, // 5% (min ₦10k, max ₦100k)
    "service_fee": 100000.00     // 2% platform fee
  },
  "total": 5575000.00,           // listing_price + all fees
  "listing": { /* full listing details */ }
}
```

## Fee Breakdown

| Fee Type | Formula | Default Rate | Example (₦5M listing) |
|----------|---------|--------------|----------------------|
| **Service Fee** | `price × 2%` | 2% + ₦0 | ₦100,000 |
| **Inspection Fee** | `price × 5%` (capped) | 5% (min ₦10k, max ₦100k) | ₦100,000 |
| **Tax (VAT)** | `price × 7.5%` | 7.5% | ₦375,000 |
| **Total** | `price + all fees` | - | ₦5,575,000 |

## Quick Test

```bash
# Replace {listingId} and {token} with actual values
curl -X GET "https://veyu.cc/api/v1/listings/checkout/{listingId}/" \
  -H "Authorization: Bearer {token}"
```

## Key Points

✅ All fees are calculated automatically using `PlatformFeeSettings`
✅ Fee rates can be changed by admins without code deployment
✅ Inspection fee is capped between ₦10,000 and ₦100,000
✅ All amounts are in Nigerian Naira (₦)
✅ Requires JWT authentication

## Related Files

- **View:** `listings/api/views.py` (CheckoutView)
- **Model:** `listings/models.py` (PlatformFeeSettings)
- **URL:** `listings/api/urls.py`
- **Full Docs:** `docs/CHECKOUT_API.md`
