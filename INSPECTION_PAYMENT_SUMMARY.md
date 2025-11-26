# Inspection Payment - Quick Reference

## Payment Flow (3 Steps)

### Step 1: Get Fee Quote
```bash
POST /api/v1/inspections/quote/
```
```json
{
  "inspection_type": "pre_purchase",
  "vehicle_id": 123
}
```
**Returns:** Fee amount (₦25k-₦50k depending on type)

---

### Step 2: Create Inspection
```bash
POST /api/v1/inspections/
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
**Returns:** Inspection with `status: "pending_payment"` and calculated fee

---

### Step 3: Pay for Inspection

#### Option A: Wallet Payment
```bash
POST /api/v1/inspections/{inspection_id}/pay/
```
```json
{
  "payment_method": "wallet",
  "amount": 50000.00
}
```
**Returns:** Instant payment confirmation, status changes to `"draft"`

#### Option B: Bank Payment (Paystack)
```bash
POST /api/v1/inspections/{inspection_id}/pay/
```
```json
{
  "payment_method": "bank",
  "amount": 50000.00
}
```
**Returns:** Payment reference for Paystack checkout

Then verify:
```bash
POST /api/v1/inspections/{inspection_id}/verify-payment/
```
```json
{
  "reference": "veyu-inspection-1-abc123"
}
```
**Returns:** Payment confirmation after Paystack verification

---

## Inspection Fees

| Type | Fee |
|------|-----|
| Pre-Purchase | ₦50,000 |
| Pre-Rental | ₦30,000 |
| Maintenance | ₦25,000 |
| Insurance | ₦40,000 |

## Status Progression

```
pending_payment → draft → in_progress → completed → signed
      ↓
   (pay here)
```

## Key Points

✅ Payment is **required** before inspection can start
✅ Fee is **auto-calculated** when inspection is created
✅ Only **customer** can pay for their inspection
✅ **Two payment methods**: Wallet (instant) or Bank (Paystack)
✅ **Transaction record** is created and linked
✅ Status automatically changes to `draft` after payment
✅ **Paystack integration** for card, bank transfer, USSD, QR payments

## Payment Status

- `unpaid` - Awaiting payment
- `paid` - Payment successful
- `refunded` - Payment returned
- `failed` - Payment failed

## Quick Test

```bash
# 1. Get quote
curl -X POST "https://veyu.cc/api/v1/inspections/quote/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inspection_type": "pre_purchase"}'

# 2. Create inspection (returns inspection_id)
curl -X POST "https://veyu.cc/api/v1/inspections/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}'

# 3. Pay for inspection
curl -X POST "https://veyu.cc/api/v1/inspections/1/pay/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"payment_method": "wallet", "amount": 50000.00}'
```

## Common Errors

**Insufficient Balance:**
```json
{
  "error": "Insufficient wallet balance",
  "available_balance": 30000.00,
  "required_amount": 50000.00
}
```

**Already Paid:**
```json
{
  "error": "Inspection has already been paid for"
}
```

**Wrong Amount:**
```json
{
  "amount": ["Payment amount must match inspection fee of ₦50,000.00"]
}
```

## Database Changes

### New Fields in `VehicleInspection`
- `inspection_fee` (Decimal)
- `payment_status` (String: unpaid/paid/refunded/failed)
- `payment_method` (String: wallet/bank)
- `payment_transaction` (FK to Transaction)
- `paid_at` (DateTime)

### New Field in `Transaction`
- `related_inspection` (FK to VehicleInspection)

### New Status in `VehicleInspection`
- `pending_payment` (initial status)

## Migration

Run migration to add payment fields:
```bash
python manage.py migrate inspections
```

## Related Docs

- Full Documentation: `inspections/PAYMENT_FLOW.md`
- Paystack Integration: `inspections/PAYSTACK_INTEGRATION.md`
- Complete Flow Diagram: `inspections/COMPLETE_FLOW.md`
- Inspection Flow: `inspections/README.md`
- Wallet API: `wallet/`
