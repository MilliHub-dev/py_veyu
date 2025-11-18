# Veyu Platform - Complete API Documentation

## Base URL
```
Production: https://dev.veyu.cc

```

## Vercel Deployment
The API is deployed on Vercel serverless infrastructure with the following characteristics:
- **Runtime**: Python 3.11
- **Function Timeout**: 10 seconds maximum
- **Cold Start**: First request may take 2-3 seconds
- **Regions**: Primary deployment in `iad1` (US East)
- **Static Files**: Served via Vercel CDN with aggressive caching



## Authentication
All API endpoints (except public endpoints) require JWT authentication:
```
Authorization: Bearer <access_token>
```

## Common Response Formats

### Success Response Format
```json
{
  "error": false,
  "message": "Operation successful",
  "data": { }
}
```

### Error Response Format
```json
{
  "error": true,
  "message": "Error description",
  "errors": { },
  "code": "ERROR_CODE"
}
```

## HTTP Status Codes
- `200 OK`: Successful GET/PUT request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data or validation error
- `401 Unauthorized`: Authentication required or invalid token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable
- `504 Gateway Timeout`: Function timeout (Vercel 10s limit exceeded)

### JWT Token Endpoints

#### Obtain Token Pair
```http
POST /api/v1/token/
```
**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```
**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Refresh Token
```http
POST /api/v1/token/refresh/
```
**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "rotate_refresh": true
}
```
**Response:**
```json
{
  "error": false,
  "message": "Token refreshed successfully",
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access_expires": 1640995200,
    "refresh_expires": 1641081600
  }
}
```

#### Verify Token
```http
POST /api/v1/token/verify/
```
**Request:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Health Check

#### System Health Check
```http
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "service": "veyu-django"
}
```
**Note:** This endpoint is used for monitoring and doesn't require authentication.

---

## 1. ACCOUNTS & AUTHENTICATION

### 1.1 User Registration & Login

#### Enhanced Sign Up
```http
POST /api/v1/accounts/signup/
#### Enhanced Sign Up
```http
POST /api/v1/accounts/signup/
```
**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "confirm_password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+2348012345678",
  "user_type": "customer|dealer|mechanic",
  "provider": "veyu",
  "action": "create-account"
}
```
**Social Auth Request:**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "user_type": "customer|dealer|mechanic",
  "provider": "google|apple|facebook",
  "oauth_token": "social_auth_token_here"
}
```
**Response:**
```json
{
  "error": false,
  "message": "Account created successfully. Please check your email to verify your account.",
  "data": {
    "user": {
      "id": 123,
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "user_type": "customer",
      "provider": "veyu",
      "verified_email": false
    },
    "tokens": {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "access_expires": 1640995200,
      "refresh_expires": 1641081600
    },
    "verification_sent": true,
    "welcome_email_sent": true
  }
}
```

#### Check Email Availability
```http
GET /api/v1/accounts/signup/?email=user@example.com
```
**Response:**
```json
{
  "error": false,
  "message": "Email is available"
}
```
POST /api/v1/accounts/login/
```
**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```
**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "user_type": "customer",
      "is_verified": true
    },
    "tokens": {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
  }
}
```

#### Logout
```http
POST /api/v1/accounts/logout/
```
**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 1.2 Email & Phone Verification

#### Verify Email (Authenticated)
```http
POST /api/v1/accounts/verify-email/
```
**Authentication:** Bearer token required
**Request:**
```json
{
  "action": "request-code|resend-code|confirm-code",
  "code": "123456"
}
```
**Note:** This endpoint requires authentication and is maintained for backward compatibility with existing clients.

#### Verify Email (Unauthenticated) - **NEW**
```http
POST /api/v1/accounts/verify-email-unauthenticated/
```
**Authentication:** None required
**Request:**
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```
**Response:**
```json
{
  "error": false,
  "message": "Email verified successfully"
}
```
**Note:** This endpoint allows users to verify their email without being logged in, addressing the 401 authentication error during verification.

#### Email Verification - Backward Compatibility

**Migration Notes:**
- Existing clients using the authenticated endpoint will continue to work without changes
- New clients should use the unauthenticated endpoint for post-signup verification
- Both endpoints implement the same security measures and rate limiting
- See [Migration Notes](.kiro/specs/email-verification-fix/MIGRATION_NOTES.md) for detailed compatibility information

#### Verify Phone
```http
POST /api/v1/accounts/verify-phone/
```
**Request:**
```json
{
  "phone_number": "+2348012345678",
  "otp": "123456"
}
```

### 1.3 Password Reset

#### Request Password Reset
```http
POST /api/v1/accounts/password/reset/
```
**Request:**
```json
{
  "email": "user@example.com"
}
```

#### Validate Reset Token
```http
POST /api/v1/accounts/password/reset/validate/
```
**Request:**
```json
{
  "token": "reset_token_here",
  "uidb64": "user_id_base64"
}
```

#### Confirm Password Reset
```http
POST /api/v1/accounts/password/reset/confirm/
```
**Request:**
```json
{
  "token": "reset_token_here",
  "uidb64": "user_id_base64",
  "new_password": "NewSecurePass123!",
  "confirm_password": "NewSecurePass123!"
}
```

### 1.4 Profile Management

#### Update Profile
```http
PUT /api/v1/accounts/profile/
```
**Description:** Update the authenticated user's profile information. Supports partial updates - all fields are optional.

**Authentication:** Required (Token or JWT)

**User Types:** customer, dealer, mechanic

**Partial Updates:** Only include fields you want to update. All fields are optional.

**Common Fields (All User Types):**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+2348012345678",
  "address": "123 Main St, Lagos",
  "profile_picture": "base64_image_or_url",
  "about": "Profile description",
  "headline": "Short tagline",
  "logo": "business_logo_file",
  "location": 1
}
```

**Dealer-Specific Optional Fields:**
```json
{
  "business_name": "ABC Motors Limited",
  "cac_number": "RC123456",
  "tin_number": "12345678-0001",
  "contact_email": "info@abcmotors.com",
  "contact_phone": "+2348098765432",
  "offers_rental": true,
  "offers_purchase": true,
  "offers_drivers": false,
  "offers_trade_in": true,
  "extended_services": "Vehicle inspection, warranty, financing"
}
```

**Mechanic-Specific Optional Fields:**
```json
{
  "business_name": "Quick Fix Auto Services",
  "contact_email": "contact@quickfix.com",
  "contact_phone": "+2347012345678",
  "available": true,
  "business_type": "auto_repair"
}
```

**Note on Business Verification Fields:**
- Fields like `cac_number`, `tin_number`, and `business_name` can be left blank if business verification has not been completed
- These fields are automatically populated when business verification is approved by an admin
- You can update these fields manually, but they will be overwritten when verification is approved

