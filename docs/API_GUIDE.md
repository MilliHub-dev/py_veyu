# Veyu API Documentation

## Overview

The Veyu API is a RESTful API that provides comprehensive access to the Veyu mobility platform. This API enables developers to integrate with Veyu's vehicle marketplace, mechanic services, real-time chat, and digital wallet functionality.

**Base URL:** `https://api.veyu.com/api/v1/`
**Authentication:** JWT Bearer Token
**Content-Type:** `application/json`

## Quick Start

### 1. Authentication

All API requests (except registration and login) require authentication using JWT tokens.

```bash
# Login to get tokens
curl -X POST https://api.veyu.com/api/v1/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "provider": "veyu"
  }'
```

### 2. Using Access Tokens

Include the access token in the Authorization header:

```bash
curl -X GET https://api.veyu.com/api/v1/listings/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Token Refresh

When your access token expires, use the refresh token:

```bash
curl -X POST https://api.veyu.com/api/v1/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

## API Endpoints

### Authentication & User Management

#### Register New User
**POST** `/accounts/register/`

Create a new user account on the Veyu platform.

**Request Body:**
```json
{
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "SecurePass123!",
  "confirm_password": "SecurePass123!",
  "user_type": "customer",
  "provider": "veyu",
  "phone_number": "+2348123456789"
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "Account created successfully",
  "data": {
    "user": {
      "id": 1,
      "email": "john.doe@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "user_type": "customer",
      "verified_email": false,
      "provider": "veyu"
    },
    "tokens": {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
  }
}
```

#### User Login
**POST** `/accounts/login/`

Authenticate user and receive JWT tokens.

**Request Body:**
```json
{
  "email": "john.doe@example.com",
  "password": "SecurePass123!",
  "provider": "veyu"
}
```

#### Update Profile
**PUT** `/accounts/update-profile/`

Update user profile information.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "phone_number": "+2348123456789",
  "bio": "Experienced automotive enthusiast"
}
```

#### Email Verification
**POST** `/accounts/verify-email/`

Verify user email with OTP code.

**Request Body:**
```json
{
  "email": "john.doe@example.com",
  "otp_code": "123456"
}
```

### Vehicle Listings

#### Get All Vehicles
**GET** `/listings/`

Retrieve paginated list of vehicle listings.

**Query Parameters:**
- `page` (int): Page number
- `page_size` (int): Items per page (max 50)
- `search` (string): Search query
- `make` (string): Vehicle make filter
- `model` (string): Vehicle model filter
- `year_min` (int): Minimum year
- `year_max` (int): Maximum year
- `price_min` (decimal): Minimum price
- `price_max` (decimal): Maximum price
- `condition` (string): new, used-foreign, used-local
- `available_for_sale` (boolean): Sale availability
- `available_for_rent` (boolean): Rental availability

**Response:**
```json
{
  "success": true,
  "data": {
    "count": 150,
    "next": "https://api.veyu.com/api/v1/listings/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "title": "2023 Toyota Camry LE",
        "make": "Toyota",
        "model": "Camry",
        "year": 2023,
        "price": "25000000.00",
        "condition": "new",
        "mileage": 0,
        "fuel_type": "Petrol",
        "transmission": "Automatic",
        "features": ["Air Conditioning", "Android Auto"],
        "images": [
          "https://api.veyu.com/media/vehicles/camry1.jpg"
        ],
        "dealer": {
          "id": 1,
          "business_name": "Toyota Lagos",
          "rating": 4.5
        },
        "available_for_sale": true,
        "available_for_rent": false
      }
    ]
  }
}
```

#### Create Vehicle Listing
**POST** `/listings/`

Create a new vehicle listing (dealers only).

**Request Body:**
```json
{
  "title": "2023 Toyota Camry LE",
  "make": "Toyota",
  "model": "Camry",
  "year": 2023,
  "price": "25000000.00",
  "condition": "new",
  "mileage": 0,
  "fuel_type": "Petrol",
  "transmission": "Automatic",
  "features": ["Air Conditioning", "Android Auto", "Keyless Entry"],
  "available_for_sale": true,
  "available_for_rent": false,
  "description": "Brand new Toyota Camry with all modern features"
}
```

#### Get Vehicle Details
**GET** `/listings/{id}/`

Get detailed information about a specific vehicle.

### Mechanic Services

#### Get Available Services
**GET** `/mechanics/services/`

Get list of available automotive services.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "Oil Change",
      "description": "Complete engine oil change service",
      "category": "maintenance"
    },
    {
      "id": 2,
      "title": "Brake Repair",
      "description": "Brake system inspection and repair",
      "category": "repair"
    }
  ]
}
```

