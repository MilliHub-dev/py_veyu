# Listing Boost Feature Documentation

## Overview
The Listing Boost feature allows dealerships and mechanics to promote their listings by paying for featured placement. Admins configure pricing, and dealers choose the duration and pay to activate the boost.

## Features
- ✅ Admin-configurable pricing (daily, weekly, monthly)
- ✅ Flexible duration selection (e.g., 2 weeks, 3 months)
- ✅ Payment tracking with reference numbers
- ✅ Automatic activation/deactivation based on dates and payment status
- ✅ Featured listings endpoint filters for active boosts
- ✅ Dealer dashboard to view all boosts

---

## Database Models

### BoostPricing
Admin-configurable pricing for listing boosts.

**Fields:**
- `duration_type` - Choice: daily, weekly, monthly (unique)
- `price` - Decimal: Price per duration unit
- `is_active` - Boolean: Whether this pricing is available

**Example:**
```python
BoostPricing.objects.create(duration_type='weekly', price=5000.00, is_active=True)
```

### ListingBoost
Tracks individual listing boosts purchased by dealers.

**Fields:**
- `listing` - OneToOne: The listing being boosted
- `dealer` - ForeignKey: The dealership that purchased the boost
- `start_date` - Date: Boost start date
- `end_date` - Date: Boost end date
- `duration_type` - Choice: daily, weekly, monthly
- `duration_count` - Integer: Number of duration units (e.g., 2 weeks)
- `amount_paid` - Decimal: Total amount paid
- `payment_status` - Choice: pending, paid, failed, refunded
- `payment_reference` - String: Payment gateway reference
- `active` - Boolean: Auto-calculated (paid + within date range)

**Properties:**
- `is_active()` - Returns True if boost is paid and within date range
- `days_remaining` - Days left in the boost period
- `duration_days` - Total duration in days
- `formatted_amount` - Formatted price string

---

## API Endpoints

### 1. Get Boost Pricing (Public)
Get current pricing for listing boosts.

```http
GET /api/v1/admin/dealership/boost/pricing/
```

**Response:**
```json
{
  "error": false,
  "data": [
    {
      "id": 1,
      "duration_type": "daily",
      "duration_display": "Daily",
      "price": "1000.00",
      "formatted_price": "₦1,000.00",
      "is_active": true
    },
    {
      "id": 2,
      "duration_type": "weekly",
      "duration_display": "Weekly",
      "price": "5000.00",
      "formatted_price": "₦5,000.00",
      "is_active": true
    },
    {
      "id": 3,
      "duration_type": "monthly",
      "duration_display": "Monthly",
      "price": "15000.00",
      "formatted_price": "₦15,000.00",
      "is_active": true
    }
  ]
}
```

---

### 2. Get Boost Status for a Listing
Check if a listing has an active boost.

```http
GET /api/v1/admin/dealership/listings/<listing_uuid>/boost/
Authorization: Bearer <token>
```

**Response (with boost):**
```json
{
  "error": false,
  "data": {
    "id": 123,
    "listing": 456,
    "listing_title": "2020 Toyota Camry",
    "listing_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "dealer": 789,
    "dealer_name": "ABC Motors",
    "start_date": "2025-11-24",
    "end_date": "2025-12-08",
    "duration_type": "weekly",
    "duration_display": "Weekly",
    "duration_count": 2,
    "amount_paid": "10000.00",
    "formatted_amount": "₦10,000.00",
    "payment_status": "paid",
    "payment_status_display": "Paid",
    "payment_reference": "PAY-123456789",
    "active": true,
    "days_remaining": 14,
    "duration_days": 14,
    "date_created": "2025-11-24T10:00:00Z"
  }
}
```

**Response (no boost):**
```json
{
  "error": false,
  "message": "No boost found for this listing",
  "data": null
}
```

---

### 3. Create a Boost
Create a boost for a listing (initiates payment flow).