**Response (Dealer Partial Update):**
```json
{
  "id": 1,
  "business_name": "ABC Motors Limited",
  "headline": "Your Trusted Auto Partner",
  "about": "We are a leading car dealership with over 10 years of experience.",
  "cac_number": null,
  "tin_number": null,
  "contact_email": "info@abcmotors.com",
  "contact_phone": "+2348098765432",
  "phone_number": "+2348012345678",
  "location": 1,
  "offers_rental": true,
  "offers_purchase": true,
  "offers_drivers": false,
  "offers_trade_in": true,
  "extended_services": "Vehicle inspection, warranty, financing",
  "logo": "https://res.cloudinary.com/veyu/image/upload/v1234567890/logos/dealer1.jpg"
}
```

**Response (Mechanic Partial Update):**
```json
{
  "id": 2,
  "business_name": "Quick Fix Auto Services",
  "headline": "Fast and Reliable Repairs",
  "about": "Professional auto repair services with certified mechanics.",
  "contact_email": "contact@quickfix.com",
  "contact_phone": "+2347012345678",
  "phone_number": "+2347012345678",
  "location": 2,
  "available": true,
  "business_type": "auto_repair",
  "logo": null
}
```

**Error Response (400):**
```json
{
  "error": true,
  "message": "Invalid user type: agent"
}
```

**Error Response (400 - Validation):**
```json
{
  "error": true,
  "message": "Validation failed",
  "errors": {
    "contact_email": ["Enter a valid email address."],
    "phone_number": ["This field must be a valid phone number."]
  }
}
```

### 1.5 Business Verification

#### Get Verification Status
```http
GET /api/v1/accounts/verification-status/
```
**Description:** Retrieve complete business verification information including all business details and document URLs.

**Authentication:** Required (Token or JWT)

**User Types:** dealer, mechanic only

**Response (Verified):**
```json
{
  "status": "verified",
  "status_display": "Verified",
  "date_created": "2025-10-20T14:30:00Z",
  "rejection_reason": null,
  "business_name": "ABC Motors Limited",
  "cac_number": "RC123456",
  "tin_number": "12345678-0001",
  "business_address": "123 Main Street, Victoria Island, Lagos",
  "business_email": "info@abcmotors.com",
  "business_phone": "+2348012345678",
  "cac_document_url": "https://res.cloudinary.com/veyu/image/upload/v1234567890/verification/cac/doc123.pdf",
  "tin_document_url": "https://res.cloudinary.com/veyu/image/upload/v1234567890/verification/tin/doc456.pdf",
  "proof_of_address_url": "https://res.cloudinary.com/veyu/image/upload/v1234567890/verification/address/doc789.pdf",
  "business_license_url": "https://res.cloudinary.com/veyu/image/upload/v1234567890/verification/license/doc012.pdf"
}
```

**Response (Not Submitted):**
```json
{
  "status": "not_submitted",
  "status_display": "Not Submitted",
  "date_created": null,
  "rejection_reason": null,
  "business_name": null,
  "cac_number": null,
  "tin_number": null,
  "business_address": null,
  "business_email": null,
  "business_phone": null,
  "cac_document_url": null,
  "tin_document_url": null,
  "proof_of_address_url": null,
  "business_license_url": null
}
```

**Response (Rejected):**
```json
{
  "status": "rejected",
  "status_display": "Rejected",
  "date_created": "2025-10-15T10:00:00Z",
  "rejection_reason": "CAC document is not clear. Please resubmit with a higher quality scan.",
  "business_name": "Quick Fix Mechanics",
  "cac_number": null,
  "tin_number": null,
  "business_address": "789 Industrial Avenue, Apapa, Lagos",
  "business_email": "info@quickfix.com",
  "business_phone": "+2347012345678",
  "cac_document_url": "https://res.cloudinary.com/veyu/image/upload/v1234567890/verification/cac/doc111.pdf",
  "tin_document_url": null,
  "proof_of_address_url": null,
  "business_license_url": null
}
```

**Status Values:**
- `not_submitted`: No verification has been submitted yet
- `pending`: Verification submitted and awaiting admin review
- `verified`: Verification approved by admin (profile automatically updated)
- `rejected`: Verification rejected by admin (check rejection_reason)

#### Submit Business Verification
```http
POST /api/v1/accounts/verify-business/
```
**Request (multipart/form-data):**
```
business_type: "dealership|mechanic"
business_name: "AutoMax Dealers Ltd"
cac_number: "RC123456"
tin_number: "12345678-0001"
business_address: "45 Commercial Ave, Lagos"
business_email: "info@automax.com"
business_phone: "+2348012345678"
cac_document: <file>
tin_document: <file>
proof_of_address: <file>
business_license: <file>
```
**Response:**
```json
{
  "error": false,
  "message": "Business verification submitted successfully. Admin will review your submission.",
  "data": {
    "id": 1,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "business_type": "dealership",
    "status": "pending",
    "business_name": "AutoMax Dealers Ltd",
    "cac_number": "RC123456",
    "tin_number": "12345678-0001",
    "business_address": "45 Commercial Ave, Lagos",
    "business_email": "info@automax.com",
    "business_phone": "+2348012345678",
    "rejection_reason": null,
    "date_created": "2025-10-20T14:30:00Z",
    "business_verification_status": "Pending Review"
  }
}
```

#### Get Document Requirements
```http
GET /api/v1/accounts/verification/requirements/
```
**Description:** Get document requirements and guidelines for business verification.

**Authentication:** Required (Token or JWT)

**Response:**
```json
{
  "error": false,
  "message": "Document requirements retrieved successfully",
  "data": {
    "requirements": {
      "cac_document": {
        "name": "CAC Registration Certificate",
        "description": "Corporate Affairs Commission registration certificate",
        "required": true
      },
      "tin_document": {
        "name": "TIN Certificate",
        "description": "Tax Identification Number certificate",
        "required": true
      },
      "proof_of_address": {
        "name": "Proof of Address",
        "description": "Utility bill or lease agreement (within 6 months)",
        "required": true
      },
      "business_license": {
        "name": "Business License",
        "description": "Business operating license",
        "required": false
      }
    },
    "max_file_size": "5MB",
    "allowed_formats": ["PDF", "JPG", "JPEG", "PNG"],
    "notes": [
      "All documents must be clear and legible",
      "Documents should be recent (within 6 months for utility bills)",
      "Business name on documents should match the business name in your profile",
      "All documents will be reviewed by our verification team"
    ]
  }
}
```

#### Get My Verification Documents
```http
GET /api/v1/accounts/verification/my-documents/
```
**Description:** Retrieve all documents uploaded by the authenticated user for business verification.

**Authentication:** Required (Token or JWT)

**User Types:** dealer, mechanic only