#### Book Service
**POST** `/mechanics/book/`

Book a mechanic service.

**Request Body:**
```json
{
  "type": "routine",
  "mechanic_id": 1,
  "services": [1, 2, 3],
  "problem_description": "Car needs regular maintenance service",
  "preferred_date": "2024-01-15T10:00:00Z",
  "location": {
    "address": "123 Main Street, Lagos",
    "latitude": 6.5244,
    "longitude": 3.3792
  }
}
```

#### Get My Bookings
**GET** `/mechanics/bookings/`

Get user's service bookings.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "type": "routine",
      "customer": {
        "id": 1,
        "name": "John Doe"
      },
      "mechanic": {
        "id": 5,
        "name": "Auto Expert Services",
        "rating": 4.8
      },
      "services": [
        {
          "id": 1,
          "title": "Oil Change",
          "price": "5000.00"
        }
      ],
      "booking_status": "accepted",
      "created_at": "2024-01-10T10:30:00Z",
      "total_cost": "15000.00"
    }
  ]
}
```

### Digital Wallet

#### Get Wallet Balance
**GET** `/wallet/balance/`

Get current wallet balance and transaction summary.

**Response:**
```json
{
  "success": true,
  "data": {
    "wallet": {
      "id": 1,
      "ledger_balance": "50000.00",
      "available_balance": "45000.00",
      "currency": "NGN"
    },
    "locked_amount": "5000.00",
    "pending_transactions": 2
  }
}
```

#### Fund Wallet
**POST** `/wallet/fund/`

Add money to wallet using Paystack.

**Request Body:**
```json
{
  "amount": "10000.00",
  "email": "user@example.com"
}
```

#### Transfer Money
**POST** `/wallet/transfer/`

Transfer money between wallets.

**Request Body:**
```json
{
  "recipient_wallet_id": 2,
  "amount": "5000.00",
  "narration": "Payment for vehicle rental"
}
```

#### Withdraw Funds
**POST** `/wallet/withdraw/`

Withdraw money to bank account.

**Request Body:**
```json
{
  "amount": "20000.00",
  "payout_info_id": 1
}
```

#### Get Transaction History
**GET** `/wallet/transactions/`

Get paginated transaction history.

**Response:**
```json
{
  "success": true,
  "data": {
    "count": 25,
    "results": [
      {
        "id": 1,
        "amount": "10000.00",
        "type": "deposit",
        "status": "completed",
        "narration": "Wallet funding via Paystack",
        "created_at": "2024-01-10T14:30:00Z"
      }
    ]
  }
}
```

### Real-time Chat

#### Get Chat Rooms
**GET** `/chat/rooms/`

Get user's chat rooms.

#### Send Message
**POST** `/chat/rooms/{room_id}/messages/`

Send a message in a chat room.

**Request Body:**
```json
{
  "content": "Hello, I'm interested in your vehicle listing."
}
```

### Notifications

#### Get Notifications
**GET** `/accounts/notifications/`

Get user notifications.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "Booking Confirmed",
      "message": "Your service booking has been confirmed",
      "type": "booking",
      "read": false,
      "created_at": "2024-01-10T15:00:00Z"
    }
  ]
}
```

## Error Handling

All API endpoints return standardized error responses:

```json
{
  "success": false,
  "message": "Error description",
  "errors": {
    "field_name": ["Specific field error"]
  }
}
```

### Common HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid or missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error

## Rate Limiting

API requests are rate-limited:
- **Authenticated users:** 1000 requests per hour
- **Unauthenticated users:** 100 requests per hour

## Pagination

List endpoints support pagination:

```json
{
  "count": 150,
  "next": "https://api.veyu.com/api/v1/listings/?page=3",
  "previous": "https://api.veyu.com/api/v1/listings/?page=1",
  "results": []
}
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 50)

## WebSocket Connections

Real-time features use WebSocket connections:

```javascript
const socket = new WebSocket('wss://api.veyu.com/ws/chat/room_1/');
```

## SDKs and Libraries

- **JavaScript/Node.js:** `npm install veyu-sdk`
- **Python:** `pip install veyu-python`
- **PHP:** Available via Composer

## Support

- **Documentation:** https://docs.veyu.com
- **API Support:** api-support@veyu.com
- **Status Page:** https://status.veyu.com