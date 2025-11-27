# Inspection Payment & Revenue Sharing System

## Overview

The inspection payment system uses **Paystack only** for all payments. When a customer pays for an inspection, the revenue is automatically split between the dealer and the platform based on configurable percentages (default: 60% dealer, 40% platform).

Business accounts (dealers/mechanics) can request manual withdrawals from their wallet balance.

## Key Features

1. **Paystack-Only Payments**: All inspection payments must go through Paystack
2. **Automatic Revenue Split**: Payment is automatically divided between dealer and platform
3. **Instant Dealer Credit**: Dealer wallet is credited immediately upon payment verification
4. **Manual Withdrawal Requests**: Business accounts can request withdrawals that require admin approval
5. **Configurable Split Percentages**: Admin can adjust revenue sharing percentages from the admin panel

## Payment Flow

### 1. Customer Initiates Payment

```
POST /api/v1/inspections/{inspection_id}/pay/
```

**Request:**
```json
{
  "amount": 5000.00
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "payment_method": "paystack",
    "amount": 5000.00,
    "inspection_id": 123,
    "transaction_id": 456,
    "reference": "veyu-inspection-123-abc123",
    "email": "customer@example.com",
    "currency": "NGN",
    "callback_url": "https://api.veyu.com/api/v1/inspections/123/verify-payment/"
  },
  "message": "Initialize Paystack payment on frontend with the provided reference"
}
```

### 2. Frontend Initializes Paystack

```javascript
const paystack = PaystackPop.setup({
  key: 'pk_live_xxxxx', // Your Paystack public key
  email: response.data.email,
  amount: response.data.amount * 100, // Convert to kobo
  ref: response.data.reference,
  callback: function(response) {
    // Verify payment on backend
    verifyPayment(response.reference);
  },
  onClose: function() {
    alert('Payment cancelled');
  }
});

paystack.openIframe();
```

### 3. Backend Verifies Payment & Splits Revenue

```
POST /api/v1/inspections/{inspection_id}/verify-payment/
```

**Request:**
```json
{
  "reference": "veyu-inspection-123-abc123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "inspection_id": 123,
    "transaction_id": 456,
    "amount_paid": 5000.00,
    "payment_method": "paystack",
    "payment_status": "paid",
    "inspection_status": "Draft",
    "paid_at": "2025-11-27T10:30:00Z",
    "reference": "veyu-inspection-123-abc123",
    "revenue_split": {
      "dealer_amount": 3000.00,
      "dealer_percentage": 60.00,
      "platform_amount": 2000.00,
      "platform_percentage": 40.00,
      "dealer_credited": true
    }
  },
  "message": "Payment verified successfully. Dealer wallet credited. Inspection can now begin."
}
```

## Revenue Sharing

### Default Split
- **Dealer**: 60% of inspection fee
- **Platform**: 40% of inspection fee

### Configuring Revenue Split

Admins can adjust the revenue split from the Django admin panel:

1. Navigate to **Inspections > Inspection Revenue Settings**
2. Click **Add Inspection Revenue Settings**
3. Set dealer and platform percentages (must total 100%)
4. Mark as **Active**
5. Save

**Note**: Only one settings record can be active at a time. When you activate a new setting, all previous settings are automatically deactivated.

### Revenue Split Process

1. **Payment Received**: Customer pays via Paystack
2. **Transaction Created**: Payment transaction is recorded
3. **Split Calculated**: System calculates dealer and platform shares based on active settings
4. **Dealer Credited**: Dealer's wallet is immediately credited with their share
5. **Platform Retained**: Platform share is retained (not transferred to any wallet)
6. **Split Recorded**: Revenue split details are saved for audit trail

### Example Calculation

```
Inspection Fee: ₦5,000
Active Settings: 60% Dealer / 40% Platform

Dealer Amount: ₦5,000 × 60% = ₦3,000
Platform Amount: ₦5,000 × 40% = ₦2,000

Dealer wallet is credited with ₦3,000
Platform retains ₦2,000
```

## Withdrawal Requests

Business accounts (dealers/mechanics) can request manual withdrawals from their wallet balance.

### Creating a Withdrawal Request

```
POST /api/v1/wallet/withdrawal-requests/
```

