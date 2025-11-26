# Complete Inspection Flow with Payment

## End-to-End Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    INSPECTION FLOW WITH PAYMENT                  │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│   CUSTOMER   │
└──────┬───────┘
       │
       │ 1. Request Fee Quote
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  POST /api/v1/inspections/quote/                                │
│  {                                                               │
│    "inspection_type": "pre_purchase",                           │
│    "vehicle_id": 123                                            │
│  }                                                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Fee: ₦50,000 │
                    └──────┬───────┘
                           │
       ┌───────────────────┘
       │
       │ 2. Create Inspection
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  POST /api/v1/inspections/                                      │
│  {                                                               │
│    "vehicle": 123,                                              │
│    "inspector": 456,                                            │
│    "customer": 789,                                             │
│    "dealer": 101,                                               │
│    "inspection_type": "pre_purchase"                            │
│  }                                                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
                    ┌──────────────────────────┐
                    │ VehicleInspection Created│
                    │ Status: pending_payment  │
                    │ Fee: ₦50,000            │
                    │ Payment: unpaid          │
                    └──────┬───────────────────┘
                           │
       ┌───────────────────┘
       │
       │ 3. Pay for Inspection
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  POST /api/v1/inspections/1/pay/                                │
│  {                                                               │
│    "payment_method": "wallet",                                  │
│    "amount": 50000.00                                           │
│  }                                                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
                    ┌──────────────────────────┐
                    │  Payment Processing      │
                    │  - Check wallet balance  │
                    │  - Deduct ₦50,000       │
                    │  - Create Transaction    │
                    └──────┬───────────────────┘
                           │
                           ▼
                    ┌──────────────────────────┐
                    │ Payment Successful!      │
                    │ Status: draft            │
                    │ Payment: paid            │
                    │ Transaction: #789        │
                    └──────┬───────────────────┘
                           │
       ┌───────────────────┘
       │
       │ 4. Inspector Starts Inspection
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  Inspection Data Collection                                     │
│  - Exterior inspection                                          │
│  - Interior inspection                                          │
│  - Engine inspection                                            │
│  - Mechanical inspection                                        │
│  - Safety inspection                                            │
│  - Photo uploads                                                │
│  - Inspector notes                                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
                    ┌──────────────────────────┐
                    │ Status: in_progress      │
                    └──────┬───────────────────┘
                           │
       ┌───────────────────┘
       │
       │ 5. Complete Inspection
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  POST /api/v1/inspections/1/complete/                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
                    ┌──────────────────────────┐
                    │ Status: completed        │
                    │ Overall Rating: Good     │
                    └──────┬───────────────────┘
                           │
       ┌───────────────────┘
       │
       │ 6. Generate Document
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  POST /api/v1/inspections/1/generate-document/                  │
│  {                                                               │
│    "template_type": "standard",                                 │
│    "include_photos": true,                                      │
│    "include_recommendations": true                              │
│  }                                                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
                    ┌──────────────────────────┐
                    │ PDF Generated            │
                    │ 3 Signature Records      │
                    │ - Inspector (pending)    │
                    │ - Customer (pending)     │
                    │ - Dealer (pending)       │
                    └──────┬───────────────────┘
                           │
       ┌───────────────────┴───────────────────┬───────────────────┐
       │                                       │                   │
       │ 7a. Inspector Signs                   │ 7b. Customer      │ 7c. Dealer
       ▼                                       ▼    Signs          ▼    Signs
┌──────────────────┐                    ┌──────────────────┐  ┌──────────────────┐
│ POST .../sign/   │                    │ POST .../sign/   │  │ POST .../sign/   │
│ Inspector        │                    │ Customer         │  │ Dealer           │
└────────┬─────────┘                    └────────┬─────────┘  └────────┬─────────┘
         │                                       │                     │
         └───────────────────┬───────────────────┴─────────────────────┘
                             │
                             ▼
                      ┌──────────────────────────┐
                      │ All Signatures Complete  │
                      │ Status: signed           │
                      │ Document: signed         │
                      └──────┬───────────────────┘
                             │
                             ▼
                      ┌──────────────────────────┐
                      │ INSPECTION COMPLETE!     │
                      │ - Paid: ✓               │
                      │ - Inspected: ✓          │
                      │ - Documented: ✓         │
                      │ - Signed: ✓             │
                      └──────────────────────────┘
```

## Status Transitions

```
pending_payment ──[pay]──> draft ──[start]──> in_progress ──[complete]──> completed ──[sign]──> signed
       │                                                                                           │
       │                                                                                           │
       └───────────────────────────────────[archive]────────────────────────────────────────────> archived
```

## Payment Status Transitions

```
unpaid ──[pay]──> paid
  │
  └──[refund]──> refunded
  │
  └──[fail]──> failed
```

## Data Flow

### 1. Payment Phase
```
Customer Wallet
    │
    ├─> Deduct ₦50,000
    │
    ├─> Create Transaction
    │   ├─> type: 'payment'
    │   ├─> amount: 50000
    │   ├─> status: 'completed'
    │   └─> related_inspection: FK
    │
    └─> Update Inspection
        ├─> payment_status: 'paid'
        ├─> payment_transaction: FK
        ├─> paid_at: timestamp
        └─> status: 'draft'
