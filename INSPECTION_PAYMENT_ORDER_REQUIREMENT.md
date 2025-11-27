# ✅ Inspection Payment Required Before Order Creation

## Summary

**For sale listings, customers MUST pay for vehicle inspection before they can create an order.**

This ensures:
- ✅ All vehicles are inspected before purchase
- ✅ Dealers receive their 60% inspection fee share
- ✅ Platform receives 40% inspection fee share
- ✅ Quality control and buyer protection

## What Changed

### Before
- Customers could create orders without inspection
- No inspection payment verification
- No revenue sharing

### After
- **Inspection payment REQUIRED** for sale listings
- Order creation blocked until inspection is paid
- Automatic revenue split (60% dealer / 40% platform)
- Dealer wallet credited immediately

## Implementation Details

### 1. Checkout Summary (GET)

**Endpoint:** `GET /api/v1/listings/checkout/{listingId}/`

**New Response Field:**
```json
{
  "inspection_status": {
    "paid": false,
    "inspection_id": null,
    "status": null,
    "can_proceed": false,
    "message": "Inspection payment required before checkout"
  }
}
```

**Status Indicators:**
- `paid: true` - Inspection has been paid ✅
- `can_proceed: true` - Customer can create order ✅
- `paid: false` - Inspection payment required ❌
- `can_proceed: false` - Order creation blocked ❌

### 2. Order Creation (POST)

**Endpoint:** `POST /api/v1/listings/checkout/{listingId}/`

**New Validation:**
```python
# For sale listings, check if inspection is paid
if listing.listing_type == 'sale':
    paid_inspection = VehicleInspection.objects.filter(
        vehicle=listing.vehicle,
        customer=customer,
        payment_status='paid'
    ).first()
    
    if not paid_inspection:
        return 402 Payment Required
```

**Error Response (402 Payment Required):**
```json
{
  "error": "Inspection payment required",
  "message": "You must pay for and complete a vehicle inspection before placing an order for this vehicle.",
  "required_action": "pay_inspection",
  "vehicle_id": 789,
  "listing_id": "c87678f6-c930-11f0-a5b2-cdce16ffe435"
}
```

## Workflow

### Complete Purchase Flow

```
1. Customer views listing
   ↓
2. Customer clicks "Buy Now"
   ↓
3. System checks: Has inspection been paid?
   ├─ YES → Proceed to checkout ✅
   └─ NO → Show "Pay for Inspection" button ❌
   ↓
4. Customer pays for inspection via Paystack
   ↓
5. Payment verified with Paystack API
   ↓
6. Revenue split: 60% dealer, 40% platform
   ↓
7. Dealer wallet credited immediately
   ↓
8. Inspection status: "paid" ✅
   ↓
9. Customer can now create order ✅
   ↓
10. Order created successfully
```

### API Call Sequence

```javascript
// 1. Get checkout summary
const summary = await fetch(`/api/v1/listings/checkout/${listingId}/`);
const data = await summary.json();

// 2. Check inspection status
if (!data.inspection_status.can_proceed) {
  // Show "Pay for Inspection" button
  showInspectionPaymentButton();
  return;
}

// 3. If inspection paid, allow order creation
const order = await fetch(`/api/v1/listings/checkout/${listingId}/`, {
  method: 'POST',
  body: JSON.stringify({ payment_option: 'pay-after-inspection' })
});
```

## Frontend Integration

### 1. Check Inspection Status

```javascript
async function checkInspectionStatus(listingId) {
  const response = await fetch(
    `/api/v1/listings/checkout/${listingId}/`,
    {
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  const data = await response.json();
  
  if (data.inspection_status && !data.inspection_status.can_proceed) {
    // Show inspection payment required message
    showInspectionPaymentRequired(data.inspection_status.message);
    return false;
  }
  
  return true;
}
```

### 2. Handle Order Creation

```javascript
async function createOrder(listingId, paymentOption) {
  // First check if inspection is paid
  const canProceed = await checkInspectionStatus(listingId);
  
  if (!canProceed) {
    alert('Please pay for vehicle inspection first');
    return;
  }
  
  // Create order
  const response = await fetch(
    `/api/v1/listings/checkout/${listingId}/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        payment_option: paymentOption
      })
    }
  );
  
  if (response.status === 402) {
    // Inspection payment required
    const error = await response.json();
    showInspectionPaymentModal(error);
    return;
  }
  
  const data = await response.json();
  // Order created successfully
  showOrderConfirmation(data);
}
```

### 3. Show Inspection Payment Modal

```javascript
function showInspectionPaymentModal(error) {
  const modal = `
    <div class="modal">
      <h2>Inspection Required</h2>
      <p>${error.message}</p>
      <button onclick="payForInspection('${error.vehicle_id}')">
        Pay for Inspection
      </button>
    </div>
  `;
  
  document.body.insertAdjacentHTML('beforeend', modal);
}

