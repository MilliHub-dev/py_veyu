# Veyu Customer API Documentation

## Base URL
```
https://dev.veyu.cc
```

## Authentication

### 1. Login
- **Endpoint**: `POST /api/v1/accounts/login/`
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "yourpassword"
  }
  ```
- **Response**: Returns `token` and user details.

### 2. Register
- **Endpoint**: `POST /api/v1/accounts/register/`
- **Request Body**:
  ```json
  {
    "action": "create-account",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!",
    "user_type": "customer",
    "provider": "veyu",
    "phone_number": "+2348012345678"
  }
  ```

### 3. Token Management
- **Get Token**: `POST /api/v1/token/` (Username/Password)
- **Refresh Token**: `POST /api/v1/token/refresh/`
- **Verify Token**: `POST /api/v1/token/verify/`

### 4. Password Reset
- **Request Reset**: `POST /api/v1/password-reset/`
  ```json
  { "email": "user@example.com" }
  ```
- **Confirm Reset**: `POST /api/v1/password-reset-confirm/<uidb64>/<token>/`
  ```json
  { "new_password": "..." }
  ```

---

## Accounts & Profile

### 1. User Profile
- **Get/Update Profile**: `GET/PUT /api/v1/accounts/profile/`
- **Payload (Update)**:
  ```json
  {
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+2348012345678",
    "location": 12  // Location ID
  }
  ```

### 2. Location Management
Manage your delivery addresses and locations.
- **List Locations**: `GET /api/v1/accounts/locations/`
- **Create Location**: `POST /api/v1/accounts/locations/`
- **Payload**:
  ```json
  {
    "country": "NG",
    "state": "Lagos",
    "city": "Ikeja",
    "address": "123 Allen Avenue",
    "zip_code": "100001",
    "lat": 6.6018,
    "lng": 3.3515,
    "google_place_id": "ChIJ..."
  }
  ```
- **Update Location**: `PUT /api/v1/accounts/locations/{id}/`
- **Delete Location**: `DELETE /api/v1/accounts/locations/{id}/`

---

## Dealership Management
Base Path: `/api/v1/admin/dealership/`

### 1. Dashboard
- **Overview**: `GET /dashboard/`
- **Analytics**: `GET /analytics/`

### 2. Listings Management
- **List Listings**: `GET /listings/`
- **Create Listing**: `POST /listings/create/`
- **Edit / Upload Media / Publish**: `POST /listings/{listing_id}/`
  - **Content-Type**: `multipart/form-data`
  - **Action: edit-listing**:
    ```json
    {
        "action": "edit-listing",
        "price": 5500000.00,
        "currency": "NGN",
        "description": "Updated description",
        "vehicle": {
            "mileage": 45000,
            "color": "Black",
            "body_type": "SUV"
        }
    }
    ```
  - **Action: upload-images**:
    - `action`: "upload-images"
    - `image`: [File1, File2] (Array of files)
  - **Action: upload-video**:
    - `action`: "upload-video"
    - `video`: File (Single video file, max 50MB)
  - **Action: remove-image**:
    ```json
    {
        "action": "remove-image",
        "image_id": "uuid-of-image"
    }
    ```
  - **Action: publish-listing**:
    ```json
    {
        "action": "publish-listing",
        "listing": "uuid-of-listing"
    }
    ```

---

## Chat & Messaging
Base Path: `/api/v1/chat/`

### 1. Chat Rooms
- **List Chat Rooms**: `GET /chats/`
- **Create/Get Room**: `GET /start-chat/{recipient_uuid}/`
  - Creates a new room or returns existing one between current user and recipient.

### 2. Messages
- **Get Messages**: `GET /room/{room_uuid}/`
- **Send Message**: `POST /send/`
  - **Payload**:
    ```json
    {
      "room_id": "uuid-of-room", // Optional if room_uuid is in URL context
      "message": "Hello, is this car still available?",
      "attachments": [File1, File2] // Optional files
    }
    ```

---

## Marketplace (Buy & Rent)
Base Path: `/api/v1/listings/`

### 1. Search & Browse
- **All Listings**: `GET /`
- **Search**: `GET /find/?brand=Toyota&price_min=5000000&body_type=suv`
- **Featured**: `GET /featured/`
- **Rentals**: `GET /rentals/`
- **Dealership Profile**: `GET /dealer/{uuid}/`

### 2. Listing Details
- **Buy Detail**: `GET /buy/{uuid}/`
- **Rent Detail**: `GET /rentals/{uuid}/`

### 3. Shopping Cart
- **Get Cart**: `GET /api/v1/accounts/cart/`
- **Add to Cart**: `POST /api/v1/accounts/cart/`
  ```json
  {
    "action": "add-to-cart",
    "listing_id": "uuid"
  }
  ```
- **Remove from Cart**: `POST /api/v1/accounts/cart/`
  ```json
  {
    "action": "remove-from-cart",
    "item": "uuid"
  }
  ```

### 4. User Dashboard
- **Personalized Feed**: `GET /my-listings/?scope=recents;top-deals`
- **My Orders**: `GET /my-orders/`
- **Cancel Order**: `POST /orders/{order_id}/cancel/`

### 5. Checkout
- **Initiate Checkout**: `POST /api/v1/listings/checkout/{listingId}/`
  - **Response**:
    ```json
    {
      "listing_price": 5000000,
      "fees": {
        "tax": 375000,
        "inspection_fee": 50000,
        "service_fee": 25000
      },
      "total": 5450000,
      "inspection_status": {
        "paid": false,
        "can_proceed": false
      }
    }
    ```
- **Book Inspection**: `POST /api/v1/listings/checkout/inspection/`

---

## Chat & Messaging
Base Path: `/api/v1/chat/`

- **List Chats**: `GET /chats/`
- **Get Messages**: `GET /chats/{room_id}/`
- **Send Message**: `POST /message/`
  ```json
  {
    "room_id": "uuid", // Optional if new chat
    "message": "Hello, is this available?",
    // If new chat:
    "other_member": "dealer", // or "mechanic"
    "dealer_id": "uuid" 
  }
  ```

---

## Mechanic Services
Base Path: `/api/v1/bookings/`

### 1. Find Mechanics
- **Search**: `GET /find/?service=Oil Change&location=Lagos`
- **Profile**: `GET /{mech_id}/`
- **Service History**: `GET /{mech_id}/history/`

### 2. Booking
- **Request Service**: `POST /{mech_id}/`
  ```json
  {
    "transaction_id": "...", 
    "problem_description": "Car won't start",
    "services": ["Diagnosis"]
  }
  ```
- **Update Booking**: `PUT /bookings/{booking_id}/`

---

## Wallet & Payments
Base Path: `/api/v1/wallet/`

### 1. Overview
- **Wallet Balance & Info**: `GET /`
- **Transaction History**: `GET /transactions/`
- **Transaction Summary**: `GET /transactions/summary/`
- **Analytics**: `GET /analytics/`

### 2. Actions
- **Transfer**: `POST /transfer/`
  ```json
  {
    "amount": 5000,
    "recipient_account_number": "1234567890",
    "bank_code": "058",
    "pin": "1234"
  }
  ```
- **Deposit**: `POST /deposit/`
- **Withdraw**: `POST /withdraw/`
  ```json
  {
    "amount": 50000,
    "account_number": "0123456789",
    "account_name": "John Doe",
    "bank_code": "058"
  }
  ```

### 3. Utilities
- **Get Banks**: `GET /banks/`
- **Get Transfer Fees**: `GET /transfer-fees/`
- **Verify Account**: `POST /resolve-account/`

---

## Inspections
Base Path: `/api/v1/inspections/`

- **List/Create Inspections**: `GET/POST /`
- **Get Quote**: `POST /quote/`
- **Inspection Detail**: `GET /{id}/`
- **Pay for Inspection**: `POST /{id}/pay/`
  - **Note**: Supports Paystack. Returns payment reference and callback URL.
- **Verify Payment**: `POST /{id}/verify-payment/`
  ```json
  { "reference": "veyu-inspection-..." }
  ```
- **Slips**:
  - **Retrieve**: `GET /slips/{slip_number}/`
  - **Verify**: `POST /slips/verify/`
  - **Regenerate**: `POST /{id}/regenerate-slip/`

---

## Support & Feedback
Base Path: `/api/v1/support/`

- **List Tickets**: `GET /tickets/`
- **Create Ticket**: `POST /tickets/`
  ```json
  {
    "subject": "Payment Issue",
    "description": "I was charged twice.",
    "category": "uuid",
    "priority": "high"
  }
  ```
- **Ticket Detail**: `GET /tickets/{id}/`
- **Get Notifications**: `GET /api/v1/accounts/notifications/`