```

### 2. Inspection Phase
```
Inspector
    │
    ├─> Collect Data
    │   ├─> exterior_data (JSON)
    │   ├─> interior_data (JSON)
    │   ├─> engine_data (JSON)
    │   ├─> mechanical_data (JSON)
    │   └─> safety_data (JSON)
    │
    ├─> Upload Photos
    │   └─> InspectionPhoto records
    │
    └─> Complete
        ├─> status: 'completed'
        ├─> completed_at: timestamp
        └─> overall_rating: calculated
```

### 3. Document Phase
```
PDF Generation Service
    │
    ├─> Generate PDF
    │   ├─> Inspection data
    │   ├─> Photos
    │   ├─> Recommendations
    │   └─> Signature boxes
    │
    ├─> Create InspectionDocument
    │   ├─> document_file: Cloudinary
    │   ├─> document_hash: SHA-256
    │   └─> status: 'ready'
    │
    └─> Create DigitalSignature records
        ├─> Inspector (pending)
        ├─> Customer (pending)
        └─> Dealer (pending)
```

### 4. Signature Phase
```
Each Party
    │
    ├─> Submit Signature
    │   ├─> signature_image
    │   ├─> signature_method
    │   ├─> IP address
    │   └─> user agent
    │
    ├─> Update DigitalSignature
    │   ├─> status: 'signed'
    │   ├─> signed_at: timestamp
    │   └─> signature_hash: SHA-256
    │
    └─> Check Completion
        └─> If all signed:
            ├─> Document status: 'signed'
            └─> Inspection status: 'signed'
```

## Key Models & Relationships

```
VehicleInspection
    ├─> Vehicle (FK)
    ├─> Inspector (FK)
    ├─> Customer (FK)
    ├─> Dealer (FK)
    ├─> payment_transaction (FK to Transaction) ← NEW
    ├─> InspectionPhoto (1-to-many)
    └─> InspectionDocument (1-to-many)
        └─> DigitalSignature (1-to-many)

Transaction
    ├─> sender_wallet (FK)
    ├─> recipient_wallet (FK)
    ├─> related_order (FK)
    ├─> related_booking (FK)
    └─> related_inspection (FK) ← NEW
```

## Payment Integration Points

### Before Payment
- ❌ Cannot start inspection
- ❌ Cannot upload photos
- ❌ Cannot complete inspection
- ✅ Can view inspection details
- ✅ Can get fee quote

### After Payment
- ✅ Can start inspection
- ✅ Can upload photos
- ✅ Can complete inspection
- ✅ Can generate documents
- ✅ Can sign documents

## Error Handling

```
Payment Attempt
    │
    ├─> Check: Is customer?
    │   └─> No → 403 Forbidden
    │
    ├─> Check: Already paid?
    │   └─> Yes → 400 Bad Request
    │
    ├─> Check: Amount matches?
    │   └─> No → 400 Bad Request
    │
    ├─> Check: Sufficient balance?
    │   └─> No → 400 Bad Request
    │
    └─> Process Payment
        ├─> Success → 200 OK
        └─> Error → 500 Internal Server Error
```

## Complete Example

```bash
# Step 1: Get Quote
curl -X POST "https://veyu.cc/api/v1/inspections/quote/" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"inspection_type": "pre_purchase", "vehicle_id": 123}'

# Response: {"total_fee": 50000.00}

# Step 2: Create Inspection
curl -X POST "https://veyu.cc/api/v1/inspections/" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "vehicle": 123,
    "inspector": 456,
    "customer": 789,
    "dealer": 101,
    "inspection_type": "pre_purchase"
  }'

# Response: {"id": 1, "status": "pending_payment", "inspection_fee": 50000.00}

# Step 3: Pay
curl -X POST "https://veyu.cc/api/v1/inspections/1/pay/" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"payment_method": "wallet", "amount": 50000.00}'

# Response: {"success": true, "inspection_status": "Draft"}

# Step 4: Start Inspection (Inspector)
# ... collect data ...

# Step 5: Complete
curl -X POST "https://veyu.cc/api/v1/inspections/1/complete/" \
  -H "Authorization: Bearer TOKEN"

# Step 6: Generate Document
curl -X POST "https://veyu.cc/api/v1/inspections/1/generate-document/" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"template_type": "standard", "include_photos": true}'

# Step 7: Sign (All parties)
curl -X POST "https://veyu.cc/api/v1/inspections/documents/1/sign/" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"signature_data": {...}}'

# Done! Inspection is complete and signed.
```

## Summary

The inspection flow now includes payment as the **first mandatory step**:

1. ✅ **Payment First** - Customer pays before inspection starts
2. ✅ **Automatic Fee Calculation** - Based on inspection type
3. ✅ **Wallet Integration** - Instant payment from user wallet
4. ✅ **Transaction Tracking** - Full audit trail
5. ✅ **Status Management** - Clear progression from payment to completion
6. ✅ **Security** - Only customer can pay, duplicate prevention
7. ✅ **Error Handling** - Clear error messages for all scenarios

This ensures inspections are only conducted after payment is confirmed, protecting both the business and the inspector.
