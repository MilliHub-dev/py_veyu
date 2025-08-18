## Veyu Platform API Documentation

Base URL: https://dev.veyu.cc

Versioned API Base: https://dev.veyu.cc/api/v1

### Authentication
- Most protected endpoints accept token authentication.
- Send header: Authorization: Token YOUR_API_TOKEN
- You can obtain YOUR_API_TOKEN from the Accounts Login or Register endpoints.
- Some endpoints also support session/JWT auth (Simple JWT endpoints are exposed), but Token is the primary method across views.

### Pagination
- Offset-based pagination is used on list endpoints via `OffsetPaginator`.
- Query params:
  - per_page: number of items per page (default 25)
  - offset: number of items to skip (default 0)

### Common Response Envelope
Unless otherwise noted, successful responses use the following structure:
{
  "error": false,
  "message": "",
  "data": { ... }
}

### Rate Limiting
No explicit rate limit headers are provided by the API at this time.

### Errors
- 400: Bad Request (validation or input errors)
- 401: Unauthorized (missing/invalid auth)
- 403: Forbidden (insufficient permissions/funds)
- 404: Not Found
- 500: Internal Server Error

### API Explorer
- Swagger UI: https://dev.veyu.cc/api/docs/
- Redoc: https://dev.veyu.cc/redoc/

## Auth and Accounts
Base: https://dev.veyu.cc/api/v1/accounts/

#### POST login/
- Auth: Public
- Body:
  - email: string
  - password: string
  - provider: string (default: "veyu"; one of: veyu, google, apple, facebook)
- Response 200:
{
  "id": number,
  "email": string,
  "token": string,
  "first_name": string,
  "last_name": string,
  "user_type": "customer|mechanic|dealer",
  "provider": string,
  "is_active": boolean,
  "dealerId"?: string,
  "verified_id"?: boolean,
  "verified_business"?: boolean,
  "mechanicId"?: string
}

#### POST register/
- Auth: Public
- Usage 1: create-account
  - Content-Type: multipart/form-data or application/json
  - Body:
    - action: "create-account"
    - email, first_name, last_name, user_type (customer|mechanic|dealer), provider (default veyu)
    - password: required when provider = veyu
    - phone_number: optional (customers)
- Usage 2: setup-business-profile (after authentication)
  - Auth required; Content-Type: multipart/form-data
  - Body (depends on user_type):
    - action: "setup-business-profile"
    - user_type: mechanic|dealer
    - logo: file
    - about, headline, business_name, contact_email, contact_phone
    - mechanic-only: business_type (business|individual)
    - dealer-only: services: array of strings including any of ["Car Sale","Car Leasing","Drivers"]
    - location: JSON string with fields { lat, lng, country, state, city, street_address, zip_code, place_id }
- Response 201: { error: false, data: { token, ...user fields... } } or business profile object

#### POST verify-email/
- Auth: Required
- Body (two-step flow):
  - action: "request-code" and email
  - action: "confirm-code", email, code
- Response: { error: false, message }

#### POST verify-phone-number/
- Auth: Required
- Body:
  - action: "request-code" and phone_number
  - action: "confirm-code" and code
- Response: { error: false, message }

#### POST verify-business/
- Auth: Required
- Body:
  - object: "dealership" | "mechanic"
  - object_id: UUID
  - verification_ref: string
  - scope: array of strings, any of ["user.verified_email","verified_id","verified_business","verified_tin"]
- Response: { error: false, message: "Verification Successful" }

#### PUT update-profile/
- Auth: Required
- Body: profile fields depend on user_type (customer|mechanic|dealer). Send only fields you wish to update.
- Response: updated profile object

#### GET cart/
- Auth: Required
- Response data contains:
  - cars: Listing[] (for sale)
  - rentals: Listing[] (for rent)
  - bookings: ServiceBooking[]
  - orders: Order[]

#### POST cart/
- Auth: Required
- Body:
  - action: "remove-from-cart"
  - item: UUID of listing
- Response: { error: false, message }

#### GET notifications/
- Auth: Required
- Response: { error: false, data: Notification[] (unread) }

#### POST notifications/
- Auth: Required
- Body: { notification_id: UUID }
- Response: { error: false, data: Notification[] (remaining unread) }

