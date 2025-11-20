# Business Location Integration Guide

## Overview

This guide explains how to integrate business location functionality in the frontend for dealer and mechanic profiles.

## Backend Location Model

The `Location` model includes:
- `country` - Country code (default: 'NG')
- `state` - State/province (required)
- `city` - City name (optional)
- `address` - Street address (required)
- `zip_code` - Postal code (optional)
- `lat` / `lng` - GPS coordinates (optional, recommended)
- `google_place_id` - Google Places ID (optional)

## Integration Methods

### 1. During Signup (Dealer/Mechanic)

Send location as a **JSON string** in the signup request:

```javascript
POST /api/v1/accounts/signup/

{
  "email": "dealer@example.com",
  "password": "SecurePass123!",
  "confirm_password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "user_type": "dealer",
  "business_name": "ABC Motors",
  "phone_number": "+2348012345678",
  "provider": "veyu",
  "location": "{\"country\":\"NG\",\"state\":\"Lagos\",\"city\":\"Lagos\",\"street_address\":\"123 Main St\",\"zip_code\":\"100001\",\"lat\":6.5244,\"lng\":3.3792,\"place_id\":\"ChIJ...\"}"
}
```

**Location Object Structure:**
```json
{
  "country": "NG",
  "state": "Lagos",
  "city": "Lagos",
  "street_address": "123 Main Street, Victoria Island",
  "zip_code": "100001",
  "lat": 6.5244,
  "lng": 3.3792,
  "place_id": "ChIJOwg_06VLOxARYcsicBLL3NI"
}
```

### 2. During Profile Update

Send location as a **Location ID** reference. You can update location via two endpoints:

#### Option A: General Profile Update
```javascript
// Step 1: Create location (if new)
POST /api/v1/locations/
Authorization: Bearer <token>

{
  "country": "NG",
  "state": "Lagos",
  "city": "Lagos",
  "address": "123 Main Street, Victoria Island",
  "zip_code": "100001",
  "lat": 6.5244,
  "lng": 3.3792,
  "google_place_id": "ChIJOwg_06VLOxARYcsicBLL3NI"
}

// Response: { "id": 1, ... }

// Step 2: Update profile with location ID
PUT /api/v1/accounts/profile/
Authorization: Bearer <token>

{
  "location": 1,
  "business_name": "ABC Motors",
  "contact_email": "info@abcmotors.com"
}
```

#### Option B: Dealership Settings Update (Dealers Only)
```javascript
// Step 1: Create location (if new)
POST /api/v1/locations/
Authorization: Bearer <token>

{
  "country": "NG",
  "state": "Lagos",
  "city": "Lagos",
  "address": "123 Main Street, Victoria Island",
  "zip_code": "100001",
  "lat": 6.5244,
  "lng": 3.3792,
  "google_place_id": "ChIJOwg_06VLOxARYcsicBLL3NI"
}

// Response: { "id": 1, ... }

// Step 2: Update dealership settings with location ID
PUT /api/v1/admin/dealership/settings/
Authorization: Bearer <token>

{
  "business_name": "ABC Motors",
  "about": "Leading car dealership...",
  "headline": "Your trusted car partner",
  "services": ["Car Sale", "Car Leasing", "Drivers"],
  "contact_phone": "+2348012345678",
  "contact_email": "info@abcmotors.com",
  "location": 1
}
```

## Google Places Autocomplete Integration

### HTML Setup

```html
<!-- Add Google Maps API -->
<script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&libraries=places"></script>

<input id="address-input" type="text" placeholder="Enter business address" />
```

### JavaScript Implementation

```javascript
// Initialize autocomplete
const input = document.getElementById('address-input');
const autocomplete = new google.maps.places.Autocomplete(input, {
  types: ['address'],
  componentRestrictions: { country: 'ng' }
});

// Listen for place selection
autocomplete.addListener('place_changed', () => {
  const place = autocomplete.getPlace();
  
  if (!place.geometry) {
    alert('Please select a valid address');
    return;
  }

  const location = extractLocationData(place);
  console.log(location);
});

// Extract location data
function extractLocationData(place) {
  const getComponent = (type) => {
    const component = place.address_components?.find(c => c.types.includes(type));
    return component?.long_name || '';
  };

  return {
    address: place.formatted_address,
    city: getComponent('locality') || getComponent('administrative_area_level_2'),
    state: getComponent('administrative_area_level_1'),
    zipCode: getComponent('postal_code'),
    lat: place.geometry.location.lat(),
    lng: place.geometry.location.lng(),
    placeId: place.place_id
  };
}
```

