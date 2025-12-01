# Checkout Payment Flow Fix

## Problem
After successful Paystack payment, the checkout endpoint was returning 402 (Payment Required) error when trying to create an order.

### Root Causes
1. **Missing Webhook Route**: The payment webhook URL (`/api/v1/hooks/payment-webhook/`) was returning 404 because utils URLs were commented out in `veyu/urls.py`
2. **Incorrect Payment Flow**: The checkout endpoint was checking if inspection was paid BEFORE accepting the payment reference, creating a chicken-and-egg problem
3. **No Payment Verification**: The checkout endpoint wasn't verifying Paystack payments or creating inspection records

## Solution

### 1. Fixed URL Routing (`veyu/urls.py`)
- Uncommented utils URLs to enable webhook endpoint
- Added proper namespace: `path('api/v1/', include('utils.urls', namespace='utils'))`
- This enables: `/api/v1/hooks/payment-webhook/` for Paystack webhooks

### 2. Updated Checkout Flow (`listings/api/views.py`)
Modified the `CheckoutView.post()` method to:

**Accept Payment Reference**:
```python
payment_reference = data.get('payment_reference')  # From Paystack
```

**Verify Payment with Paystack**:
- Calls Paystack API to verify transaction
- Validates payment status and amount
- Handles verification errors gracefully

**Create/Update Inspection Record**:
- Creates VehicleInspection with `payment_status='paid'`
- Updates existing inspection if found
- Links payment reference to inspection

**Create Transaction Record**:
- Records payment in Transaction model
- Prevents duplicate processing with `get_or_create()`
- Links transaction to inspection

**Then Create Order**:
- Only after payment is verified and inspection is created
- Order creation proceeds normally

### 3. Payment Flow Sequence

**Frontend**:
1. User initiates Paystack payment
2. Paystack payment succeeds
3. Frontend receives payment reference
4. Frontend calls checkout endpoint with `payment_reference`

**Backend**:
1. Receives payment reference
2. Verifies with Paystack API
3. Creates inspection payment record
4. Creates transaction record
5. Creates order
6. Returns success response

**Webhook (Async)**:
- Paystack sends webhook notification
- Backend processes webhook (idempotent)
- Updates records if needed
- Sends confirmation emails

## API Changes

### Checkout Endpoint
**POST** `/api/v1/listings/checkout/{listingId}/`

**Request Body**:
```json
{
  "payment_option": "pay-after-inspection",
  "payment_reference": "T166503098007364"
}
```

**Success Response** (200):
```json
{
  "error": false,
  "message": "Your order was created",
  "data": {
    "uuid": "...",
    "order_status": "pending",
    "paid": true,
    ...
  }
}
```

**Error Responses**:
- **402**: Payment verification failed
- **400**: Customer profile not found
- **500**: Payment verification error

## Testing

### Test Payment Flow
```bash
# 1. Initiate Paystack payment (frontend)
# 2. After success, create order with reference
curl -X POST "https://dev.veyu.cc/api/v1/listings/checkout/{listingId}/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_option": "pay-after-inspection",
    "payment_reference": "T166503098007364"
  }'
```

### Test Webhook
```bash
curl -X POST "https://dev.veyu.cc/api/v1/hooks/payment-webhook/" \
  -H "Content-Type: application/json" \
  -H "X-Paystack-Signature: {signature}" \
  -d '{
    "event": "charge.success",
    "data": {
      "reference": "T166503098007364",
      "amount": 5000000,
      "customer": {"email": "user@example.com"},
      "metadata": {
        "purpose": "inspection",
        "related_id": "123",
        "user_id": "456"
      }
    }
  }'
```

## Deployment Notes

1. **Environment Variables**: Ensure `PAYSTACK_SECRET_KEY` is set
2. **Webhook Configuration**: Update Paystack dashboard with webhook URL
3. **Database**: No migrations needed (uses existing models)
4. **Frontend**: Update to send `payment_reference` in checkout request

## Additional Improvements

### Webhook Fallback Handler
Added fallback in `utils/views.py` to handle payments without metadata:
- Creates generic transaction record
- Logs warning for tracking
- Prevents payment from being lost

### Smart Inspection Detection
Updated checkout to detect recent payments:
- Checks for transactions in last 5 minutes
- Automatically creates inspection record if payment found
- Handles race condition between webhook and checkout

### Enhanced Logging
Added detailed logging throughout:
- Payment verification steps
- Inspection lookup results
- Transaction creation
- Helps debug payment flow issues

## Files Modified
- `veyu/urls.py` - Enabled utils URLs for webhook
- `listings/api/views.py` - Added payment verification and smart inspection detection
- `utils/views.py` - Added fallback handler for payments without metadata
