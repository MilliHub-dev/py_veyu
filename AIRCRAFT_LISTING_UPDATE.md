# Aircraft Listing Update - Drivetrain & VIN Optional

## Summary
Updated the listing creation and editing endpoints to make `drivetrain` and `vin` fields optional for aircraft (planes) and other non-car vehicles.

## Changes Made

### 1. Model Imports (`listings/api/dealership_views.py`)
- Added imports for `Plane`, `Boat`, and `Bike` models alongside the existing `Car` model

### 2. Create Listing Endpoint
**Updated validation logic:**
- Added `vehicle_type` field (values: `car`, `plane`, `boat`, `bike`)
- Made `drivetrain`, `seats`, `doors`, and `vin` required **only for cars**
- Common required fields for all vehicles: `title`, `brand`, `model`, `condition`, `transmission`, `fuel_system`, `listing_type`, `price`

**Vehicle creation logic:**
- Now creates the appropriate vehicle type based on `vehicle_type` parameter
- **Car**: Requires `drivetrain`, `seats`, `doors`, `vin`
- **Plane**: Optional fields include `registration_number`, `aircraft_type`, `engine_type`, `max_altitude`, `wing_span`, `range`
- **Boat**: Optional fields include `hull_material`, `engine_count`, `propeller_type`, `length`, `beam_width`, `draft`
- **Bike**: Optional fields include `engine_capacity`, `bike_type`, `saddle_height`

### 3. Edit Listing Endpoint
**Updated to handle all vehicle types:**
- Uses `hasattr()` to check which vehicle type is being edited
- Only updates fields that exist for that specific vehicle type
- Prevents errors when trying to set car-specific fields on planes/boats/bikes

### 4. API Documentation (Swagger)
**Create Listing:**
- Updated operation description to clarify field requirements per vehicle type
- Added all vehicle-type specific fields to the schema
- Marked car-specific fields with "Required for cars only" description

**Edit Listing:**
- Added all vehicle-type specific fields to the vehicle schema
- Marked fields with appropriate descriptions indicating which vehicle type they apply to

## Backward Compatibility
- Default `vehicle_type` is set to `'car'` for backward compatibility
- Existing car listings will continue to work without changes
- All car-specific validations remain in place for car listings

## Usage Examples

### Creating an Aircraft Listing
```json
{
  "action": "create-listing",
  "vehicle_type": "plane",
  "title": "Cessna 172 Skyhawk",
  "brand": "Cessna",
  "model": "172 Skyhawk",
  "condition": "used-foreign",
  "transmission": "manual",
  "fuel_system": "petrol",
  "listing_type": "sale",
  "price": 150000000,
  "color": "White",
  "registration_number": "N12345",
  "aircraft_type": "propeller",
  "max_altitude": 14000,
  "wing_span": 11.0,
  "range": 1185
}
```

### Creating a Car Listing (Still Requires All Fields)
```json
{
  "action": "create-listing",
  "vehicle_type": "car",
  "title": "2020 Toyota Camry",
  "brand": "Toyota",
  "model": "Camry",
  "condition": "used-foreign",
  "transmission": "auto",
  "fuel_system": "petrol",
  "drivetrain": "FWD",
  "seats": 5,
  "doors": 4,
  "vin": "1HGBH41JXMN109186",
  "listing_type": "sale",
  "price": 5000000
}
```

## Testing Recommendations
1. Test creating aircraft listings without `drivetrain` and `vin`
2. Test creating car listings (should still require all fields)
3. Test editing aircraft listings
4. Test editing car listings
5. Verify backward compatibility with existing car listings
