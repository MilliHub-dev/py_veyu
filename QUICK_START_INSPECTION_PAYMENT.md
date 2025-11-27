# 🚀 Quick Start: Inspection Payment System

## TL;DR

✅ **Paystack-only** payments for inspections
✅ **60% dealer / 40% platform** automatic split
✅ **Instant dealer credit** on payment
✅ **Manual withdrawals** with admin approval

## 🎯 Key Changes

### Before
- Customers could pay with wallet or bank
- No revenue sharing
- No withdrawal system

### After
- **Customers MUST use Paystack** for inspection payments
- **Automatic 60/40 split** (dealer/platform)
- **Dealer wallet credited immediately**
- **Business accounts can request withdrawals**

## 📋 Setup (3 Steps)

### 1. Migration (Already Done ✅)
```bash
python manage.py migrate inspections
```

### 2. Create Revenue Settings
**Admin Panel → Inspections → Inspection Revenue Settings → Add**
- Dealer Percentage: `60.00`
- Platform Percentage: `40.00`
- Is Active: ✅
- Save

### 3. Configure Paystack
```python
# .env or settings.py
PAYSTACK_PUBLIC_KEY = 'pk_live_xxxxx'
PAYSTACK_SECRET_KEY = 'sk_live_xxxxx'
```

## 🔄 Payment Flow

```
Customer → Pay for Inspection
    ↓
Backend → Returns Paystack Reference
    ↓
Frontend → Shows Paystack Popup
    ↓
Customer → Completes Payment
    ↓
Frontend → Calls Verify Endpoint
    ↓
Backend → Verifies with Paystack
    ↓
Backend → Splits Revenue (60/40)
    ↓
Dealer Wallet → Credited Immediately ✅
Platform → Retains 40%
    ↓
Inspection → Status: "Draft" (Can Begin)
```

## 💰 Revenue Split Example

```
Inspection Fee: ₦10,000

Dealer (60%):    ₦6,000  → Credited to dealer wallet
Platform (40%):  ₦4,000  → Retained by platform
```

## 🏦 Withdrawal Flow

```
Dealer → Requests Withdrawal
    ↓
Admin → Reviews Request
    ↓
Admin → Approves/Rejects
    ↓
If Approved → Admin Processes
    ↓
Wallet → Amount Deducted
    ↓
Status → "Completed" ✅
```

## 📡 API Endpoints

### Payment
```bash
# Initiate payment
POST /api/v1/inspections/{id}/pay/

# Verify payment
POST /api/v1/inspections/{id}/verify-payment/
Body: { "reference": "veyu-inspection-123-abc" }
```

### Withdrawals
```bash
# List requests
GET /api/v1/wallet/withdrawal-requests/

# Create request
POST /api/v1/wallet/withdrawal-requests/
Body: { "amount": 10000, "payout_info_id": 5 }

# Cancel request
POST /api/v1/wallet/withdrawal-requests/{id}/cancel/

# Statistics
GET /api/v1/wallet/withdrawal-requests/statistics/
```

## 🎨 Admin Panel

### Revenue Settings
**Location:** Inspections → Inspection Revenue Settings
**Actions:** Configure split percentages

### Revenue Splits
**Location:** Inspections → Inspection Revenue Splits
**Actions:** View all splits (read-only)

### Withdrawal Requests
**Location:** Inspections → Withdrawal Requests
**Actions:** Approve, reject, process

## 💻 Frontend Integration

```javascript
// 1. Initiate payment
const response = await fetch(`/api/v1/inspections/${id}/pay/`, {
  method: 'POST',
  headers: { 'Authorization': `Token ${token}` }
});
const data = await response.json();

// 2. Show Paystack popup
const paystack = PaystackPop.setup({
  key: 'pk_live_xxxxx',
  email: data.data.email,
  amount: data.data.amount * 100, // Convert to kobo
  ref: data.data.reference,
  callback: function(response) {
    // 3. Verify payment
    verifyPayment(response.reference);
  },
  onClose: function() {
    alert('Payment cancelled');
  }
});
paystack.openIframe();

// 4. Verify payment
async function verifyPayment(reference) {
  const response = await fetch(
    `/api/v1/inspections/${id}/verify-payment/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ reference })
    }
  );
  const data = await response.json();
  
  if (data.success) {
    // Payment verified!
    // Dealer wallet credited
    // Inspection can begin
    console.log('Revenue split:', data.data.revenue_split);
  }
}
```

## 🧪 Testing

### Test Payment
```bash
# Use Paystack test keys
PAYSTACK_PUBLIC_KEY = 'pk_test_xxxxx'
PAYSTACK_SECRET_KEY = 'sk_test_xxxxx'

# Test card (success)
Card: 4084084084084081
CVV: 408
Expiry: Any future date
PIN: 0000
OTP: 123456
```

### Test Revenue Split
```python
from inspections.models import VehicleInspection

inspection = VehicleInspection.objects.get(id=123)
split = inspection.revenue_split

print(f"Dealer: ₦{split.dealer_amount} ({split.dealer_percentage}%)")
print(f"Platform: ₦{split.platform_amount} ({split.platform_percentage}%)")
print(f"Dealer Credited: {split.dealer_credited}")
```

### Test Withdrawal
```python
from inspections.models_revenue import WithdrawalRequest

# Create request
withdrawal = WithdrawalRequest.objects.create(
    user=dealer_user,
    wallet=dealer_wallet,
    amount=10000,
    payout_info=payout_info,
    status='pending'
)

# Approve
withdrawal.approve(admin_user)

# Process
withdrawal.process_withdrawal()
```

## 🔍 Troubleshooting

### Payment Not Splitting
- Check revenue settings exist and are active
- Verify payment transaction is completed
- Check logs for errors

### Dealer Not Credited
- Check `dealer_credited` field on split
- Verify dealer has a wallet
- Check transaction logs

### Withdrawal Stuck
- Check status in admin panel
- Verify admin approved request
- Check wallet balance sufficient

## 📚 Full Documentation

- **Complete Guide:** `docs/INSPECTION_PAYMENT_REVENUE_SHARING.md`
- **Implementation Details:** `INSPECTION_PAYMENT_IMPLEMENTATION.md`
- **Status:** `INSPECTION_PAYMENT_COMPLETE.md`

## ✅ Checklist

- [x] Migration applied
- [ ] Revenue settings created in admin
- [ ] Paystack keys configured
- [ ] Frontend integrated
- [ ] Payment flow tested
- [ ] Withdrawal flow tested

## 🎉 You're Ready!

The system is fully implemented and tested. Just:
1. Create revenue settings in admin
2. Configure Paystack keys
3. Update frontend to use Paystack
4. Test and deploy!

---

**Questions?** Check `docs/INSPECTION_PAYMENT_REVENUE_SHARING.md`