**Response:**
```json
{
  "error": false,
  "message": "Documents retrieved successfully",
  "data": {
    "submission_exists": true,
    "submission_id": 1,
    "status": "pending",
    "status_display": "Pending Review",
    "documents": {
      "cac_document": {
        "filename": "cac_certificate.pdf",
        "public_id": "verification/cac/doc123",
        "uploaded_date": "2025-10-20T14:30:00Z",
        "url": "/api/v1/accounts/verification/documents/1/cac_document/",
        "thumbnail_url": "https://res.cloudinary.com/veyu/image/upload/c_thumb,w_200/verification/cac/doc123.jpg",
        "has_document": true
      },
      "tin_document": {
        "filename": "tin_certificate.pdf",
        "public_id": "verification/tin/doc456",
        "uploaded_date": "2025-10-20T14:35:00Z",
        "url": "/api/v1/accounts/verification/documents/1/tin_document/",
        "thumbnail_url": "https://res.cloudinary.com/veyu/image/upload/c_thumb,w_200/verification/tin/doc456.jpg",
        "has_document": true
      },
      "proof_of_address": {
        "filename": "utility_bill.pdf",
        "public_id": "verification/address/doc789",
        "uploaded_date": "2025-10-20T14:40:00Z",
        "url": "/api/v1/accounts/verification/documents/1/proof_of_address/",
        "thumbnail_url": "https://res.cloudinary.com/veyu/image/upload/c_thumb,w_200/verification/address/doc789.jpg",
        "has_document": true
      },
      "business_license": {
        "filename": null,
        "public_id": null,
        "uploaded_date": null,
        "url": null,
        "thumbnail_url": null,
        "has_document": false
      }
    },
    "business_name": "ABC Motors Limited",
    "submission_date": "2025-10-20T14:30:00Z"
  }
}
```

#### Get Secure Document URL
```http
GET /api/v1/accounts/verification/documents/{submission_id}/{document_type}/?expires_in=3600
```
**Description:** Generate a secure, time-limited URL for accessing business verification documents.

**Authentication:** Required (Token or JWT)

**Path Parameters:**
- `submission_id` (integer): Business verification submission ID
- `document_type` (string): Type of document - one of: `cac_document`, `tin_document`, `proof_of_address`, `business_license`

**Query Parameters:**
- `expires_in` (integer, optional): URL expiration time in seconds (default: 3600 = 1 hour)

**Access Control:**
- Document owner (dealer/mechanic who submitted)
- Admin/staff users
- Assigned reviewer

**Response:**
```json
{
  "error": false,
  "secure_url": "https://res.cloudinary.com/veyu/image/upload/s--signature--/v1234567890/verification/cac/doc123.pdf",
  "expires_in": 3600,
  "document_type": "cac_document",
  "submission_id": 1,
  "message": "Secure document URL generated successfully"
}
```

### 1.6 OTP Security

#### Get OTP Security Status
```http
GET /api/v1/accounts/otp/security/status/
```

#### OTP Security Actions
```http
POST /api/v1/accounts/otp/security/actions/
```
**Request:**
```json
{
  "action": "enable|disable|reset",
  "phone_number": "+2348012345678"
}
```

#### Get OTP System Status (Admin)
```http
GET /api/v1/accounts/otp/system/status/
```

### 1.7 Cart & Notifications

#### Get/Update Cart
```http
GET/POST /api/v1/accounts/cart/
```
**Add to Cart:**
```json
{
  "listing_id": "uuid",
  "quantity": 1
}
```

#### Get Notifications
```http
GET /api/v1/accounts/notifications/
```

---

## 2. VEHICLE LISTINGS

### 2.1 Browse Listings

#### Get All Listings
```http
GET /api/v1/listings/
```
**Query Parameters:**
- `page`: Page number
- `limit`: Items per page
- `type`: buy|rent
- `brand`: Vehicle brand
- `min_price`: Minimum price
- `max_price`: Maximum price
- `location`: Location filter

#### Get Featured Listings
```http
GET /api/v1/listings/featured/
```

#### Get Buy Listings
```http
GET /api/v1/listings/buy/
```

#### Get Rental Listings
```http
GET /api/v1/listings/rentals/
```

#### Search Listings
```http
GET /api/v1/listings/find/
```
**Query Parameters:**
- `q`: Search query
- `brand`: Vehicle brand
- `model`: Vehicle model
- `year_min`: Minimum year
- `year_max`: Maximum year
- `price_min`: Minimum price
- `price_max`: Maximum price
- `condition`: new|used|certified
- `transmission`: automatic|manual
- `fuel_type`: petrol|diesel|electric|hybrid

### 2.2 Listing Details

#### Get Buy Listing Detail
```http
GET /api/v1/listings/buy/{uuid}/
```

#### Get Rental Listing Detail
```http
GET /api/v1/listings/rentals/{uuid}/
```

#### Get Dealership Info
```http
GET /api/v1/listings/dealer/{uuid_or_slug}/
```

### 2.3 My Listings

#### Get My Listings
```http
GET /api/v1/listings/my-listings/
```

### 2.4 Checkout

#### Checkout Listing
```http
POST /api/v1/listings/checkout/{listingId}/
```
**Request:**
```json
{
  "payment_method": "card|bank_transfer|wallet",
  "delivery_address": "123 Main St, Lagos",
  "rental_start_date": "2024-01-20",
  "rental_end_date": "2024-01-27"
}
```

#### Get Checkout Documents
```http
GET /api/v1/listings/checkout/documents/
```

#### Book Inspection
```http
POST /api/v1/listings/checkout/inspection/
```
**Request:**
```json
{
  "listing_id": "uuid",
  "preferred_date": "2024-01-20",
  "preferred_time": "10:00",
  "inspection_type": "pre_purchase|pre_rental"
}
```

---

## 3. DEALERSHIP ADMIN

### 3.1 Dashboard

#### Get Dealership Info
```http
GET /api/v1/admin/dealership/
```
**Response:**
```json
{
  "error": false,
  "data": {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "business_name": "AutoMax Dealers",
    "logo": "https://res.cloudinary.com/...",
    "about": "Leading car dealership",
    "headline": "Your trusted car partner",
    "contact_email": "info@automax.com",
    "contact_phone": "+2348012345678",
    "offers_purchase": true,
    "offers_rental": true,
    "offers_drivers": false,
    "offers_trade_in": false,
    "extended_services": [
      {
        "name": "Vehicle Financing",
        "description": "Flexible financing options for vehicle purchases",
        "price_range": "Varies based on loan amount"
      }
    ],
    "verified_business": true,
    "verified_id": true,
    "business_verification_status": "verified"
  }
}
```
**Error Response (404):**
```json
{
  "error": true,
  "message": "Dealership profile not found. Please complete your dealership profile setup."
}
```