### Password Reset (dj-rest-auth)
Base: https://dev.veyu.cc/api/v1/
- POST password-reset/ { email }
- POST password-reset-confirm/<uidb64>/<token>/ with form payload required by dj-rest-auth

### Simple JWT
Base: https://dev.veyu.cc/api/v1/
- POST token/
- POST token/refresh/
- POST token/verify/

## Listings (Customer)
Base: https://dev.veyu.cc/api/v1/listings/

#### GET buy/
- Auth: Optional
- Filters (query):
  - brands: comma-separated, e.g. brands=Toyota,Honda
  - condition: enum (new, used-foreign, used-local)
  - type: vehicle type(s), comma-separated
  - transmission: comma-separated
  - fuel_system: comma-separated
  - model: string
  - price: price range in the form min-max, e.g. price=1000000-15000000
  - location: string
  - mileage: range (not currently implemented)
- Pagination: per_page, offset
- Response: paginated { results: Listing[] }

#### GET rentals/
- Auth: Optional
- Filters (query): same style as `buy/` (uses rental filterset)
- Pagination: per_page, offset
- Response: paginated { results: Listing[] }

#### GET find/?find=free-text
- Auth: Optional
- Response: paginated { results: Listing[] }

#### GET dealer/<uuid>/
#### GET dealer/<slug>/
- Auth: Required
- Response: { error: false, data: Dealer }

#### GET my-listings/?scope=recents;favorites;top-deals
- Auth: Required
- Response keys vary by scope (recents, top_deals.sales, top_deals.rentals)

#### GET buy/<uuid>/
- Auth: Required
- Response: { listing: Listing, recommended: Listing[] }

#### POST buy/<uuid>/
- Auth: Required
- Body:
  - action: "add-to-cart" | "buy-now"
- Response: { error: false, message }

#### GET rentals/<uuid>/
- Auth: Optional
- Response: { listing: Listing, recommended: Listing[] }

#### GET checkout/<uuid:listingId>/
- Auth: Required
- Response: fee breakdown and selected listing

#### POST checkout/<uuid:listingId>/
- Auth: Required
- Body:
  - payment_option: "card" | "transfer" | "cash" (card marks order paid=true)
- Side effects: marks vehicle unavailable; associates order to customer and dealer
- Response: { error: false, message, data: Order }

#### POST checkout/inspection/
- Auth: Required
- Body:
  - listing_id: UUID
  - date: string (DD/MM/YYYY)
  - time: string (e.g. "14:00")
- Response: { error: false, data: "Inspection Scheduled" }

#### GET checkout/documents/?doc_type=order-slip&order_id=<uuid>
- Auth: Required
- Response: { file_id: UUID, url: absolute_url_to_pdf }

#### POST checkout/documents/
- Auth: Required
- Body:
  - file_id: UUID (from GET)
  - signature: data URL (e.g. data:image/png;base64,....)
- Response: { file_id, url }

## Mechanics (Customer-facing)
Base: https://dev.veyu.cc/api/v1/mechanics/

#### GET /
- Auth: Optional
- Query:
  - lat: number, lng: number (optional; used for proximity and distance field)
  - Filters (from MechanicFilter):
    - available: boolean
    - verified_phone_number: boolean
    - verified_email: boolean
    - services: comma-separated service titles
    - rating, location (reserved)
- Pagination: per_page, offset
- Response: paginated { results: Mechanic[] }

#### GET find/?find=term
- Auth: Optional
- Response: paginated { results: Mechanic[] }

#### GET <mech_id>/
- Auth: Required
- Response: { error: false, data: Mechanic }

#### POST <mech_id>/ (create service booking)
- Auth: Required
- Body:
  - problem_description: string
  - services: string[] (titles of services offered by mechanic)
  - transaction_id: string (payment gateway transaction reference)
- Response: { error: false, message, data: ServiceBooking }

#### GET <mech_id>/history/
- Auth: Required
- Response: { error: false, data: ServiceBooking[] (completed jobs) }

#### GET bookings/<booking_id>/
- Auth: Mechanic only
- Response: { error: false, data: BookingDetail }

#### POST bookings/<booking_id>/ (update booking)
- Auth: Mechanic only
- Body: action: one of ["accept","complete","decline","respond"]
- Response: { error: false, data: BookingDetail }

