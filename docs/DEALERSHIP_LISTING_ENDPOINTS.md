# Dealership Listing Management Endpoints

## Base URL
All dealership endpoints are prefixed with: `/api/v1/admin/dealership/`

## Authentication
All endpoints require authentication:
- JWT Token (Bearer token)
- Session Authentication
- Token Authentication

Permission: `IsAuthenticated` + `IsDealerOrStaff`

---

## 📋 Listing Endpoints Summary

### 1. **List All Listings**
- **Endpoint**: `GET /api/v1/admin/dealership/listings/`
- **Description**: Get all listings for the authenticated dealer
- **Response**: Array of listing objects

### 2. **Create Listing**
- **Endpoint**: `POST /api/v1/admin/dealership/listings/create/`
- **Content Types**: `application/json`, `multipart/form-data`, `application/x-www-form-urlencoded`
- **Actions**:
  - `create-listing` - Create a new listing
  - `upload-images` - Upload images to an existing listing
  - `publish-listing` - Publish a listing

### 3. **Get Listing Detail**
- **Endpoint**: `GET /api/v1/admin/dealership/listings/<listing_id>/`
- **Description**: Retrieve a single listing by UUID

### 4. **Edit Listing**
- **Endpoint**: `POST /api/v1/admin/dealership/listings/<listing_id>/`
- **Content Types**: `application/json`, `multipart/form-data`, `application/x-www-form-urlencoded`
- **Actions**:
  - `edit-listing` - Update listing and vehicle details
  - `upload-images` - Add more images
  - `remove-image` - Delete an image by UUID
  - `publish-listing` - Publish the listing

### 5. **Delete Listing**
- **Endpoint**: `DELETE /api/v1/admin/dealership/listings/<listing_id>/`
- **Description**: Permanently delete a listing

### 6. **Quick Actions (Publish/Unpublish/Delete)**
- **Endpoint**: `POST /api/v1/admin/dealership/listings/`
- **Actions**:
  - `publish` - Mark listing as verified (published)
  - `unpublish` - Mark listing as not verified (unpublished)
  - `delete` - Delete the listing
- **Required Fields**: `action`, `listing` (UUID)

---

## 🚀 Detailed Endpoint Documentation

### Create Listing
```http
POST /api/v1/admin/dealership/listings/create/
Content-Type: application/json

{
  "action": "create-listing",
  "title": "2020 Toyota Camry XLE",
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
  "price": 5000000,
  "currency": "NGN",
  "color": "Black",
  "mileage": 25000,
  "body_type": "sedan",
  "notes": "Well maintained with full service history",
  "features": ["AC", "Bluetooth"]
}
```

**Required Fields**:
- `title`, `brand`, `model`, `condition`, `transmission`, `fuel_system`
- `drivetrain`, `seats`, `doors`, `vin`, `listing_type`, `price`
- For rentals: `payment_cycle` (daily/weekly/monthly)

### Upload Images
```http
POST /api/v1/admin/dealership/listings/create/
Content-Type: multipart/form-data

action=upload-images
listing=<listing-uuid>
image=<file1>
image=<file2>
```

**Note**: Images are automatically uploaded to Cloudinary in the `vehicles/images/` folder.

### Edit Listing
```http
POST /api/v1/admin/dealership/listings/<listing_id>/
Content-Type: application/json

{
  "action": "edit-listing",
  "title": "Updated Title",
  "price": 4500000,
  "notes": "Updated notes",
  "listing_type": "sale",
  "vehicle": {
    "brand": "Toyota",
    "model": "Camry",
    "condition": "used-foreign",
    "transmission": "auto",
    "fuel_system": "petrol",
    "color": "Black",
    "mileage": 26000,
    "drivetrain": "FWD",
    "seats": 5,
    "doors": 4,
    "vin": "1HGBH41JXMN109186",
    "features": ["AC", "Bluetooth", "Sunroof"]
  }
}
```

### Remove Image
```http
POST /api/v1/admin/dealership/listings/<listing_id>/
Content-Type: application/json

{
  "action": "remove-image",
  "image_id": "<image-uuid>"
}
```

