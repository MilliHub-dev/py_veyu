## Veyu REST API

Base URL: https://dev.veyu.cc

- All JSON bodies must be UTF-8 encoded and sent with header: `Content-Type: application/json` unless noted.
- Authentication: Bearer JWT in `Authorization: Bearer <token>` unless an endpoint is marked public. Session and cookie-based auth are also enabled, but JWT is recommended.
- Pagination: When a list endpoint uses pagination, pass `per_page` and `offset`. Responses include a `data.pagination` object with `offset`, `limit`, `count`, `next`, `previous`.

### Authentication and Sessions

- Issue access tokens (JWT)
  - POST /api/v1/token/
  - POST /api/v1/token/refresh/
  - POST /api/v1/token/verify/
- Password reset
  - POST /api/v1/password-reset/
  - GET  /api/v1/password-reset-confirm/<uidb64>/<token>/

Example request (get token):

```bash
curl -X POST https://dev.veyu.cc/api/v1/token/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"john@example.com","password":"Secret123!"}'
```

Response
```json
{"refresh":"<refresh>","access":"<access>"}
```

Notes
- The platform also exposes `dj_rest_auth` under `/api/v1/accounts/auth/` for session-based flows.

### Conventions

- Common wrapper: most endpoints return `{ error: boolean, message?: string, data?: any }`.
- Errors: on validation errors, endpoints typically return `{ error: true, message: string }` with 4xx status.

---

## Accounts API

Namespace: /api/v1/accounts/

### POST /api/v1/accounts/register/
- Auth: Public
- Body (create account):
```json
{
  "action": "create-account",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "password": "SecurePass123!",
  "provider": "veyu",
  "user_type": "customer",
  "phone_number": "+2348012345678"
}
```
- Body (setup business profile, after login):
```json
{
  "action": "setup-business-profile",
  "user_type": "mechanic", // or "dealer"
  "logo": "<file or URL>",
  "about": "...",
  "headline": "...",
  "contact_email": "biz@example.com",
  "contact_phone": "+2348000000000",
  "business_name": "Acme Motors",
  "business_type": "workshop", // mechanics only
  "services": ["Car Sale", "Car Leasing", "Drivers"], // dealers only, determines offers_*
  "location": {
    "lat": 6.5244,
    "lng": 3.3792,
    "country": "NG",
    "state": "Lagos",
    "city": "Ikeja",
    "street_address": "...",
    "zip_code": "100271",
    "place_id": "..."
  }
}
```
- Responses: returns `{ error, data: { token, ...account } }` on success

GET /api/v1/accounts/register/?email=<email>
- Checks if an email already exists
- Response: `{ error: false, message: "Email OK" }` or 400/409

### POST /api/v1/accounts/login/
- Auth: Public
- Body:
```json
{ "email": "john@example.com", "password": "Secret123!", "provider": "veyu" }
```
- Response includes `token` and basic user info; for dealers/mechanics includes their profile IDs.

### PUT /api/v1/accounts/update-profile/
- Auth: Bearer
- Body: fields depend on `user_type` (customer, mechanic, dealer); typical profile fields include names, contact info, etc.
- Response: updated profile object

### POST /api/v1/accounts/verify-email/
- Auth: Bearer
- Body (request code): `{ "action": "request-code", "email": "john@example.com" }`
- Body (confirm): `{ "action": "confirm-code", "email": "john@example.com", "code": "123456" }`

### POST /api/v1/accounts/verify-phone-number/
- Auth: Bearer
- Body (request code): `{ "action": "request-code", "phone_number": "+2348012345678" }`
- Body (confirm): `{ "action": "confirm-code", "phone_number": "+2348012345678", "code": "123456" }`

### POST /api/v1/accounts/verify-business/
- Auth: Bearer
- Body:
```json
{
  "object": "dealership", // or "mechanic"
  "object_id": "<uuid>",
  "verification_ref": "provider-ref",
  "scope": ["user.verified_email", "verified_id", "verified_business", "verified_tin"]
}
```

