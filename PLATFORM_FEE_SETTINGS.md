# Platform Fee Settings Implementation

## Overview
Implemented a configurable fee system that allows administrators to set and manage platform fees, inspection fees, and taxes through the Django admin panel.

## Features

### 1. PlatformFeeSettings Model
Located in `listings/models.py`, this model stores all fee configurations:

**Service Fee (Platform Fee):**
- `service_fee_percentage`: Percentage-based fee (default: 2%)
- `service_fee_fixed`: Fixed amount added to percentage (default: ₦0)

**Inspection Fee:**
- `inspection_fee_percentage`: Percentage of listing price (default: 5%)
- `inspection_fee_minimum`: Minimum fee amount (default: ₦10,000)
- `inspection_fee_maximum`: Maximum fee cap (default: ₦100,000, 0 for no limit)

**Tax:**
- `tax_percentage`: Tax rate (default: 7.5% VAT)

**Status:**
- `is_active`: Only one settings instance can be active at a time
- `effective_date`: When the settings take effect

### 2. Admin Interface
Accessible at `/admin/listings/platformfeesettings/`

**Features:**
- Easy-to-use form with organized fieldsets
- List view showing all fee percentages and status
- Only one active settings instance allowed at a time
- Cannot delete active settings (prevents accidental removal)
- Automatic deactivation of previous settings when activating new ones

### 3. Checkout API Enhancement
**Endpoint:** `GET /api/v1/listings/checkout/{listingId}/`

**Response includes:**
```json
{
  "error": false,
  "listing_price": 5000000,
  "fees": {
    "tax": 375000,
    "inspection_fee": 250000,
    "service_fee": 100000
  },
  "total": 5725000,
  "listing": { ... }
}
```

**Calculations:**
- Tax = listing_price × (tax_percentage / 100)
- Inspection Fee = max(listing_price × (inspection_fee_percentage / 100), inspection_fee_minimum)
  - Capped at inspection_fee_maximum if set
- Service Fee = (listing_price × (service_fee_percentage / 100)) + service_fee_fixed
- **Total = listing_price + tax + inspection_fee + service_fee**

### 4. Helper Methods

**PlatformFeeSettings.get_active_settings()**
- Returns the currently active fee settings
- Creates default settings if none exist

**calculate_service_fee(amount)**
- Calculates service fee for a given amount

**calculate_inspection_fee(listing_price)**
- Calculates inspection fee with min/max constraints

**calculate_tax(amount)**
- Calculates tax for a given amount

## Usage

### For Administrators:
1. Navigate to Django Admin → Listings → Platform Fee Settings
2. Click "Add Platform Fee Settings" to create new configuration
3. Set desired percentages and amounts
4. Mark as "Active" to apply immediately
5. Previous active settings will be automatically deactivated

### For Developers:
```python
from listings.models import PlatformFeeSettings

# Get active settings
settings = PlatformFeeSettings.get_active_settings()

# Calculate fees
service_fee = settings.calculate_service_fee(listing_price)
inspection_fee = settings.calculate_inspection_fee(listing_price)
tax = settings.calculate_tax(listing_price)
```

## Migration
Run the migration to create the database table:
```bash
python manage.py migrate listings
```

## Default Values
- Service Fee: 2% + ₦0 fixed
- Inspection Fee: 5% (min: ₦10,000, max: ₦100,000)
- Tax: 7.5%

## Benefits
1. **Flexibility**: Change fees without code deployment
2. **Transparency**: Clear fee breakdown for customers
3. **History**: Keep track of fee changes over time
4. **Control**: Prevent accidental deletion of active settings
5. **Automation**: Total price calculated automatically

## Files Modified
- `listings/models.py` - Added PlatformFeeSettings model
- `listings/admin.py` - Added admin interface
- `listings/api/views.py` - Updated CheckoutView to use settings
- `listings/migrations/0003_platformfeesettings.py` - Database migration
- `api.md` - Updated API documentation
