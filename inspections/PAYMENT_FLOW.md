# Inspection Payment Flow

## Overview

The inspection payment system allows customers to pay for vehicle inspections before the inspection process begins. This ensures that inspections are only conducted after payment is confirmed.

## Payment Flow

### 1. Get Fee Quote

Before creating an inspection, customers can get a fee quote:

**Endpoint:** `POST /api/v1/inspections/quote/`

**Request:**
```json
{
  "inspection_type": "pre_purchase",
  "vehicle_id": 123  // optional
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "inspection_type": "pre_purchase",
    "base_fee": 50000.00,
    "vehicle_info": {
      "id": 123,
      "name": "Toyota Camry 2020",
      "brand": "Toyota",
      "model": "Camry"
    },
    "total_fee": 50000.00,
    "currency": "NGN"
  },
  "message": "Fee quote generated successfully"
}
```

### 2. Create Inspection

When creating an inspection, the fee is automatically calculated and the status is set to `pending_payment`:

**Endpoint:** `POST /api/v1/inspections/`

**Request:**
```json
{
  "vehicle": 123,
  "inspector": 456,
  "customer": 789,
  "dealer": 101,
  "inspection_type": "pre_purchase"
}
```

**Response:**
```json
{
  "id": 1,
  "vehicle_name": "Toyota Camry 2020",
  "inspection_type": "pre_purchase",
  "status": "pending_payment",
  "payment_status": "unpaid",
  "inspection_fee": 50000.00,
  "paid_at": null
}
```

### 3. Pay for Inspection

Customer pays for the inspection using wallet or bank:

**Endpoint:** `POST /api/v1/inspections/{inspection_id}/pay/`

#### Option A: Wallet Payment

**Request:**
```json
{
  "payment_method": "wallet",
  "amount": 50000.00
}
```

**Response (Success):**
```json
{
  "success": true,
  "data": {
    "inspection_id": 1,
    "transaction_id": 789,
    "amount_paid": 50000.00,
    "payment_method": "wallet",
    "payment_status": "paid",
    "inspection_status": "Draft",
    "paid_at": "2024-01-15T10:30:00Z",
    "remaining_balance": 450000.00
  },
  "message": "Payment successful. Inspection can now begin."
}
```

**Response (Insufficient Balance):**
```json
{
  "error": "Insufficient wallet balance",
  "available_balance": 30000.00,
  "required_amount": 50000.00
}
```

#### Option B: Bank Payment (Paystack)

**Request:**
```json
{
  "payment_method": "bank",
  "amount": 50000.00
}
```

**Response (Payment Initialization):**
```json
{
  "success": true,
  "data": {
    "payment_method": "bank",
    "amount": 50000.00,
    "inspection_id": 1,
    "transaction_id": 789,
    "reference": "veyu-inspection-1-abc123def456",
    "email": "customer@example.com",
    "currency": "NGN",
    "callback_url": "https://veyu.cc/api/v1/inspections/1/verify-payment/"
  },
  "message": "Initialize Paystack payment on frontend with the provided reference"
}
```

**Frontend Integration:**
```javascript
// Use Paystack Popup
const paystack = new PaystackPop();
paystack.newTransaction({
  key: 'YOUR_PAYSTACK_PUBLIC_KEY',
  email: response.data.email,
  amount: response.data.amount * 100, // Convert to kobo
  ref: response.data.reference,
  currency: response.data.currency,
  onSuccess: (transaction) => {
    // Verify payment on backend
    verifyPayment(transaction.reference);
  },
  onCancel: () => {
    console.log('Payment cancelled');
  }
});
```

### 3b. Verify Bank Payment

After Paystack payment, verify on backend:

**Endpoint:** `POST /api/v1/inspections/{inspection_id}/verify-payment/`

**Request:**
```json
{
  "reference": "veyu-inspection-1-abc123def456"
}
```

**Response (Success):**
```json
{
  "success": true,
  "data": {
    "inspection_id": 1,
    "transaction_id": 789,
    "amount_paid": 50000.00,
    "payment_method": "bank",
    "payment_status": "paid",
    "inspection_status": "Draft",
    "paid_at": "2024-01-15T10:30:00Z",
    "reference": "veyu-inspection-1-abc123def456"
  },
  "message": "Payment verified successfully. Inspection can now begin."
}
```

### 4. Start Inspection

After payment is confirmed, the inspector can begin the inspection process. The status automatically changes from `pending_payment` to `draft` after payment.

## Inspection Fee Structure

| Inspection Type | Base Fee |
|----------------|----------|
| Pre-Purchase | ₦50,000 |
| Pre-Rental | ₦30,000 |
| Maintenance | ₦25,000 |
| Insurance | ₦40,000 |

## Status Flow

```
pending_payment → draft → in_progress → completed → signed → archived
       ↓
    (payment)
```

## Payment Status