## React Component Example

```jsx
import { useEffect, useRef, useState } from 'react';

const LocationInput = ({ onLocationSelect }) => {
  const [location, setLocation] = useState(null);
  const autocompleteRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (window.google && inputRef.current) {
      autocompleteRef.current = new window.google.maps.places.Autocomplete(
        inputRef.current,
        {
          types: ['address'],
          componentRestrictions: { country: 'ng' }
        }
      );

      autocompleteRef.current.addListener('place_changed', handlePlaceSelect);
    }
  }, []);

  const handlePlaceSelect = () => {
    const place = autocompleteRef.current.getPlace();
    
    if (!place.geometry) return;

    const getComponent = (type) => {
      const component = place.address_components?.find(c => c.types.includes(type));
      return component?.long_name || '';
    };

    const locationData = {
      address: place.formatted_address,
      city: getComponent('locality'),
      state: getComponent('administrative_area_level_1'),
      zipCode: getComponent('postal_code'),
      lat: place.geometry.location.lat(),
      lng: place.geometry.location.lng(),
      placeId: place.place_id
    };

    setLocation(locationData);
    onLocationSelect(locationData);
  };

  return (
    <div>
      <input
        ref={inputRef}
        type="text"
        placeholder="Enter business address"
        className="form-control"
      />
      {location && (
        <div className="mt-2">
          <small>Selected: {location.address}</small>
        </div>
      )}
    </div>
  );
};

export default LocationInput;
```

## Complete Examples

### Signup with Location

```javascript
const signupWithLocation = async (formData, locationData) => {
  const payload = {
    email: formData.email,
    password: formData.password,
    confirm_password: formData.confirmPassword,
    first_name: formData.firstName,
    last_name: formData.lastName,
    user_type: 'dealer', // or 'mechanic'
    business_name: formData.businessName,
    phone_number: formData.phoneNumber,
    provider: 'veyu',
    
    // Location as JSON string
    location: JSON.stringify({
      country: 'NG',
      state: locationData.state,
      city: locationData.city,
      street_address: locationData.address,
      zip_code: locationData.zipCode,
      lat: locationData.lat,
      lng: locationData.lng,
      place_id: locationData.placeId
    })
  };

  const response = await fetch('https://dev.veyu.cc/api/v1/accounts/signup/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  return await response.json();
};
```

### Update Dealership Settings with Location

```javascript
const updateDealershipSettings = async (formData, locationId, authToken) => {
  const payload = {
    business_name: formData.businessName,
    about: formData.about,
    headline: formData.headline,
    services: formData.services, // Array: ["Car Sale", "Car Leasing", "Drivers"]
    contact_phone: formData.contactPhone,
    contact_email: formData.contactEmail,
    location: locationId // Location ID
  };

  const response = await fetch('https://dev.veyu.cc/api/v1/admin/dealership/settings/', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
    body: JSON.stringify(payload)
  });

  return await response.json();
};
```

## Field Requirements

| Field | Required | Notes |
|-------|----------|-------|
| `state` | ✅ Yes | Must be at least 2 characters |
| `address` | ✅ Yes | Must be at least 5 characters |
| `country` | No | Defaults to 'NG' |
| `city` | No | Recommended for better UX |
| `zip_code` | No | Optional postal code |
| `lat` / `lng` | No | Recommended for map features |
| `google_place_id` | No | Recommended for accuracy |

## Validation Rules

- **State**: 2+ characters, letters/spaces/hyphens only
- **Address**: 5+ characters minimum
- **Zip Code**: 3-10 digits (if provided)
- **Latitude**: -90 to 90 (if provided)
- **Longitude**: -180 to 180 (if provided)

## Display Location in UI

```javascript
// Fetch business profile
const response = await fetch('https://dev.veyu.cc/api/v1/dealers/{uuid}/', {
  headers: { 'Authorization': `Bearer ${token}` }
});

const business = await response.json();

// Display location
console.log(business.location); // "Lagos, Lagos State, Nigeria - John Doe"
```

## Best Practices

1. **Use Google Places Autocomplete** for accurate addresses and auto-populated coordinates
2. **Capture GPS coordinates** (`lat`/`lng`) for distance calculations and map features
3. **Validate required fields** (`state` and `address`) before submission
4. **Handle errors gracefully** with user-friendly messages
5. **Show location preview** after selection for user confirmation
6. **Store location ID** after creation for future updates

## Error Handling

