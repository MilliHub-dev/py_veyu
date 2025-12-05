# UAV (Drone) Vehicle Type Addition

## Overview
Added UAV (Unmanned Aerial Vehicle/Drone) as a new vehicle type to the platform, supporting both sale and rental listings.

## Changes Made

### 1. Model (`listings/models.py`)
Created new `UAV` model extending `Vehicle` with drone-specific fields:

**UAV-Specific Fields:**
- `registration_number` - Registration/serial number
- `uav_type` - Type: quadcopter, hexacopter, octocopter, fixed-wing, hybrid
- `purpose` - Use case: recreational, photography, surveying, agriculture, delivery, inspection, racing, military
- `max_flight_time` - Maximum flight duration in minutes
- `max_range` - Maximum range in kilometers
- `max_altitude` - Maximum altitude in meters
- `max_speed` - Maximum speed in km/h
- `camera_resolution` - Camera quality (e.g., "4K", "8K")
- `payload_capacity` - Maximum payload weight in kg
- `weight` - Drone weight in kg
- `rotor_count` - Number of rotors
- `has_obstacle_avoidance` - Boolean for obstacle avoidance feature
- `has_gps` - Boolean for GPS capability (default: True)
- `has_return_to_home` - Boolean for return-to-home feature (default: True)

### 2. Admin (`listings/admin.py`)
- Added `UAVAdmin` class with custom fieldsets for drone management
- Registered UAV model in admin panel
- Display fields: name, brand, uav_type, purpose, max_flight_time, available

### 3. Serializers (`listings/api/serializers.py`)
- Added `UAVSerializer` for API responses
- Imported UAV model

### 4. Filters (`listings/api/filters.py`)
- Updated both `CarSaleFilter` and `CarRentalFilter` to support UAV filtering
- Added 'uav' and 'drone' (alias) to vehicle type map
- Updated filter labels and documentation

### 5. API Views (`listings/api/views.py`)
- Added `UAVSchema` for OpenAPI/Swagger documentation
- Updated `VehicleOneOf` schema to include UAV
- Updated all filter parameter descriptions to include 'uav'

### 6. Dealership Views (`listings/api/dealership_views.py`)
- Updated create-listing endpoint to support UAV creation
- Updated edit-listing endpoint to handle UAV-specific fields
- Added UAV fields to Swagger documentation
- Supports both 'uav' and 'drone' as vehicle_type values

## API Usage

### Create UAV Listing

```json
POST /api/v1/dealership/listings/
{
  "action": "create-listing",
  "vehicle_type": "uav",
  "title": "DJI Mavic 3 Pro",
  "brand": "DJI",
  "model": "Mavic 3 Pro",
  "condition": "new",
  "listing_type": "sale",
  "price": 2500000,
  "color": "Gray",
  
  "uav_type": "quadcopter",
  "purpose": "photography",
  "max_flight_time": 43,
  "max_range": 30,
  "max_altitude": 6000,
  "max_speed": 75,
  "camera_resolution": "5.1K",
  "payload_capacity": 0.9,
  "weight": 0.895,
  "rotor_count": 4,
  "has_obstacle_avoidance": true,
  "has_gps": true,
  "has_return_to_home": true,
  
  "features": ["4K Camera", "Obstacle Avoidance", "GPS", "Return to Home"],
  "notes": "Professional drone with Hasselblad camera"
}
```

### Filter UAV Listings

```bash
# Get only UAV listings
GET /api/v1/listings/buy/?vehicle_type=uav

# Get UAVs and planes
GET /api/v1/listings/buy/?vehicle_type=uav,plane

# Filter by brand and type
GET /api/v1/listings/buy/?vehicle_type=uav&brands=DJI,Autel&price=-3000000

# Using 'drone' alias
GET /api/v1/listings/rent/?vehicle_type=drone
```

### API Response

```json
{
  "error": false,
  "data": {
    "results": [
      {
        "uuid": "...",
        "title": "DJI Mavic 3 Pro",
        "price": 2500000,
        "vehicle": {
          "kind": "uav",
          "brand": "DJI",
          "model": "Mavic 3 Pro",
          "uav_type": "quadcopter",
          "purpose": "photography",
          "max_flight_time": 43,
          "max_range": 30,
          "camera_resolution": "5.1K",
          "has_obstacle_avoidance": true,
          "has_gps": true,
          "has_return_to_home": true
        }
      }
    ]
  }
}
```

## UAV Types

### UAV Type Choices
- `quadcopter` - 4 rotor drone (most common)
- `hexacopter` - 6 rotor drone (more stable)
- `octocopter` - 8 rotor drone (heavy lift)
- `fixed-wing` - Airplane-style drone (long range)
- `hybrid` - VTOL (Vertical Take-Off and Landing)

### Purpose Choices
- `recreational` - Hobby/fun flying
- `photography` - Photo/video capture
- `surveying` - Land surveying and mapping
- `agriculture` - Crop monitoring and spraying
- `delivery` - Package delivery
- `inspection` - Infrastructure inspection
- `racing` - FPV racing drones
- `military` - Defense applications

## Database Migration

After deploying these changes, run:

```bash
python manage.py makemigrations
python manage.py migrate
```

This will create the `listings_uav` table with all UAV-specific fields.

## Admin Panel

UAVs can be managed in the admin panel at:
- `/admin/listings/uav/`

The admin interface includes organized fieldsets:
1. Basic Information
2. UAV Specifications
3. Performance
4. Camera & Features
5. Additional

## Backward Compatibility

- All existing vehicle types (car, boat, plane, bike) continue to work
- The 'drone' keyword is an alias for 'uav' in filters
- UAV fields are optional during creation (except those required by business logic)
- Existing API calls are not affected

## Testing Checklist

- [ ] Create UAV listing via API
- [ ] Upload images for UAV listing
- [ ] Edit UAV listing
- [ ] Filter listings by vehicle_type=uav
- [ ] Filter listings by vehicle_type=drone (alias)
- [ ] Combine UAV filter with other filters (brand, price)
- [ ] View UAV listing details
- [ ] Verify UAV appears in admin panel
- [ ] Test UAV rental listings
- [ ] Verify 'kind' field returns 'uav' in API responses

## Popular UAV Brands

For reference, common UAV brands to add:
- DJI (Mavic, Phantom, Inspire, Matrice)
- Autel Robotics (EVO series)
- Parrot (Anafi)
- Skydio (autonomous drones)
- Yuneec (Typhoon)
- Holy Stone (budget drones)
- Hubsan (entry-level)
- Freefly Systems (professional cinema)