#### Get Dashboard Stats
```http
GET /api/v1/admin/dealership/dashboard/
```

#### Get Analytics
```http
GET /api/v1/admin/dealership/analytics/
```

### 3.2 Listing Management

#### Get Dealership Listings
```http
GET /api/v1/admin/dealership/listings/
```

#### Create Listing
```http
POST /api/v1/admin/dealership/listings/create/
```
**Request (multipart/form-data):**
```
name: "Toyota Camry 2020"
brand: "Toyota"
model: "Camry"
year: 2020
price: 15000000
listing_type: "buy|rent"
condition: "new|used|certified"
mileage: 45000
transmission: "automatic|manual"
fuel_type: "petrol|diesel|electric|hybrid"
color: "Silver"
description: "Well maintained vehicle..."
features: ["Air Conditioning", "Leather Seats", "Sunroof"]
images: [<file1>, <file2>, <file3>]
```

#### Get Listing Detail
```http
GET /api/v1/admin/dealership/listings/{listing_id}/
```

#### Update Listing
```http
PUT /api/v1/admin/dealership/listings/{listing_id}/
```

#### Delete Listing
```http
DELETE /api/v1/admin/dealership/listings/{listing_id}/
```

### 3.3 Orders

#### Get Orders
```http
GET /api/v1/admin/dealership/orders/
```
**Query Parameters:**
- `status`: pending|confirmed|completed|cancelled
- `date_from`: Start date
- `date_to`: End date

### 3.4 Settings

#### Get Dealership Settings
```http
GET /api/v1/admin/dealership/settings/
```
**Response:**
```json
{
  "error": false,
  "data": {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "business_name": "AutoMax Dealers",
    "logo": "https://res.cloudinary.com/...",
    "about": "Leading car dealership in Lagos",
    "headline": "Your trusted car partner",
    "contact_email": "info@automax.com",
    "contact_phone": "+2348012345678",
    "offers_purchase": true,
    "offers_rental": true,
    "offers_drivers": false,
    "offers_trade_in": false,
    "extended_services": [
      {
        "name": "Car Detailing",
        "description": "Professional car cleaning and detailing services",
        "price_range": "₦15,000 - ₦50,000"
      },
      {
        "name": "Vehicle Inspection",
        "description": "Pre-purchase vehicle inspection services",
        "price_range": "₦10,000 - ₦25,000"
      }
    ],
    "verified_business": true,
    "level": "top"
  }
}
```

#### Update Dealership Settings
```http
PUT /api/v1/admin/dealership/settings/
```
**Request (multipart/form-data):**
```
new-logo: <file> (optional)
business_name: "AutoMax Dealers Ltd"
about: "Leading car dealership in Lagos..."
slug: "automax-dealers" (optional)
headline: "Your trusted car partner"
services: ["Car Sale", "Car Leasing", "Drivers", "Car Detailing", "Vehicle Inspection"]
contact_phone: "+2348012345678"
contact_email: "info@automax.com"
offers_purchase: true
offers_rental: true
offers_drivers: true
offers_trade_in: false
```
**Response:**
```json
{
  "error": false,
  "data": {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "business_name": "AutoMax Dealers Ltd",
    "logo": "https://res.cloudinary.com/...",
    "about": "Leading car dealership in Lagos...",
    "headline": "Your trusted car partner",
    "contact_email": "info@automax.com",
    "contact_phone": "+2348012345678",
    "offers_purchase": true,
    "offers_rental": true,
    "offers_drivers": true,
    "offers_trade_in": false,
    "extended_services": [
      {
        "name": "Car Detailing",
        "description": "Professional car cleaning and detailing services",
        "price_range": "₦15,000 - ₦50,000"
      },
      {
        "name": "Vehicle Inspection",
        "description": "Pre-purchase vehicle inspection services",
        "price_range": "₦10,000 - ₦25,000"
      }
    ]
  }
}
```

### Service Mapping Behavior

The dealership service mapping system now supports both core boolean services and extended custom services:

**Core Services (Boolean Fields):**
- `offers_purchase`: Vehicle sales (mapped from "Car Sale", "Car Sales", "Vehicle Sales")
- `offers_rental`: Vehicle rentals (mapped from "Car Rental", "Car Leasing", "Vehicle Rental", "Vehicle Leasing")
- `offers_drivers`: Driver services (mapped from "Drivers", "Driver Services", "Chauffeur Services")
- `offers_trade_in`: Trade-in services (mapped from "Trade-In Services", "Trade In", "Vehicle Trade-In")

**Extended Services (JSON Array):**
- Custom services beyond the core offerings: Vehicle Financing, Vehicle Inspection, Extended Warranty, Vehicle Insurance, Vehicle Maintenance, Parts & Accessories, Vehicle Delivery, Test Drive Services, Vehicle Registration, Export Services, Aircraft Sales & Leasing, Boat Sales & Leasing, UAV/Drone Sales, Motorbike Sales & Leasing
- Each service includes: `name`, `description`, and optional `price_range`
- Processed through the `DealershipServiceProcessor` for validation and mapping
- Maintains backward compatibility with existing API consumers

**Service Processing:**
- Case-insensitive service name matching prevents mapping failures
- Unmapped services are logged for debugging purposes
- Service validation ensures at least one service is selected
- Enhanced error messages provide suggestions for typos or invalid service names

**API Response Format:**
All dealership endpoints now include both core service flags and extended services in responses:
```json
{
  "offers_purchase": true,
  "offers_rental": true,
  "offers_drivers": false,
  "offers_trade_in": false,
  "extended_services": [
    {
      "name": "Vehicle Financing",
      "description": "Flexible financing options for vehicle purchases",
      "price_range": "Varies based on loan amount"
    }
  ]
}
```

**Backward Compatibility:**
- Existing API consumers will continue to receive core service fields
- New `extended_services` field is included in all dealership responses
- Legacy service arrays are automatically mapped to appropriate fields
- No breaking changes to existing API contracts
- All dealership-related endpoints (`/api/v1/admin/dealership/`, `/api/v1/admin/dealership/settings/`, `/api/v1/listings/dealer/{uuid}/`) now include `extended_services` field

**Note:** Logo upload is supported via the `new-logo` field in multipart/form-data format.

**⚠️ Deprecation Notice:** The POST method for this endpoint is deprecated and will be removed on December 1, 2025. Please use PUT method instead. The POST method currently returns deprecation headers for backward compatibility.

### 3.5 Service Mapping

#### Service Mapping Overview

The Veyu platform uses a hybrid service mapping system that combines core boolean service flags with extended custom services to provide maximum flexibility for dealerships.

**Core Service Fields:**
- `offers_purchase` (boolean): Vehicle sales capability
- `offers_rental` (boolean): Vehicle rental services
- `offers_drivers` (boolean): Driver/chauffeur services
- `offers_trade_in` (boolean): Vehicle trade-in acceptance