## Mechanics Admin (Mechanic dashboard)
Base: https://dev.veyu.cc/api/v1/admin/mechanics/

#### GET /
- Auth: Mechanic required
- Response: mechanic overview

#### GET dashboard/
- Auth: Mechanic required
- Response: metrics, current_job, booking_history, pending_requests

#### GET analytics/
- Auth: Mechanic required
- Response: revenue chart data and job counts

#### GET bookings/
- Auth: Mechanic required
- Response: { bookings: { history: ServiceBooking[], requests: ServiceBooking[] } }

#### POST bookings/<booking_id>/
- Auth: Mechanic required
- Body: action: "accept" | "complete" | "decline" | "respond" | "start-job"
- Response: updated booking

#### GET services/
- Auth: Mechanic required
- Response: list of service offerings for the mechanic

#### POST services/add/
- Auth: Mechanic required
- Body: { title: string, charge: number, charge_rate: string }
- Response: created service offering summary

#### GET settings/
- Auth: Mechanic required
- Response: mechanic profile

#### POST settings/
- Auth: Mechanic required; Content-Type: multipart/form-data
- Body: one or more of: business_name, about, headline, cac_number, tin_number, contact_email, contact_phone, new-logo (file)
- Response: updated mechanic profile

## Dealership Admin (Dealer dashboard)
Base: https://dev.veyu.cc/api/v1/admin/dealership/

#### GET /
- Auth: Dealer required
- Response: dealership profile

#### GET dashboard/
- Auth: Dealer required
- Response: revenue, impressions, recent_orders, chart_data

#### GET analytics/
- Auth: Dealer required
- Response: revenue and sales charts; order summary

#### GET orders/
- Auth: Dealer required
- Response: Order[]

#### GET listings/
- Auth: Dealer required
- Response: Listing[] for this dealer

#### POST listings/
- Auth: Dealer required
- Body:
  - action: "delete" | "unpublish" | "publish"
  - listing: UUID
- Response: { error: false, message }

#### POST listings/create/
- Auth: Dealer required; Content-Type: multipart/form-data
- Usage 1: create-listing
  - Body fields: listing_type (sale|rental), title, price, brand, model, condition, vehicle_type, transmission, fuel_system, drivetrain, seats, doors, vin, mileage (optional), features (rental), payment_cycle (rental)
- Usage 2: upload-images
  - Body: action="upload-images", listing: UUID, image: file[] (multiple)
- Usage 3: publish-listing
  - Body: action="publish-listing", listing: UUID
- Response: { error: false, message, data: Listing }

#### GET listings/<uuid:listing_id>/
- Auth: Dealer required
- Response: Listing

#### POST listings/<uuid:listing_id>/
- Auth: Dealer required
- Actions:
  - edit-listing: update listing + nested vehicle fields
  - upload-images: image: file[]
  - remove-image: image_id: UUID
  - publish-listing: listing: UUID
- Response: { error: false, message, data: Listing }

#### DELETE listings/<uuid:listing_id>/
- Auth: Dealer required
- Response: 200 on success

#### GET settings/
- Auth: Dealer required
- Response: Dealer settings snapshot

#### POST settings/
- Auth: Dealer required; Content-Type: multipart/form-data
- Body: business_name, about, headline, services (array of strings), contact_phone, contact_email, slug (optional), new-logo (file)
- Response: updated dealer profile

## Wallet
Base: https://dev.veyu.cc/api/v1/wallet/

#### GET /
- Auth: Required
- Response: wallet overview with balances and transactions

#### GET balance/
- Auth: Required
- Response: { ledger_balance, balance, currency, id }

#### GET transactions/
- Auth: Required
- Response: { transactions: Transaction[] }

#### POST transfer/
- Auth: Required
- Body: { recipient: email, amount: decimal string >= 100.00 }
- Responses:
  - 200: "<amount> transferred to <recipient> successfully"
  - 403: { error: "Insufficient funds" }

#### POST deposit/
- Auth: Required
- Body (as sent back from gateway webhook/confirmation step):
  - status: string (e.g. "success")
  - tx_ref: string
  - reference: string (gateway reference)
  - currency: string (e.g. NGN)
  - amount: string/number