### GET /api/v1/accounts/cart/
- Auth: Bearer (customer)
- Response includes cars, rentals, bookings, orders

### POST /api/v1/accounts/cart/
- Auth: Bearer (customer)
- Body: `{ "action": "remove-from-cart", "item": "<listing-uuid>" }`

### GET /api/v1/accounts/notifications/
- Auth: Bearer
- Returns unread notifications

### POST /api/v1/accounts/notifications/
- Auth: Bearer
- Body: `{ "notification_id": "<uuid>" }` marks one as read, returns remaining unread

Other routes
- `accounts/` and `auth/` under this namespace expose Django and dj_rest_auth defaults.

---

## Mechanics (Customer-facing)

Namespace: /api/v1/mechanics/

### GET /
- Auth: Optional
- Query params:
  - Filtering: `available`, `verified_phone_number`, `verified_email`
  - Discovery: `lat`, `lng` (prioritizes mechanics within ~30km)
  - Pagination: `per_page`, `offset`
- Response: `{ error, data: { pagination, results: [Mechanic] } }`

### GET /find/
- Auth: Optional
- Query: `find` (name/service search), plus standard pagination

### GET /<mech_id>/
- Auth: Bearer
- Returns mechanic profile

### POST /<mech_id>/
- Auth: Bearer (customer)
- Description: Create a booking after a successful card payment
- Body:
```json
{
  "transaction_id": "<paystack/processor-ref>",
  "problem_description": "Car won’t start",
  "services": ["Oil Change", "Inspection"]
}
```
- Response: booking summary

### GET /<mech_id>/history/
- Auth: Bearer
- Returns completed jobs for the mechanic

### GET /bookings/<booking_id>/
### POST /bookings/<booking_id>/
- Auth: Bearer (mechanic only)
- POST actions: `accept`, `complete`, `decline`, `respond`
- Body: `{ "action": "accept" }`

---

## Mechanics Admin

Namespace: /api/v1/admin/mechanics/

### GET /
- Auth: Bearer (mechanic)
- Returns mechanic overview

### GET /dashboard/
- Auth: Bearer (mechanic)
- Returns stats: current_job, history, pending requests

### GET /analytics/
- Auth: Bearer (mechanic)
- Returns revenue/jobs analytics (chart datasets)

### GET /bookings/
### POST /bookings/
- Auth: Bearer (mechanic)
- POST actions: `start-job`, `complete-job`, `cancel-job`

### GET /services/
- Auth: Bearer (mechanic)
- Returns current service offerings

### POST /services/
- Auth: Bearer (mechanic)
- Body: `{ "action": "make-active" }` or `{ "action": "make-inactive" }`

### GET /services/add/
- Auth: Bearer (mechanic)
- Lists base service catalog

### POST /services/add/
- Auth: Bearer (mechanic)
- Body:
```json
{ "title": "Inspection", "charge": 10000, "charge_rate": "flat" }
```

### GET /settings/
### POST /settings/
- Auth: Bearer (mechanic)
- POST body (multipart or JSON):
```json
{
  "business_name": "Acme Mechanics",
  "about": "...",
  "headline": "Reliable Services",
  "cac_number": "...",
  "tin_number": "...",
  "contact_email": "biz@example.com",
  "contact_phone": "+2348000000000",
  "new-logo": "<file>"
}
```

---

## Listings (Marketplace)

Namespace: /api/v1/listings/

### GET /buy/
- Auth: Optional
- Filters (CarSaleFilter):
  - `brands` (comma list)
  - `condition`, `type`, `transmission`, `fuel_system`, `model`
  - `price` formatted as `min-max` (e.g., `1500000-5000000`)
  - `location`, `mileage`
- Pagination: `per_page`, `offset`

### GET /find/
- Auth: Optional
- Query: `find` (free-text on name/brand/services), plus pagination