async function payForInspection(vehicleId) {
  // Create inspection
  const inspection = await createInspection(vehicleId);
  
  // Initiate Paystack payment
  const payment = await initiateInspectionPayment(inspection.id);
  
  // Show Paystack popup
  showPaystackPopup(payment.data);
}
```

## Error Handling

### HTTP Status Codes

- **200 OK** - Checkout summary retrieved successfully
- **402 Payment Required** - Inspection payment required before order
- **400 Bad Request** - Invalid request or missing customer profile
- **401 Unauthorized** - Authentication required
- **404 Not Found** - Listing not found

### Error Messages

**Inspection Not Paid:**
```json
{
  "error": "Inspection payment required",
  "message": "You must pay for and complete a vehicle inspection before placing an order for this vehicle.",
  "required_action": "pay_inspection",
  "vehicle_id": 789,
  "listing_id": "abc-123"
}
```

**No Customer Profile:**
```json
{
  "error": "Customer profile not found. Please complete your profile first."
}
```

## Testing

### Test Scenario 1: Order Without Inspection

```bash
# Try to create order without inspection payment
curl -X POST "http://localhost:8000/api/v1/listings/checkout/{listingId}/" \
  -H "Authorization: Token {token}" \
  -H "Content-Type: application/json" \
  -d '{"payment_option": "pay-after-inspection"}'

# Expected: 402 Payment Required
```

### Test Scenario 2: Order With Inspection

```bash
# 1. Pay for inspection
curl -X POST "http://localhost:8000/api/v1/inspections/{id}/pay/" \
  -H "Authorization: Token {token}"

# 2. Verify payment
curl -X POST "http://localhost:8000/api/v1/inspections/{id}/verify-payment/" \
  -H "Authorization: Token {token}" \
  -d '{"reference": "veyu-inspection-123-abc"}'

# 3. Create order (should succeed)
curl -X POST "http://localhost:8000/api/v1/listings/checkout/{listingId}/" \
  -H "Authorization: Token {token}" \
  -d '{"payment_option": "pay-after-inspection"}'

# Expected: 200 OK with order data
```

### Test Scenario 3: Check Inspection Status

```bash
# Get checkout summary
curl -X GET "http://localhost:8000/api/v1/listings/checkout/{listingId}/" \
  -H "Authorization: Token {token}"

# Check inspection_status field in response
# paid: true/false
# can_proceed: true/false
```

## Database Queries

### Check If Inspection Is Paid

```python
from inspections.models import VehicleInspection

paid_inspection = VehicleInspection.objects.filter(
    vehicle=vehicle,
    customer=customer,
    payment_status='paid',
    status__in=['draft', 'in_progress', 'completed', 'signed']
).first()

if paid_inspection:
    print("Inspection paid - can create order")
else:
    print("Inspection not paid - block order creation")
```

### Get Inspection Status for Listing

```python
from listings.models import Listing
from inspections.models import VehicleInspection

listing = Listing.objects.get(uuid=listing_id)

if listing.listing_type == 'sale':
    inspection = VehicleInspection.objects.filter(
        vehicle=listing.vehicle,
        customer=customer,
        payment_status='paid'
    ).first()
    
    if inspection:
        print(f"Inspection #{inspection.id} - Status: {inspection.status}")
    else:
        print("No paid inspection found")
```

## Business Rules

### Sale Listings
- ✅ Inspection payment REQUIRED
- ✅ Order creation blocked until paid
- ✅ Revenue split: 60% dealer / 40% platform
- ✅ Dealer wallet credited immediately

### Rental Listings
- ⚠️ Inspection payment OPTIONAL
- ✅ Order can be created without inspection
- ℹ️ Inspection recommended but not enforced

## Files Modified

1. **listings/api/views.py**
   - Updated `CheckoutView.get()` - Added inspection status
   - Updated `CheckoutView.post()` - Added inspection payment check

2. **docs/CHECKOUT_API.md**
   - Added inspection status documentation
   - Added order creation requirements
   - Added error response examples

## Related Documentation

- **Complete Guide:** `docs/INSPECTION_PAYMENT_REVENUE_SHARING.md`
- **Implementation:** `INSPECTION_PAYMENT_IMPLEMENTATION.md`
- **Quick Start:** `QUICK_START_INSPECTION_PAYMENT.md`
- **Checkout API:** `docs/CHECKOUT_API.md`

## Summary

✅ **Inspection payment is now REQUIRED before order creation for sale listings**
✅ **Checkout summary includes inspection status**
✅ **Order creation blocked with 402 error if inspection not paid**
✅ **Revenue split automatic: 60% dealer, 40% platform**
✅ **Dealer wallet credited immediately on payment**

The system now enforces inspection payment before allowing customers to purchase vehicles, ensuring quality control and proper revenue distribution.

---

**Implementation Date:** November 27, 2025
**Status:** ✅ COMPLETE
**Applies To:** Sale listings only
**Enforcement:** Server-side validation (cannot be bypassed)