- Response 200: { error: false, message: "Deposit successfully received!", transaction: Transaction }

#### POST withdraw/
- Auth: Required
- Body: { amount, account_number, account_name, bank_code }
- Responses:
  - 200: gateway response JSON
  - 403: { error: "Insufficient funds" }
  - 400: validation errors

## Chat
Base: https://dev.veyu.cc/api/v1/chat/

#### GET chats/
- Auth: Required
- Response: { data: [{ uuid, id, last_message: { message, date }, recipient: { name, image } }] }

#### GET chats/<room_id>/
- Auth: Required
- Response: { data: ChatRoom (members, messages[], etc.) }

#### POST message/
- Auth: Required
- Body (two modes):
  1) Create or reuse 1:1 room by other member type
     - other_member: "dealer" | "mechanic" | "customer"
     - dealer_id | mechanic_id | customer_id: UUID (depending on type)
     - message: string
  2) To existing room (if supported by backend)
     - room_id: UUID
     - message: string
- Response: { error: false, message: "Message sent!" }

#### POST new/
- Auth: Required
- Body: { recipient: Account UUID, message: string }
- Response: { error: false, data: ChatMessage }

## Utility & Webhooks
Base: https://dev.veyu.cc/

#### POST emailer/
- Auth: Internal use
- Body: { template_name: string, recipients: string[] , subject: string, context: object }
- Response: 200

#### POST hooks/payment-webhook/
- Auth: HMAC via Paystack header X-Paystack-Signature
- Body: Paystack event payload
- Response: 200

#### POST hooks/verification/
- Auth: None
- Body: verification provider callback payload
- Response: 200

## JWT (Optional)
Base: https://dev.veyu.cc/api/v1/
- POST token/: { email, password } -> { access, refresh }
- POST token/refresh/: { refresh } -> { access }
- POST token/verify/: { token }

## Notes
- Media/file upload endpoints require multipart/form-data.
- Many responses embed absolute URLs for media when request context is available.
- Some filter fields are placeholders/not fully implemented; unsupported filters are ignored by backend.

## Veyu Platform API Documentation

Base URL: https://dev.veyu.cc

Versioned API Base: https://dev.veyu.cc/api/v1

### Authentication
- Most protected endpoints accept token authentication.
- Send header: Authorization: Token YOUR_API_TOKEN
- You can obtain YOUR_API_TOKEN from the Accounts Login or Register endpoints.
- Some endpoints also support session/JWT auth (Simple JWT endpoints are exposed), but Token is the primary method across views.

### Pagination
- Offset-based pagination is used on list endpoints via `OffsetPaginator`.
- Query params:
  - per_page: number of items per page (default 25)
  - offset: number of items to skip (default 0)

### Common Response Envelope
Unless otherwise noted, successful responses use the following structure:
{
  "error": false,
  "message": "",
  "data": { ... }
}

### Rate Limiting
No explicit rate limit headers are provided by the API at this time.

### Errors
- 400: Bad Request (validation or input errors)
- 401: Unauthorized (missing/invalid auth)
- 403: Forbidden (insufficient permissions/funds)
- 404: Not Found
- 500: Internal Server Error

### API Explorer
- Swagger UI: https://dev.veyu.cc/api/docs/
- Redoc: https://dev.veyu.cc/redoc/

## Auth and Accounts
Base: https://dev.veyu.cc/api/v1/accounts/

#### POST login/
- Auth: Public
- Body:
  - email: string
  - password: string
  - provider: string (default: "veyu"; one of: veyu, google, apple, facebook)
- Response 200:
{
  "id": number,
  "email": string,
  "token": string,             // Use this in Authorization header as Token <token>
  "first_name": string,
  "last_name": string,
  "user_type": "customer|mechanic|dealer",
  "provider": string,
  "is_active": boolean,
  // dealer-only
  "dealerId"?: string,
  "verified_id"?: boolean,
  "verified_business"?: boolean,
  // mechanic-only
  "mechanicId"?: string
}

#### POST register/
- Auth: Public
- Usage 1: create-account
  - Content-Type: multipart/form-data or application/json
  - Body:
    - action: "create-account"
    - email, first_name, last_name, user_type (customer|mechanic|dealer), provider (default veyu)
    - password: required when provider = veyu
    - phone_number: optional (customers)
