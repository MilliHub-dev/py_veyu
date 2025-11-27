# Checkout API Documentation

## Endpoint: Get Checkout Summary

Calculate service fees, taxes, inspection fees, and total price for a listing.

### Request

```
GET /api/v1/listings/checkout/{listingId}/
```

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Path Parameters:**
- `listingId` (UUID, required) - The UUID of the listing

### Response

**Success Response (200 OK):**

```json
{
  "error": false,
  "listing_price": 5000000.00,
  "fees": {
    "tax": 375000.00,
    "inspection_fee": 100000.00,
    "service_fee": 100000.00
  },
  "total": 5575000.00,
  "listing": {
    "uuid": "c87678f6-c930-11f0-a5b2-cdce16ffe435",
    "title": "2020 Toyota Camry",
    "price": 5000000.00,
    "vehicle": {
      "name": "Toyota Camry",
      "year": 2020,
      "make": "Toyota",
      "model": "Camry"
    },
    // ... other listing details
  },
  "inspection_status": {
    "paid": true,
    "inspection_id": 123,
    "status": "completed",
    "can_proceed": true
  }
}
```

**Note:** For sale listings, `inspection_status` indicates whether the customer has paid for a vehicle inspection. If `can_proceed` is `false`, the customer must pay for an inspection before creating an order.

### Fee Calculation Details

The endpoint uses `PlatformFeeSettings` to calculate fees:

#### 1. Service Fee
- **Formula:** `(listing_price × service_fee_percentage / 100) + service_fee_fixed`
- **Default:** 2% + ₦0
- **Example:** ₦5,000,000 × 2% = ₦100,000

#### 2. Inspection Fee
- **Formula:** `listing_price × inspection_fee_percentage / 100`
- **Constraints:**
  - Minimum: ₦10,000
  - Maximum: ₦100,000
- **Default:** 5%
- **Example:** ₦5,000,000 × 5% = ₦250,000 → capped at ₦100,000

#### 3. Tax (VAT)
- **Formula:** `listing_price × tax_percentage / 100`
- **Default:** 7.5%
- **Example:** ₦5,000,000 × 7.5% = ₦375,000

#### 4. Total
- **Formula:** `listing_price + service_fee + inspection_fee + tax`
- **Example:** ₦5,000,000 + ₦100,000 + ₦100,000 + ₦375,000 = ₦5,575,000

### Error Responses

**404 Not Found:**
```json
{
  "detail": "Not found."
}
```

**401 Unauthorized:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error"
}
```

### Example Usage

#### cURL
```bash
curl -X GET "https://veyu.cc/api/v1/listings/checkout/c87678f6-c930-11f0-a5b2-cdce16ffe435/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json"
```

#### JavaScript (Fetch)
```javascript
const response = await fetch(
  'https://veyu.cc/api/v1/listings/checkout/c87678f6-c930-11f0-a5b2-cdce16ffe435/',
  {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${jwtToken}`,
      'Content-Type': 'application/json'
    }
  }
);

const data = await response.json();
console.log('Total:', data.total);
console.log('Service Fee:', data.fees.service_fee);
```

#### Python (Requests)
```python
import requests

url = "https://veyu.cc/api/v1/listings/checkout/c87678f6-c930-11f0-a5b2-cdce16ffe435/"
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)
data = response.json()

print(f"Total: ₦{data['total']:,.2f}")
print(f"Service Fee: ₦{data['fees']['service_fee']:,.2f}")
```

### Platform Fee Settings

Fee settings are configurable via Django admin at `/admin/listings/platformfeesettings/`.

**Current Active Settings:**
- Service Fee: 2% + ₦0 fixed
- Inspection Fee: 5% (min: ₦10,000, max: ₦100,000)
- Tax: 7.5%

Only one `PlatformFeeSettings` record can be active at a time. The system automatically uses the active settings for all calculations.

## Endpoint: Create Order

Create an order for a listing. **For sale listings, inspection payment is REQUIRED before order creation.**

### Request

```
POST /api/v1/listings/checkout/{listingId}/
```

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Body:**
```json
{
  "payment_option": "pay-after-inspection"
}
```

**Payment Options:**
- `pay-after-inspection` - Payment after inspection (default)
- `wallet` - Pay from Veyu wallet
- `card` - Credit/Debit card payment
- `financial-aid` - Financing aid

### Response

**Success Response (200 OK):**

```json
{
  "error": false,
  "message": "Your order was created",
  "data": {
    "id": 456,
    "uuid": "abc-123-def",
    "order_type": "sale",
    "order_status": "pending",
    "paid": false,
    "payment_option": "pay-after-inspection",
    "customer": {...},
    "order_item": {...}
  }
}
```

**Error Response - Inspection Not Paid (402 Payment Required):**

```json
{
  "error": "Inspection payment required",
  "message": "You must pay for and complete a vehicle inspection before placing an order for this vehicle.",
  "required_action": "pay_inspection",
  "vehicle_id": 789,
  "listing_id": "c87678f6-c930-11f0-a5b2-cdce16ffe435"
}
```

**Error Response - No Customer Profile (400 Bad Request):**

```json
{
  "error": "Customer profile not found. Please complete your profile first."
}
```

### Inspection Payment Requirement

**For Sale Listings:**
- ✅ Customer MUST pay for vehicle inspection before creating order
- ✅ Inspection payment is verified via Paystack
- ✅ Dealer receives 60% of inspection fee
- ✅ Platform retains 40% of inspection fee
- ✅ Order creation blocked until inspection is paid

**Workflow:**
1. Customer views listing
2. Customer pays for inspection via Paystack
3. Inspection payment verified and revenue split
4. Dealer wallet credited with 60%
5. Customer can now create order ✅

**For Rental Listings:**
- Inspection payment is optional
- Order can be created without inspection

### Related Endpoints

- `GET /api/v1/listings/checkout/{listingId}/` - Get checkout summary
- `POST /api/v1/inspections/{id}/pay/` - Pay for inspection
- `POST /api/v1/inspections/{id}/verify-payment/` - Verify inspection payment
- `GET /api/v1/listings/buy/{uuid}/` - Get listing details
- `POST /api/v1/listings/checkout/inspection/` - Book inspection

### Notes

1. All monetary values are in Nigerian Naira (₦)
2. All calculations are rounded to 2 decimal places
3. The endpoint requires authentication
4. Fee settings can be updated by admins without code changes
5. If no active fee settings exist, default settings are automatically created
6. **Inspection payment is REQUIRED for sale listings before order creation**
7. Inspection payments use Paystack only (no wallet option)
8. Revenue split is automatic: 60% dealer, 40% platform
