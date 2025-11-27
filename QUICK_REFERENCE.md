# 🚀 Quick Reference - Paystack Webhook & Transaction History

## 📍 Webhook URL
```
Production: https://veyu.cc/api/v1/hooks/payment-webhook/
Staging: https://staging.veyu.cc/api/v1/hooks/payment-webhook/
```

## 🔑 Environment Variables
```bash
PAYSTACK_TEST_PUBLIC_KEY=pk_test_xxxxx
PAYSTACK_TEST_SECRET_KEY=sk_test_xxxxx
PAYSTACK_LIVE_PUBLIC_KEY=pk_live_xxxxx
PAYSTACK_LIVE_SECRET_KEY=sk_live_xxxxx
```

## 📡 API Endpoints

### User Endpoints
```bash
# Get transaction history
GET /api/v1/wallet/transactions/
Query params: type, status, source, start_date, end_date, limit, offset

# Get transaction summary
GET /api/v1/wallet/transactions/summary/

# Get wallet balance
GET /api/v1/wallet/balance/
```

### Admin Endpoints
```bash
# Get analytics (staff only)
GET /api/v1/wallet/analytics/?days=30
```

### Admin Panel
```
Transactions: /admin/wallet/transaction/
Wallets: /admin/wallet/wallet/
```

## 💻 Code Examples

### Frontend: Get Transactions
```javascript
fetch('https://veyu.cc/api/v1/wallet/transactions/?limit=20', {
  headers: { 'Authorization': 'Token ' + userToken }
})
.then(res => res.json())
.then(data => console.log(data.transactions));
```

### Backend: Payment Metadata
```python
metadata = {
    'purpose': 'inspection',  # or 'wallet_deposit', 'order', 'booking'
    'related_id': inspection.id,
    'user_id': request.user.id
}
```

### Python: Get Analytics
```python
from wallet.analytics import TransactionAnalytics

summary = TransactionAnalytics.get_transaction_summary()
top_users = TransactionAnalytics.get_top_users_by_transaction_volume()
```

## 🎨 Transaction Types
- `deposit` - Wallet deposit from bank
- `withdraw` - Withdrawal to bank
- `transfer_in` - Received from another wallet
- `transfer_out` - Sent to another wallet
- `payment` - Payment for services
- `charge` - System charges

## 📊 Transaction Status
- `pending` - Being processed
- `completed` - Successfully completed
- `failed` - Transaction failed
- `reversed` - Reversed/refunded
- `locked` - Locked (escrow)

## 🔍 Filtering Examples
```bash
# Get deposits only
GET /api/v1/wallet/transactions/?type=deposit

# Get failed transactions
GET /api/v1/wallet/transactions/?status=failed

# Get transactions from last 7 days
GET /api/v1/wallet/transactions/?start_date=2025-11-20

# Get bank transactions
GET /api/v1/wallet/transactions/?source=bank

# Pagination
GET /api/v1/wallet/transactions/?limit=20&offset=40
```

## 🐛 Troubleshooting

### Check Webhook Logs
```bash
tail -f logs/django.log | grep "Paystack webhook"
```

### Test Webhook Locally
```bash
curl -X POST http://localhost:8000/api/v1/hooks/payment-webhook/ \
  -H "Content-Type: application/json" \
  -H "X-Paystack-Signature: test" \
  -d '{"event":"charge.success","data":{"reference":"test"}}'
```

### Check Transaction Status
```python
from wallet.models import Transaction
tx = Transaction.objects.get(tx_ref='PSK_123456')
print(f"Status: {tx.status}")
```

## 📚 Documentation
- Setup Guide: `docs/PAYSTACK_WEBHOOK_SETUP.md`
- API Docs: `docs/TRANSACTION_HISTORY_API.md`
- Admin Guide: `docs/ADMIN_TRANSACTION_GUIDE.md`
- Full Overview: `docs/TRANSACTION_FEATURES_README.md`

## ✅ Quick Setup
1. Configure webhook in Paystack dashboard
2. Set environment variables
3. Test with Paystack test cards
4. Monitor logs for webhook processing

## 🎯 Key Features
✅ Automatic payment processing
✅ Transaction history with filtering
✅ Admin dashboard with analytics
✅ Email notifications
✅ Duplicate webhook handling
✅ Comprehensive documentation

---
**Status:** ✅ Ready for Production
**Last Updated:** November 27, 2025