### Publish/Unpublish/Delete (Quick Actions)
```http
POST /api/v1/admin/dealership/listings/
Content-Type: application/json

{
  "action": "publish",  // or "unpublish" or "delete"
  "listing": "<listing-uuid>"
}
```

### Delete Listing (Alternative)
```http
DELETE /api/v1/admin/dealership/listings/<listing_id>/
```

---

## ✅ Boost Functionality

### Status: **FULLY IMPLEMENTED**

The Listing Boost feature is now fully functional with admin-configurable pricing.

### Features
- ✅ Admin sets pricing for daily, weekly, and monthly boosts
- ✅ Dealers can create boosts with flexible duration
- ✅ Payment tracking with reference numbers
- ✅ Automatic activation/deactivation
- ✅ View all boosts (active and inactive)
- ✅ Cancel pending boosts

### Boost Endpoints

1. **Get Boost Pricing (Public)**
   ```
   GET /api/v1/admin/dealership/boost/pricing/
   ```

2. **Get Boost Status**
   ```
   GET /api/v1/admin/dealership/listings/<listing_uuid>/boost/
   ```

3. **Create Boost**
   ```
   POST /api/v1/admin/dealership/listings/<listing_uuid>/boost/
   Body: { "duration_type": "weekly", "duration_count": 2 }
   ```

4. **Confirm Payment**
   ```
   POST /api/v1/admin/dealership/boost/confirm-payment/
   Body: { "boost_id": 123, "payment_reference": "PAY-123" }
   ```

5. **Cancel Boost**
   ```
   DELETE /api/v1/admin/dealership/listings/<listing_uuid>/boost/
   ```

6. **List All My Boosts**
   ```
   GET /api/v1/admin/dealership/boost/my-boosts/
   ```

### Featured Listings
Boosted listings appear in the featured listings endpoint:
```http
GET /api/v1/listings/featured/
```

This filters for listings with `listing_boost__active=True`.

### Documentation
See [BOOST_LISTING_FEATURE.md](./BOOST_LISTING_FEATURE.md) for complete documentation including:
- Payment flow
- Admin configuration
- API examples
- Testing guide

---

## ✅ Functionality Status

| Feature | Status | Notes |
|---------|--------|-------|
| Create Listing | ✅ Fully Functional | Supports JSON, form-data, form-urlencoded |
| Edit Listing | ✅ Fully Functional | Multiple actions supported |
| Delete Listing | ✅ Fully Functional | Two methods available |
| Upload Images | ✅ Fully Functional | Cloudinary integration |
| Remove Images | ✅ Fully Functional | Delete by UUID |
| Publish/Unpublish | ✅ Fully Functional | Quick actions available |
| Boost Listing | ✅ Fully Functional | Admin pricing, payment flow, auto-activation |

---

## 🔧 Recent Fixes

### Form URL Encoded Support (Nov 24, 2025)
Added `FormParser` to the following views to support `application/x-www-form-urlencoded` content type:
- `CreateListingView`
- `ListingDetailView`
- `SettingsView`

This fixes the "Unsupported media type" error when clients send form-urlencoded data.

---

## 📝 Notes

1. **Image Storage**: All vehicle images use Cloudinary (`CloudinaryField`)
2. **Vercel Compatible**: No local file storage used
3. **Multiple Actions**: Both create and edit endpoints support multiple actions via the `action` parameter
4. **Validation**: Required fields are validated before creating listings
5. **Permissions**: All endpoints require dealer authentication
6. **Soft Delete**: Listings are permanently deleted (no soft delete)

---

## 🐛 Known Issues

1. **Delete Response**: The delete endpoint doesn't return a proper success response (returns None)
2. **Error Handling**: Some endpoints use generic exception handling instead of specific error types

---

## 🎯 Recommended Improvements

1. **Standardize Responses**: Ensure all endpoints return consistent response format
2. **Add Pagination**: List endpoints should support pagination
3. **Add Filtering**: Support filtering by status, type, price range, etc.
4. **Add Bulk Actions**: Support bulk publish/unpublish/delete
5. **Add Analytics**: Track views, clicks, and engagement per listing
6. **Add Draft Mode**: Allow saving listings as drafts before publishing
7. **Boost Analytics**: Track boost performance (views, clicks during boost period)