**Extended Services Field:**
- `extended_services` (JSON array): Custom services beyond core offerings

#### Service Processing

When dealerships submit service selections through the settings API, the system:

1. **Maps Core Services**: Standard services are mapped to boolean fields
2. **Processes Extended Services**: Custom services are validated and stored in JSON format
3. **Maintains Compatibility**: Existing API consumers continue to work without changes
4. **Validates Service Data**: Ensures service names, descriptions, and pricing are properly formatted

#### Example Service Mapping

**Input Services Array:**
```json
["Car Sale", "Car Leasing", "Drivers", "Trade-In Services", "Vehicle Financing", "Vehicle Inspection"]
```

**Processed Output:**
```json
{
  "offers_purchase": true,
  "offers_rental": true,
  "offers_drivers": true,
  "offers_trade_in": true,
  "extended_services": [
    {
      "name": "Vehicle Financing",
      "description": "Flexible financing options for vehicle purchases",
      "price_range": "Varies based on loan amount"
    },
    {
      "name": "Vehicle Inspection", 
      "description": "Pre-purchase vehicle inspection services",
      "price_range": "₦10,000 - ₦25,000"
    }
  ]
}
```

**Error Handling Example:**

When invalid or unmapped services are provided:

**Input:**
```json
["Car Sale", "Invalid Service", "Vehicle Detailing"]
```

**Error Response:**
```json
{
  "error": true,
  "message": "Service validation failed. Please check your service selections.",
  "details": {
    "field_errors": {
      "services": ["Dealership must offer at least one service"]
    },
    "unmapped_services": ["Invalid Service"],
    "suggestions": ["Car Sales", "Vehicle Sales", "Car Rental"],
    "suggestion_message": "Did you mean: Car Sales, Vehicle Sales, Car Rental?",
    "available_service_categories": ["core_services", "extended_services"]
  }
}
```

#### API Response Format

All dealership endpoints now include both core service flags and extended services:

```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "business_name": "AutoMax Dealers",
  "offers_purchase": true,
  "offers_rental": true,
  "offers_drivers": false,
  "offers_trade_in": false,
  "extended_services": [
    {
      "name": "Car Detailing",
      "description": "Professional car cleaning and detailing services",
      "price_range": "₦15,000 - ₦50,000"
    }
  ]
}
```

---

## 4. MECHANIC SERVICES

### 4.1 Mechanic Profile

#### Get Mechanic Overview
```http
GET /api/v1/admin/mechanics/
```

#### Get Mechanic Profile
```http
GET /api/v1/admin/mechanics/{mech_id}/
```

#### Search Mechanics
```http
GET /api/v1/admin/mechanics/find/
```
**Query Parameters:**
- `location`: Location
- `service_type`: Service type
- `rating_min`: Minimum rating
- `available`: true|false

### 4.2 Dashboard

#### Get Mechanic Dashboard
```http
GET /api/v1/admin/mechanics/dashboard/
```

#### Get Analytics
```http
GET /api/v1/admin/mechanics/analytics/
```

### 4.3 Bookings

#### Get Bookings
```http
GET /api/v1/admin/mechanics/bookings/
```
**Query Parameters:**
- `status`: pending|confirmed|in_progress|completed|cancelled
- `date_from`: Start date
- `date_to`: End date

#### Update Booking
```http
PUT /api/v1/admin/mechanics/bookings/{booking_id}/
```
**Request:**
```json
{
  "status": "confirmed|in_progress|completed|cancelled",
  "notes": "Additional notes",
  "estimated_completion": "2024-01-20T15:00:00Z"
}
```

### 4.4 Services

#### Get Services
```http
GET /api/v1/admin/mechanics/services/
```

#### Create Service Offering
```http
POST /api/v1/admin/mechanics/services/add/
```
**Request:**
```json
{
  "service_name": "Oil Change",
  "description": "Complete oil change service",
  "price": 15000,
  "duration_minutes": 60,
  "category": "maintenance|repair|inspection"
}
```

#### Update Service Offering
```http
PUT /api/v1/admin/mechanics/services/{service}/
```

#### Delete Service Offering
```http
DELETE /api/v1/admin/mechanics/services/{service}/
```

### 4.5 Settings

#### Get Mechanic Settings
```http
GET /api/v1/admin/mechanics/settings/
```
**Response:**
```json
{
  "error": false,
  "data": {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "business_name": "AutoFix Mechanics",
    "logo": "https://res.cloudinary.com/...",
    "about": "Professional automotive repair services",
    "headline": "Your trusted car repair partner",
    "contact_email": "info@autofix.com",
    "contact_phone": "+2348012345678",
    "business_type": "business",
    "available": true,
    "verified_business": true,
    "level": "level-1",
    "services": [
      {
        "id": 1,
        "service_name": "Oil Change",
        "description": "Complete oil change service",
        "price": 15000,
        "duration_minutes": 60,
        "category": "maintenance"
      }
    ],
    "average_rating": 4.5,
    "total_services": 8,
    "completed_jobs": 45,
    "availability_status": "Available"
  }
}
```
**Error Response (404):**
```json
{
  "error": true,
  "message": "Mechanic profile not found. Please complete your mechanic profile setup."
}
```

#### Update Mechanic Settings
```http
PUT /api/v1/admin/mechanics/settings/
```
**Request (multipart/form-data):**
```
new-logo: <file> (optional)
business_name: "AutoFix Mechanics Ltd"
about: "Professional automotive repair services with 10+ years experience..."
slug: "autofix-mechanics" (optional)
headline: "Your trusted car repair partner"
business_type: "business|individual"
contact_phone: "+2348012345678"
contact_email: "info@autofix.com"
available: true
```
**Response:**
```json
{
  "error": false,
  "data": {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "business_name": "AutoFix Mechanics Ltd",
    "logo": "https://res.cloudinary.com/...",
    "about": "Professional automotive repair services with 10+ years experience...",
    "headline": "Your trusted car repair partner",
    "contact_email": "info@autofix.com",
    "contact_phone": "+2348012345678",
    "business_type": "business",
    "available": true,
    "verified_business": true,
    "level": "level-1"
  }
}
```

---

## 5. WALLET & TRANSACTIONS

### 5.1 Wallet Overview

#### Get Wallet Overview
```http
GET /api/v1/wallet/
```
**Response:**
```json
{
  "success": true,
  "data": {
    "balance": 150000.00,
    "currency": "NGN",
    "wallet_id": "uuid",
    "recent_transactions": []
  }
}
```

### 5.2 Balance

#### Get Balance
```http
GET /api/v1/wallet/balance/
```

### 5.3 Transactions

