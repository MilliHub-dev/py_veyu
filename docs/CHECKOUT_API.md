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
- `POST /api/v1/listings/checkout/inspection/` - Book inspection (see below)

### Notes

1. All monetary values are in Nigerian Naira (₦)
2. All calculations are rounded to 2 decimal places
3. The endpoint requires authentication
4. Fee settings can be updated by admins without code changes
5. If no active fee settings exist, default settings are automatically created
6. **Inspection payment is REQUIRED for sale listings before order creation**
7. Inspection payments use Paystack only (no wallet option)
8. Revenue split is automatic: 60% dealer, 40% platform


## Endpoint: Book Inspection

Schedule a vehicle inspection for a listing.

### Request

```
POST /api/v1/listings/checkout/inspection/
```

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Body:**
```json
{
  "listing_id": "c87678f6-c930-11f0-a5b2-cdce16ffe435",
  "date": "2024-12-15",
  "time": "10:00"
}
```

**Alternative Field Names (Accepted):**
- `date` OR `inspection_date` OR `scheduled_date`
- `time` OR `inspection_time` OR `scheduled_time`

**Parameters:**
- `listing_id` (UUID, required) - The UUID of the listing
- `date` (string, required) - Inspection date in YYYY-MM-DD format
- `time` (string, required) - Inspection time in HH:MM format (24-hour)

### Response

**Success Response (200 OK):**

```json
{
  "success": true,
  "message": "Inspection Scheduled",
  "slip_reference": "INSP-123456",
  "inspection_slip": {
    "id": 123456,
    "slip_reference": "INSP-123456",
    "inspection_date": "2024-12-15",
    "inspection_time": "10:00",
    "status": "scheduled",
    "order_id": 789,
    "customer": {
      "id": 101,
      "name": "John Doe",
      "email": "john@example.com"
    },
    "vehicle": {
      "id": 456,
      "name": "Toyota Camry 2020",
      "make": "Toyota",
      "model": "Camry",
      "year": 2020
    },
    "listing": {
      "id": 789,
      "uuid": "c87678f6-c930-11f0-a5b2-cdce16ffe435",
      "title": "2020 Toyota Camry - Excellent Condition"
    },
    "dealer": {
      "id": 202,
      "name": "AutoHub Motors",
      "location": "123 Main Street, Lagos",
      "contact_person": "Jane Smith",
      "contact_phone": "+234 801 234 5678"
    },
    "created_at": "2024-12-02T10:30:00Z"
  }
}
```

**Error Response - Missing Required Field (400 Bad Request):**

```json
{
  "error": "listing_id is required"
}
```

```json
{
  "error": "date, inspection_date, or scheduled_date is required",
  "received_fields": ["listing_id", "time"]
}
```

**Error Response - No Order Found (404 Not Found):**

```json
{
  "error": "No order found for this listing. Please create an order first."
}
```

**Error Response - Server Error (500 Internal Server Error):**

```json
{
  "error": true,
  "message": "Error message details"
}
```

### Workflow

1. Customer creates an order for a listing
2. Customer books an inspection using this endpoint
3. Order status changes to `awaiting-inspection`
4. Customer receives email notification with inspection details
5. Inspection slip reference (`INSP-XXXXXX`) is generated and returned
6. Customer can use the slip reference to track the inspection

### Email Notification

When an inspection is successfully scheduled, the customer receives an email with:
- Inspection reference number (e.g., `INSP-123456`)
- Scheduled date and time
- Vehicle details
- Dealership location and contact information
- Inspection checklist
- What to bring to the inspection

### Example Usage

#### cURL
```bash
curl -X POST "https://veyu.cc/api/v1/listings/checkout/inspection/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "listing_id": "c87678f6-c930-11f0-a5b2-cdce16ffe435",
    "date": "2024-12-15",
    "time": "10:00"
  }'
```

#### JavaScript (Fetch)
```javascript
const response = await fetch(
  'https://veyu.cc/api/v1/listings/checkout/inspection/',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${jwtToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      listing_id: 'c87678f6-c930-11f0-a5b2-cdce16ffe435',
      date: '2024-12-15',
      time: '10:00'
    })
  }
);

const data = await response.json();
console.log('Inspection Reference:', data.slip_reference);
console.log('Inspection Details:', data.inspection_slip);
```

#### Python (Requests)
```python
import requests

url = "https://veyu.cc/api/v1/listings/checkout/inspection/"
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}
payload = {
    "listing_id": "c87678f6-c930-11f0-a5b2-cdce16ffe435",
    "date": "2024-12-15",
    "time": "10:00"
}

response = requests.post(url, headers=headers, json=payload)
data = response.json()

print(f"Inspection Reference: {data['slip_reference']}")
print(f"Scheduled for: {data['inspection_slip']['inspection_date']} at {data['inspection_slip']['inspection_time']}")
```

### Notes

1. An order must exist before booking an inspection
2. The inspection reference format is `INSP-{inspection_id}`
3. The endpoint accepts multiple field name variations for flexibility
4. Email notifications are sent automatically upon successful booking
5. The order status is automatically updated to `awaiting-inspection`
6. All timestamps are in ISO 8601 format (UTC)
