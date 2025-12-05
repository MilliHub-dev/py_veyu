# Deployment Note - Aircraft Listing Fix

## Issue
Frontend was receiving 400 error: "Missing required fields: drivetrain, vin" when creating aircraft listings.

## Root Cause
Backend was requiring car-specific fields (`drivetrain`, `vin`, `seats`, `doors`) for all vehicle types.

## Solution Implemented
Made all vehicle-type specific fields optional in the backend API:
- `drivetrain` - optional
- `vin` - optional  
- `seats` - optional (defaults to 5 for cars)
- `doors` - optional (defaults to 4 for cars)
- `transmission` - optional
- `fuel_system` - optional

## Minimal Required Fields
Only these fields are now required for ANY vehicle listing:
- `title`
- `brand`
- `model`
- `condition`
- `listing_type`
- `price`

## Deployment Steps
1. **Backend**: Restart the Django application to load the updated `listings/api/dealership_views.py`
2. **Frontend**: No changes needed - existing code will work
3. **Testing**: Try creating an aircraft listing without `drivetrain` and `vin` fields

## Files Modified
- `listings/api/dealership_views.py` - Updated validation and vehicle creation logic
- `AIRCRAFT_LISTING_UPDATE.md` - Detailed documentation of changes

## Backward Compatibility
✅ Existing requests with all fields will continue to work
✅ New requests without optional fields will now work
✅ Default values provided for `seats` (5) and `doors` (4) when not specified

## Test Cases
1. Create aircraft listing with minimal fields (should succeed)
2. Create car listing with all fields (should succeed)
3. Create car listing with minimal fields (should succeed)
4. Create boat/bike listing (should succeed)
