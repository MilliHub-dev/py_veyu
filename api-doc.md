# Veyu Platform API Documentation

## Overview

Veyu is a comprehensive mobility platform that redefines vehicle marketplace and services. The platform provides endpoints for vehicle marketplace (cars, boats, aircraft, motorbikes), mechanic services, real-time chat, digital wallet, and user management.

**Base URL:** `https://dev.veyu.cc`  
**API Version:** v1  
**API Base URL:** `https://dev.veyu.cc/api/v1`

## Table of Contents

1. [Authentication](#authentication)
2. [Common Patterns](#common-patterns)
3. [Account Management](#account-management)
4. [Vehicle Listings](#vehicle-listings)
5. [Dealership Management](#dealership-management)
6. [Mechanic Services](#mechanic-services)
7. [Real-time Chat](#real-time-chat)
8. [Digital Wallet](#digital-wallet)
9. [Error Handling](#error-handling)
10. [API Explorer](#api-explorer)

---

## Authentication

Veyu API uses Token-based authentication as the primary method, with additional support for JWT and session authentication.

### Authentication Methods

- **Token Authentication** (Primary): `Authorization: Token YOUR_API_TOKEN`
- **JWT Authentication**: `Authorization: Bearer YOUR_JWT_TOKEN`
- **Session Authentication**: For web-based clients

### JWT Token Endpoints

#### Obtain Token Pair
```http
POST /api/v1/token/
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Refresh Token
```http
POST /api/v1/token/refresh/
```

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Verify Token
```http
POST /api/v1/token/verify/
```

**Request Body:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

## Common Patterns

### Response Format

All API responses follow a consistent envelope format:

```json
{
  "error": false,
  "message": "Success message or error description",
  "data": {
    // Response data here
  }
}
```

### Pagination

List endpoints use offset-based pagination:

**Query Parameters:**
- `per_page`: Items per page (default: 25, max: 100)
- `offset`: Number of items to skip (default: 0)

**Pagination Response:**
```json
{
  "error": false,
  "data": {
    "pagination": {
      "offset": 0,
      "limit": 25,
      "count": 150,
      "next": "https://dev.veyu.cc/api/v1/listings/buy/?offset=25",
      "previous": null
    },
    "results": [...]
  }
}
```

### Filtering and Search

Many endpoints support filtering using Django Filter Backend:

**Common Filter Parameters:**
- Vehicle listings: `brand`, `model`, `condition`, `fuel_system`, `transmission`, `min_price`, `max_price`
- Location-based: `location`, `radius` (in kilometers)
- Date ranges: `date_from`, `date_to`

---

## Account Management

Base URL: `/api/v1/accounts/`

### User Registration

#### Create Account
```http
POST /api/v1/accounts/register/
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "securepassword123",
  "confirm_password": "securepassword123",
  "user_type": "customer",
  "provider": "veyu",
  "phone_number": "+234XXXXXXXXXX"
}
```

**User Types:**
- `customer`: Regular platform users
- `dealer`: Vehicle dealers/dealerships
- `mechanic`: Service providers

**Response:**
```json
{
  "error": false,
  "message": "Account created successfully",
  "data": {
    "id": 123,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "user_type": "customer",
    "provider": "veyu",
    "api_token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "verified_email": false,
    "is_active": true,
    "date_joined": "2024-01-15T10:30:00Z"
  }
}
```

#### Setup Business Profile
```http
POST /api/v1/accounts/register/
Content-Type: multipart/form-data
Authorization: Token YOUR_API_TOKEN
```

**Request Body (Dealership):**
```json
{
  "action": "setup-business-profile",
  "user_type": "dealer",
  "business_name": "Premium Auto Sales",
  "about": "Leading car dealership in Lagos",
  "headline": "Quality Cars, Trusted Service",
  "contact_email": "sales@premiumauto.com",
  "contact_phone": "+234XXXXXXXXXX",
  "services": ["Car Sale", "Car Leasing", "Drivers"],
  "location": "{\"lat\": 6.5244, \"lng\": 3.3792, \"country\": \"Nigeria\", \"state\": \"Lagos\", \"city\": \"Lagos\", \"street_address\": \"123 Victoria Island\", \"zip_code\": \"101241\", \"place_id\": \"ChIJ...\"}"
}
```

**Request Body (Mechanic):**
```json
{
  "action": "setup-business-profile",
  "user_type": "mechanic",
  "business_name": "Expert Auto Repair",
  "business_type": "business",
  "about": "Professional auto repair services",
  "headline": "Expert Repairs, Fair Prices",
  "contact_email": "info@expertauto.com",
  "contact_phone": "+234XXXXXXXXXX",
  "location": "{\"lat\": 6.5244, \"lng\": 3.3792, \"country\": \"Nigeria\", \"state\": \"Lagos\", \"city\": \"Lagos\", \"street_address\": \"456 Mainland Street\", \"zip_code\": \"101241\", \"place_id\": \"ChIJ...\"}"
}
```

### User Login

```http
POST /api/v1/accounts/login/
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "provider": "veyu"
}
```

**Response:**
```json
{
  "error": false,
  "data": {
    "id": 123,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "first_name": "John",
    "last_name": "Doe",
    "user_type": "customer",
    "provider": "veyu",
    "is_active": true,
    "verified_email": false,
    "dealerId": "uuid-if-dealer",
    "mechanicId": "uuid-if-mechanic"
  }
}
```

### Email Verification

```http
POST /api/v1/accounts/verify-email/
Authorization: Token YOUR_API_TOKEN
```

**Request Code:**
```json
{
  "action": "request-code",
  "email": "user@example.com"
}
```

**Verify Code:**
```json
{
  "action": "confirm-code",
  "email": "user@example.com",
  "code": "123456"
}
```

### Phone Number Verification

```http
POST /api/v1/accounts/verify-phone-number/
Authorization: Token YOUR_API_TOKEN
```

**Request Code:**
```json
{
  "action": "request-code",
  "phone_number": "+234XXXXXXXXXX"
}
```

**Verify Code:**
```json
{
  "action": "confirm-code",
  "code": "123456"
}
```

### Business Verification

```http
POST /api/v1/accounts/verify-business/
Authorization: Token YOUR_API_TOKEN
Content-Type: multipart/form-data
```

**Request Body:**
```json
{
  "cac_certificate": "file_upload",
  "tin_certificate": "file_upload",
  "business_address_proof": "file_upload",
  "id_document": "file_upload"
}
```

### Update Profile

```http
PUT /api/v1/accounts/update-profile/
Authorization: Token YOUR_API_TOKEN
```

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+234XXXXXXXXXX",
  "location": {
    "lat": 6.5244,
    "lng": 3.3792,
    "country": "Nigeria",
    "state": "Lagos",
    "city": "Lagos"
  }
}
```

### User Cart

```http
GET /api/v1/accounts/cart/
Authorization: Token YOUR_API_TOKEN
```

**Response:**
```json
{
  "error": false,
  "data": {
    "cart_items": [
      {
        "id": 456,
        "title": "2022 Toyota Camry - Premium Sedan",
        "price": "15000000.00",
        "listing_type": "sale",
        "vehicle": {
          "brand": "Toyota",
          "model": "Camry",
          "year": 2022,
          "images": [...]
        }
      }
    ],
    "total_value": "15000000.00"
  }
}
```

### Notifications

```http
GET /api/v1/accounts/notifications/
Authorization: Token YOUR_API_TOKEN
```

**Query Parameters:**
- `unread_only`: boolean (default: false)
- `per_page`: integer (default: 25)
- `offset`: integer (default: 0)

---

## Vehicle Listings

Base URL: `/api/v1/listings/`

### Vehicle Types Supported

1. **Cars** - Standard passenger vehicles
2. **Boats** - Marine vessels
3. **Aircraft/Planes** - Aviation vehicles
4. **Motorbikes** - Two-wheeled vehicles

### Browse Listings for Sale

```http
GET /api/v1/listings/buy/
```

**Query Parameters:**
- `brand`: Vehicle brand (e.g., "Toyota", "Honda")
- `model`: Vehicle model
- `condition`: `new`, `used-foreign`, `used-local`
- `fuel_system`: `diesel`, `electric`, `petrol`, `hybrid`
- `transmission`: `auto`, `manual`
- `min_price`: Minimum price filter
- `max_price`: Maximum price filter
- `location`: Location filter
- `vehicle_type`: `car`, `boat`, `plane`, `bike`
- `per_page`: Items per page (default: 25)
- `offset`: Pagination offset

**Response:**
```json
{
  "error": false,
  "data": {
    "pagination": {
      "offset": 0,
      "limit": 25,
      "count": 150,
      "next": "...",
      "previous": null
    },
    "results": [
      {
        "id": 123,
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "title": "2022 Toyota Camry - Premium Sedan",
        "listing_type": "sale",
        "price": "15000000.00",
        "verified": true,
        "approved": true,
        "vehicle": {
          "id": 456,
          "uuid": "vehicle-uuid",
          "name": "2022 Toyota Camry",
          "brand": "Toyota",
          "model": "Camry",
          "condition": "New",
          "fuel_system": "Petrol",
          "transmission": "Automatic",
          "color": "Silver",
          "mileage": "0",
          "doors": 4,
          "seats": 5,
          "drivetrain": "Front Wheel Drive",
          "features": ["Air Conditioning", "Android Auto", "Keyless Entry"],
          "images": [
            {
              "id": 789,
              "uuid": "image-uuid",
              "url": "https://dev.veyu.cc/media/vehicles/images/camry_1.jpg"
            }
          ],
          "dealer": {
            "uuid": "dealer-uuid",
            "business_name": "Premium Auto Sales",
            "location": "Lagos, Nigeria",
            "rating": 4.8,
            "verified": true
          }
        },
        "created_by": {
          "name": "John Dealer",
          "email": "john@premiumauto.com"
        },
        "date_created": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

### Browse Rental Listings

```http
GET /api/v1/listings/rentals/
```

**Query Parameters:** Same as buy listings plus:
- `payment_cycle`: `single`, `day`, `week`, `month`, `year`
- `available_from`: Date availability filter
- `available_to`: Date availability filter

**Response:** Similar structure to buy listings with rental-specific fields:
```json
{
  "error": false,
  "data": {
    "results": [
      {
        "id": 124,
        "title": "2023 Honda Accord - Daily Rental",
        "listing_type": "rental",
        "price": "25000.00",
        "payment_cycle": "Daily Payments",
        "vehicle": {
          "available": true,
          "current_rental": null,
          "trips": 15
        }
      }
    ]
  }
}
```

### Search Listings

```http
GET /api/v1/listings/find/
```

**Query Parameters:**
- `q`: Search query (searches in title, brand, model)
- `scope`: Comma-separated list of scopes: `recents`, `favorites`, `top-deals`
- All other listing filter parameters

**Response:**
```json
{
  "error": false,
  "data": {
    "recents": [...],
    "favorites": [...],
    "top_deals": {
      "sales": [...],
      "rentals": [...],
      "services": [...]
    },
    "search_results": [...]
  }
}
```

### Get Listing Details (Sale)

```http
GET /api/v1/listings/buy/{listing_uuid}/
```

**Response:**
```json
{
  "error": false,
  "data": {
    "id": 123,
    "uuid": "listing-uuid",
    "title": "2022 Toyota Camry - Premium Sedan",
    "listing_type": "sale",
    "price": "15000000.00",
    "notes": "Well maintained vehicle with full service history",
    "verified": true,
    "approved": true,
    "vehicle": {
      // Complete vehicle details including all fields
      "features": ["Air Conditioning", "Android Auto", "Keyless Entry"],
      "custom_duty": false,
      "video": "https://dev.veyu.cc/media/vehicles/videos/camry_tour.mp4"
    },
    "offers": [
      {
        "id": 789,
        "bidder": "Customer Name",
        "amount": "14500000.00",
        "date_created": "2024-01-16T10:30:00Z"
      }
    ],
    "testdrives": [
      {
        "id": 101,
        "requested_by": "Customer Name",
        "granted": true,
        "testdrive_complete": false
      }
    ],
    "viewers_count": 45,
    "date_created": "2024-01-15T10:30:00Z"
  }
}
```

### Get Rental Listing Details

```http
GET /api/v1/listings/rentals/{listing_uuid}/
```

**Response:** Similar to sale details with rental-specific fields:
```json
{
  "error": false,
  "data": {
    "payment_cycle": "month",
    "vehicle": {
      "available": true,
      "current_rental": null,
      "last_rental": {
        "customer": "Previous Renter",
        "rent_from": "2024-01-01",
        "rent_until": "2024-01-31"
      }
    }
  }
}
```

### Get Dealership Details

```http
GET /api/v1/listings/dealer/{dealer_uuid}/
```

**Response:**
```json
{
  "error": false,
  "data": {
    "uuid": "dealer-uuid",
    "business_name": "Premium Auto Sales",
    "about": "Leading car dealership in Lagos",
    "headline": "Quality Cars, Trusted Service",
    "location": {
      "country": "Nigeria",
      "state": "Lagos",
      "city": "Lagos",
      "street_address": "123 Victoria Island"
    },
    "logo": "https://dev.veyu.cc/media/dealers/logos/premium_auto.jpg",
    "rating": 4.8,
    "verified": true,
    "services": ["Car Sale", "Car Leasing", "Drivers"],
    "offers_rental": true,
    "offers_purchase": true,
    "offers_drivers": true,
    "offers_trade_in": true,
    "contact_email": "sales@premiumauto.com",
    "contact_phone": "+234XXXXXXXXXX",
    "cac_number": "RC123456",
    "tin_number": "TIN123456",
    "owner": {
      "user_id": "owner-uuid",
      "email": "owner@premiumauto.com",
      "name": "John Dealer",
      "phone_number": "+234XXXXXXXXXX"
    },
    "reviews": [
      {
        "id": 456,
        "reviewer": "Customer Name",
        "rating": 5,
        "comment": "Excellent service and quality vehicles",
        "date_created": "2024-01-10T10:30:00Z"
      }
    ]
  }
}
```

### User's Listings

```http
GET /api/v1/listings/my-listings/
Authorization: Token YOUR_API_TOKEN
```

**Response:**
```json
{
  "error": false,
  "data": {
    "active_listings": [...],
    "pending_approval": [...],
    "sold_listings": [...],
    "rented_listings": [...]
  }
}
```

### Checkout Process

#### Get Checkout Documents

```http
GET /api/v1/listings/checkout/documents/
Authorization: Token YOUR_API_TOKEN
```

**Query Parameters:**
- `listing_id`: UUID of the listing

#### Book Inspection

```http
POST /api/v1/listings/checkout/inspection/
Authorization: Token YOUR_API_TOKEN
```

**Request Body:**
```json
{
  "listing_id": "listing-uuid",
  "inspection_date": "2024-02-01",
  "inspection_time": "14:30:00"
}
```

#### Complete Checkout

```http
POST /api/v1/listings/checkout/{listing_uuid}/
Authorization: Token YOUR_API_TOKEN
```

**Request Body (Purchase):**
```json
{
  "order_type": "sale",
  "payment_option": "wallet",
  "applied_coupons": ["DISCOUNT10"],
  "inspection_required": true
}
```

**Request Body (Rental):**
```json
{
  "order_type": "rental",
  "payment_option": "card",
  "is_recurring": true,
  "payment_cycle": "month",
  "rent_from": "2024-02-01",
  "rent_until": "2024-03-01"
}
```

**Response:**
```json
{
  "error": false,
  "data": {
    "order_id": "order-uuid",
    "order_type": "sale",
    "order_status": "pending",
    "sub_total": "15000000.00",
    "total": "15075000.00",
    "payment_link": "https://payment.veyu.cc/pay/order-uuid",
    "inspection_scheduled": true,
    "inspection_date": "2024-02-01",
    "inspection_time": "14:30:00"
  }
}
```

---

## Dealership Management

Base URL: `/api/v1/admin/dealership/`  
**Authentication Required:** Dealer account

### Dashboard Overview

```http
GET /api/v1/admin/dealership/dashboard/
Authorization: Token YOUR_API_TOKEN
```

**Response:**
```json
{
  "error": false,
  "data": {
    "total_listings": 45,
    "active_listings": 38,
    "pending_approval": 7,
    "total_orders": 156,
    "pending_orders": 12,
    "completed_orders": 134,
    "total_revenue": "450000000.00",
    "monthly_revenue": "75000000.00",
    "recent_orders": [...],
    "top_performing_listings": [...]
  }
}
```

### Manage Listings

#### Get All Listings

```http
GET /api/v1/admin/dealership/listings/
Authorization: Token YOUR_API_TOKEN
```

**Query Parameters:**
- `status`: `active`, `pending`, `sold`, `rented`
- `listing_type`: `sale`, `rental`
- `per_page`, `offset`: Pagination

#### Create New Listing

```http
POST /api/v1/admin/dealership/listings/create/
Authorization: Token YOUR_API_TOKEN
Content-Type: multipart/form-data
```

**Request Body:**
```json
{
  "listing_type": "sale",
  "price": "15000000.00",
  "title": "2022 Toyota Camry - Premium Sedan",
  "payment_cycle": "single",
  "notes": "Well maintained vehicle",
  "vehicle": {
    "name": "2022 Toyota Camry",
    "brand": "Toyota",
    "model": "Camry",
    "condition": "new",
    "fuel_system": "petrol",
    "transmission": "auto",
    "color": "Silver",
    "mileage": "0",
    "doors": 4,
    "seats": 5,
    "drivetrain": "FWD",
    "features": ["Air Conditioning", "Android Auto"],
    "custom_duty": false
  },
  "images": ["file1", "file2", "file3"],
  "video": "file"
}
```

#### Update Listing

```http
PUT /api/v1/admin/dealership/listings/{listing_uuid}/
Authorization: Token YOUR_API_TOKEN
```

#### Delete Listing

```http
DELETE /api/v1/admin/dealership/listings/{listing_uuid}/
Authorization: Token YOUR_API_TOKEN
```

### Order Management

```http
GET /api/v1/admin/dealership/orders/
Authorization: Token YOUR_API_TOKEN
```

**Query Parameters:**
- `status`: Filter by order status
- `order_type`: `sale`, `rental`
- `date_from`, `date_to`: Date range filter

**Response:**
```json
{
  "error": false,
  "data": {
    "pagination": {...},
    "results": [
      {
        "id": "order-uuid",
        "order_type": "sale",
        "order_status": "completed",
        "customer": {
          "name": "John Customer",
          "email": "john@example.com",
          "phone": "+234XXXXXXXXXX"
        },
        "order_item": {
          "title": "2022 Toyota Camry",
          "price": "15000000.00"
        },
        "total": "15075000.00",
        "payment_option": "wallet",
        "paid": true,
        "date_created": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

### Analytics

```http
GET /api/v1/admin/dealership/analytics/
Authorization: Token YOUR_API_TOKEN
```

**Query Parameters:**
- `period`: `week`, `month`, `quarter`, `year`
- `date_from`, `date_to`: Custom date range

**Response:**
```json
{
  "error": false,
  "data": {
    "sales_analytics": {
      "total_sales": "450000000.00",
      "sales_count": 134,
      "average_sale_value": "3358208.96",
      "sales_by_month": [...]
    },
    "rental_analytics": {
      "total_rental_revenue": "15000000.00",
      "active_rentals": 22,
      "rental_utilization_rate": 0.78
    },
    "listing_performance": [
      {
        "listing_title": "2022 Toyota Camry",
        "views": 245,
        "inquiries": 12,
        "conversion_rate": 0.049
      }
    ],
    "customer_analytics": {
      "new_customers": 45,
      "returning_customers": 23,
      "customer_satisfaction": 4.6
    }
  }
}
```

### Settings

```http
GET /api/v1/admin/dealership/settings/
PUT /api/v1/admin/dealership/settings/
Authorization: Token YOUR_API_TOKEN
```

**Update Request Body:**
```json
{
  "business_name": "Premium Auto Sales",
  "about": "Updated description",
  "headline": "New headline",
  "contact_email": "new@premiumauto.com",
  "contact_phone": "+234XXXXXXXXXX",
  "services": ["Car Sale", "Car Leasing"],
  "offers_rental": true,
  "offers_purchase": true,
  "offers_drivers": false,
  "offers_trade_in": true
}
```

---

## Mechanic Services

Base URL: `/api/v1/mechanics/`

### Browse Mechanics

```http
GET /api/v1/mechanics/
```

**Query Parameters:**
- `location`: Location filter
- `radius`: Search radius in km
- `service_type`: Filter by service offerings
- `rating_min`: Minimum rating filter
- `business_type`: `business`, `individual`
- `per_page`, `offset`: Pagination

**Response:**
```json
{
  "error": false,
  "data": {
    "pagination": {...},
    "results": [
      {
        "id": "mechanic-uuid",
        "business_name": "Expert Auto Repair",
        "business_type": "business",
        "about": "Professional auto repair services",
        "headline": "Expert Repairs, Fair Prices",
        "location": {
          "city": "Lagos",
          "state": "Lagos",
          "country": "Nigeria",
          "distance": 2.5
        },
        "rating": 4.7,
        "total_reviews": 156,
        "verified_business": true,
        "verified_id": true,
        "services": [
          {
            "id": 123,
            "service": "Engine Diagnostics",
            "charge": "15000.00",
            "charge_rate": "flat",
            "hires": 45
          }
        ],
        "owner": {
          "name": "John Mechanic",
          "phone_number": "+234XXXXXXXXXX"
        },
        "response_time": "< 2 hours",
        "availability": "Available"
      }
    ]
  }
}
```

### Search Mechanics

```http
GET /api/v1/mechanics/find/
```

**Query Parameters:** Same as browse mechanics plus:
- `q`: Search query (business name, services)
- `emergency_available`: boolean

### Get Mechanic Profile

```http
GET /api/v1/mechanics/{mechanic_uuid}/
```

**Response:**
```json
{
  "error": false,
  "data": {
    "id": "mechanic-uuid",
    "business_name": "Expert Auto Repair",
    "business_type": "business",
    "about": "Professional auto repair services with 10+ years experience",
    "headline": "Expert Repairs, Fair Prices",
    "logo": "https://dev.veyu.cc/media/mechanics/logos/expert_auto.jpg",
    "location": {
      "lat": 6.5244,
      "lng": 3.3792,
      "country": "Nigeria",
      "state": "Lagos",
      "city": "Lagos",
      "street_address": "456 Mainland Street"
    },
    "rating": 4.7,
    "total_reviews": 156,
    "verified_business": true,
    "verified_id": true,
    "contact_email": "info@expertauto.com",
    "contact_phone": "+234XXXXXXXXXX",
    "services": [
      {
        "id": 123,
        "service": {
          "title": "Engine Diagnostics",
          "description": "Complete engine diagnostic and troubleshooting"
        },
        "charge": "15000.00",
        "charge_rate": "Flat Rate",
        "hires": 45
      }
    ],
    "portfolio": [
      {
        "title": "Engine Overhaul - 2020 Honda Civic",
        "description": "Complete engine rebuild",
        "images": [...]
      }
    ],
    "reviews": [
      {
        "id": 456,
        "reviewer": "Customer Name",
        "rating": 5,
        "comment": "Excellent service, fixed my car perfectly",
        "date_created": "2024-01-10T10:30:00Z"
      }
    ],
    "certifications": [
      "ASE Certified",
      "Honda Certified Technician"
    ],
    "years_experience": 12,
    "response_time": "< 2 hours",
    "availability": "Available"
  }
}
```

### Get Mechanic Service History

```http
GET /api/v1/mechanics/{mechanic_uuid}/history/
```

**Response:**
```json
{
  "error": false,
  "data": {
    "total_bookings": 234,
    "completed_bookings": 220,
    "success_rate": 0.94,
    "recent_bookings": [
      {
        "id": "booking-uuid",
        "type": "routine",
        "customer": "Customer Name",
        "services": ["Engine Diagnostics", "Oil Change"],
        "booking_status": "completed",
        "total_amount": "25000.00",
        "completed_date": "2024-01-15T10:30:00Z",
        "customer_rating": 5
      }
    ]
  }
}
```

### Book Mechanic Service

```http
POST /api/v1/mechanics/{mechanic_uuid}/book/
Authorization: Token YOUR_API_TOKEN
```

**Request Body:**
```json
{
  "type": "routine",
  "services": [123, 456],
  "problem_description": "Engine making strange noises, needs diagnostics",
  "preferred_date": "2024-02-01",
  "preferred_time": "10:00:00",
  "location": {
    "type": "customer_location",
    "address": "123 Customer Street, Lagos"
  }
}
```

**Service Types:**
- `routine`: Regular maintenance/repair
- `emergency`: Emergency assistance

**Response:**
```json
{
  "error": false,
  "data": {
    "booking_id": "booking-uuid",
    "type": "routine",
    "booking_status": "requested",
    "mechanic": {
      "business_name": "Expert Auto Repair",
      "contact_phone": "+234XXXXXXXXXX"
    },
    "services": [
      {
        "service": "Engine Diagnostics",
        "charge": "15000.00"
      }
    ],
    "sub_total": "25000.00",
    "estimated_completion": "2024-02-01T14:00:00Z",
    "chat_room": "chat-room-uuid"
  }
}
```

### Update Booking Status

```http
PUT /api/v1/mechanics/bookings/{booking_uuid}/
Authorization: Token YOUR_API_TOKEN
```

**Request Body (Customer):**
```json
{
  "action": "approve_completion",
  "rating": 5,
  "feedback": "Excellent service, highly recommended"
}
```

**Request Body (Mechanic):**
```json
{
  "action": "accept_booking",
  "estimated_start": "2024-02-01T10:00:00Z",
  "estimated_completion": "2024-02-01T14:00:00Z"
}
```

---

## Mechanic Admin Panel

Base URL: `/api/v1/admin/mechanics/`  
**Authentication Required:** Mechanic account

### Dashboard Overview

```http
GET /api/v1/admin/mechanics/dashboard/
Authorization: Token YOUR_API_TOKEN
```

**Response:**
```json
{
  "error": false,
  "data": {
    "total_bookings": 234,
    "pending_bookings": 5,
    "active_bookings": 3,
    "completed_bookings": 220,
    "total_revenue": "2500000.00",
    "monthly_revenue": "450000.00",
    "average_rating": 4.7,
    "response_time": "< 2 hours",
    "recent_bookings": [...],
    "revenue_chart": [...]
  }
}
```

### Manage Bookings

```http
GET /api/v1/admin/mechanics/bookings/
Authorization: Token YOUR_API_TOKEN
```

**Query Parameters:**
- `status`: `requested`, `accepted`, `working`, `completed`, `canceled`
- `type`: `routine`, `emergency`
- `date_from`, `date_to`: Date range

### Service Offerings Management

#### Get Services

```http
GET /api/v1/admin/mechanics/services/
Authorization: Token YOUR_API_TOKEN
```

#### Add New Service

```http
POST /api/v1/admin/mechanics/services/add/
Authorization: Token YOUR_API_TOKEN
```

**Request Body:**
```json
{
  "service_id": 123,
  "charge": "15000.00",
  "charge_rate": "flat",
  "description": "Custom service description"
}
```

#### Update Service

```http
PUT /api/v1/admin/mechanics/services/{service_id}/
Authorization: Token YOUR_API_TOKEN
```

### Analytics

```http
GET /api/v1/admin/mechanics/analytics/
Authorization: Token YOUR_API_TOKEN
```

**Response:**
```json
{
  "error": false,
  "data": {
    "booking_analytics": {
      "total_bookings": 234,
      "completion_rate": 0.94,
      "average_booking_value": "25000.00",
      "bookings_by_month": [...]
    },
    "service_analytics": [
      {
        "service": "Engine Diagnostics",
        "bookings": 45,
        "revenue": "675000.00",
        "average_rating": 4.8
      }
    ],
    "customer_analytics": {
      "new_customers": 23,
      "returning_customers": 67,
      "customer_retention_rate": 0.74
    }
  }
}
```

---

## Real-time Chat

Base URL: `/api/v1/chat/`

### Get Chat Rooms

```http
GET /api/v1/chat/chats/
Authorization: Token YOUR_API_TOKEN
```

**Response:**
```json
{
  "error": false,
  "data": {
    "chat_rooms": [
      {
        "id": "room-uuid",
        "room_type": "sales-chat",
        "members": [
          {
            "name": "John Customer",
            "user_type": "customer"
          },
          {
            "name": "Premium Auto Sales",
            "user_type": "dealer"
          }
        ],
        "last_message": {
          "text": "Is this vehicle still available?",
          "sender": "John Customer",
          "sent": "2 hours ago"
        },
        "unread_count": 3,
        "date_created": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

### Get Chat Room Messages

```http
GET /api/v1/chat/chats/{room_uuid}/
Authorization: Token YOUR_API_TOKEN
```

**Query Parameters:**
- `per_page`: Messages per page (default: 50)
- `offset`: Pagination offset

**Response:**
```json
{
  "error": false,
  "data": {
    "room_info": {
      "id": "room-uuid",
      "room_type": "sales-chat",
      "members": [...]
    },
    "messages": [
      {
        "id": "message-uuid",
        "sender": {
          "name": "John Customer",
          "user_type": "customer"
        },
        "message_type": "user",
        "text": "Is this vehicle still available?",
        "attachments": [
          {
            "id": "attachment-uuid",
            "file": "https://dev.veyu.cc/media/chat/attachments/image.jpg",
            "file_type": "image"
          }
        ],
        "sent": "2 hours ago",
        "date_created": "2024-01-15T08:30:00Z"
      }
    ]
  }
}
```

### Create New Chat

```http
POST /api/v1/chat/new/
Authorization: Token YOUR_API_TOKEN
```

**Request Body:**
```json
{
  "room_type": "sales-chat",
  "members": ["user-uuid-1", "user-uuid-2"],
  "initial_message": "Hi, I'm interested in your vehicle listing"
}
```

### Send Message

```http
POST /api/v1/chat/message/
Authorization: Token YOUR_API_TOKEN
Content-Type: multipart/form-data
```

**Request Body:**
```json
{
  "room_id": "room-uuid",
  "text": "Thank you for your interest!",
  "attachments": ["file1", "file2"]
}
```

### WebSocket Connection

For real-time messaging, connect to:
```
wss://dev.veyu.cc/ws/chat/{room_uuid}/
```

**Authentication:** Include token in connection headers or query parameters

**Message Format:**
```json
{
  "type": "chat_message",
  "message": {
    "room_id": "room-uuid",
    "text": "Hello!",
    "sender": "user-uuid",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

---

## Digital Wallet

Base URL: `/api/v1/wallet/`

### Wallet Overview

```http
GET /api/v1/wallet/
Authorization: Token YOUR_API_TOKEN
```

**Response:**
```json
{
  "error": false,
  "data": {
    "wallet_id": "wallet-uuid",
    "ledger_balance": "150000.00",
    "available_balance": "145000.00",
    "currency": "NGN",
    "locked_funds": "5000.00",
    "pending_transactions": 2,
    "recent_transactions": [
      {
        "id": "transaction-uuid",
        "type": "deposit",
        "amount": "50000.00",
        "status": "completed",
        "narration": "Bank deposit",
        "date_created": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

### Check Balance

```http
GET /api/v1/wallet/balance/
Authorization: Token YOUR_API_TOKEN
```

**Response:**
```json
{
  "error": false,
  "data": {
    "available_balance": "145000.00",
    "ledger_balance": "150000.00",
    "locked_funds": "5000.00",
    "currency": "NGN"
  }
}
```

### Deposit Funds

```http
POST /api/v1/wallet/deposit/
Authorization: Token YOUR_API_TOKEN
```

**Request Body:**
```json
{
  "amount": "50000.00",
  "source": "bank",
  "narration": "Wallet funding"
}
```

**Response:**
```json
{
  "error": false,
  "data": {
    "transaction_id": "transaction-uuid",
    "amount": "50000.00",
    "payment_link": "https://payment.veyu.cc/deposit/transaction-uuid",
    "reference": "VYU_DEP_123456789",
    "status": "pending"
  }
}
```

### Transfer Funds

```http
POST /api/v1/wallet/transfer/
Authorization: Token YOUR_API_TOKEN
```

**Request Body:**
```json
{
  "recipient_email": "recipient@example.com",
  "amount": "25000.00",
  "narration": "Payment for Toyota Camry"
}
```

**Response:**
```json
{
  "error": false,
  "data": {
    "transaction_id": "transaction-uuid",
    "sender": "Your Name",
    "recipient": "Recipient Name",
    "amount": "25000.00",
    "status": "completed",
    "new_balance": "120000.00"
  }
}
```

### Withdraw Funds

```http
POST /api/v1/wallet/withdraw/
Authorization: Token YOUR_API_TOKEN
```

**Request Body:**
```json
{
  "amount": "30000.00",
  "payout_info_id": "payout-info-uuid",
  "narration": "Withdrawal to bank account"
}
```

**Response:**
```json
{
  "error": false,
  "data": {
    "transaction_id": "transaction-uuid",
    "amount": "30000.00",
    "payout_info": {
      "bank_name": "GTBank",
      "account_number": "0123456789",
      "account_name": "John Doe"
    },
    "status": "pending",
    "processing_time": "1-3 business days"
  }
}
```

### Transaction History

```http
GET /api/v1/wallet/transactions/
Authorization: Token YOUR_API_TOKEN
```

**Query Parameters:**
- `type`: `deposit`, `withdraw`, `transfer_in`, `transfer_out`, `payment`, `charge`
- `status`: `pending`, `completed`, `failed`, `reversed`, `locked`
- `date_from`, `date_to`: Date range filter
- `per_page`, `offset`: Pagination

**Response:**
```json
{
  "error": false,
  "data": {
    "pagination": {...},
    "summary": {
      "total_deposits": "200000.00",
      "total_withdrawals": "50000.00",
      "total_transfers_out": "25000.00",
      "total_transfers_in": "10000.00",
      "net_balance_change": "135000.00"
    },
    "transactions": [
      {
        "id": "transaction-uuid",
        "type": "Payment",
        "amount": "15000000.00",
        "status": "completed",
        "sender": "Me",
        "recipient": "Premium Auto Sales",
        "narration": "Payment for 2022 Toyota Camry",
        "source": "wallet",
        "related_order": {
          "id": "order-uuid",
          "title": "2022 Toyota Camry Purchase"
        },
        "date_created": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

---

## Error Handling

### HTTP Status Codes

- **200 OK**: Successful request
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Permission denied or insufficient funds
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation errors
- **500 Internal Server Error**: Server error

### Error Response Format

```json
{
  "error": true,
  "message": "Error description",
  "details": {
    "field_name": ["This field is required."],
    "email": ["Enter a valid email address."]
  }
}
```

### Common Error Scenarios

#### Authentication Errors

```json
{
  "error": true,
  "message": "Authentication credentials were not provided.",
  "code": "authentication_required"
}
```

#### Validation Errors

```json
{
  "error": true,
  "message": "Validation failed",
  "details": {
    "email": ["This field is required."],
    "password": ["This field must be at least 8 characters."]
  }
}
```

#### Insufficient Funds

```json
{
  "error": true,
  "message": "Insufficient funds to complete this transaction.",
  "code": "insufficient_funds",
  "available_balance": "50000.00",
  "required_amount": "75000.00"
}
```

#### Resource Not Found

```json
{
  "error": true,
  "message": "Listing not found or no longer available.",
  "code": "resource_not_found"
}
```

---

## API Explorer

### Interactive Documentation

- **Swagger UI**: https://dev.veyu.cc/api/docs/
- **ReDoc**: https://dev.veyu.cc/redoc/

### Postman Collection

A comprehensive Postman collection is available with pre-configured requests for all endpoints. Contact the API team for access.

### Rate Limiting

Currently, no explicit rate limiting is implemented. However, reasonable usage patterns are expected:
- Maximum 1000 requests per hour per user
- Maximum 10 concurrent connections for WebSocket endpoints

### API Versioning

The current API version is v1. Future versions will be backward compatible where possible. Breaking changes will be introduced in new versions with appropriate migration guides.

---

## Vehicle Type Specifications

### Cars
**Specific Fields:**
- `doors`: Number of doors (integer)
- `seats`: Number of seats (integer)
- `drivetrain`: `4WD`, `AWD`, `FWD`, `RWD`
- `vin`: Vehicle Identification Number

### Boats
**Specific Fields:**
- `hull_material`: Hull material type
- `engine_count`: Number of engines
- `propeller_type`: Type of propeller
- `length`: Length in feet/meters (decimal)
- `beam_width`: Width of the boat (decimal)
- `draft`: Draft depth (decimal)

### Aircraft/Planes
**Specific Fields:**
- `registration_number`: Aircraft registration
- `engine_type`: Engine type/model
- `aircraft_type`: `jet`, `propeller`, `glider`, `helicopter`
- `max_altitude`: Maximum altitude in feet
- `wing_span`: Wing span measurement (decimal)
- `range`: Flight range in km/nautical miles

### Motorbikes
**Specific Fields:**
- `engine_capacity`: Engine capacity in CC
- `bike_type`: `cruiser`, `sport`, `touring`, `offroad`
- `saddle_height`: Saddle height in inches/cm (decimal)

---

## Support and Contact

For API support, integration assistance, or reporting issues:

- **Email**: api@veyu.com
- **Documentation**: https://dev.veyu.cc/api/docs/
- **Status Page**: https://status.veyu.cc
- **Developer Portal**: https://developers.veyu.cc

---

*This documentation is regularly updated. Last updated: January 2024*