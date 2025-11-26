# Inspection API - Quick Reference Card

## Base URL
```
https://veyu.cc/api/v1
```

## Authentication
```
Authorization: Bearer YOUR_JWT_TOKEN
```

---

## Complete Flow (8 Steps)

### 1️⃣ Get Fee Quote (Optional)
```bash
POST /inspections/quote/
```
```json
{"inspection_type": "pre_purchase", "vehicle_id": 123}
```
**Returns:** Fee amount

---

### 2️⃣ Create Inspection
```bash
POST /inspections/
```
```json
{
  "vehicle": 123,
  "inspector": 456,
  "customer": 789,
  "dealer": 101,
  "inspection_type": "pre_purchase"
}
```
**Returns:** Inspection with `status: "pending_payment"`

---

### 3️⃣ Pay for Inspection

#### Option A: Wallet
```bash
POST /inspections/{id}/pay/
```
```json
{"payment_method": "wallet", "amount": 50000.00}
```
**Returns:** Instant confirmation

#### Option B: Bank (Paystack)
```bash
POST /inspections/{id}/pay/
```
```json
{"payment_method": "bank", "amount": 50000.00}
```
**Returns:** Payment reference

Then verify:
```bash
POST /inspections/{id}/verify-payment/
```
```json
{"reference": "veyu-inspection-1-abc123"}
```
**Returns:** Payment confirmation

---

### 4️⃣ Conduct Inspection (Inspector)

#### Get Details
```bash
GET /inspections/{id}/
```

#### Update Data
```bash
PUT /inspections/{id}/
```
```json
{
  "status": "in_progress",
  "exterior_data": {...},
  "interior_data": {...},
  "engine_data": {...},
  "mechanical_data": {...},
  "safety_data": {...},
  "inspector_notes": "...",
  "recommended_actions": [...]
}
```

#### Upload Photos
```bash
POST /inspections/{id}/photos/
```
FormData: `category`, `image`, `description`

---

### 5️⃣ Complete Inspection
```bash
POST /inspections/{id}/complete/
```
**Returns:** Status changes to `"completed"`

---

### 6️⃣ Generate Document
```bash
POST /inspections/{id}/generate-document/
```
```json
{
  "template_type": "standard",
  "include_photos": true,
  "include_recommendations": true
}
```
**Returns:** PDF document + 3 signature records

---

### 7️⃣ Sign Document (All Parties)

#### Preview
```bash
GET /inspections/documents/{doc_id}/preview/
```

#### Sign
```bash
POST /inspections/documents/{doc_id}/sign/
```
```json
{
  "signature_data": {
    "signature_image": "data:image/png;base64,...",
    "signature_method": "drawn"
  },
  "signature_field_id": "inspector_signature"
}
```

---

### 8️⃣ Download Document
```bash
GET /inspections/documents/{doc_id}/download/
```
**Returns:** PDF file

---

## Status Flow

```
pending_payment → draft → in_progress → completed → signed
```

---

## Inspection Types & Fees

| Type | Code | Fee |
|------|------|-----|
| Pre-Purchase | `pre_purchase` | ₦50,000 |
| Pre-Rental | `pre_rental` | ₦30,000 |
| Maintenance | `maintenance` | ₦25,000 |
| Insurance | `insurance` | ₦40,000 |

---

## Photo Categories

- `exterior_front`, `exterior_rear`, `exterior_left`, `exterior_right`
- `interior_dashboard`, `interior_seats`
- `engine_bay`, `tires_wheels`
- `damage_detail`, `documents`, `other`

---

## Condition Ratings

- `excellent` - Excellent
- `good` - Good
- `fair` - Fair (needs attention)
- `poor` - Poor (immediate attention)

---

## Paystack Test Card

**Card:** 4084084084084081  
**CVV:** 408  
**Expiry:** 12/30  
**PIN:** 0000  
**OTP:** 123456

---

## Common Errors

| Code | Error | Solution |
|------|-------|----------|
| 400 | Already paid | Check payment status |
| 403 | Permission denied | Verify user role |
| 404 | Not found | Check ID |
| 500 | Server error | Contact support |

---

## Quick Test

```bash
# 1. Get quote
curl -X POST "https://veyu.cc/api/v1/inspections/quote/" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"inspection_type": "pre_purchase"}'

# 2. Create
curl -X POST "https://veyu.cc/api/v1/inspections/" \
  -H "Authorization: Bearer TOKEN" \
  -d '{...}'

# 3. Pay
curl -X POST "https://veyu.cc/api/v1/inspections/1/pay/" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"payment_method": "wallet", "amount": 50000.00}'

# 4. Complete
curl -X POST "https://veyu.cc/api/v1/inspections/1/complete/" \
  -H "Authorization: Bearer TOKEN"

# 5. Generate
curl -X POST "https://veyu.cc/api/v1/inspections/1/generate-document/" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"template_type": "standard"}'

# 6. Sign
curl -X POST "https://veyu.cc/api/v1/inspections/documents/1/sign/" \
  -H "Authorization: Bearer TOKEN" \
  -d '{...}'

# 7. Download
curl -X GET "https://veyu.cc/api/v1/inspections/documents/1/download/" \
  -H "Authorization: Bearer TOKEN" \
  --output inspection.pdf
```

---

**Full Documentation:** `docs/INSPECTION_FRONTEND_GUIDE.md`  
**Version:** 1.0.0