**Request:**
```json
{
  "amount": 10000.00,
  "payout_info_id": 5
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 789,
    "user_name": "Manga Autos",
    "user_email": "dealer@mangaautos.com",
    "amount": 10000.00,
    "status": "pending",
    "status_display": "Pending Review",
    "bank_name": "GTBank",
    "account_name": "Manga Autos Ltd",
    "account_number": "0123456789",
    "date_created": "2025-11-27T11:00:00Z"
  },
  "message": "Withdrawal request submitted successfully. It will be reviewed by our team."
}
```

### Viewing Withdrawal Requests

```
GET /api/v1/wallet/withdrawal-requests/
```

**Query Parameters:**
- `status`: Filter by status (pending, approved, completed, rejected, cancelled)
- `limit`: Number of requests to return (default: 50)

**Response:**
```json
{
  "success": true,
  "data": {
    "wallet": {
      "balance": 25000.00,
      "ledger_balance": 25000.00,
      "currency": "NGN"
    },
    "withdrawal_requests": [
      {
        "id": 789,
        "amount": 10000.00,
        "status": "pending",
        "status_display": "Pending Review",
        "bank_name": "GTBank",
        "account_name": "Manga Autos Ltd",
        "account_number": "0123456789",
        "date_created": "2025-11-27T11:00:00Z"
      }
    ],
    "total_requests": 1
  }
}
```

### Cancelling a Withdrawal Request

```
POST /api/v1/wallet/withdrawal-requests/{request_id}/cancel/
```

**Response:**
```json
{
  "success": true,
  "message": "Withdrawal request cancelled successfully"
}
```

### Withdrawal Statistics

```
GET /api/v1/wallet/withdrawal-requests/statistics/
```

**Response:**
```json
{
  "success": true,
  "data": {
    "wallet": {
      "balance": 25000.00,
      "ledger_balance": 25000.00,
      "currency": "NGN"
    },
    "statistics": {
      "total_requests": 10,
      "pending_requests": 1,
      "approved_requests": 0,
      "completed_requests": 8,
      "rejected_requests": 1,
      "total_withdrawn": 80000.00,
      "pending_amount": 10000.00
    },
    "recent_requests": [...]
  }
}
```

## Admin Panel Management

### Revenue Settings Management

**Location**: Admin Panel > Inspections > Inspection Revenue Settings

**Features**:
- View all revenue split configurations
- See which configuration is currently active
- View usage statistics for each configuration
- Create new revenue split configurations
- Activate/deactivate configurations

### Revenue Split Tracking

**Location**: Admin Panel > Inspections > Inspection Revenue Splits

**Features**:
- View all revenue splits
- Filter by inspection type, date, dealer
- See dealer credit status
- View split calculations
- Export split data

### Withdrawal Request Management

**Location**: Admin Panel > Inspections > Withdrawal Requests

**Features**:
- View all withdrawal requests
- Filter by status, date, user
- Approve/reject requests
- Add rejection reasons
- Process approved withdrawals
- View bank account details
- Track payment references

**Actions**:
1. **Approve**: Changes status to "approved" and sets reviewer
2. **Reject**: Changes status to "rejected" and requires rejection reason
3. **Process**: Deducts from wallet and creates withdrawal transaction (for approved requests)

## Database Models

### InspectionRevenueSettings

Stores configurable revenue split percentages.

**Fields**:
- `dealer_percentage`: Percentage for dealer (0-100)
- `platform_percentage`: Percentage for platform (0-100)
- `is_active`: Whether this configuration is active
- `effective_date`: When configuration became effective
- `notes`: Admin notes

**Constraints**:
- Percentages must total 100%
- Only one configuration can be active at a time

### InspectionRevenueSplit

Tracks revenue distribution for each inspection payment.

**Fields**:
- `inspection`: Related inspection (OneToOne)
- `payment_transaction`: Related payment transaction
- `total_amount`: Total inspection fee
- `dealer_amount`: Amount allocated to dealer
- `dealer_percentage`: Percentage used for dealer
- `platform_amount`: Amount retained by platform
- `platform_percentage`: Percentage used for platform
- `dealer_credited`: Whether dealer wallet was credited
- `dealer_credited_at`: When dealer was credited
- `revenue_settings`: Settings used for this split

### WithdrawalRequest

Tracks withdrawal requests from business accounts.