- Usage 2: setup-business-profile (after authentication)
  - Auth required; Content-Type: multipart/form-data
  - Body (depends on user_type):
    - action: "setup-business-profile"
    - user_type: mechanic|dealer
    - logo: file
    - about, headline, business_name, contact_email, contact_phone
    - mechanic-only: business_type (business|individual)
    - dealer-only: services: array of strings including any of ["Car Sale","Car Leasing","Drivers"]
    - location: JSON string with fields { lat, lng, country, state, city, street_address, zip_code, place_id }
- Response 201: { error: false, data: { token, ...user fields... } } or business profile object

#### POST verify-email/
- Auth: Required
- Body (two-step flow):
  - action: "request-code" and email
  - action: "confirm-code", email, code
- Response: { error: false, message }

#### POST verify-phone-number/
- Auth: Required
- Body:
  - action: "request-code" and phone_number
  - action: "confirm-code" and code
- Response: { error: false, message }

#### POST verify-business/
- Auth: Required
- Body:
  - object: "dealership" | "mechanic"
  - object_id: UUID
  - verification_ref: string
  - scope: array of strings, any of ["user.verified_email","verified_id","verified_business","verified_tin"]
- Response: { error: false, message: "Verification Successful" }

#### PUT update-profile/
- Auth: Required
- Body: profile fields depend on user_type (customer|mechanic|dealer). Send only fields you wish to update.
- Response: updated profile object

#### GET cart/
- Auth: Required
- Response data contains:
  - cars: Listing[] (for sale)
  - rentals: Listing[] (for rent)
  - bookings: ServiceBooking[]
  - orders: Order[]

#### POST cart/
- Auth: Required
- Body:
  - action: "remove-from-cart"
  - item: UUID of listing
- Response: { error: false, message }

#### GET notifications/
- Auth: Required
- Response: { error: false, data: Notification[] (unread) }

#### POST notifications/
- Auth: Required
- Body: { notification_id: UUID }
- Response: { error: false, data: Notification[] (remaining unread) }

### Password Reset (dj-rest-auth)
Base: https://dev.veyu.cc/api/v1/
- POST password-reset/ { email }
- POST password-reset-confirm/<uidb64>/<token>/ with form payload required by dj-rest-auth

### Simple JWT
Base: https://dev.veyu.cc/api/v1/
- POST token/
- POST token/refresh/
- POST token/verify/

## Listings (Customer)
Base: https://dev.veyu.cc/api/v1/listings/

#### GET buy/
- Auth: Optional
- Filters (query):
  - brands: comma-separated, e.g. brands=Toyota,Honda
  - condition: enum (new, used-foreign, used-local)
  - type: vehicle type(s), comma-separated
  - transmission: comma-separated
  - fuel_system: comma-separated
  - model: string
  - price: price range in the form min-max, e.g. price=1000000-15000000
  - location: string
  - mileage: range (not currently implemented)
- Pagination: per_page, offset
- Response: paginated { results: Listing[] }

#### GET rentals/
- Auth: Optional
- Filters (query): same style as `buy/` (uses rental filterset)
- Pagination: per_page, offset
- Response: paginated { results: Listing[] }

#### GET find/?find=free-text
- Auth: Optional
- Response: paginated { results: Listing[] }

#### GET dealer/<uuid>/
#### GET dealer/<slug>/
- Auth: Required
- Response: { error: false, data: Dealer }

#### GET my-listings/?scope=recents;favorites;top-deals
- Auth: Required
- Response keys vary by scope (recents, top_deals.sales, top_deals.rentals)

#### GET buy/<uuid>/
- Auth: Required
- Response: { listing: Listing, recommended: Listing[] }

#### POST buy/<uuid>/
- Auth: Required
- Body:
  - action: "add-to-cart" | "buy-now"
- Response: { error: false, message }

#### GET rentals/<uuid>/
- Auth: Optional
- Response: { listing: Listing, recommended: Listing[] }

#### GET checkout/<uuid:listingId>/
- Auth: Required
- Response: fee breakdown and selected listing

