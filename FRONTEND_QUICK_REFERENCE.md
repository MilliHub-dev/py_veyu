# Frontend Quick Reference: Vehicle Filters & UAV

## Quick Links
- **Detailed Filter Guide:** `FRONTEND_VEHICLE_FILTERS_GUIDE.md`
- **Detailed UAV Guide:** `FRONTEND_UAV_GUIDE.md`
- **Backend API Docs:** `VEHICLE_TYPE_FILTER_UPDATE.md`, `UAV_VEHICLE_TYPE_UPDATE.md`

## Vehicle Types

| Type | API Value | Alternative |
|------|-----------|-------------|
| Cars | `car` | - |
| Boats | `boat` | - |
| Planes | `plane` | - |
| Bikes | `bike` | - |
| Drones | `uav` | `drone` |

## API Endpoints Cheat Sheet

### Get Listings
```
GET /api/v1/listings/buy/          # Sale listings
GET /api/v1/listings/rent/         # Rental listings
GET /api/v1/listings/search/       # All listings
```

### Create Listing (Dealer)
```
POST /api/v1/dealership/listings/
Content-Type: application/json
Authorization: Bearer {token}
```

## Query Parameters

```
?vehicle_type=car,bike,uav         # Filter by types
?brands=Toyota,DJI,Honda           # Filter by brands
?transmission=auto,manual          # Filter transmission
?fuel_system=electric,hybrid       # Filter fuel
?price=1000000-5000000            # Price range
?find=mavic                        # Search term
?ordering=-created_at              # Sort (newest first)
```

## Quick Code Snippets

### Fetch UAVs Only
```javascript
const response = await fetch('/api/v1/listings/buy/?vehicle_type=uav');
const data = await response.json();
const uavs = data.data.results;
```

### Fetch Multiple Types
```javascript
const types = ['car', 'bike', 'uav'].join(',');
const response = await fetch(`/api/v1/listings/buy/?vehicle_type=${types}`);
```

### Create UAV Listing
```javascript
const uavData = {
  action: 'create-listing',
  vehicle_type: 'uav',
  title: 'DJI Mavic 3 Pro',
  brand: 'DJI',
  model: 'Mavic 3 Pro',
  condition: 'new',
  listing_type: 'sale',
  price: 2500000,
  color: 'Gray',
  uav_type: 'quadcopter',
  purpose: 'photography',
  max_flight_time: 43,
  max_range: 30,
  camera_resolution: '5.1K',
  has_obstacle_avoidance: true,
  has_gps: true,
  has_return_to_home: true
};

const response = await fetch('/api/v1/dealership/listings/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify(uavData)
});
```

## UAV Fields Reference

### Required Fields
- `title` - Listing title
- `brand` - Manufacturer (e.g., DJI, Autel)
- `model` - Model name
- `condition` - new | used-foreign | used-local
- `listing_type` - sale | rental
- `price` - Price in Naira

### Optional UAV Fields
- `registration_number` - Registration/serial number
- `uav_type` - quadcopter | hexacopter | octocopter | fixed-wing | hybrid
- `purpose` - recreational | photography | surveying | agriculture | delivery | inspection | racing | military
- `max_flight_time` - Minutes
- `max_range` - Kilometers
- `max_altitude` - Meters
- `max_speed` - km/h
- `camera_resolution` - e.g., "4K", "8K"
- `payload_capacity` - kg
- `weight` - kg
- `rotor_count` - Number of rotors
- `has_obstacle_avoidance` - Boolean
- `has_gps` - Boolean (default: true)
- `has_return_to_home` - Boolean (default: true)

## Response Structure

### Vehicle Object (UAV)
```json
{
  "kind": "uav",
  "brand": "DJI",
  "model": "Mavic 3",
  "uav_type": "quadcopter",
  "purpose": "photography",
  "max_flight_time": 46,
  "max_range": 30,
  "camera_resolution": "5.1K",
  "has_obstacle_avoidance": true,
  "has_gps": true,
  "has_return_to_home": true,
  "images": [...],
  "dealer": {...}
}
```