**Fields**:
- `user`: User requesting withdrawal
- `wallet`: User's wallet
- `amount`: Withdrawal amount (minimum ₦100)
- `payout_info`: Bank account for withdrawal
- `status`: Request status (pending, approved, processing, completed, rejected, cancelled)
- `reviewed_by`: Admin who reviewed
- `reviewed_at`: When reviewed
- `rejection_reason`: Reason for rejection
- `admin_notes`: Internal admin notes
- `processed_at`: When processed
- `payment_reference`: Payment reference
- `transaction`: Related withdrawal transaction

## API Endpoints Summary

### Inspection Payment
- `POST /api/v1/inspections/{id}/pay/` - Initiate Paystack payment
- `POST /api/v1/inspections/{id}/verify-payment/` - Verify payment and split revenue

### Withdrawal Requests
- `GET /api/v1/wallet/withdrawal-requests/` - List withdrawal requests
- `POST /api/v1/wallet/withdrawal-requests/` - Create withdrawal request
- `GET /api/v1/wallet/withdrawal-requests/{id}/` - Get withdrawal request details
- `POST /api/v1/wallet/withdrawal-requests/{id}/cancel/` - Cancel withdrawal request
- `GET /api/v1/wallet/withdrawal-requests/statistics/` - Get withdrawal statistics

## Security Considerations

1. **Payment Verification**: Always verify payments with Paystack before crediting
2. **Withdrawal Approval**: All withdrawals require admin approval
3. **Balance Checks**: System validates sufficient balance before allowing withdrawals
4. **Audit Trail**: All revenue splits and withdrawals are logged
5. **Transaction Integrity**: Uses database transactions to ensure consistency

## Testing

### Test Paystack Payment

```python
# Use Paystack test keys
PAYSTACK_PUBLIC_KEY = 'pk_test_xxxxx'
PAYSTACK_SECRET_KEY = 'sk_test_xxxxx'

# Test card numbers
# Success: 4084084084084081
# Insufficient funds: 4084080000000409
```

### Test Revenue Split

```python
from inspections.models import VehicleInspection
from inspections.models_revenue import InspectionRevenueSplit

# Get inspection
inspection = VehicleInspection.objects.get(id=123)

# Check revenue split
split = inspection.revenue_split
print(f"Dealer: ₦{split.dealer_amount} ({split.dealer_percentage}%)")
print(f"Platform: ₦{split.platform_amount} ({split.platform_percentage}%)")
print(f"Dealer Credited: {split.dealer_credited}")
```

### Test Withdrawal Request

```python
from inspections.models_revenue import WithdrawalRequest
from wallet.models import Wallet

# Get user wallet
wallet = Wallet.objects.get(user=user)
print(f"Balance: ₦{wallet.balance}")

# Create withdrawal request
withdrawal = WithdrawalRequest.objects.create(
    user=user,
    wallet=wallet,
    amount=10000,
    payout_info=payout_info,
    status='pending'
)

# Approve and process
withdrawal.approve(admin_user)
withdrawal.process_withdrawal()
```

## Troubleshooting

### Payment Not Splitting

1. Check if InspectionRevenueSettings exists and is active
2. Verify payment transaction is marked as completed
3. Check logs for errors during split creation

### Dealer Not Credited

1. Check `dealer_credited` field on InspectionRevenueSplit
2. Verify dealer has a wallet
3. Check transaction logs for credit transaction

### Withdrawal Request Stuck

1. Check request status in admin panel
2. Verify admin has approved the request
3. Check wallet balance is sufficient
4. Review admin notes for any issues

## Migration

To apply the new models:

```bash
python manage.py migrate inspections
```

This will create:
- `inspections_inspectionrevenuesettings` table
- `inspections_inspectionrevenuesplit` table
- `inspections_withdrawalrequest` table

## Future Enhancements

1. **Automated Withdrawals**: Auto-process approved withdrawals via payment gateway
2. **Withdrawal Limits**: Set daily/monthly withdrawal limits
3. **Fee Tiers**: Different revenue splits based on dealer tier/volume
4. **Batch Processing**: Process multiple withdrawals at once
5. **Email Notifications**: Notify users of withdrawal status changes
6. **SMS Alerts**: Send SMS for important withdrawal updates
