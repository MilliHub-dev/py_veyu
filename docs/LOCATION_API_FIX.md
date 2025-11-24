# Location API Endpoint Fix

## Issue
The application was returning a 404 error when making POST requests to `/api/v1/locations/`:
```
INFO 2025-11-24 09:46:02,937 api.vercel_app Processing POST request to /api/v1/locations/
127.0.0.1 - - [24/Nov/2025 09:46:03] "POST /api/v1/locations/ HTTP/1.1" 404 -
```

## Root Cause
The `Location` model and `LocationSerializer` existed in the codebase, but there was no ViewSet or URL route registered to handle HTTP requests to the `/api/v1/locations/` endpoint.

## Solution
Implemented the missing API components:

### 1. Created LocationViewSet
**File:** `accounts/api/views.py`

Added a complete ViewSet with the following operations:
- `POST /api/v1/accounts/locations/` - Create new location
- `GET /api/v1/accounts/locations/` - List user's locations
- `GET /api/v1/accounts/locations/{id}/` - Retrieve specific location
- `PUT /api/v1/accounts/locations/{id}/` - Update location
- `PATCH /api/v1/accounts/locations/{id}/` - Partial update
- `DELETE /api/v1/accounts/locations/{id}/` - Delete location

Features:
- Automatic user association (locations are tied to authenticated user)
- Query filtering (users can only see their own locations)
- Full Swagger/OpenAPI documentation
- Authentication required (Token or JWT)

### 2. Registered URL Routes
**File:** `accounts/api/urls.py`

- Added Django REST Framework router
- Registered `LocationViewSet` with basename `'location'`
- Routes are now accessible under `/api/v1/accounts/locations/`

### 3. Updated Imports
- Added `viewsets` import from `rest_framework`
- Added `LocationSerializer` to view imports
- Added `LocationViewSet` to URL imports

## API Endpoints

### Create Location
```http
POST /api/v1/accounts/locations/
Authorization: Bearer <token>
Content-Type: application/json

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
```

**Response (201 Created):**
```json
{
  "id": 1,
  "user": 123,
  "country": "NG",
  "state": "Lagos",
  "city": "Lagos",
  "address": "123 Main Street, Victoria Island",
  "zip_code": "100001",
  "lat": 6.5244,
  "lng": 3.3792,
  "google_place_id": "ChIJOwg_06VLOxARYcsicBLL3NI",
  "full_address": "123 Main Street, Victoria Island, Lagos, Lagos, Nigeria",
  "has_coordinates": true,
  "coordinates": {
    "lat": 6.5244,
    "lng": 3.3792
  },
  "date_created": "2025-11-24T09:46:03.123456Z",
  "last_updated": "2025-11-24T09:46:03.123456Z"
}
```

### List Locations
```http
GET /api/v1/accounts/locations/
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user": 123,
    "country": "NG",
    "state": "Lagos",
    "city": "Lagos",
    "address": "123 Main Street, Victoria Island",
    "full_address": "123 Main Street, Victoria Island, Lagos, Lagos, Nigeria",
    "has_coordinates": true,
    "coordinates": {
      "lat": 6.5244,
      "lng": 3.3792
    }
  }
]
```

### Retrieve Location
```http
GET /api/v1/accounts/locations/{id}/
Authorization: Bearer <token>
```

### Update Location
```http
PUT /api/v1/accounts/locations/{id}/
Authorization: Bearer <token>
Content-Type: application/json

{
  "state": "Lagos",
  "address": "456 New Address",
  "city": "Ikeja"
}
```

### Partial Update
```http
PATCH /api/v1/accounts/locations/{id}/
Authorization: Bearer <token>
Content-Type: application/json

{
  "city": "Lekki"
}
```

### Delete Location
```http
DELETE /api/v1/accounts/locations/{id}/
Authorization: Bearer <token>
```

## Validation Rules

### Required Fields
- `state`: Minimum 2 characters
- `address`: Minimum 5 characters

### Optional Fields
- `country`: Defaults to 'NG'
- `city`: Optional
- `zip_code`: Optional
- `lat`: Must be between -90 and 90 (if provided)
- `lng`: Must be between -180 and 180 (if provided)
- `google_place_id`: Optional

## Integration with Business Profiles

The Location API integrates with the existing business profile workflow:

### During Signup
Location can be passed as a JSON string in the `location` field (existing behavior maintained).

### During Profile Update
1. Create location via `POST /api/v1/accounts/locations/`
2. Get the location ID from response
3. Update profile with location ID via `PUT /api/v1/accounts/profile/` or `PUT /api/v1/admin/dealership/settings/`

Example:
```javascript
// Step 1: Create location
const locationResponse = await fetch('/api/v1/accounts/locations/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    country: 'NG',
    state: 'Lagos',
    city: 'Lagos',
    address: '123 Main Street',
    lat: 6.5244,
    lng: 3.3792
  })
});

const location = await locationResponse.json();

// Step 2: Update profile with location ID
await fetch('/api/v1/accounts/profile/', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    location: location.id,
    business_name: 'My Business'
  })
});
```

## Testing

A test script is available at `test_location_endpoint.py`. To use it:

1. Start your development server
2. Get an authentication token (login)
3. Update the `auth_token` variable in the script
4. Run: `python test_location_endpoint.py`

## Files Modified

1. `accounts/api/views.py` - Added `LocationViewSet`
2. `accounts/api/urls.py` - Registered location routes
3. `docs/LOCATION_API_FIX.md` - This documentation
4. `test_location_endpoint.py` - Test script

## Deployment Notes

- No database migrations required (Location model already exists)
- No environment variables needed
- Compatible with existing Vercel deployment
- Backward compatible with existing signup flow

## Related Documentation

- See `docs/BUSINESS_LOCATION_INTEGRATION.md` for frontend integration guide
- See API documentation at `/api/docs/` for interactive Swagger UI