## Common Patterns

### Filter Hook (React)
```javascript
const useVehicleFilters = (initialFilters) => {
  const [filters, setFilters] = useState(initialFilters);
  const [listings, setListings] = useState([]);
  
  useEffect(() => {
    const params = new URLSearchParams();
    if (filters.vehicleTypes?.length) {
      params.append('vehicle_type', filters.vehicleTypes.join(','));
    }
    // ... add other filters
    
    fetch(`/api/v1/listings/buy/?${params}`)
      .then(res => res.json())
      .then(data => setListings(data.data.results));
  }, [filters]);
  
  return { listings, filters, setFilters };
};
```

### Type Guard (TypeScript)
```typescript
const isUAV = (vehicle: Vehicle): vehicle is UAVVehicle => {
  return vehicle.kind === 'uav';
};

// Usage
if (isUAV(listing.vehicle)) {
  console.log(listing.vehicle.max_flight_time); // TypeScript knows this exists
}
```

### Dynamic Specs Renderer
```javascript
const renderVehicleSpecs = (vehicle) => {
  const specMap = {
    car: ['doors', 'seats', 'transmission', 'fuel_system'],
    uav: ['max_flight_time', 'max_range', 'camera_resolution', 'weight'],
    plane: ['aircraft_type', 'max_altitude', 'wing_span', 'range'],
    boat: ['hull_material', 'engine_count', 'length'],
    bike: ['bike_type', 'engine_capacity']
  };
  
  const specs = specMap[vehicle.kind] || [];
  return specs.map(spec => vehicle[spec]).filter(Boolean);
};
```

## Popular UAV Brands
- **DJI** - Mavic, Phantom, Inspire, Matrice
- **Autel Robotics** - EVO series
- **Parrot** - Anafi
- **Skydio** - Autonomous drones
- **Yuneec** - Typhoon
- **Holy Stone** - Budget drones

## Icons Reference
```javascript
const vehicleIcons = {
  car: '🚗',
  boat: '⛵',
  plane: '✈️',
  bike: '🏍️',
  uav: '🚁'
};

const uavFeatureIcons = {
  obstacle_avoidance: '🛡️',
  gps: '📍',
  return_to_home: '🏠',
  camera: '📷',
  flight_time: '🕐',
  range: '📏',
  weight: '⚖️'
};
```

## Error Handling

### Common Errors
```javascript
try {
  const response = await fetch('/api/v1/listings/buy/?vehicle_type=uav');
  const data = await response.json();
  
  if (data.error) {
    // Handle API error
    console.error(data.message);
  }
} catch (error) {
  // Handle network error
  console.error('Network error:', error);
}
```

### Validation
```javascript
const validateUAV = (data) => {
  const errors = {};
  if (!data.title) errors.title = 'Required';
  if (!data.brand) errors.brand = 'Required';
  if (data.price <= 0) errors.price = 'Must be positive';
  return errors;
};
```

## Testing Checklist

- [ ] Filter by single vehicle type
- [ ] Filter by multiple vehicle types
- [ ] Combine vehicle type with other filters
- [ ] Create UAV listing
- [ ] Display UAV specs correctly
- [ ] Show UAV features (GPS, obstacle avoidance)
- [ ] Handle missing optional fields
- [ ] Test with 'drone' alias
- [ ] Validate form inputs
- [ ] Handle API errors gracefully

## Need Help?

1. **Filter Issues:** See `FRONTEND_VEHICLE_FILTERS_GUIDE.md`
2. **UAV Integration:** See `FRONTEND_UAV_GUIDE.md`
3. **API Details:** See `VEHICLE_TYPE_FILTER_UPDATE.md` and `UAV_VEHICLE_TYPE_UPDATE.md`
4. **Backend Setup:** See `MIGRATION_COMMANDS.md`