#### Get Transactions
```http
GET /api/v1/wallet/transactions/
```
**Query Parameters:**
- `type`: deposit|withdrawal|transfer
- `status`: pending|completed|failed
- `date_from`: Start date
- `date_to`: End date
- `page`: Page number
- `limit`: Items per page

### 5.4 Deposit

#### Deposit Funds
```http
POST /api/v1/wallet/deposit/
```
**Request:**
```json
{
  "amount": 50000,
  "payment_method": "card|bank_transfer",
  "payment_reference": "optional_reference"
}
```

### 5.5 Withdrawal

#### Withdraw Funds
```http
POST /api/v1/wallet/withdraw/
```
**Request:**
```json
{
  "amount": 25000,
  "bank_account": {
    "account_number": "0123456789",
    "bank_code": "058",
    "account_name": "John Doe"
  }
}
```

### 5.6 Transfer

#### Transfer Funds
```http
POST /api/v1/wallet/transfer/
```
**Request:**
```json
{
  "recipient_id": "uuid",
  "amount": 10000,
  "description": "Payment for service",
  "pin": "1234"
}
```

---

## 6. CHAT & MESSAGING

### 6.1 Chat Rooms

#### Get All Chats
```http
GET /api/v1/chat/chats/
```
**Response:**
```json
{
  "success": true,
  "data": {
    "chats": [
      {
        "room_id": "uuid",
        "participant": {
          "id": "uuid",
          "name": "John Doe",
          "avatar": "url"
        },
        "last_message": {
          "content": "Hello there",
          "timestamp": "2024-01-15T10:30:00Z",
          "is_read": false
        },
        "unread_count": 3
      }
    ]
  }
}
```

#### Get Chat Room
```http
GET /api/v1/chat/chats/{room_id}/
```
**Response:**
```json
{
  "success": true,
  "data": {
    "room_id": "uuid",
    "participants": [],
    "messages": [
      {
        "id": "uuid",
        "sender": {
          "id": "uuid",
          "name": "John Doe"
        },
        "content": "Hello",
        "timestamp": "2024-01-15T10:30:00Z",
        "is_read": true
      }
    ]
  }
}
```

### 6.2 Messaging

#### Create New Chat
```http
POST /api/v1/chat/new/
```
**Request:**
```json
{
  "recipient_id": "uuid",
  "initial_message": "Hi, I'm interested in your listing"
}
```

#### Send Message
```http
POST /api/v1/chat/message/
```
**Request:**
```json
{
  "room_id": "uuid",
  "content": "Hello there",
  "message_type": "text|image|file",
  "attachment_url": "optional_url"
}
```

---

## 7. VEHICLE INSPECTIONS

### 7.1 Inspection Management

#### List Inspections
```http
GET /api/v1/inspections/
```
**Query Parameters:**
- `status`: draft|in_progress|completed|signed|archived
- `type`: pre_purchase|pre_rental|maintenance|insurance
- `vehicle_id`: Filter by vehicle
- `date_from`: Start date
- `date_to`: End date

#### Create Inspection
```http
POST /api/v1/inspections/
```
**Request:**
```json
{
  "vehicle": "vehicle_id",
  "inspector": "inspector_id",
  "customer": "customer_id",
  "dealer": "dealer_id",
  "inspection_type": "pre_purchase|pre_rental|maintenance|insurance",
  "exterior_data": {
    "body_condition": "excellent|good|fair|poor",
    "paint_condition": "excellent|good|fair|poor",
    "windshield_condition": "excellent|good|fair|poor",
    "lights_condition": "excellent|good|fair|poor",
    "tires_condition": "excellent|good|fair|poor"
  },
  "interior_data": {
    "seats_condition": "excellent|good|fair|poor",
    "dashboard_condition": "excellent|good|fair|poor",
    "ac_condition": "excellent|good|fair|poor",
    "audio_system_condition": "excellent|good|fair|poor"
  },
  "engine_data": {
    "engine_condition": "excellent|good|fair|poor",
    "oil_level": "excellent|good|fair|poor",
    "coolant_level": "excellent|good|fair|poor",
    "battery_condition": "excellent|good|fair|poor"
  },
  "mechanical_data": {
    "transmission_condition": "excellent|good|fair|poor",
    "brakes_condition": "excellent|good|fair|poor",
    "suspension_condition": "excellent|good|fair|poor",
    "steering_condition": "excellent|good|fair|poor"
  },
  "safety_data": {
    "airbags_condition": "excellent|good|fair|poor",
    "seatbelts_condition": "excellent|good|fair|poor",
    "warning_lights": "excellent|good|fair|poor"
  },
  "inspector_notes": "Vehicle is in good condition",
  "recommended_actions": ["Replace brake pads", "Check tire pressure"]
}
```

#### Get Inspection Detail
```http
GET /api/v1/inspections/{id}/
```

#### Update Inspection
```http
PUT /api/v1/inspections/{id}/
```

#### Delete Inspection
```http
DELETE /api/v1/inspections/{id}/
```

#### Complete Inspection
```http
POST /api/v1/inspections/{inspection_id}/complete/
```

### 7.2 Photos

#### Upload Inspection Photo
```http
POST /api/v1/inspections/{inspection_id}/photos/
```
**Request (multipart/form-data):**
```
category: "exterior_front|exterior_rear|interior_dashboard|engine_bay|..."
image: <file>
description: "Front view of vehicle"
```

### 7.3 Documents

#### Generate Document
```http
POST /api/v1/inspections/{inspection_id}/generate-document/
```
**Request:**
```json
{
  "template_type": "standard|detailed|legal",
  "include_photos": true,
  "include_recommendations": true,
  "language": "en",
  "compliance_standards": ["NURTW", "FRSC", "SON"]
}
```

#### Get Document Preview
```http
GET /api/v1/inspections/documents/{document_id}/preview/
```

#### Download Document
```http
GET /api/v1/inspections/documents/{document_id}/download/
```

#### Sign Document
```http
POST /api/v1/inspections/documents/{document_id}/sign/
```
**Request:**
```json
{
  "signature_data": {
    "signature_image": "data:image/png;base64,iVBORw0KGgo...",
    "signature_method": "drawn|typed|uploaded",
    "coordinates": {
      "x": 100,
      "y": 200,
      "width": 200,
      "height": 50
    }
  },
  "signature_field_id": "inspector_signature"
}
```

### 7.4 Statistics & Templates

#### Get Inspection Stats
```http
GET /api/v1/inspections/stats/
```

#### Get Inspection Templates
```http
GET /api/v1/inspections/templates/
```

#### Validate Inspection Data
```http
GET /api/v1/inspections/validate/
```
**Query Parameters:**
- `data`: JSON inspection data

---

## 8. DIGITAL SIGNATURES

### 8.1 Signature Validation