### GET /rentals/
- Auth: Optional
- Filters (CarRentalFilter): `make`, `type`, `transmission`, `fuel_system`, `model`, `price` (min-max), `location`, `mileage`
- Pagination supported

### GET /dealer/<uuid>/ or /dealer/<slug>/
- Auth: Bearer
- Returns a dealership profile

### GET /my-listings/?scope=recents;top-deals;favorites
- Auth: Bearer
- Returns requested collections. Supported scope items: `recents`, `favorites`, `top-deals`.

### GET /buy/<uuid>/
- Auth: Bearer
- Returns listing and recommended listings

### POST /buy/<uuid>/
- Auth: Bearer (customer)
- Body:
```json
{ "action": "add-to-cart" }
```
or
```json
{ "action": "buy-now" }
```

### GET /rentals/<uuid>/
- Auth: Optional
- Returns rental listing details + recommendations

### GET /checkout/<uuid:listingId>/
- Auth: Bearer
- Returns pricing breakdown and fees

### POST /checkout/<uuid:listingId>/
- Auth: Bearer
- Body:
```json
{ "payment_option": "card" }
```
- Response: order object; also marks vehicle unavailable

### POST /checkout/inspection/
- Auth: Bearer
- Body:
```json
{ "listing_id": "<uuid>", "date": "20/12/2025", "time": "14:00" }
```

### GET /checkout/documents/?doc_type=order-slip&order_id=<listing-uuid>
- Auth: Bearer
- Generates a PDF document, returns `{ file_id, url }`

### POST /checkout/documents/
- Auth: Bearer
- Body (sign document):
```json
{ "file_id": "<uuid>", "signature": "data:image/png;base64,<...>" }
```

---

## Dealership Admin

Namespace: /api/v1/admin/dealership/

### GET /
- Auth: Bearer (dealer)
- Returns dealership profile

### GET /dashboard/
- Auth: Bearer (dealer)
- Summary metrics and recent orders

### GET /orders/
- Auth: Bearer (dealer)
- Returns dealer orders

### GET /listings/
- Auth: Bearer (dealer)
- Returns dealer listings

### POST /listings/
- Auth: Bearer (dealer)
- Body:
```json
{ "action": "delete", "listing": "<uuid>" }
```
or `{ "action": "publish" | "unpublish", "listing": "<uuid>" }`

### POST /listings/create/
- Auth: Bearer (dealer)
- Multipart/JSON. Supported actions:
  - `create-listing` (create `Vehicle` + `Listing`)
  - `upload-images` (field name: `image`, multiple)
  - `publish-listing`
- Create listing payload (minimum):
```json
{
  "listing_type": "sale", // or "rental"
  "title": "Toyota Corolla 2018",
  "price": 5500000,
  "vehicle_type": "sedan",
  "brand": "Toyota",
  "model": "Corolla",
  "condition": "used",
  "transmission": "automatic",
  "fuel_system": "petrol",
  "drivetrain": "fwd",
  "mileage": 45000,
  "seats": 5,
  "doors": 4,
  "vin": "...",
  "payment_cycle": "monthly" // rentals only
}
```

### GET /listings/<uuid:listing_id>/
- Auth: Bearer (dealer)

### POST /listings/<uuid:listing_id>/
- Auth: Bearer (dealer)
- Actions:
  - `edit-listing` (update listing + vehicle fields)
  - `upload-images` (add images)
  - `remove-image` (with `image_id`)
  - `publish-listing`

### DELETE /listings/<uuid:listing_id>/
- Auth: Bearer (dealer)

### GET /settings/
### POST /settings/
- Auth: Bearer (dealer)
- Body similar to mechanics settings; supports `new-logo` file

### GET /analytics/
- Auth: Bearer (dealer)
- Returns `revenue`, `sales`, `orders` metrics and chart datasets

---

## Chat API

Namespace: /api/v1/chat/

### GET /chats/
- Auth: Bearer
- Returns chat room list with last message and recipient overview

