# Veyu API Documentation

## Base URL
```
https://dev.veyu.cc
```

## Table of Contents
1. [Authentication](#authentication)
2. [Response Format](#response-format)
3. [Accounts](#accounts)
   - [User Registration](#user-registration)
   - [Email Verification](#email-verification)
   - [Phone Verification](#phone-verification)
   - [User Profile](#user-profile)
   - [Business Verification](#business-verification)
4. [Authentication](#authentication-1)
   - [Login](#login)
   - [Token Management](#token-management)
   - [Password Reset](#password-reset)
5. [Mechanics](#mechanics)
6. [Dealerships](#dealerships)
7. [Listings](#listings)
8. [Bookings](#bookings)
9. [Chat](#chat)
10. [Wallet](#wallet)
11. [Feedback](#feedback)
12. [Error Handling](#error-handling)
13. [Rate Limiting](#rate-limiting)
14. [Webhooks](#webhooks)
15. [Versioning](#versioning)
16. [Support](#support)

## Authentication
- **JWT Authentication** (recommended)
  - Header: `Authorization: Bearer <token>`
  - Token endpoints:
    - `POST /api/v1/token/` - Get access token
    - `POST /api/v1/token/refresh/` - Refresh access token
    - `POST /api/v1/token/verify/` - Verify token

- **Session Authentication** (browser-based)
  - Uses Django's session middleware
  - CSRF token required for state-changing requests

## Response Format
```json
{
  "error": false,
  "message": "Success message",
  "data": {} // Response data
}
```

## Table of Contents
1. [Accounts](#accounts)
2. [Authentication](#authentication)
3. [Mechanics](#mechanics)
4. [Dealerships](#dealerships)
5. [Listings](#listings)
6. [Bookings](#bookings)
7. [Chat](#chat)
8. [Wallet](#wallet)
9. [Feedback](#feedback)

## Accounts

### User Types
- `customer`: Regular app user who can book services
- `mechanic`: Service provider who offers automotive services
- `dealer`: Car dealership that can list vehicles for sale
- `admin`: System administrator with full access

### User Registration

#### 1. Regular Registration
- **Endpoint**: `POST /api/v1/accounts/register/`
- **Authentication**: Public
- **Request Body**:
  ```json
  {
    "action": "create-account",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!",
    "provider": "veyu",
    "user_type": "customer",
    "phone_number": "+2348012345678",
    "accept_terms": true,
    "marketing_consent": false
  }
  ```

#### 2. Social Registration
- **Endpoint**: `POST /api/v1/accounts/register/`
- **Authentication**: Public
- **Request Body**:
  ```json
  {
    "action": "social-auth",
    "provider": "google", // or facebook, apple
    "access_token": "social-provider-token",
    "user_type": "customer"
  }
  ```

#### 3. Business Registration (Mechanic/Dealer)
- **Endpoint**: `POST /api/v1/accounts/register/`
- **Authentication**: Public
- **Request Body**:
  ```json
  {
    "action": "create-business-account",
    "user_type": "mechanic", // or "dealer"
    "business_name": "John's Auto Care",
    "email": "business@example.com",
    "phone_number": "+2348012345678",
    "business_type": "workshop", // or "mobile", "dealership", etc.
    "tax_id": "1234567890",
    "address": {
      "street": "123 Main St",
      "city": "Lagos",
      "state": "Lagos",
      "country": "Nigeria",
      "postal_code": "100001",
      "coordinates": {
        "lat": 6.5244,
        "lng": 3.3792
      }
    },
    "documents": {
      "cac_certificate": "base64_encoded_file",
      "tax_certificate": "base64_encoded_file",
      "id_card": "base64_encoded_file"
    },
    "accept_terms": true
  }
  ```
- **Endpoint**: `POST /api/v1/accounts/register/`
- **Authentication**: Public
- **Request Body**:
  ```json
  {
    "action": "create-account",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!",
    "provider": "veyu",
    "user_type": "customer",
    "phone_number": "+2348012345678"
  }
  ```
- **Responses**:
  - 201 Created: Account created successfully
  - 400 Bad Request: Validation error
  - 409 Conflict: Email already exists

### Email Verification

#### 1. Request Verification Email
- **Endpoint**: `POST /api/v1/accounts/verify-email/`
- **Authentication**: Bearer token required
- **Request Body**:
  ```json
  {
    "action": "request-code"
  }
  ```

#### 2. Verify Email with Code
- **Endpoint**: `POST /api/v1/accounts/verify-email/`
- **Authentication**: Bearer token required
- **Request Body**:
  ```json
  {
    "action": "verify-code",
    "code": "123456"
  }
  ```

#### 3. Resend Verification Email
- **Endpoint**: `POST /api/v1/accounts/resend-verification/`
- **Authentication**: Bearer token required
- **Request Body**:
  ```json
  {
    "email": "user@example.com"
  }
  ```

### Business Verification

#### 1. Submit Business Verification
- **Endpoint**: `POST /api/v1/accounts/verify-business/`
- **Authentication**: Bearer token required (Business accounts only)
- **Request Body**:
  ```json
  {
    "business_type": "mechanic", // or "dealer"
    "documents": {
      "cac_certificate": "base64_encoded_file",
      "tax_certificate": "base64_encoded_file",
      "proof_of_address": "base64_encoded_file",
      "valid_id": "base64_encoded_file"
    },
    "business_details": {
      "registration_number": "RC12345678",
      "tax_identification_number": "TIN123456789",
      "business_address": "123 Business St, Lagos",
      "year_established": 2015
    }
  }
  ```

#### 2. Check Verification Status
- **Endpoint**: `GET /api/v1/accounts/verification-status/`
- **Authentication**: Bearer token required
- **Response**:
  ```json
  {
    "status": "verified", // pending, verified, rejected
    "verified_at": "2023-05-15T10:30:00Z",
    "rejection_reason": null,
    "next_review_date": "2024-05-15T10:30:00Z"
  }
  ```
- **Endpoint**: `POST /api/v1/accounts/verify-email/`
- **Authentication**: Bearer token required
- **Request Body**:
  ```json
  {
    "code": "123456"
  }
  ```
- **Responses**:
  - 200 OK: Email verified successfully
  - 400 Bad Request: Invalid or expired code

### Phone Verification
- **Endpoint**: `POST /api/v1/accounts/verify-phone/`
- **Authentication**: Bearer token required
- **Request Body**:
  ```json
  {
    "phone_number": "+2348012345678",
    "action": "request-code" // or "verify-code"
  }
  ```
- **Responses**:
  - 200 OK: Code sent/verified
  - 400 Bad Request: Invalid request

### User Profile

#### 1. Get User Profile
- **Endpoint**: `GET /api/v1/accounts/profile/`
- **Authentication**: Bearer token required
- **Response**:
  ```json
  {
    "id": "user-uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "user_type": "customer",
    "verified_email": true,
    "email_verified_at": "2023-01-01T10:00:00Z",
    "phone_number": "+2348012345678",
    "phone_verified": true,
    "phone_verified_at": "2023-01-02T11:30:00Z",
    "date_joined": "2023-01-01T00:00:00Z",
    "last_login": "2023-10-31T15:45:00Z",
    "profile_photo_url": "https://dev.veyu.cc/media/profile_photos/user123.jpg",
    "settings": {
      "notifications": {
        "email": true,
        "sms": true,
        "push": true
      },
      "privacy": {
        "show_phone": "contacts_only",
        "show_email": "anyone"
      }
    },
    "preferences": {
      "language": "en",
      "currency": "NGN",
      "theme": "system"
    },
    "metadata": {
      "referral_code": "VEYU1234",
      "referred_by": null,
      "last_ip": "197.210.76.34",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    },
    "business_profile": {
      "id": "biz-123",
      "business_name": "John's Auto Care",
      "business_type": "workshop",
      "verification_status": "verified",
      "rating": 4.8,
      "reviews_count": 42,
      "joined_date": "2023-01-15T09:00:00Z"
    }
  }
  ```

#### 2. Update Profile
- **Endpoint**: `PUT /api/v1/accounts/profile/`
- **Authentication**: Bearer token required
- **Request Body**: (Partial updates supported)
  ```json
  {
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+2348012345678",
    "date_of_birth": "1990-01-01",
    "gender": "male", // male, female, other, prefer_not_to_say
    "address": {
      "street": "123 Main St",
      "city": "Lagos",
      "state": "Lagos",
      "country": "Nigeria",
      "postal_code": "100001",
      "is_default": true,
      "location": {
        "type": "Point",
        "coordinates": [3.3792, 6.5244] // [longitude, latitude]
      }
    },
    "preferences": {
      "language": "en",
      "currency": "NGN",
      "notifications": {
        "email": true,
        "sms": true,
        "push": true
      }
    }
  }
  ```

#### 3. Upload Profile Photo
- **Endpoint**: `POST /api/v1/accounts/profile/photo/`
- **Authentication**: Bearer token required
- **Content-Type**: `multipart/form-data`
- **Request Body**:
  ```
  photo: [binary file]
  ```
- **Response**:
  ```json
  {
    "photo_url": "https://dev.veyu.cc/media/profile_photos/user123.jpg",
    "thumbnail_url": "https://dev.veyu.cc/media/profile_photos/thumbnails/user123.jpg"
  }
  ```

#### 4. Change Password
- **Endpoint**: `POST /api/v1/accounts/change-password/`
- **Authentication**: Bearer token required
- **Request Body**:
  ```json
  {
    "current_password": "oldPassword123!",
    "new_password": "newSecurePassword456!",
    "confirm_password": "newSecurePassword456!"
  }
  ```
- **Endpoint**: `PUT /api/v1/accounts/profile/`
- **Authentication**: Bearer token required
- **Request Body**: (Partial updates allowed)
  ```json
  {
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+2348012345678"
  }
  ```

## Authentication

### Login

#### 1. Email/Password Login
- **Endpoint**: `POST /api/v1/accounts/login/`
- **Authentication**: Public
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "password123",
    "device": {
      "id": "device-12345",
      "name": "iPhone 13 Pro",
      "model": "iPhone14,2",
      "os": "iOS 15.4",
      "push_token": "apns_token_12345"
    }
  }
  ```
- **Response**:
  ```json
  {
    "token": {
      "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "expires_in": 3600,
      "token_type": "Bearer"
    },
    "user": {
      "id": "user-uuid",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "user_type": "customer",
      "email_verified": true,
      "phone_verified": true,
      "profile_photo_url": "https://dev.veyu.cc/media/profile_photos/user123.jpg",
      "permissions": [
        "bookings:create",
        "listings:view"
      ],
      "requires_2fa": false
    },
    "requires_2fa": false
  }
  ```

#### 2. Social Login
- **Endpoint**: `POST /api/v1/accounts/social-login/`
- **Authentication**: Public
- **Request Body**:
  ```json
  {
    "provider": "google", // or facebook, apple
    "access_token": "social-provider-token",
    "device": {
      "id": "device-12345",
      "name": "iPhone 13 Pro",
      "os": "iOS 15.4"
    }
  }
  ```

#### 3. Two-Factor Authentication
- **Endpoint**: `POST /api/v1/accounts/2fa/verify/`
- **Authentication**: Bearer token (temporary)
- **Request Body**:
  ```json
  {
    "code": "123456",
    "method": "sms" // or "email", "authenticator"
  }
  ```

### Token Management

#### 1. Refresh Token
- **Endpoint**: `POST /api/v1/token/refresh/`
- **Request Body**:
  ```json
  {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
- **Response**:
  ```json
  {
    "access": "new.access.token.here",
    "refresh": "new.refresh.token.here",
    "expires_in": 3600,
    "token_type": "Bearer"
  }
  ```

#### 2. Verify Token
- **Endpoint**: `POST /api/v1/token/verify/`
- **Request Body**:
  ```json
  {
    "token": "jwt.token.here"
  }
  ```
- **Response** (if valid):
  ```json
  {}
  ```
  **Status Codes**:
  - 200: Token is valid
  - 401: Token is invalid or expired

### Session Management

#### 1. Get Active Sessions
- **Endpoint**: `GET /api/v1/accounts/sessions/`
- **Response**:
  ```json
  [
    {
      "id": "session-123",
      "ip_address": "197.210.76.34",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
      "location": "Lagos, Nigeria",
      "is_current_device": true,
      "last_active": "2023-10-31T15:30:00Z",
      "created_at": "2023-10-30T10:15:00Z"
    },
    {
      "id": "session-122",
      "ip_address": "197.210.45.12",
      "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4)",
      "location": "Abuja, Nigeria",
      "is_current_device": false,
      "last_active": "2023-10-30T14:20:00Z",
      "created_at": "2023-10-29T08:10:00Z"
    }
  ]
  ```

#### 2. Revoke Session
- **Endpoint**: `DELETE /api/v1/accounts/sessions/{session_id}/`
- **Response**: 204 No Content
- **Endpoint**: `POST /api/v1/accounts/login/`
- **Authentication**: Public
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```
- **Response**:
  ```json
  {
    "token": "jwt.token.here",
    "user": {
      "id": "user-uuid",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "user_type": "customer"
    }
  }
  ```

### Password Reset

#### 1. Request Password Reset
- **Endpoint**: `POST /api/v1/accounts/password/reset/`
- **Authentication**: Public
- **Request Body**:
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **Response**:
  ```json
  {
    "message": "Password reset link has been sent to your email",
    "reset_token": "reset-token-123" // For development/testing only
  }
  ```

#### 2. Verify Reset Token
- **Endpoint**: `GET /api/v1/accounts/password/reset/verify/`
- **Query Params**:
  - `token`: Reset token from email
  - `email`: User's email
- **Response**:
  ```json
  {
    "valid": true,
    "email": "user@example.com"
  }
  ```

#### 3. Confirm Password Reset
- **Endpoint**: `POST /api/v1/accounts/password/reset/confirm/`
- **Request Body**:
  ```json
  {
    "token": "reset-token-123",
    "email": "user@example.com",
    "new_password": "NewSecurePassword123!",
    "confirm_password": "NewSecurePassword123!"
  }
  ```
- **Response**:
  ```json
  {
    "message": "Password has been reset successfully",
    "login_url": "/login"
  }
  ```

#### 4. Password Strength Check
- **Endpoint**: `POST /api/v1/accounts/password/strength/`
- **Request Body**:
  ```json
  {
    "password": "password-to-check"
  }
  ```
- **Response**:
  ```json
  {
    "score": 3,
    "strength": "strong",
    "suggestions": [
      "Add another word or two. Uncommon words are better.",
      "Avoid common words and character sequences."
    ]
  }
  ```
- **Request Reset**: `POST /api/v1/accounts/password/reset/`
- **Confirm Reset**: `POST /api/v1/accounts/password/reset/confirm/`

## Mechanics

### Get All Mechanics
- **Endpoint**: `GET /api/v1/mechanics/`
- **Query Params**:
  - `lat` (float): User's latitude
  - `lng` (float): User's longitude
  - `radius` (int): Search radius in km (default: 30)
  - `services` (string): Comma-separated service IDs
  - `page` (int): Page number
  - `page_size` (int): Items per page

### Get Mechanic Details
- **Endpoint**: `GET /api/v1/mechanics/{mechanic_id}/`
- **Response**:
  ```json
  {
    "id": "mechanic-uuid",
    "user": {
      "first_name": "John",
      "last_name": "Doe",
      "email": "mechanic@example.com"
    },
    "business_name": "John's Auto Care",
    "services": ["Oil Change", "Brake Service"],
    "rating": 4.5,
    "reviews_count": 24,
    "distance": 2.5,
    "available": true
  }
  ```

### 1. Vehicle Types & Categories

#### Types
- `car`: Passenger vehicles
- `motorcycle`: Two/three-wheeled motor vehicles
- `aircraft`: Fixed-wing and rotary aircraft
- `boat`: Watercraft and marine vessels
- `uav`: Unmanned Aerial Vehicles (Drones)
- `truck`: Commercial vehicles
- `bus`: Passenger transport
- `trailer`: Non-motorized hauling units
- `van`: Multi-purpose vehicles
- `suv`: Sport utility vehicles
- `pickup`: Light trucks with open cargo area
- `tractor`: Agricultural/industrial use
- `heavy_equipment`: Construction/farming machinery
- `rv`: Recreational vehicles
- `atv`: All-terrain vehicles
- `snowmobile`: Snow vehicles
- `golf_cart`: Small electric vehicles
- `emergency`: Emergency service vehicles
- `military`: Military vehicles
- `other`: Other vehicle types

#### Categories

##### Cars
- `sedan`: 4-door passenger cars
- `suv`: Sport utility vehicles
- `coupe`: 2-door cars
- `convertible`: Open-top cars
- `hatchback`: Compact cars with rear door
- `wagon`: Estate cars
- `crossover`: Car-based SUVs
- `sports_car`: High-performance cars
- `electric`: Electric vehicles
- `hybrid`: Hybrid vehicles
- `luxury`: Premium vehicles
- `vintage`: Classic/antique cars
- `limousine`: Luxury stretched vehicles
- `micro`: Mini/compact cars
- `supercar`: Ultra-high-performance cars
- `hypercar`: Limited production supercars
- `muscle_car`: High-performance American cars
- `police`: Law enforcement vehicles
- `taxi`: Taxicabs
- `hearse`: Funeral vehicles
- `armored`: Armored/security vehicles
- `racing`: Competition vehicles
- `kit_car`: Homemade/replica vehicles
- `other`: Other car types

##### Aircraft
- `single_engine`: Single-engine propeller planes
- `multi_engine`: Multi-engine propeller planes
- `jet`: Business jets and airliners
- `helicopter`: Rotary-wing aircraft
- `glider`: Motorless aircraft
- `ultralight`: Lightweight recreational aircraft
- `military`: Military aircraft
- `business_jet`: Private/corporate jets
- `seaplane`: Floatplanes and flying boats
- `crop_duster`: Agricultural aircraft
- `experimental`: Homebuilt/experimental aircraft

##### Boats
- `sailboat`: Wind-powered vessels
- `motorboat`: Powerboats
- `yacht`: Luxury motor/sail yachts
- `fishing_boat`: Commercial/recreational fishing
- `pontoon`: Flat-decked boats
- `jetski`: Personal watercraft
- `catamaran`: Multi-hull vessels
- `houseboat`: Floating residences
- `speedboat`: High-performance boats
- `dinghy`: Small boats
- `trawler`: Fishing vessels
- `submarine`: Underwater vessels
- `kayak_canoe`: Paddle craft
- `commercial`: Commercial vessels
- `naval`: Military watercraft

##### Motorcycles
- `sport`: High-performance bikes
- `cruiser`: Comfort-oriented bikes
- `touring`: Long-distance bikes
- `scooter`: Step-through design
- `off_road`: Dirt bikes and dual-sport
- `electric`: Electric-powered bikes
- `naked`: Standard/street bikes
- `adventure`: Dual-sport/adventure bikes
- `chopper`: Custom motorcycles
- `moped`: Small motorized bikes
- `trike`: Three-wheeled motorcycles
- `sidecar`: Motorcycles with sidecar

##### UAVs (Drones)
- `consumer`: Recreational/hobby drones
- `commercial`: Professional/commercial drones
- `racing`: FPV racing drones
- `photography`: Camera drones
- `industrial`: Industrial inspection drones
- `military`: Military/surveillance drones
- `delivery`: Cargo delivery drones
- `agricultural`: Crop monitoring/spraying drones
- `fixed_wing`: Fixed-wing UAVs
- `vtol`: Vertical Take-Off and Landing drones

### 2. Available Filters

#### Basic Filters
- `type`: Vehicle type (car, motorcycle, truck, etc.)
- `category`: Vehicle category (sedan, suv, etc.)
- `make`: Manufacturer (Toyota, Honda, etc.)
- `model`: Vehicle model
- `year_min`/`year_max`: Model year range
- `price_min`/`price_max`: Price range in NGN
- `mileage_max`: Maximum mileage
- `transmission`: `automatic` or `manual`
- `fuel_type`: `petrol`, `diesel`, `hybrid`, `electric`
- `condition`: `new`, `used`, `refurbished`
- `color`: Vehicle color
- `doors`: Number of doors
- `seats`: Number of seats
- `cylinders`: Number of engine cylinders

#### Advanced Filters
- `features`: Comma-separated list (e.g., "bluetooth,backup_camera")
- `dealer_id`: Filter by specific dealer
- `status`: `active`, `sold`, `pending`
- `financing_available`: `true`/`false`
- `warranty`: `true`/`false`
- `imported`: `true` for foreign-used vehicles
- `customs_duty_paid`: `true`/`false`
- `accident_free`: `true`/`false`
- `service_history`: `full`, `partial`, `none`

#### Location Filters
- `location`: Location name or address
- `lat`/`lng`: Coordinates for proximity search
- `radius`: Search radius in km (default: 50)
- `state`: Nigerian state
- `city`: City within state

#### Sorting Options
- `sort_by`: 
  - `price`: Vehicle price
  - `mileage`: Odometer reading
  - `year`: Model year
  - `date_posted`: Listing creation date
  - `relevance`: Search relevance (when using keyword)
- `order`: `asc` or `desc` (default: `desc`)

### 3. Get All Listings
- **Endpoint**: `GET /api/v1/listings/`
- **Authentication**: Optional (Public)
- **Description**: Retrieve a paginated list of vehicle listings with advanced filtering, sorting, and search capabilities. Supports geolocation-based search when coordinates are provided.
- **Query Parameters**:
  - `type`: `car|part|accessory` - Filter by listing type
  - `type`: Filter by vehicle type (see Vehicle Types section)
  - `category`: Filter by vehicle category
  - `make`: Filter by manufacturer
  - `model`: Filter by model name
  - `year_min`/`year_max`: Filter by model year range
  - `price_min`/`price_max`: Filter by price range (NGN)
  - `mileage_max`: Maximum vehicle mileage
  - `transmission`: `automatic` or `manual`
  - `fuel_type`: `petrol`, `diesel`, `hybrid`, `electric`
  - `condition`: `new`, `used`, `refurbished`
  - `color`: Vehicle color
  - `doors`: Number of doors
  - `seats`: Number of seats
  - `cylinders`: Engine cylinders
  - `features`: Comma-separated list of features
  - `dealer_id`: Filter by dealer
  - `status`: `active`, `sold`, `pending`
  - `financing_available`: `true`/`false`
  - `warranty`: `true`/`false`
  - `imported`: `true` for foreign-used
  - `customs_duty_paid`: `true`/`false`
  - `accident_free`: `true`/`false`
  - `service_history`: `full`, `partial`, `none`
  - `location`: Location name/address
  - `lat`/`lng`: Coordinates for proximity search
  - `radius`: Search radius in km (default: 50)
  - `state`: Nigerian state
  - `city`: City within state
  - `sort_by`: `price`, `mileage`, `year`, `date_posted`, `relevance`
  - `order`: `asc` or `desc` (default: `desc`)
  - `page`: Page number (default: 1)
  - `page_size`: Items per page (default: 20, max: 100)
  - `keyword`: Full-text search in title/description

- **Example Request**:
  ```http
  GET /api/v1/listings/?type=car&make=Toyota&year_min=2018&price_max=10000000&sort_by=price&order=asc&page=1&page_size=10&features=bluetooth,backup_camera&radius=50&lat=6.5244&lng=3.3792
  ```

- **Response Fields**:
  - `data`: Array of listing objects
    - `id`: Unique identifier
    - `type`: Listing type (car/part/accessory)
    - `title`: Listing title
    - `description`: Detailed description
    - `price`: Listing price in NGN
    - `currency`: Currency code (default: NGN)
    - `make`: Vehicle make
    - `model`: Vehicle model
    - `year`: Model year
    - `mileage`: Vehicle mileage
    - `condition`: Vehicle condition
    - `status`: Listing status
    - `features`: Array of features
    - `images`: Array of image objects with URLs and metadata
    - `location`: Location details including coordinates
    - `seller`: Seller information
    - `created_at`: ISO timestamp of creation
    - `updated_at`: ISO timestamp of last update
    - `view_count`: Number of views
    - `saved_count`: Number of saves by users
  - `pagination`: Pagination metadata
  - `filters`: Available filter options based on current results

- **Example Response**:
  ```json
  {
    "data": [
      {
        "id": "listing-123",
        "type": "car",
        "title": "2020 Toyota Camry XLE",
        "description": "Excellent condition, one owner, full service history...",
        "price": 15000000,
        "currency": "NGN",
        "make": "Toyota",
        "model": "Camry",
        "year": 2020,
        "mileage": 25000,
        "transmission": "automatic",
        "fuel_type": "petrol",
        "engine_size": 2.5,
        "color": "Pearl White",
        "condition": "used",
        "features": ["leather_seats", "sunroof", "navigation", "backup_camera"],
        "images": [
          {
            "url": "https://dev.veyu.cc/media/listings/camry-1.jpg",
            "is_primary": true,
            "position": 1,
            "dimensions": {"width": 1200, "height": 800}
          }
        ],
        "location": {
          "address": "123 Auto Mall, Victoria Island",
          "city": "Lagos",
          "state": "Lagos",
          "country": "Nigeria",
          "coordinates": {
            "lat": 6.4281,
            "lng": 3.4219
          },
          "distance": 2.5
        },
        "seller": {
          "id": "user-123",
          "name": "John's Auto Sales",
          "type": "dealer",
          "rating": 4.8,
          "total_reviews": 124,
          "verified": true,
          "response_rate": 98,
          "response_time": "1 hour"
        },
        "status": "active",
        "view_count": 245,
        "saved_count": 12,
        "created_at": "2023-10-15T14:30:00Z",
        "updated_at": "2023-10-20T09:15:00Z",
        "metadata": {
          "vin": "JT2BF22K1W0123456",
          "insurance": true,
          "warranty": {
            "available": true,
            "months": 12,
            "mileage_km": 10000
          },
          "financing": {
            "available": true,
            "interest_rate": 12.5,
            "duration_months": 36,
            "down_payment_percent": 30
          }
        }
      }
    ],
    "pagination": {
      "total": 42,
      "count": 20,
      "per_page": 20,
      "current_page": 1,
      "total_pages": 3,
      "links": {
        "next": "https://dev.veyu.cc/api/v1/listings/?page=2",
        "prev": null
      }
    },
    "filters": {
      "makes": [
        {"id": "toyota", "name": "Toyota", "count": 15},
        {"id": "honda", "name": "Honda", "count": 12},
        {"id": "nissan", "name": "Nissan", "count": 8}
      ],
      "models": {
        "toyota": [
          {"id": "camry", "name": "Camry", "count": 5},
          {"id": "corolla", "name": "Corolla", "count": 7},
          {"id": "rav4", "name": "RAV4", "count": 3}
        ]
      },
      "price_range": {"min": 500000, "max": 50000000},
      "year_range": {"min": 2010, "max": 2023},
      "mileage_range": {"min": 0, "max": 200000},
      "features": [
        {"id": "bluetooth", "name": "Bluetooth", "count": 32},
        {"id": "backup_camera", "name": "Backup Camera", "count": 28}
      ]
    }
  }
  ```

### 4. Create Listing
- **Endpoint**: `POST /api/v1/listings/`
- **Authentication**: Bearer token (Dealer/Private Seller)
- **Required Permissions**: `listings.add_listing`
- **Request Body**:
  ```json
  {
    "type": "car",
    "category": "suv",
    "title": "2020 Toyota RAV4 XLE",
    "description": "Excellent condition, one owner, full service history...",
    "price": 18000000,
    "currency": "NGN",
    "make": "Toyota",
    "model": "RAV4",
    "year": 2020,
    "mileage": 35000,
    "transmission": "automatic",
    "fuel_type": "petrol",
    "engine_size": 2.5,
    "color": "Silver",
    "condition": "used",
    "features": ["leather_seats", "sunroof", "navigation"],
    "vehicle_details": {
      "vin": "JTMFB3FV0MD123456",
      "trim": "XLE",
      "interior_color": "Black",
      "exterior_color": "Silver",
      "doors": 5,
      "seats": 5,
      "cylinders": 4,
      "drive_type": "AWD",
      "fuel_economy": {
        "city": 10.2,
        "highway": 7.8,
        "unit": "L/100km"
      },
      "safety_rating": 5,
      "previous_owners": 1,
      "service_history": "full",
      "accident_free": true,
      "warranty_remaining": 12
    },
    "location": {
      "address": "123 Auto Mall, Victoria Island",
      "city": "Lagos",
      "state": "Lagos",
      "country": "Nigeria",
      "coordinates": {
        "lat": 6.4281,
        "lng": 3.4219
      }
    },
    "contact_info": {
      "contact_name": "John Doe",
      "phone": "+2348012345678",
      "email": "seller@example.com",
      "show_phone_publicly": true
    },
    "metadata": {
      "imported": false,
      "customs_duty_paid": true,
      "service_records": [
        {
          "date": "2023-01-15",
          "mileage": 25000,
          "service_type": "major",
          "description": "Oil change, brake inspection, tire rotation",
          "performed_by": "Toyota Lekki"
        }
      ],
      "features": {
        "safety": ["abs", "airbags", "backup_camera", "parking_sensors"],
        "comfort": ["ac", "cruise_control", "keyless_entry", "power_windows"],
        "entertainment": ["bluetooth", "touchscreen", "usb_ports"],
        "exterior": ["alloy_wheels", "fog_lights", "sunroof"],
        "interior": ["leather_seats", "heated_seats", "navigation"]
      },
      "warranty": {
        "available": true,
        "type": "manufacturer",
        "months_remaining": 12,
        "mileage_remaining_km": 20000,
        "transferable": true
      },
      "financing": {
        "available": true,
        "interest_rate": 12.5,
        "duration_months": 36,
        "down_payment_percent": 30,
        "monthly_payment": 185000,
        "approved": true
      },
      "inspection": {
        "available": true,
        "report_url": "https://dev.veyu.cc/inspections/12345.pdf"
      },
      "documents": [
        {
          "type": "insurance",
          "name": "Insurance Certificate",
          "url": "https://dev.veyu.cc/documents/insurance.pdf",
          "expiry_date": "2024-12-31"
        },
        {
          "type": "roadworthiness",
          "name": "Roadworthiness Certificate",
          "url": "https://dev.veyu.cc/documents/roadworthy.pdf",
          "expiry_date": "2024-06-30"
        }
      ]
    },
    "images": [
      {
        "file_data": "base64_encoded_image",
        "is_primary": true,
        "position": 1,
        "description": "Front view"
      },
      {
        "file_data": "base64_encoded_image",
        "is_primary": false,
        "position": 2,
        "description": "Interior dashboard"
      }
    ],
    "status": "draft"
  }
  ```
- **Response**:
  ```json
  {
    "id": "listing-123",
    "status": "pending_review",
    "message": "Listing created successfully and is pending admin approval",
    "preview_url": "https://dev.veyu.cc/listings/2020-toyota-rav4-xle-12345"
  }
  ```

### 5. Update Listing
- **Endpoint**: `PUT /api/v1/listings/{listing_id}/`
- **Authentication**: Bearer token (Owner/Admin)
- **Required Permissions**: `listings.change_listing`
- **Request Body**: Same as create, but all fields are optional
- **Response**: Updated listing object

### 6. Delete Listing
- **Endpoint**: `DELETE /api/v1/listings/{listing_id}/`
- **Authentication**: Bearer token (Owner/Admin)
- **Required Permissions**: `listings.delete_listing`
- **Response**: 204 No Content

### 7. Get Listing Statistics
- **Endpoint**: `GET /api/v1/listings/statistics/`
- **Authentication**: Bearer token (Owner/Admin)
- **Query Parameters**:
  - `timeframe`: `day|week|month|year` (default: month)
  - `start_date`: ISO date string
  - `end_date`: ISO date string
- **Response**:
  ```json
  {
    "total_listings": 45,
    "active_listings": 32,
    "sold_listings": 10,
    "pending_approval": 3,
    "views": 1245,
    "leads": 87,
    "conversion_rate": 6.99,
    "average_price": 18500000,
    "by_category": [
      {"category": "sedan", "count": 15, "percentage": 46.9},
      {"category": "suv", "count": 12, "percentage": 37.5},
      {"category": "truck", "count": 5, "percentage": 15.6}
    ],
    "trends": {
      "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
      "views": [120, 190, 300, 250, 400, 500],
      "leads": [5, 8, 12, 10, 18, 25],
      "sales": [1, 2, 3, 2, 5, 7]
    }
  }
  ```

### 8. Error Handling
- **400 Bad Request**: Invalid parameters or missing required fields
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Listing not found
- **429 Too Many Requests**: Rate limit exceeded

### 9. Rate Limiting
- 60 requests per minute for authenticated users
- 30 requests per minute for anonymous users
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

### 10. Caching
- Public listings are cached for 5 minutes
- Use `Cache-Control: no-cache` to bypass cache
- ETag supported for conditional requests
  - `make`: String - Filter by vehicle make (e.g., "Toyota")
  - `model`: String - Filter by vehicle model (e.g., "Camry")
  - `min_price`: Number - Minimum price filter
  - `max_price`: Number - Maximum price filter
  - `year_min`: Number - Minimum year
  - `year_max`: Number - Maximum year
  - `mileage_max`: Number - Maximum mileage
  - `condition`: `new|used|refurbished` - Item condition
  - `location`: String - Location name or coordinates
  - `radius`: Number - Search radius in kilometers (default: 50)
  - `sort_by`: `price|mileage|year|date_posted` - Sort field
  - `order`: `asc|desc` - Sort order (default: desc)
  - `page`: Number - Page number (default: 1)
  - `page_size`: Number - Items per page (default: 20, max: 100)
  - `features`: Comma-separated list of features (e.g., "bluetooth,backup_camera")
  - `dealer_id`: Filter by specific dealer
  - `status`: `active|sold|pending` - Listing status

- **Response**:
  ```json
  {
    "data": [
      {
        "id": "listing-123",
        "type": "car",
        "title": "Toyota Camry 2020 XLE",
        "description": "Excellent condition, one owner, full service history",
        "price": 15000000,
        "currency": "NGN",
        "make": "Toyota",
        "model": "Camry",
        "year": 2020,
        "mileage": 25000,
        "condition": "used",
        "transmission": "automatic",
        "fuel_type": "petrol",
        "engine_size": 2.5,
        "color": "Pearl White",
        "features": ["leather_seats", "sunroof", "navigation"],
        "images": [
          {
            "url": "https://dev.veyu.cc/media/listings/camry-1.jpg",
            "is_primary": true,
            "position": 1
          }
        ],
        "location": {
          "city": "Lagos",
          "state": "Lagos",
          "country": "Nigeria",
          "coordinates": {
            "lat": 6.5244,
            "lng": 3.3792
          }
        },
        "seller": {
          "id": "user-123",
          "name": "John's Auto Sales",
          "type": "dealer",
          "rating": 4.8,
          "total_reviews": 124
        },
        "status": "active",
        "created_at": "2023-10-15T14:30:00Z",
        "updated_at": "2023-10-20T09:15:00Z"
      }
    ],
    "pagination": {
      "total": 42,
      "count": 20,
      "per_page": 20,
      "current_page": 1,
      "total_pages": 3,
      "links": {
        "next": "https://dev.veyu.cc/api/v1/listings/?page=2",
        "prev": null
      }
    },
    "filters": {
      "makes": ["Toyota", "Honda", "Nissan"],
      "models": {"Toyota": ["Camry", "Corolla", "RAV4"]},
      "price_range": {"min": 500000, "max": 50000000},
      "year_range": {"min": 2010, "max": 2023}
    }
  }
  ```

### 2. Get Single Listing
- **Endpoint**: `GET /api/v1/listings/{listing_id}/`
- **Authentication**: Optional (Public)
- **Response**: Same as all listings but for a single item

### 3. Create Listing
- **Endpoint**: `POST /api/v1/listings/`
- **Authentication**: Bearer token (Dealer/Mechanic)
- **Required Permissions**: `listings.add_listing`
- **Request Body**:
  ```json
  {
    "type": "car",
    "title": "Toyota Camry 2020 XLE",
    "description": "Excellent condition, one owner",
    "price": 15000000,
    "currency": "NGN",
    "make": "Toyota",
    "model": "Camry",
    "year": 2020,
    "mileage": 25000,
    "condition": "used",
    "transmission": "automatic",
    "fuel_type": "petrol",
    "engine_size": 2.5,
    "color": "Pearl White",
    "features": ["leather_seats", "sunroof", "navigation"],
    "images": [
      {
        "file_data": "base64_encoded_image",
        "is_primary": true,
        "position": 1
      }
    ],
    "location": {
      "address": "123 Auto Mall",
      "city": "Lagos",
      "state": "Lagos",
      "country": "Nigeria",
      "postal_code": "100001",
      "coordinates": {
        "lat": 6.5244,
        "lng": 3.3792
      }
    },
    "contact_info": {
      "contact_name": "John Doe",
      "phone": "+2348012345678",
      "email": "seller@example.com",
      "show_phone_publicly": true
    },
    "status": "draft" // draft, pending_review, active, sold
  }
  ```
- **Response**:
  ```json
  {
    "id": "listing-123",
    "status": "pending_review",
    "message": "Listing created successfully and is pending admin approval"
  }
  ```

### 4. Update Listing
- **Endpoint**: `PUT /api/v1/listings/{listing_id}/`
- **Authentication**: Bearer token (Owner/Admin)
- **Required Permissions**: `listings.change_listing`
- **Request Body**: Same as create, but all fields are optional

### 5. Delete Listing
- **Endpoint**: `DELETE /api/v1/listings/{listing_id}/`
- **Authentication**: Bearer token (Owner/Admin)
- **Required Permissions**: `listings.delete_listing`
- **Response**: 204 No Content

### 6. Get Listing Statistics
- **Endpoint**: `GET /api/v1/listings/statistics/`
- **Authentication**: Bearer token (Owner/Admin)
- **Query Parameters**:
  - `timeframe`: `day|week|month|year` (default: month)
  - `start_date`: ISO date string
  - `end_date`: ISO date string
- **Response**:
  ```json
  {
    "total_listings": 45,
    "active_listings": 32,
    "sold_listings": 10,
    "pending_approval": 3,
    "views": 1245,
    "leads": 87,
    "conversion_rate": 6.99,
    "average_price": 18500000,
    "by_category": [
      {"category": "sedan", "count": 15, "percentage": 46.9},
      {"category": "suv", "count": 12, "percentage": 37.5},
      {"category": "truck", "count": 5, "percentage": 15.6}
    ],
    "trends": {
      "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
      "views": [120, 190, 300, 250, 400, 500],
      "leads": [5, 8, 12, 10, 18, 25],
      "sales": [1, 2, 3, 2, 5, 7]
    }
  }
  ```

## Bookings

### 1. Create Booking
- **Endpoint**: `POST /api/v1/bookings/`
- **Authentication**: Bearer token (Customer)
- **Required Permissions**: `bookings.add_booking`
- **Request Body**:
  ```json
  {
    "service_type": "repair",
    "service_id": "service-123", // Optional if service_type is custom
    "mechanic_id": "mechanic-123", // Optional, system will assign if not provided
    "vehicle_id": "vehicle-123", // Optional, can provide vehicle details instead
    "vehicle_details": {
      "make": "Toyota",
      "model": "Camry",
      "year": 2020,
      "vin": "JT2BF22K1W0123456",
      "license_plate": "ABC123XY",
      "mileage": 35000
    },
    "problem_description": "Engine making strange knocking noise when accelerating",
    "preferred_date": "2023-12-15",
    "preferred_time_slot": "morning", // morning, afternoon, evening
    "preferred_time": "14:00", // Specific time if known
    "location_type": "customer_location", // customer_location, mechanic_location, other
    "location": {
      "address": "123 Main St, Victoria Island",
      "city": "Lagos",
      "state": "Lagos",
      "landmark": "Opposite Eko Hotel",
      "coordinates": {
        "lat": 6.4281,
        "lng": 3.4219
      }
    },
    "contact_person": {
      "name": "Jane Smith",
      "phone": "+2348012345678",
      "email": "jane@example.com",
      "relationship": "owner" // owner, driver, representative
    },
    "diagnostic_fee": 5000, // in kobo
    "estimated_cost": 150000, // in kobo
    "estimated_duration": 120, // in minutes
    "special_requests": "Please bring extra engine oil",
    "images": [
      {
        "file_data": "base64_encoded_image",
        "description": "Engine noise"
      }
    ]
  }
  ```
- **Response**:
  ```json
  {
    "id": "booking-123",
    "booking_reference": "VEYU-BK-20231101-1234",
    "status": "pending",
    "payment_status": "pending",
    "estimated_arrival_time": "2023-12-15T14:00:00+01:00",
    "assigned_mechanic": {
      "id": "mechanic-123",
      "name": "John's Auto Care",
      "rating": 4.8,
      "distance": 2.5,
      "estimated_arrival_time": "15 minutes"
    },
    "next_steps": [
      {
        "step": "payment",
        "status": "pending",
        "action_required": true,
        "message": "Complete payment to confirm your booking"
      },
      {
        "step": "mechanic_confirmation",
        "status": "pending",
        "action_required": false,
        "message": "Waiting for mechanic to confirm"
      }
    ],
    "payment_options": [
      {
        "id": "paystack",
        "name": "Card Payment",
        "description": "Pay with card, bank transfer, or USSD",
        "fee": 0,
        "currency": "NGN"
      },
      {
        "id": "wallet",
        "name": "Veyu Wallet",
        "description": "Pay from your Veyu wallet balance",
        "fee": 0,
        "currency": "NGN",
        "balance": 25000
      }
    ]
  }
  ```

### 2. Get Booking Details
- **Endpoint**: `GET /api/v1/bookings/{booking_id}/`
- **Authentication**: Bearer token (Customer/Mechanic/Admin)
- **Required Permissions**: `bookings.view_booking`
- **Response**:
  ```json
  {
    "id": "booking-123",
    "booking_reference": "VEYU-BK-20231101-1234",
    "status": "confirmed",
    "status_history": [
      {
        "status": "pending",
        "timestamp": "2023-11-01T10:00:00Z",
        "message": "Booking created"
      },
      {
        "status": "payment_received",
        "timestamp": "2023-11-01T10:05:23Z",
        "message": "Payment of ₦5,000 received"
      },
      {
        "status": "confirmed",
        "timestamp": "2023-11-01T10:15:45Z",
        "message": "Mechanic John D. has accepted your booking"
      }
    ],
    "service_type": {
      "id": "service-123",
      "name": "Engine Diagnostics",
      "description": "Complete engine diagnostic check",
      "duration": 60,
      "price": 5000
    },
    "vehicle": {
      "id": "vehicle-123",
      "make": "Toyota",
      "model": "Camry",
      "year": 2020,
      "color": "Silver",
      "license_plate": "ABC123XY"
    },
    "customer": {
      "id": "user-456",
      "name": "Jane Smith",
      "phone": "+2348012345678",
      "email": "jane@example.com",
      "rating": 4.5,
      "total_bookings": 3
    },
    "mechanic": {
      "id": "mechanic-123",
      "business_name": "John's Auto Care",
      "contact_person": "John Doe",
      "phone": "+2348098765432",
      "rating": 4.8,
      "total_completed": 124,
      "distance": 2.5,
      "estimated_arrival": "2023-12-15T14:15:00+01:00"
    },
    "location": {
      "type": "customer_location",
      "address": "123 Main St, Victoria Island",
      "city": "Lagos",
      "landmark": "Opposite Eko Hotel",
      "coordinates": {
        "lat": 6.4281,
        "lng": 3.4219
      },
      "notes": "Gate code: 1234"
    },
    "schedule": {
      "preferred_date": "2023-12-15",
      "preferred_time_slot": "afternoon",
      "scheduled_start": "2023-12-15T14:00:00+01:00",
      "scheduled_end": "2023-12-15T16:00:00+01:00",
      "actual_start": null,
      "actual_end": null,
      "duration": 120
    },
    "payment": {
      "status": "paid",
      "method": "card",
      "amount": 5000,
      "currency": "NGN",
      "transaction_id": "TXN123456789",
      "paid_at": "2023-11-01T10:05:23Z",
      "invoice_url": "https://dev.veyu.cc/invoices/VEYU-INV-12345.pdf"
    },
    "diagnosis": {
      "status": "pending",
      "findings": null,
      "recommendations": null,
      "images": []
    },
    "created_at": "2023-11-01T10:00:00Z",
    "updated_at": "2023-11-01T10:15:45Z",
    "cancellation_policy": {
      "can_cancel": true,
      "refund_amount": 4000,
      "cancellation_fee": 1000,
      "deadline": "2023-12-14T14:00:00+01:00"
    },
    "actions": {
      "can_cancel": true,
      "can_reschedule": true,
      "can_message": true,
      "can_rate": false,
      "can_pay": false
    }
  }
  ```

### 3. Update Booking Status
- **Endpoint**: `PATCH /api/v1/bookings/{booking_id}/status/`
- **Authentication**: Bearer token (Customer/Mechanic/Admin)
- **Required Permissions**: `bookings.change_booking`
- **Request Body**:
  ```json
  {
    "status": "in_progress",
    "notes": "Mechanic has arrived at location",
    "metadata": {
      "location": {
        "lat": 6.4281,
        "lng": 3.4219,
        "accuracy": 15.5
      },
      "images": ["image1_url", "image2_url"]
    }
  }
  ```
- **Possible Status Values**:
  - `pending`: Initial status
  - `confirmed`: Mechanic has accepted
  - `en_route`: Mechanic is on the way
  - "arrived": Mechanic has arrived
  - `in_progress`: Service has started
  - `completed`: Service completed
  - `cancelled`: Booking was cancelled
  - `rejected`: Mechanic rejected the booking
  - `expired`: Booking expired without confirmation

### 4. List Bookings
- **Endpoint**: `GET /api/v1/bookings/`
- **Authentication**: Bearer token
- **Query Parameters**:
  - `status`: Filter by status
  - `type`: `upcoming|past|cancelled`
  - `from_date`: Filter from date
  - `to_date`: Filter to date
  - `page`: Page number
  - `page_size`: Items per page
- **Response**: Paginated list of bookings

### 5. Cancel Booking
- **Endpoint**: `POST /api/v1/bookings/{booking_id}/cancel/`
- **Authentication**: Bearer token (Customer/Mechanic/Admin)
- **Request Body**:
  ```json
  {
    "reason": "Found another mechanic",
    "feedback": "The service was too expensive"
  }
  ```
- **Response**:
  ```json
  {
    "status": "cancelled",
    "refund_amount": 4000,
    "refund_status": "pending",
    "message": "Booking has been cancelled. Refund will be processed within 3-5 business days."
  }
  ```

### 6. Rate Booking
- **Endpoint**: `POST /api/v1/bookings/{booking_id}/rate/`
- **Authentication**: Bearer token (Customer)
- **Request Body**:
  ```json
  {
    "rating": 5,
    "review": "Excellent service! The mechanic was very professional.",
    "aspects": {
      "punctuality": 5,
      "quality": 5,
      "communication": 4,
      "price_value": 4
    },
    "anonymous": false,
    "recommend": true
  }
  ```
- **Response**:
  ```json
  {
    "message": "Thank you for your feedback!",
    "rating_id": "rating-123"
  }
  ```

## Chat

### 1. Get Conversations
- **Endpoint**: `GET /api/v1/chat/conversations/`
- **Authentication**: Bearer token required
- **Query Parameters**:
  - `unread_only`: Boolean - Show only unread conversations
  - `limit`: Number - Number of conversations to return (default: 20)
  - `offset`: Number - Pagination offset
- **Response**:
  ```json
  {
    "conversations": [
      {
        "id": "conv-123",
        "type": "direct", // direct, group, support
        "title": "John's Auto Care",
        "last_message": {
          "id": "msg-456",
          "sender": {
            "id": "user-123",
            "name": "John Doe",
            "avatar": "https://dev.veyu.cc/media/avatars/john.jpg"
          },
          "content": "I'll be there in 15 minutes",
          "type": "text",
          "status": "delivered",
          "created_at": "2023-11-02T14:30:45Z"
        },
        "unread_count": 2,
        "is_online": true,
        "last_seen": "2023-11-02T14:32:10Z",
        "participants": [
          {
            "id": "user-123",
            "name": "John Doe",
            "role": "mechanic",
            "avatar": "https://dev.veyu.cc/media/avatars/john.jpg"
          },
          {
            "id": "user-456",
            "name": "Jane Smith",
            "role": "customer",
            "avatar": "https://dev.veyu.cc/media/avatars/jane.jpg"
          }
        ],
        "metadata": {
          "booking_id": "booking-123",
          "service_type": "Engine Repair",
          "status": "in_progress"
        },
        "created_at": "2023-11-01T10:15:30Z",
        "updated_at": "2023-11-02T14:30:45Z"
      }
    ],
    "unread_total": 5,
    "pagination": {
      "total": 15,
      "count": 10,
      "per_page": 10,
      "current_page": 1,
      "total_pages": 2
    }
  }
  ```

### 2. Get Conversation Messages
- **Endpoint**: `GET /api/v1/chat/conversations/{conversation_id}/messages/`
- **Authentication**: Bearer token required
- **Query Parameters**:
  - `before`: Message ID - Get messages before this ID
  - `after`: Message ID - Get messages after this ID
  - `limit`: Number - Messages per page (default: 50, max: 100)
- **Response**:
  ```json
  {
    "messages": [
      {
        "id": "msg-123",
        "conversation_id": "conv-123",
        "sender": {
          "id": "user-123",
          "name": "John Doe",
          "avatar": "https://dev.veyu.cc/media/avatars/john.jpg"
        },
        "content": "Hi Jane, I'm on my way to your location",
        "type": "text",
        "status": "read",
        "metadata": {
          "location": {
            "lat": 6.5244,
            "lng": 3.3792,
            "name": "Current Location"
          },
          "estimated_arrival": "15 minutes"
        },
        "created_at": "2023-11-02T14:15:30Z",
        "updated_at": "2023-11-02T14:15:30Z"
      },
      {
        "id": "msg-122",
        "conversation_id": "conv-123",
        "sender": {
          "id": "user-456",
          "name": "Jane Smith",
          "avatar": "https://dev.veyu.cc/media/avatars/jane.jpg"
        },
        "content": "Thanks John, I'll be waiting",
        "type": "text",
        "status": "delivered",
        "created_at": "2023-11-02T14:16:45Z",
        "updated_at": "2023-11-02T14:16:45Z"
      },
      {
        "id": "msg-121",
        "conversation_id": "conv-123",
        "sender": {
          "id": "system",
          "name": "System"
        },
        "content": "Mechanic is on the way",
        "type": "system",
        "metadata": {
          "event_type": "mechanic_en_route",
          "booking_id": "booking-123"
        },
        "created_at": "2023-11-02T14:10:00Z",
        "updated_at": "2023-11-02T14:10:00Z"
      }
    ],
    "has_more": true,
    "pagination": {
      "total": 42,
      "count": 20,
      "per_page": 20,
      "current_page": 1,
      "total_pages": 3
    }
  }
  ```

### 3. Send Message
- **Endpoint**: `POST /api/v1/chat/messages/`
- **Authentication**: Bearer token required
- **Request Body**:
  ```json
  {
    "conversation_id": "conv-123",
    "message": "I'll be there in 15 minutes",
    "type": "text", // text, image, location, file, system
    "metadata": {
      "location": {
        "lat": 6.5244,
        "lng": 3.3792,
        "name": "My Location"
      },
      "estimated_arrival": "15 minutes"
    },
    "reply_to": "msg-100", // Optional: Reply to a specific message
    "temporary_id": "temp-123" // Client-generated ID for tracking
  }
  ```
- **Response**:
  ```json
  {
    "id": "msg-124",
    "conversation_id": "conv-123",
    "sender": {
      "id": "user-123",
      "name": "John Doe",
      "avatar": "https://dev.veyu.cc/media/avatars/john.jpg"
    },
    "content": "I'll be there in 15 minutes",
    "type": "text",
    "status": "sent",
    "created_at": "2023-11-02T14:30:45Z",
    "updated_at": "2023-11-02T14:30:45Z",
    "temporary_id": "temp-123"
  }
  ```

### 4. Send Media Message
- **Endpoint**: `POST /api/v1/chat/messages/media/`
- **Authentication**: Bearer token required
- **Content-Type**: `multipart/form-data`
- **Request Body**:
  ```
  conversation_id: "conv-123"
  type: "image" // image, video, document, audio
  file: [binary file]
  caption: "Check this issue"
  ```
- **Response**: Same as text message with media URLs

### 5. Mark Messages as Read
- **Endpoint**: `POST /api/v1/chat/messages/mark-read/`
- **Authentication**: Bearer token required
- **Request Body**:
  ```json
  {
    "conversation_id": "conv-123",
    "message_ids": ["msg-121", "msg-122"]
  }
  ```
- **Response**:
  ```json
  {
    "conversation_id": "conv-123",
    "read_count": 2,
    "unread_count": 3
  }
  ```

### 6. Typing Indicator
- **Endpoint**: `POST /api/v1/chat/typing/`
- **Authentication**: Bearer token required
- **Request Body**:
  ```json
  {
    "conversation_id": "conv-123",
    "is_typing": true
  }
  ```
- **WebSocket Event**:
  ```json
  {
    "event": "typing",
    "conversation_id": "conv-123",
    "user": {
      "id": "user-123",
      "name": "John Doe"
    },
    "is_typing": true,
    "timestamp": "2023-11-02T14:35:20Z"
  }
  ```

### 7. Real-time Updates (WebSocket)
Connect to: `wss://dev.veyu.cc/ws/chat/?token=<jwt_token>`

**Events**:
- `message`: New message received
- `message_updated`: Message was updated
- `message_deleted`: Message was deleted
- `typing`: User is typing
- `conversation_updated`: Conversation details updated
- `user_online`: User came online
- `user_offline`: User went offline

**Example Message Event**:
```json
{
  "event": "message",
  "data": {
    "id": "msg-124",
    "conversation_id": "conv-123",
    "sender": {
      "id": "user-123",
      "name": "John Doe",
      "avatar": "https://dev.veyu.cc/media/avatars/john.jpg"
    },
    "content": "I'll be there in 15 minutes",
    "type": "text",
    "created_at": "2023-11-02T14:30:45Z"
  }
}
```

## Wallet

### Get Wallet Balance
- **Endpoint**: `GET /api/v1/wallet/balance/`
- **Authentication**: Bearer token required
- **Response**:
  ```json
  {
    "balance": 5000.00,
    "currency": "NGN"
  }
  ```

### Fund Wallet
- **Endpoint**: `POST /api/v1/wallet/fund/`
- **Authentication**: Bearer token required
- **Request Body**:
  ```json
  {
    "amount": 10000,
    "payment_method": "card",
    "card_details": {
      "number": "4111111111111111",
      "exp_month": 12,
      "exp_year": 2025,
      "cvv": "123"
    }
  }
  ```

## Feedback

### Submit Feedback
- **Endpoint**: `POST /api/v1/feedback/`
- **Authentication**: Bearer token required
- **Request Body**:
  ```json
  {
    "booking_id": "booking-uuid",
    "rating": 5,
    "comment": "Great service!",
    "anonymous": false
  }
  ```

## Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "error": true,
  "message": "Validation error",
  "errors": {
    "field_name": ["Error message"]
  }
}
```

#### 401 Unauthorized
```json
{
  "error": true,
  "message": "Authentication credentials were not provided."
}
```

#### 403 Forbidden
```json
{
  "error": true,
  "message": "You do not have permission to perform this action."
}
```

#### 404 Not Found
```json
{
  "error": true,
  "message": "Not found."
}
```

#### 500 Internal Server Error
```json
{
  "error": true,
  "message": "An unexpected error occurred."
}
```

## Rate Limiting
- Public endpoints: 100 requests per minute
- Authenticated endpoints: 1000 requests per minute
- Response headers:
  - `X-RateLimit-Limit`: Request limit
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time when limit resets (UTC timestamp)

## Webhooks
- **Endpoint**: `POST /api/v1/webhooks/payment/`
- **Headers**:
  - `X-Veyu-Signature`: HMAC signature
  - `X-Veyu-Event`: Event type

### Supported Events
- `payment.success`
- `payment.failed`
- `booking.completed`
- `booking.cancelled`

## Versioning
- Current API version: `v1`
- Version is included in the URL path
- Example: `/api/v1/endpoint`

## Support
For support, please contact:
- Email: support@veyu.cc
- Phone: +234 800 000 0000