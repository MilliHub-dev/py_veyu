# Vehicle Type Filter Feature

## Overview
Added vehicle type filtering capability to both sale and rental listing endpoints.

## Changes Made

### 1. Filter Classes (`listings/api/filters.py`)
Added `vehicle_type` filter to both `CarSaleFilter` and `CarRentalFilter` classes.

**New Filter Method:**
```python
def filter_vehicle_type(self, queryset, name, value):
    """Filter by vehicle type: car, boat, plane, bike, uav (comma-separated)"""
```

**Supported Vehicle Types:**
- `car` - Standard cars with drivetrain, seats, doors, VIN
- `boat` - Boats with hull material, engine count, propeller type, dimensions
- `plane` - Aircraft with registration number, aircraft type, engine type, altitude, wingspan, range
- `bike` - Motorcycles with engine capacity, bike type, saddle height
- `uav` / `drone` - Unmanned aerial vehicles with flight specs, camera, payload capacity

### 2. API Documentation (`listings/api/views.py`)
Updated Swagger documentation for three endpoints:
- `BuyListingView` - Sale listings
- `RentListingView` - Rental listings
- `ListingSearchView` - Search across all listings

## API Usage

### Single Vehicle Type
Filter for only cars:
```
GET /api/v1/listings/buy/?vehicle_type=car
GET /api/v1/listings/rent/?vehicle_type=boat
GET /api/v1/listings/buy/?vehicle_type=uav
```

### Multiple Vehicle Types
Filter for multiple types (comma-separated):
```
GET /api/v1/listings/buy/?vehicle_type=car,bike
GET /api/v1/listings/rent/?vehicle_type=plane,boat,uav
GET /api/v1/listings/buy/?vehicle_type=drone,plane
```

### Combined Filters
Combine with other filters:
```
GET /api/v1/listings/buy/?vehicle_type=car&brands=Toyota,Honda&transmission=auto&price=2000000-5000000
GET /api/v1/listings/rent/?vehicle_type=boat,plane&fuel_system=diesel&price=-1000000
```

### Search Endpoint
```
GET /api/v1/listings/search/?find=cessna&vehicle_type=plane
GET /api/v1/listings/search/?vehicle_type=car,bike&transmission=manual
```

## Implementation Details

### How It Works
1. Accepts comma-separated vehicle type values (case-insensitive)
2. Maps each type to its corresponding Django model (Car, Boat, Plane, Bike)
3. Retrieves all vehicle IDs for the specified types
4. Filters listings where `vehicle_id` matches any of the collected IDs
5. Returns distinct results

### Performance
- Uses `values_list('id', flat=True)` for efficient ID retrieval
- Applies `distinct()` to avoid duplicate results
- Leverages existing database indexes on vehicle relationships

## Backward Compatibility
- Filter is optional - existing API calls without `vehicle_type` continue to work
- Returns all vehicle types when filter is not specified
- Invalid vehicle types are silently ignored (returns empty if all types are invalid)

## Testing Examples

### Test 1: Filter for cars only
```bash
curl "http://localhost:8000/api/v1/listings/buy/?vehicle_type=car"
```

### Test 2: Filter for planes and boats
```bash
curl "http://localhost:8000/api/v1/listings/rent/?vehicle_type=plane,boat"
```

### Test 3: Combined filters
```bash
curl "http://localhost:8000/api/v1/listings/buy/?vehicle_type=car&brands=Toyota&price=2000000-5000000"
```

### Test 4: Search with vehicle type
```bash
curl "http://localhost:8000/api/v1/listings/search/?find=honda&vehicle_type=car,bike"
```

## Response Format
The API response includes the `kind` field in the vehicle object to identify the type:

```json
{
  "error": false,
  "data": {
    "results": [
      {
        "uuid": "...",
        "title": "Cessna 172 Skyhawk",
        "vehicle": {
          "kind": "plane",
          "brand": "Cessna",
          "model": "172",
          "registration_number": "N12345",
          "aircraft_type": "propeller"
        }
      }
    ]
  }
}
```

## Notes
- Vehicle type filtering works across all listing types (sale/rental)
- The filter is case-insensitive
- Multiple types can be specified for OR logic (car OR bike OR uav)
- 'drone' is an alias for 'uav' and can be used interchangeably
- Invalid type names are ignored without error