### GET /chats/<room_id>/
- Auth: Bearer
- Returns a chat room with messages and members

### POST /message/
- Auth: Bearer
- Body (start or continue chat):
```json
{
  "other_member": "dealer" | "mechanic" | "customer",
  "dealer_id": "<uuid>",   // if other_member == dealer
  "mechanic_id": "<uuid>", // if other_member == mechanic
  "customer_id": "<uuid>", // if other_member == customer
  "message": "Hello there!"
}
```

### POST /new/
- Auth: Bearer
- Body: `{ "recipient": "<account-uuid>", "message": "Hi" }`

---

## Wallet API

Namespace: /api/v1/wallet/

### GET /
- Auth: Bearer
- Returns wallet summary

### GET /balance/
- Auth: Bearer
- Returns `{ ledger_balance, balance, currency, id }`

### GET /transactions/
- Auth: Bearer
- Returns wallet transactions

### POST /transfer/
- Auth: Bearer
- Body:
```json
{ "recipient": "recipient@example.com", "amount": 2500.00 }
```

### POST /deposit/
- Auth: Bearer
- Body:
```json
{
  "status": "success",
  "tx_ref": "<provider-tx-ref>",
  "reference": "<provider-reference>",
  "currency": "NGN",
  "amount": 5000
}
```
- On success, credits wallet and records a `deposit` transaction

### POST /withdraw/
- Auth: Bearer
- Body:
```json
{
  "account_number": "0123456789",
  "bank_code": "044",
  "account_name": "John Doe",
  "amount": 2500.00
}
```

---

## Utilities & Webhooks

Namespace: varies; base utils router is included at root

### POST /emailer/
- Auth: Internal use
- Body:
```json
{
  "template_name": "welcome_email",
  "recipients": ["to@example.com"],
  "context": {"name": "John"},
  "subject": "Welcome"
}
```

### POST /hooks/payment-webhook/
- Auth: Provider signed (Paystack). Header `X-Paystack-Signature`
- Body: Paystack event payload. Events include `charge.success`, `transfer.successful` etc. Validates signature and processes accordingly.

### POST /hooks/verification/
- Auth: Provider signed (Dojah/KYC). For verification callbacks.

---

## Query Parameters & Pagination

- Pagination params: `per_page`, `offset`.
- Mechanic filters (on `/api/v1/mechanics/` and `/find/`):
  - `available`, `verified_phone_number`, `verified_email`
  - `services` as comma-separated titles (e.g., `services=Oil%20Change,Inspection`)
  - `lat`, `lng` to sort/limit by proximity (~30km)
- Listing filters `/api/v1/listings/buy/`:
  - `brands`, `condition`, `type`, `transmission`, `fuel_system`, `model`, `price=min-max`, `location`, `mileage`
- Listing filters `/api/v1/listings/rentals/`:
  - `make`, `type`, `transmission`, `fuel_system`, `model`, `price=min-max`, `location`, `mileage`

---

## Authentication Details

Headers
- `Authorization: Bearer <access_token>`

Acquiring tokens
- Use `/api/v1/accounts/login/` to get an `api_token` field for legacy flows, or the JWT endpoints under `/api/v1/token/*` for Bearer JWT.

---

## Response Shapes (Examples)

Paginated list (mechanics, listings):
```json
{
  "error": false,
  "message": "",
  "data": {
    "pagination": {
      "offset": 0,
      "limit": 25,
      "count": 120,
      "next": "https://dev.veyu.cc/api/v1/...&offset=25",
      "previous": null
    },
    "results": [ { /* item */ } ]
  }
}
```

Error example
```json
{ "error": true, "message": "Invalid credentials" }
```

---

## Notes & Gotchas

- Certain admin routes require specific roles (Dealer vs Mechanic). Ensure the authenticated user’s `user_type` matches.
- For bookings, customer must complete payment with the gateway and submit the `transaction_id` in the booking request.
- Document generation/signing returns a `file_id` and a signed `url` for download.