```http
POST /api/v1/admin/dealership/listings/<listing_uuid>/boost/
Authorization: Bearer <token>
Content-Type: application/json

{
  "duration_type": "weekly",
  "duration_count": 2
}
```

**Request Parameters:**
- `duration_type` (required) - Choice: daily, weekly, monthly
- `duration_count` (required) - Integer: 1-12 (number of duration units)

**Response:**
```json
{
  "error": false,
  "message": "Boost created successfully. Please proceed with payment.",
  "data": {
    "boost_id": 123,
    "boost_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "total_cost": "10000.00",
    "formatted_cost": "₦10,000.00",
    "duration_type": "weekly",
    "duration_count": 2,
    "start_date": "2025-11-24",
    "end_date": "2025-12-08",
    "payment_status": "pending",
    "listing": {
      "uuid": "...",
      "title": "2020 Toyota Camry",
      ...
    }
  }
}
```

**Validation Errors:**
```json
{
  "error": true,
  "message": "Validation failed",
  "errors": {
    "listing": ["This listing already has an active boost until 2025-12-15"],
    "duration_type": ["Boost pricing for daily is not available. Please contact support."]
  }
}
```

---

### 4. Confirm Boost Payment
Confirm payment after successful payment processing.

```http
POST /api/v1/admin/dealership/boost/confirm-payment/
Authorization: Bearer <token>
Content-Type: application/json

{
  "boost_id": 123,
  "payment_reference": "PAY-123456789"
}
```

**Request Parameters:**
- `boost_id` (required) - Integer: Boost ID from create response
- `payment_reference` (required) - String: Payment gateway reference

**Response:**
```json
{
  "error": false,
  "message": "Payment confirmed. Your listing is now boosted!",
  "data": {
    "id": 123,
    "listing_title": "2020 Toyota Camry",
    "active": true,
    "days_remaining": 14,
    "payment_status": "paid",
    ...
  }
}
```

---

### 5. Cancel/Delete a Boost
Cancel a pending boost or delete an inactive boost.

```http
DELETE /api/v1/admin/dealership/listings/<listing_uuid>/boost/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "error": false,
  "message": "Boost cancelled successfully"
}
```

**Error (active boost):**
```json
{
  "error": true,
  "message": "Cannot delete an active paid boost. Please contact support for refunds."
}
```

---

### 6. List All My Boosts
Get all boosts (active and inactive) for the authenticated dealer.

```http
GET /api/v1/admin/dealership/boost/my-boosts/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "error": false,
  "data": {
    "active_boosts": [
      {
        "id": 123,
        "listing_title": "2020 Toyota Camry",
        "active": true,
        "days_remaining": 14,
        ...
      }
    ],
    "inactive_boosts": [
      {
        "id": 122,
        "listing_title": "2019 Honda Accord",
        "active": false,
        "days_remaining": 0,
        ...
      }
    ],
    "total_active": 1,
    "total_inactive": 1
  }
}
```

---

## Payment Flow

### Step 1: Get Pricing
```javascript
// Get available pricing options
const response = await fetch('/api/v1/admin/dealership/boost/pricing/');
const { data: pricing } = await response.json();
// Display pricing to user
```

### Step 2: Create Boost
```javascript
// User selects duration and count
const boostData = {
  duration_type: 'weekly',
  duration_count: 2
};

const response = await fetch(`/api/v1/admin/dealership/listings/${listingId}/boost/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(boostData)
});

const { data } = await response.json();
// data.boost_id - Save this for confirmation
// data.total_cost - Amount to charge
```

### Step 3: Process Payment
```javascript
// Integrate with your payment gateway (Paystack, Flutterwave, etc.)
const paymentResponse = await processPayment({
  amount: data.total_cost,
  email: userEmail,
  reference: generateReference()
});

// Get payment reference from gateway
const paymentReference = paymentResponse.reference;
```

### Step 4: Confirm Payment
```javascript
// After successful payment
const confirmResponse = await fetch('/api/v1/admin/dealership/boost/confirm-payment/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    boost_id: data.boost_id,
    payment_reference: paymentReference
  })
});