```javascript
try {
  const response = await fetch('/api/v1/accounts/signup/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const error = await response.json();
    
    if (error.errors?.location) {
      alert('Location error: ' + error.errors.location.join(', '));
    }
  }
} catch (error) {
  console.error('Network error:', error);
}
```

## Common Issues

**Issue**: Location not saving during signup  
**Solution**: Ensure location is sent as a JSON string, not an object

**Issue**: Invalid state/address error  
**Solution**: Check minimum character requirements (state: 2+, address: 5+)

**Issue**: Coordinates not captured  
**Solution**: Ensure Google Places selection triggers before form submission

**Issue**: Location not appearing in profile  
**Solution**: Verify location was created successfully and ID is correct

## API Endpoints Reference

- `POST /api/v1/accounts/signup/` - Create account with location (JSON string)
- `POST /api/v1/locations/` - Create new location
- `GET /api/v1/locations/{id}/` - Get location details
- `PUT /api/v1/locations/{id}/` - Update location
- `PUT /api/v1/accounts/profile/` - Update profile with location ID
- `PUT /api/v1/admin/dealership/settings/` - Update dealership settings with location ID (dealers only)

## Support

For issues or questions, refer to the main API documentation at `api.md`.


## Dealership Settings Update with Location

For dealers, you can also update location through the dealership settings endpoint:

```javascript
const updateDealershipWithLocation = async (formData, locationData, authToken) => {
  // Step 1: Create new location if needed
  let locationId = formData.existingLocationId; // Use existing if available
  
  if (locationData) {
    const locationResponse = await fetch('https://dev.veyu.cc/api/v1/locations/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({
        country: 'NG',
        state: locationData.state,
        city: locationData.city,
        address: locationData.address,
        zip_code: locationData.zipCode,
        lat: locationData.lat,
        lng: locationData.lng,
        google_place_id: locationData.placeId
      })
    });

    const location = await locationResponse.json();
    locationId = location.id;
  }

  // Step 2: Update dealership settings with location
  const settingsResponse = await fetch('https://dev.veyu.cc/api/v1/admin/dealership/settings/', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
    body: JSON.stringify({
      business_name: formData.businessName,
      about: formData.about,
      headline: formData.headline,
      services: formData.services, // ["Car Sale", "Car Leasing", "Drivers"]
      contact_phone: formData.contactPhone,
      contact_email: formData.contactEmail,
      location: locationId // Location ID reference
    })
  });

  return await settingsResponse.json();
};
```

### React Component for Dealership Settings

```jsx
const DealershipSettingsPage = () => {
  const [settings, setSettings] = useState(null);
  const authToken = localStorage.getItem('access_token');

  const handleSettingsUpdate = async (formData, locationData) => {
    try {
      // Create location if new address provided
      let locationId = settings?.location?.id;
      
      if (locationData) {
        const locationResponse = await fetch('https://dev.veyu.cc/api/v1/locations/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          body: JSON.stringify({
            country: 'NG',
            state: locationData.state,
            city: locationData.city,
            address: locationData.address,
            zip_code: locationData.zipCode,
            lat: locationData.lat,
            lng: locationData.lng,
            google_place_id: locationData.placeId
          })
        });

        if (!locationResponse.ok) {
          throw new Error('Failed to create location');
        }

        const location = await locationResponse.json();
        locationId = location.id;
      }

      // Update dealership settings
      const response = await fetch('https://dev.veyu.cc/api/v1/admin/dealership/settings/', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          business_name: formData.businessName,
          about: formData.about,
          headline: formData.headline,
          services: formData.services,
          contact_phone: formData.contactPhone,
          contact_email: formData.contactEmail,
          location: locationId
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to update settings');
      }

      const result = await response.json();
      setSettings(result.data);
      alert('Settings updated successfully!');
    } catch (error) {
      console.error('Error updating settings:', error);
      alert('Failed to update settings: ' + error.message);
    }
  };

  return (
    <div>
      <h2>Dealership Settings</h2>
      <BusinessLocationForm onSubmit={handleSettingsUpdate} />
    </div>
  );
};
```

## Notes

- **Dealership Settings Endpoint**: The `/api/v1/admin/dealership/settings/` endpoint supports location updates via the `location` field (location ID)
- **Location Validation**: The endpoint validates that the location ID exists and belongs to the authenticated user
- **Error Handling**: Returns detailed error messages if location ID is invalid or not found
- **Optional Field**: Location is optional in the settings update - you can update other fields without changing location
