# Frontend API Updates

## 1. Currency Support for Listings

We have added support for multi-currency listings (Naira and Dollar).

### Endpoints Affected
- **Create Listing**: `POST /api/v1/admin/dealership/listings/create/`
- **Edit Listing**: `POST /api/v1/admin/dealership/listings/<listing_id>/` (action: `edit-listing`)
- **Listing Detail**: `GET /api/v1/admin/dealership/listings/<listing_id>/`

### Payload Changes
Add the `currency` field to your request payload.

**Create Listing Example:**
```json
{
  "action": "create-listing",
  "vehicle_type": "car",
  "title": "2020 Toyota Camry",
  "price": 15000,
  "currency": "USD",  // New Field. Options: "NGN", "USD". Default: "NGN"
  "listing_type": "sale",
  "brand": "Toyota",
  "model": "Camry",
  "condition": "used-foreign",
  ...
}
```

**Edit Listing Example:**
```json
{
  "action": "edit-listing",
  "title": "2020 Toyota Camry",
  "price": 15000,
  "currency": "USD",
  ...
}
```

### Response Changes
The listing object in the response will now include the `currency` field (e.g., "NGN" or "USD").

---

## 2. Vehicle Category (Body Type) for Cars

We have added a `body_type` field specifically for Cars to categorize them (e.g., SUV, Sedan).

### Endpoints Affected
- **Create Listing**: `POST /api/v1/admin/dealership/listings/create/` (when `vehicle_type` is "car")
- **Edit Listing**: `POST /api/v1/admin/dealership/listings/<listing_id>/` (action: `edit-listing`)

### Payload Changes
Add the `body_type` field to your request payload.

**Create Listing (Car) Example:**
```json
{
  "action": "create-listing",
  "vehicle_type": "car",
  "title": "Lexus LX 570",
  "body_type": "suv", // New Field
  ...
}
```

**Edit Listing (Car) Example:**
```json
{
  "action": "edit-listing",
  ...
  "vehicle": {
      "brand": "Lexus",
      "model": "LX 570",
      "body_type": "suv", // New Field
      ...
  }
}
```

### Available Body Types
The `body_type` field accepts the following values (lowercase):
- `suv`
- `sedan`
- `hatchback`
- `coupe`
- `convertible`
- `pickup`
- `van` (Van/Minivan)
- `wagon`
- `luxury`
- `sport` (Sports Car)

### Response Changes
The vehicle object in the response will now include a `body_type` field.
**Note**: The API response for `body_type` will be the human-readable label (e.g., "SUV" instead of "suv") for display purposes.
