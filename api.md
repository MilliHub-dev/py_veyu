# Veyu Platform - Complete API Documentation

## Base URL
```
Production: https://api.veyu.cc
Development: http://localhost:8000
```

## Authentication
All API endpoints (except public endpoints) require JWT authentication:
```
Authorization: Bearer <access_token>
```

### Token Endpoints

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
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
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

---

## 1. ACCOUNTS & AUTHENTICATION

### 1.1 User Registration & Login

#### Enhanced Sign Up
```http
POST /api/v1/accounts/signup/
```
**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+2348012345678",
  "user_type": "customer|dealer|mechanic",
  "business_name": "Optional for dealers/mechanics",
  "accept_terms": true
}
```
**Response:**
```json
{
  "success": true,
  "message": "Account created successfully",
  "data": {
    "user_id": "uuid",
    "email": "user@example.com",
    "tokens": {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
  }
}
```

#### Enhanced Login
```http
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

#### Verify Email
```http
POST /api/v1/accounts/verify-email/
```
**Request:**
```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

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

#### Get/Update Profile
```http
GET/PUT /api/v1/accounts/profile/
```
**Update Request:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+2348012345678",
  "address": "123 Main St, Lagos",
  "profile_picture": "base64_image_or_url"
}
```

### 1.5 Business Verification

#### Submit Business Verification
```http
POST /api/v1/accounts/verify-business/
```
**Request (multipart/form-data):**
```
business_name: "AutoMax Dealers Ltd"
business_registration_number: "RC123456"
tax_identification_number: "TIN987654"
business_address: "45 Commercial Ave, Lagos"
business_type: "dealership|mechanic_shop"
cac_certificate: <file>
tax_clearance: <file>
proof_of_address: <file>
```

#### Get Document Requirements
```http
GET /api/v1/accounts/verification/requirements/
```

#### Get My Verification Documents
```http
GET /api/v1/accounts/verification/my-documents/
```

#### Serve Verification Document
```http
GET /api/v1/accounts/verification/documents/{submission_id}/{document_type}/
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

#### Get/Update Settings
```http
GET/PUT /api/v1/admin/dealership/settings/
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

#### Get/Update Mechanic Settings
```http
GET/PUT /api/v1/admin/mechanics/settings/
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
  apiKey: 'your_api_key',
  environment: 'production'
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

---

## SUPPORT

For API support and questions:
- Email: api@veyu.cc
- Documentation: https://docs.veyu.cc
- Status Page: https://status.veyu.cc

---

**Last Updated:** January 2024  
**API Version:** v1  
**Documentation Version:** 1.0.0