#### POST checkout/<uuid:listingId>/
- Auth: Required
- Body:
  - payment_option: "card" | "transfer" | "cash" (card marks order paid=true)
- Side effects: marks vehicle unavailable; associates order to customer and dealer
- Response: { error: false, message, data: Order }

#### POST checkout/inspection/
- Auth: Required
- Body:
  - listing_id: UUID
  - date: string (DD/MM/YYYY)
  - time: string (e.g. "14:00")
- Response: { error: false, data: "Inspection Scheduled" }

#### GET checkout/documents/?doc_type=order-slip&order_id=<uuid>
- Auth: Required
- Response: { file_id: UUID, url: absolute_url_to_pdf }

#### POST checkout/documents/
- Auth: Required
- Body:
  - file_id: UUID (from GET)
  - signature: data URL (e.g. data:image/png;base64,....)
- Response: { file_id, url }

## Mechanics (Customer-facing)
Base: https://dev.veyu.cc/api/v1/mechanics/

#### GET /
- Auth: Optional
- Query:
  - lat: number, lng: number (optional; used for proximity and distance field)
  - Filters (from MechanicFilter):
    - available: boolean
    - verified_phone_number: boolean
    - verified_email: boolean
    - services: comma-separated service titles
    - rating, location (reserved)
- Pagination: per_page, offset
- Response: paginated { results: Mechanic[] }

#### GET find/?find=term
- Auth: Optional
- Response: paginated { results: Mechanic[] }

#### GET <mech_id>/
- Auth: Required
- Response: { error: false, data: Mechanic }

#### POST <mech_id>/ (create service booking)
- Auth: Required
- Body:
  - problem_description: string
  - services: string[] (titles of services offered by mechanic)
  - transaction_id: string (payment gateway transaction reference)
- Response: { error: false, message, data: ServiceBooking }

#### GET <mech_id>/history/
- Auth: Required
- Response: { error: false, data: ServiceBooking[] (completed jobs) }

#### GET bookings/<booking_id>/
- Auth: Mechanic only
- Response: { error: false, data: BookingDetail }

#### POST bookings/<booking_id>/ (update booking)
- Auth: Mechanic only
- Body: action: one of ["accept","complete","decline","respond"]
- Response: { error: false, data: BookingDetail }

## Mechanics Admin (Mechanic dashboard)
Base: https://dev.veyu.cc/api/v1/admin/mechanics/

#### GET /
- Auth: Mechanic required
- Response: mechanic overview

#### GET dashboard/
- Auth: Mechanic required
- Response: metrics, current_job, booking_history, pending_requests

#### GET analytics/
- Auth: Mechanic required
- Response: revenue chart data and job counts

#### GET bookings/
- Auth: Mechanic required
- Response: { bookings: { history: ServiceBooking[], requests: ServiceBooking[] } }

#### POST bookings/<booking_id>/
- Auth: Mechanic required
- Body: action: "accept" | "complete" | "decline" | "respond" | "start-job"
- Response: updated booking

#### GET services/
- Auth: Mechanic required
- Response: list of service offerings for the mechanic

#### POST services/add/
- Auth: Mechanic required
- Body: { title: string, charge: number, charge_rate: string }
- Response: created service offering summary

#### GET settings/
- Auth: Mechanic required
- Response: mechanic profile

#### POST settings/
- Auth: Mechanic required; Content-Type: multipart/form-data
- Body: one or more of: business_name, about, headline, cac_number, tin_number, contact_email, contact_phone, new-logo (file)
- Response: updated mechanic profile

## Dealership Admin (Dealer dashboard)
Base: https://dev.veyu.cc/api/v1/admin/dealership/

#### GET /
- Auth: Dealer required
- Response: dealership profile

#### GET dashboard/
- Auth: Dealer required
- Response: revenue, impressions, recent_orders, chart_data

#### GET analytics/
- Auth: Dealer required
- Response: revenue and sales charts; order summary

#### GET orders/
- Auth: Dealer required
- Response: Order[]

#### GET listings/
- Auth: Dealer required
- Response: Listing[] for this dealer

#### POST listings/
- Auth: Dealer required
- Body:
  - action: "delete" | "unpublish" | "publish"
  - listing: UUID
- Response: { error: false, message }

