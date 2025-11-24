# Boost Listing - Quick Start Guide

## For Admins

### 1. Initialize Pricing (One-time setup)
```bash
python manage.py init_boost_pricing
```

This creates default pricing:
- Daily: ₦1,000
- Weekly: ₦5,000
- Monthly: ₦15,000

### 2. Modify Pricing (Optional)
1. Go to Django Admin: `/admin/`
2. Navigate to **Listings > Boost Pricing**
3. Click on a pricing record
4. Change the `price` field
5. Save

---

## For Dealers (API Integration)

### Step 1: Get Available Pricing
```javascript
GET /api/v1/admin/dealership/boost/pricing/

Response:
{
  "error": false,
  "data": [
    {
      "duration_type": "weekly",
      "price": "5000.00",
      "formatted_price": "₦5,000.00"
    }
  ]
}
```

### Step 2: Create Boost
```javascript
POST /api/v1/admin/dealership/listings/{listing_uuid}/boost/
Authorization: Bearer {token}
Content-Type: application/json

{
  "duration_type": "weekly",
  "duration_count": 2
}

Response:
{
  "error": false,
  "message": "Boost created successfully. Please proceed with payment.",
  "data": {
    "boost_id": 123,
    "total_cost": "10000.00",
    "start_date": "2025-11-24",
    "end_date": "2025-12-08"
  }
}
```

### Step 3: Process Payment
Use your payment gateway (Paystack, Flutterwave, etc.) to charge the `total_cost`.

### Step 4: Confirm Payment
```javascript
POST /api/v1/admin/dealership/boost/confirm-payment/
Authorization: Bearer {token}
Content-Type: application/json

{
  "boost_id": 123,
  "payment_reference": "PAY-123456789"
}

Response:
{
  "error": false,
  "message": "Payment confirmed. Your listing is now boosted!",
  "data": {
    "active": true,
    "days_remaining": 14
  }
}
```

### Step 5: Check Boost Status
```javascript
GET /api/v1/admin/dealership/listings/{listing_uuid}/boost/
Authorization: Bearer {token}

Response:
{
  "error": false,
  "data": {
    "active": true,
    "days_remaining": 14,
    "end_date": "2025-12-08"
  }
}
```

---

## Common Use Cases

### Cancel a Pending Boost
```javascript
DELETE /api/v1/admin/dealership/listings/{listing_uuid}/boost/
Authorization: Bearer {token}
```

### View All My Boosts
```javascript
GET /api/v1/admin/dealership/boost/my-boosts/
Authorization: Bearer {token}
```

### Check if Listing is Boosted
```javascript
GET /api/v1/admin/dealership/listings/{listing_uuid}/boost/
Authorization: Bearer {token}

// If no boost:
{
  "error": false,
  "message": "No boost found for this listing",
  "data": null
}
```

---

## Pricing Examples

| Duration | Count | Total Cost |
|----------|-------|------------|
| Daily | 7 days | ₦7,000 |
| Weekly | 2 weeks | ₦10,000 |
| Weekly | 4 weeks | ₦20,000 |
| Monthly | 1 month | ₦15,000 |
| Monthly | 3 months | ₦45,000 |

---

## Error Handling

### Listing Already Boosted
```json
{
  "error": true,
  "message": "Validation failed",
  "errors": {
    "listing": ["This listing already has an active boost until 2025-12-15"]
  }
}
```

### Invalid Duration Type
```json
{
  "error": true,
  "message": "Validation failed",
  "errors": {
    "duration_type": ["Boost pricing for daily is not available. Please contact support."]
  }
}
```

### Cannot Delete Active Boost
```json
{
  "error": true,
  "message": "Cannot delete an active paid boost. Please contact support for refunds."
}
```

---

## Frontend Integration Example

```javascript
class BoostService {
  constructor(apiUrl, token) {
    this.apiUrl = apiUrl;
    this.token = token;
  }

  async getPricing() {
    const response = await fetch(`${this.apiUrl}/boost/pricing/`);
    return response.json();
  }

  async createBoost(listingId, durationType, durationCount) {
    const response = await fetch(
      `${this.apiUrl}/listings/${listingId}/boost/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          duration_type: durationType,
          duration_count: durationCount
        })
      }
    );
    return response.json();
  }

  async confirmPayment(boostId, paymentReference) {
    const response = await fetch(
      `${this.apiUrl}/boost/confirm-payment/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          boost_id: boostId,
          payment_reference: paymentReference
        })
      }
    );
    return response.json();
  }

  async getMyBoosts() {
    const response = await fetch(
      `${this.apiUrl}/boost/my-boosts/`,
      {
        headers: {
          'Authorization': `Bearer ${this.token}`
        }
      }
    );
    return response.json();
  }
}

// Usage
const boostService = new BoostService('http://localhost:8000/api/v1/admin/dealership', token);

// Get pricing
const pricing = await boostService.getPricing();

// Create boost
const boost = await boostService.createBoost(listingId, 'weekly', 2);

// Process payment with your gateway
const payment = await processPayment(boost.data.total_cost);

// Confirm payment
const confirmation = await boostService.confirmPayment(
  boost.data.boost_id,
  payment.reference
);
```

---

## Testing Checklist

- [ ] Initialize pricing with management command
- [ ] Verify pricing appears in admin panel
- [ ] Create a test listing
- [ ] Get boost pricing via API
- [ ] Create a boost for the listing
- [ ] Verify boost is in "pending" status
- [ ] Confirm payment with test reference
- [ ] Verify boost is now "active"
- [ ] Check listing appears in featured endpoint
- [ ] View boost in "my-boosts" endpoint
- [ ] Wait for boost to expire (or manually change dates)
- [ ] Verify boost becomes inactive

---

## Support

For issues or questions:
1. Check the full documentation: `docs/BOOST_LISTING_FEATURE.md`
2. Review implementation summary: `docs/BOOST_IMPLEMENTATION_SUMMARY.md`
3. Check Django admin for boost status
4. Review server logs for errors

---

## Quick Commands

```bash
# Initialize pricing
python manage.py init_boost_pricing

# Create migration (if needed)
python manage.py makemigrations listings

# Apply migration
python manage.py migrate listings

# Run development server
python manage.py runserver

# Access admin
http://localhost:8000/admin/
```