#### Validate Signature
```http
POST /api/v1/inspections/signatures/validate/
```
**Request:**
```json
{
  "signature_data": {
    "signature_image": "data:image/png;base64,iVBORw0KGgo...",
    "coordinates": {
      "x": 100,
      "y": 200,
      "width": 200,
      "height": 50
    }
  }
}
```

### 8.2 Signature Permissions & Status

#### Check Signature Permission
```http
GET /api/v1/inspections/signatures/documents/{document_id}/permission-check/
```

#### Get Signature Status
```http
GET /api/v1/inspections/signatures/documents/{document_id}/status/
```
**Response:**
```json
{
  "success": true,
  "data": {
    "document_id": 123,
    "document_status": "Ready for Signature",
    "total_signatures": 3,
    "completed_signatures": 1,
    "pending_signatures": 2,
    "completion_percentage": 33.33,
    "signatures": [
      {
        "id": 1,
        "role": "Inspector",
        "status": "Signed",
        "signer_name": "John Doe",
        "signature_method": "Hand Drawn",
        "signed_at": "2024-01-15T10:30:00Z",
        "is_verified": true
      }
    ]
  }
}
```

#### Get Signature Audit Trail
```http
GET /api/v1/inspections/signatures/documents/{document_id}/audit-trail/
```

### 8.3 Signature Verification

#### Verify Signature
```http
POST /api/v1/inspections/signatures/{signature_id}/verify/
```

### 8.4 Signature Actions

#### Resend Signature Notification
```http
POST /api/v1/inspections/signatures/{signature_id}/resend-notification/
```

#### Reject Signature
```http
POST /api/v1/inspections/signatures/{signature_id}/reject/
```
**Request:**
```json
{
  "reason": "Document contains errors"
}
```

### 8.5 Bulk Operations

#### Get Bulk Signature Status
```http
POST /api/v1/inspections/signatures/bulk-status/
```
**Request:**
```json
{
  "document_ids": [1, 2, 3, 4, 5]
}
```

---

## 9. FRONTEND INTEGRATION APIs

### 9.1 Inspection Data Collection

#### Collect Inspection Data
```http
POST /api/v1/inspections/frontend/collect-data/
```
**Request:**
```json
{
  "vehicle_id": 123,
  "customer_id": 456,
  "dealer_id": 789,
  "inspection_type": "pre_purchase",
  "exterior": {
    "body_condition": "good",
    "paint_condition": "excellent"
  },
  "interior": {
    "seats_condition": "good",
    "dashboard_condition": "excellent"
  },
  "engine": {
    "engine_condition": "good",
    "oil_level": "excellent"
  },
  "mechanical": {
    "transmission_condition": "good",
    "brakes_condition": "good"
  },
  "safety": {
    "airbags_condition": "excellent",
    "seatbelts_condition": "good"
  },
  "notes": "Vehicle in good condition",
  "recommendations": ["Replace brake pads"]
}
```

### 9.2 Document Preview

#### Generate Document Preview
```http
POST /api/v1/inspections/frontend/inspections/{inspection_id}/generate-preview/
```
**Request:**
```json
{
  "template_type": "standard",
  "include_photos": true,
  "include_recommendations": true
}
```

### 9.3 Signature Submission

#### Submit Signature
```http
POST /api/v1/inspections/frontend/documents/{document_id}/submit-signature/
```
**Request:**
```json
{
  "signature_image": "data:image/png;base64,iVBORw0KGgo...",
  "signature_method": "drawn",
  "coordinates": {
    "x": 100,
    "y": 200,
    "width": 200,
    "height": 50
  }
}
```

### 9.4 Document Retrieval

#### Retrieve Document
```http
GET /api/v1/inspections/frontend/documents/{document_id}/
```

### 9.5 Status Updates

#### Get Inspection Status
```http
GET /api/v1/inspections/frontend/inspections/{inspection_id}/status/
```
**Response:**
```json
{
  "success": true,
  "data": {
    "inspection_id": 123,
    "status": "Completed",
    "overall_rating": "Good",
    "inspection_date": "2024-01-15T10:00:00Z",
    "completed_at": "2024-01-15T11:00:00Z",
    "is_completed": true,
    "requires_signature": true,
    "document_count": 1,
    "signed_document_count": 0,
    "document_progress": [
      {
        "document_id": 1,
        "template_type": "Standard Report",
        "status": "Ready for Signature",
        "signature_progress": {
          "signed": 1,
          "total": 3,
          "percentage": 33.33
        }
      }
    ],
    "overall_completion": 0.0,
    "last_updated": "2024-01-15T11:00:00Z"
  }
}
```

### 9.6 Photo Upload

#### Upload Photo
```http
POST /api/v1/inspections/frontend/inspections/{inspection_id}/upload-photo/
```
**Request (multipart/form-data):**
```
category: "exterior_front"
image: <file>
description: "Front view"
```

### 9.7 Form Schema

#### Get Form Schema
```http
GET /api/v1/inspections/frontend/form-schema/
```
**Response:**
```json
{
  "success": true,
  "data": {
    "sections": [
      {
        "name": "exterior",
        "label": "Exterior Inspection",
        "fields": [
          {
            "name": "body_condition",
            "label": "Body Condition",
            "type": "select",
            "options": ["excellent", "good", "fair", "poor"],
            "required": true
          }
        ]
      }
    ],
    "photo_categories": [
      {
        "value": "exterior_front",
        "label": "Exterior - Front View"
      }
    ]
  }
}
```

---

## 10. DOCUMENT MANAGEMENT

### 10.1 Access Control

#### Check Document Access
```http
GET /api/v1/inspections/management/documents/{document_id}/access-check/
```
**Response:**
```json
{
  "success": true,
  "data": {
    "document_id": 123,
    "can_view": true,
    "can_download": true,
    "can_sign": true,
    "can_manage": false
  }
}
```

### 10.2 Version Management

#### Get Version History
```http
GET /api/v1/inspections/management/documents/{document_id}/versions/
```
**Response:**
```json
{
  "success": true,
  "data": {
    "document_id": 123,
    "current_version": 1,
    "versions": [
      {
        "version_number": 1,
        "created_at": "2024-01-15T10:00:00Z",
        "status": "signed",
        "file_hash": "sha256_hash",
        "is_current": true
      }
    ]
  }
}
```

### 10.3 Audit Trail

#### Get Document Audit Trail
```http
GET /api/v1/inspections/management/documents/{document_id}/audit-trail/
```
**Query Parameters:**
- `start_date`: Filter start date
- `end_date`: Filter end date