const result = await confirmResponse.json();
// Boost is now active!
```

---

## Admin Configuration

### Setting Up Boost Pricing

1. **Login to Django Admin**
   - Navigate to `/admin/`
   - Login with admin credentials

2. **Configure Pricing**
   - Go to **Listings > Boost Pricing**
   - You should see 3 records (or create them):
     - Daily Boost
     - Weekly Boost
     - Monthly Boost
   
3. **Set Prices**
   - Click on each pricing record
   - Set the `price` field (e.g., 1000 for daily, 5000 for weekly, 15000 for monthly)
   - Ensure `is_active` is checked
   - Save

4. **Manage Boosts**
   - Go to **Listings > Listing Boosts**
   - View all boosts from all dealers
   - Filter by payment status, active status, duration type
   - Manually update payment status if needed

### Initial Data Setup

Run this in Django shell to create initial pricing:

```python
from listings.models import BoostPricing

# Create pricing if not exists
BoostPricing.objects.get_or_create(
    duration_type='daily',
    defaults={'price': 1000.00, 'is_active': True}
)

BoostPricing.objects.get_or_create(
    duration_type='weekly',
    defaults={'price': 5000.00, 'is_active': True}
)

BoostPricing.objects.get_or_create(
    duration_type='monthly',
    defaults={'price': 15000.00, 'is_active': True}
)
```

---

## Featured Listings Integration

The existing featured listings endpoint automatically filters for active boosts:

```http
GET /api/v1/listings/featured/
```

This endpoint filters for:
- `verified=True`
- `vehicle__available=True`
- `listing_boost__active=True` ← Boost filter
- `vehicle__dealer__verified_business=True`
- `vehicle__dealer__verified_id=True`

---

## Automatic Boost Deactivation

Boosts are automatically deactivated when:
1. The end date is reached
2. Payment status is not 'paid'

The `active` field is auto-calculated on save:
```python
def is_active(self):
    return (
        self.payment_status == 'paid' and
        self.start_date <= now().date() <= self.end_date
    )
```

### Cron Job (Optional)
For better performance, create a cron job to update boost statuses:

```python
# management/commands/update_boost_status.py
from django.core.management.base import BaseCommand
from listings.models import ListingBoost

class Command(BaseCommand):
    def handle(self, *args, **options):
        boosts = ListingBoost.objects.all()
        for boost in boosts:
            boost.save()  # Triggers active recalculation
        self.stdout.write(f'Updated {boosts.count()} boosts')
```

Run daily:
```bash
python manage.py update_boost_status
```

---

## Testing

### Test Boost Creation
```bash
curl -X POST http://localhost:8000/api/v1/admin/dealership/listings/<uuid>/boost/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "duration_type": "weekly",
    "duration_count": 2
  }'
```

### Test Payment Confirmation
```bash
curl -X POST http://localhost:8000/api/v1/admin/dealership/boost/confirm-payment/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "boost_id": 123,
    "payment_reference": "TEST-PAY-123"
  }'
```

---

## Security Considerations

1. **Authorization**: All endpoints require dealer authentication
2. **Ownership Validation**: Dealers can only boost their own listings
3. **Payment Verification**: Always verify payment with your payment gateway before confirming
4. **Duplicate Prevention**: One listing can only have one active boost at a time
5. **Refund Policy**: Active paid boosts cannot be deleted (contact support for refunds)

---

## Migration Applied

Migration file: `listings/migrations/0003_boostpricing_listingboost_dealer_and_more.py`

**Changes:**
- Created `BoostPricing` model
- Added fields to `ListingBoost`: dealer, duration_count, duration_type, payment_reference, payment_status
- Updated `active` and `amount_paid` fields with defaults
- Created database indexes for performance

---

## Date Implemented
November 24, 2025