- **unpaid**: Inspection created but not paid
- **paid**: Payment successful, inspection can proceed
- **refunded**: Payment refunded to customer
- **failed**: Payment attempt failed

## Inspection Status

- **pending_payment**: Waiting for payment (initial state)
- **draft**: Payment completed, ready to start inspection
- **in_progress**: Inspector is conducting inspection
- **completed**: Inspection finished, awaiting signatures
- **signed**: All parties have signed the document
- **archived**: Inspection archived

## Payment Methods

### 1. Wallet Payment (Implemented ✅)

- Deducts from customer's Veyu wallet
- Instant confirmation
- Transaction recorded in wallet history
- No additional fees

**Flow:**
```
Customer → Pay with Wallet → Instant Deduction → Inspection Starts
```

### 2. Bank Payment via Paystack (Implemented ✅)

- Integration with Paystack payment gateway
- Supports: Card, Bank Transfer, USSD, QR Code
- Real-time payment verification
- Secure payment processing

**Flow:**
```
Customer → Pay with Bank → Paystack Checkout → Verify Payment → Inspection Starts
```

## Database Schema

### VehicleInspection Model (New Fields)

```python
inspection_fee = DecimalField(max_digits=10, decimal_places=2, default=0.00)
payment_status = CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
payment_method = CharField(max_length=20, blank=True, null=True)
payment_transaction = ForeignKey('wallet.Transaction', null=True, blank=True)
paid_at = DateTimeField(blank=True, null=True)
```

### Transaction Model (New Field)

```python
related_inspection = ForeignKey('inspections.VehicleInspection', null=True, blank=True)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/inspections/quote/` | Get fee quote |
| POST | `/api/v1/inspections/` | Create inspection (auto-calculates fee) |
| POST | `/api/v1/inspections/{id}/pay/` | Pay for inspection (wallet or bank) |
| POST | `/api/v1/inspections/{id}/verify-payment/` | Verify Paystack payment |
| GET | `/api/v1/inspections/{id}/` | Get inspection details (includes payment info) |
| GET | `/api/v1/inspections/` | List inspections (includes payment status) |

## Security & Validation

1. **Authorization**: Only the customer can pay for their inspection
2. **Duplicate Payment Prevention**: Cannot pay for already-paid inspections
3. **Amount Validation**: Payment amount must match inspection fee
4. **Balance Check**: Wallet balance verified before deduction
5. **Atomic Transactions**: Payment and status updates are atomic

## Error Handling

### Common Errors

**403 Forbidden**
```json
{
  "error": "Only the customer can pay for this inspection"
}
```

**400 Bad Request**
```json
{
  "error": "Inspection has already been paid for"
}
```

**400 Bad Request**
```json
{
  "error": "Insufficient wallet balance",
  "available_balance": 30000.00,
  "required_amount": 50000.00
}
```

**400 Bad Request**
```json
{
  "amount": ["Payment amount must match inspection fee of ₦50,000.00"]
}
```

## Testing

### Test Scenario 1: Successful Payment

```bash
# 1. Get quote
curl -X POST "https://veyu.cc/api/v1/inspections/quote/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"inspection_type": "pre_purchase", "vehicle_id": 123}'

# 2. Create inspection
curl -X POST "https://veyu.cc/api/v1/inspections/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle": 123,
    "inspector": 456,
    "customer": 789,
    "dealer": 101,
    "inspection_type": "pre_purchase"
  }'

# 3. Pay for inspection
curl -X POST "https://veyu.cc/api/v1/inspections/1/pay/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_method": "wallet",
    "amount": 50000.00
  }'
```

### Test Scenario 2: Insufficient Balance

```bash
# Attempt payment with insufficient balance
curl -X POST "https://veyu.cc/api/v1/inspections/1/pay/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_method": "wallet",
    "amount": 50000.00
  }'

# Expected: 400 error with balance details
```

## Future Enhancements

1. **Dynamic Pricing**: Adjust fees based on vehicle value, location, urgency
2. **Discount Codes**: Support promotional codes and discounts
3. **Payment Plans**: Allow installment payments for expensive inspections
4. **Refund System**: Automated refunds for cancelled inspections
5. **Bank Integration**: Complete Paystack/Flutterwave integration
6. **Payment Reminders**: Notify customers of pending payments
7. **Receipt Generation**: PDF receipts for completed payments

## Related Files

- **Models**: `inspections/models.py`
- **Views**: `inspections/views.py`
- **Serializers**: `inspections/serializers.py`
- **Services**: `inspections/services.py` (InspectionFeeService)
- **URLs**: `inspections/urls.py`
- **Migrations**: `inspections/migrations/0002_add_payment_fields.py`

## Support

For payment-related issues:
1. Check wallet balance: `GET /api/v1/wallet/balance/`
2. View transaction history: `GET /api/v1/wallet/transactions/`
3. Contact support with transaction ID for disputes