**Response:**
```json
{
  "success": true,
  "data": {
    "document_id": 123,
    "audit_entries": [
      {
        "timestamp": "2024-01-15T10:00:00Z",
        "action": "document_created",
        "user": "System",
        "details": {
          "template_type": "standard",
          "status": "generating"
        }
      },
      {
        "timestamp": "2024-01-15T10:30:00Z",
        "action": "document_signed",
        "user": "john@example.com",
        "details": {
          "role": "inspector",
          "signature_method": "drawn",
          "ip_address": "192.168.1.1"
        }
      }
    ],
    "total_entries": 2
  }
}
```

### 10.4 Search & Filtering

#### Search Documents
```http
POST /api/v1/inspections/management/documents/search/
```
**Request:**
```json
{
  "inspection_id": 123,
  "status": "signed",
  "template_type": "standard",
  "date_from": "2024-01-01",
  "date_to": "2024-01-31",
  "vehicle_id": 456,
  "customer_id": 789,
  "dealer_id": 101,
  "document_hash": "sha256_hash"
}
```

### 10.5 Retention Management

#### Check Retention Status
```http
GET /api/v1/inspections/management/documents/{document_id}/retention-status/
```
**Response:**
```json
{
  "success": true,
  "data": {
    "document_id": 123,
    "status": "active",
    "age_days": 45,
    "should_archive": false,
    "should_delete": false,
    "days_until_archive": 320,
    "days_until_deletion": null
  }
}
```

#### Archive Document
```http
POST /api/v1/inspections/management/documents/{document_id}/archive/
```
**Request:**
```json
{
  "reason": "Manual archival per user request"
}
```

#### Run Retention Cleanup (Admin Only)
```http
POST /api/v1/inspections/management/documents/retention-cleanup/
```
**Response:**
```json
{
  "success": true,
  "message": "Retention cleanup completed",
  "data": {
    "archived_count": 15,
    "deleted_count": 3
  }
}
```

### 10.6 Document Sharing

#### Share Document
```http
POST /api/v1/inspections/management/documents/{document_id}/share/
```
**Request:**
```json
{
  "email": "recipient@example.com",
  "permission_level": "view|download",
  "expiry_hours": 24
}
```
**Response:**
```json
{
  "success": true,
  "message": "Document shared successfully",
  "data": {
    "document_id": 123,
    "share_token": "uuid",
    "shared_by": "sender@example.com",
    "shared_with": "recipient@example.com",
    "permission_level": "view",
    "created_at": "2024-01-15T10:00:00Z",
    "expires_at": "2024-01-16T10:00:00Z",
    "is_active": true
  }
}
```

#### List Document Shares
```http
GET /api/v1/inspections/management/documents/{document_id}/shares/
```

#### Revoke Share
```http
POST /api/v1/inspections/management/documents/{document_id}/revoke-share/
```
**Request:**
```json
{
  "share_token": "uuid"
}
```

---

## ERROR RESPONSES

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error message",
  "details": "Additional error details"
}
```

### Common HTTP Status Codes
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Common Error Codes
- `VALIDATION_ERROR`: Invalid request data
- `AUTHENTICATION_REQUIRED`: Missing or invalid token
- `PERMISSION_DENIED`: Insufficient permissions
- `RESOURCE_NOT_FOUND`: Resource doesn't exist
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error

---

## RATE LIMITS

- **Authentication**: 5 requests per minute
- **Document Generation**: 10 requests per minute
- **Signature Submission**: 5 requests per minute
- **Document Download**: 50 requests per minute
- **General API**: 100 requests per minute

## VERCEL SERVERLESS CONSIDERATIONS

### Function Limitations
- **Timeout**: 10 seconds maximum per request
- **Memory**: 1024MB maximum
- **Package Size**: 50MB maximum
- **Cold Start**: 2-3 seconds for first request after inactivity

### Performance Optimization
- **Database Connections**: Optimized for serverless (no persistent connections)
- **Static Files**: Served via CDN with 1-year cache headers
- **Media Files**: Stored on Cloudinary CDN
- **Caching**: In-memory caching disabled for serverless compatibility

### Best Practices
- **Timeout Handling**: Implement client-side timeouts for long operations
- **Retry Logic**: Implement exponential backoff for failed requests
- **File Uploads**: Use direct Cloudinary uploads for large files
- **Batch Operations**: Split large operations into smaller chunks

### CORS Configuration
The API is configured to accept requests from:
- `https://veyu.vercel.app`
- `https://veyu.cc`
- `https://dev.veyu.cc`
- `https://*.vercel.app` (for preview deployments)

### Response Headers
All API responses include:
- `Access-Control-Allow-Origin`: Configured origins
- `Access-Control-Allow-Methods`: GET, POST, PUT, DELETE, OPTIONS
- `Access-Control-Allow-Headers`: Content-Type, Authorization
- `Cache-Control`: Appropriate caching headers for static content

---

## PAGINATION

List endpoints support pagination:

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)

**Response Format:**
```json
{
  "success": true,
  "data": {
    "results": [],
    "pagination": {
      "current_page": 1,
      "total_pages": 5,
      "total_items": 87,
      "items_per_page": 20,
      "has_next": true,
      "has_previous": false
    }
  }
}
```

---

## WEBHOOKS (Coming Soon)

Veyu will support webhooks for real-time event notifications:

### Supported Events
- `inspection.completed`
- `document.generated`
- `document.signed`
- `payment.completed`
- `booking.confirmed`

---

## SDK & LIBRARIES

### JavaScript/TypeScript
```bash
npm install @veyu/sdk
```

### Python
```bash
pip install veyu-sdk
```

### Usage Example
```javascript
import { VeyuClient } from '@veyu/sdk';

const client = new VeyuClient({
  baseURL: 'https://veyu.vercel.app',
  apiKey: 'your_jwt_token',
  timeout: 8000 // 8 seconds (less than Vercel's 10s limit)
});

// Create inspection
const inspection = await client.inspections.create({
  vehicle_id: 'uuid',
  // ... inspection data
});

// Generate document
const document = await client.documents.generate(inspection.id, {
  template_type: 'standard'
});

// Submit signature
await client.signatures.submit(document.id, {
  signature_image: signatureData
});
```

### Fetch Example
```javascript
// Direct API call with proper timeout
const response = await fetch('https://veyu.vercel.app/api/v1/listings/', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer your_jwt_token',
    'Content-Type': 'application/json'
  },
  signal: AbortSignal.timeout(8000) // 8 second timeout
});

const data = await response.json();
```

---

## SUPPORT

For API support and questions:
- Email: api@veyu.cc
- Documentation: https://veyu.vercel.app/api/docs/
- Swagger UI: https://veyu.vercel.app/api/docs/
- ReDoc: https://veyu.vercel.app/redoc/
- Status Page: https://status.veyu.cc

---

**Last Updated:** November 2024  
**API Version:** v1  
**Documentation Version:** 1.1.0  
**Deployment**: Vercel Serverless (Python 3.11)  
**Region**: US East (iad1)