#### POST listings/create/
- Auth: Dealer required; Content-Type: multipart/form-data
- Usage 1: create-listing
  - Body fields: listing_type (sale|rental), title, price, brand, model, condition, vehicle_type, transmission, fuel_system, drivetrain, seats, doors, vin, mileage (optional), features (rental), payment_cycle (rental)
- Usage 2: upload-images
  - Body: action="upload-images", listing: UUID, image: file[] (multiple)
- Usage 3: publish-listing
  - Body: action="publish-listing", listing: UUID
- Response: { error: false, message, data: Listing }

#### GET listings/<uuid:listing_id>/
- Auth: Dealer required
- Response: Listing

#### POST listings/<uuid:listing_id>/
- Auth: Dealer required
- Actions:
  - edit-listing: update listing + nested vehicle fields (see serializer fields used in code)
  - upload-images: image: file[]
  - remove-image: image_id: UUID
  - publish-listing: listing: UUID
- Response: { error: false, message, data: Listing }

#### DELETE listings/<uuid:listing_id>/
- Auth: Dealer required
- Response: 200 on success

#### GET settings/
- Auth: Dealer required
- Response: Dealer settings snapshot

#### POST settings/
- Auth: Dealer required; Content-Type: multipart/form-data
- Body: business_name, about, headline, services (array of strings), contact_phone, contact_email, slug (optional), new-logo (file)
- Response: updated dealer profile

## Wallet
Base: https://dev.veyu.cc/api/v1/wallet/

#### GET /
- Auth: Required
- Response: wallet overview with balances and transactions

#### GET balance/
- Auth: Required
- Response: { ledger_balance, balance, currency, id }

#### GET transactions/
- Auth: Required
- Response: { transactions: Transaction[] }

#### POST transfer/
- Auth: Required
- Body: { recipient: email, amount: decimal string >= 100.00 }
- Responses:
  - 200: "<amount> transferred to <recipient> successfully"
  - 403: { error: "Insufficient funds" }

#### POST deposit/
- Auth: Required
- Body (as sent back from gateway webhook/confirmation step):
  - status: string (e.g. "success")
  - tx_ref: string
  - reference: string (gateway reference)
  - currency: string (e.g. NGN)
  - amount: string/number
- Response 200: { error: false, message: "Deposit successfully received!", transaction: Transaction }

#### POST withdraw/
- Auth: Required
- Body: { amount, account_number, account_name, bank_code }
- Responses:
  - 200: gateway response JSON
  - 403: { error: "Insufficient funds" }
  - 400: validation errors

## Chat
Base: https://dev.veyu.cc/api/v1/chat/

#### GET chats/
- Auth: Required
- Response: { data: [{ uuid, id, last_message: { message, date }, recipient: { name, image } }] }

#### GET chats/<room_id>/
- Auth: Required
- Response: { data: ChatRoom (members, messages[], etc.) }

#### POST message/
- Auth: Required
- Body (two modes):
  1) Create or reuse 1:1 room by other member type
     - other_member: "dealer" | "mechanic" | "customer"
     - dealer_id | mechanic_id | customer_id: UUID (depending on type)
     - message: string
  2) To existing room (if supported by backend)
     - room_id: UUID
     - message: string
- Response: { error: false, message: "Message sent!" }

#### POST new/
- Auth: Required
- Body: { recipient: Account UUID, message: string }
- Response: { error: false, data: ChatMessage }

## Utility & Webhooks
Base: https://dev.veyu.cc/

#### POST emailer/
- Auth: Internal use
- Body: { template_name: string, recipients: string[] , subject: string, context: object }
- Response: 200

#### POST hooks/payment-webhook/
- Auth: HMAC via Paystack header X-Paystack-Signature
- Body: Paystack event payload
- Response: 200

#### POST hooks/verification/
- Auth: None
- Body: verification provider callback payload
- Response: 200

## JWT (Optional)
Base: https://dev.veyu.cc/api/v1/
- POST token/: { email, password } -> { access, refresh }
- POST token/refresh/: { refresh } -> { access }
- POST token/verify/: { token }

## Notes
- Media/file upload endpoints require multipart/form-data.
- Many responses embed absolute URLs for media when request context is available.
- Some filter fields are placeholders/not fully implemented; unsupported filters are ignored by backend.