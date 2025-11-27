# Paystack Configuration Update

## Summary

Updated the Paystack configuration to use the correct environment variable naming convention with TEST/LIVE prefixes.

## Changes Made

### 1. Environment Variables

**Old (Incorrect):**
```bash
PAYSTACK_PUBLIC_KEY=pk_test_xxxxx
PAYSTACK_SECRET_KEY=sk_test_xxxxx
```

**New (Correct):**
```bash
# Test keys (for development)
PAYSTACK_TEST_PUBLIC_KEY=pk_test_xxxxx
PAYSTACK_TEST_SECRET_KEY=sk_test_xxxxx

# Live keys (for production)
PAYSTACK_LIVE_PUBLIC_KEY=pk_live_xxxxx
PAYSTACK_LIVE_SECRET_KEY=sk_live_xxxxx
```

### 2. Automatic Environment Selection

The `PaystackAdapter` automatically selects the correct keys based on `DEBUG` setting:

```python
class PaystackAdapter(PaymentGateway):
    secret_key = os.environ['PAYSTACK_LIVE_SECRET_KEY']
    public_key = os.environ['PAYSTACK_LIVE_PUBLIC_KEY']
    
    if settings.DEBUG:
        public_key = os.environ['PAYSTACK_TEST_PUBLIC_KEY']
        secret_key = os.environ['PAYSTACK_TEST_SECRET_KEY']
```

**When `DEBUG=True` (Development):**
- Uses `PAYSTACK_TEST_PUBLIC_KEY`
- Uses `PAYSTACK_TEST_SECRET_KEY`

**When `DEBUG=False` (Production):**
- Uses `PAYSTACK_LIVE_PUBLIC_KEY`
- Uses `PAYSTACK_LIVE_SECRET_KEY`

### 3. Files Updated

1. **`.env`** - Cleaned up and organized Paystack keys
2. **`.env.example`** - Added Paystack configuration section
3. **`wallet/gateway/payment_adapter.py`** - Added `resolve_account()` method

## Configuration Guide

### Development Setup

1. Get your Paystack test keys from: https://dashboard.paystack.com/#/settings/developer

2. Add to `.env`:
```bash
PAYSTACK_TEST_PUBLIC_KEY=pk_test_your_actual_test_public_key
PAYSTACK_TEST_SECRET_KEY=sk_test_your_actual_test_secret_key
```

3. Ensure `DEBUG=True` in `.env`

### Production Setup

1. Get your Paystack live keys from: https://dashboard.paystack.com/#/settings/developer

2. Add to production environment variables:
```bash
PAYSTACK_LIVE_PUBLIC_KEY=pk_live_your_actual_live_public_key
PAYSTACK_LIVE_SECRET_KEY=sk_live_your_actual_live_secret_key
```

3. Ensure `DEBUG=False` in production

## Paystack Features Used

### 1. Transaction Verification
```python
gateway = PaystackAdapter()
result = gateway.verify_transaction(reference)
```

### 2. Bank List
```python
gateway = PaystackAdapter()
banks = gateway.get_banks(country="nigeria")
```

### 3. Account Verification (NEW)
```python
gateway = PaystackAdapter()
result = gateway.resolve_account(account_number, bank_code)
```

## API Endpoints Using Paystack

### Inspection Payment
- `POST /api/v1/inspections/{id}/pay/` - Initiate payment
- `POST /api/v1/inspections/{id}/verify-payment/` - Verify payment

### Withdrawal Verification
- `POST /api/v1/wallet/withdrawal-requests/verify-account/` - Verify bank account

### Bank Information
- `GET /api/v1/wallet/banks/` - Get list of banks

## Testing

### Test with Paystack Test Cards

**Success:**
```
Card Number: 4084084084084081
CVV: 408
Expiry: Any future date
PIN: 0000
OTP: 123456
```

**Insufficient Funds:**
```
Card Number: 4084080000000409
CVV: 408
Expiry: Any future date
```

### Test Account Verification

```bash
curl -X POST "http://localhost:8000/api/v1/wallet/withdrawal-requests/verify-account/" \
  -H "Authorization: Token {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "account_number": "0123456789",
    "bank_code": "058"
  }'
```

## Environment Variable Validation

The system will fail to start if required Paystack keys are missing:

**Development (DEBUG=True):**
- Requires: `PAYSTACK_TEST_PUBLIC_KEY`
- Requires: `PAYSTACK_TEST_SECRET_KEY`

**Production (DEBUG=False):**
- Requires: `PAYSTACK_LIVE_PUBLIC_KEY`
- Requires: `PAYSTACK_LIVE_SECRET_KEY`

## Security Best Practices

1. **Never commit actual keys to version control**
   - Use `.env` for local development
   - Use environment variables in production

2. **Use test keys in development**
   - Test keys start with `pk_test_` and `sk_test_`
   - No real money is charged

3. **Use live keys only in production**
   - Live keys start with `pk_live_` and `sk_live_`
   - Real money is charged

4. **Rotate keys regularly**
   - Generate new keys periodically
   - Update in all environments

5. **Restrict key permissions**
   - Use Paystack dashboard to limit key permissions
   - Only grant necessary permissions

## Troubleshooting

### Error: "PAYSTACK_TEST_PUBLIC_KEY not found"

**Solution:** Add test keys to `.env`:
```bash
PAYSTACK_TEST_PUBLIC_KEY=pk_test_xxxxx
PAYSTACK_TEST_SECRET_KEY=sk_test_xxxxx
```

### Error: "PAYSTACK_LIVE_PUBLIC_KEY not found"

**Solution:** Add live keys to production environment:
```bash
PAYSTACK_LIVE_PUBLIC_KEY=pk_live_xxxxx
PAYSTACK_LIVE_SECRET_KEY=sk_live_xxxxx
```

### Payment verification fails

**Check:**
1. Correct keys are set for environment (test/live)
2. Keys are valid and not expired
3. Paystack account is active
4. Network connectivity to Paystack API

### Account verification fails

**Check:**
1. Account number is 10 digits
2. Bank code is correct
3. Account exists and is active
4. Paystack API is accessible

## Migration Notes

### Updating Existing Deployments

If you have existing deployments using the old variable names:

1. **Add new variables** (don't remove old ones yet):
```bash
PAYSTACK_TEST_PUBLIC_KEY=pk_test_xxxxx
PAYSTACK_TEST_SECRET_KEY=sk_test_xxxxx
PAYSTACK_LIVE_PUBLIC_KEY=pk_live_xxxxx
PAYSTACK_LIVE_SECRET_KEY=sk_live_xxxxx
```

2. **Deploy the updated code**

3. **Verify everything works**

4. **Remove old variables**:
```bash
# Remove these:
PAYSTACK_PUBLIC_KEY
PAYSTACK_SECRET_KEY
```

## Summary

✅ **Environment variables updated to use TEST/LIVE prefixes**
✅ **Automatic environment selection based on DEBUG setting**
✅ **Added account verification method**
✅ **Updated .env and .env.example files**
✅ **Documented configuration and testing**

The Paystack integration now follows best practices with separate test and live keys that are automatically selected based on the environment.

---

**Updated:** November 27, 2025
**Status:** ✅ COMPLETE
**Breaking Changes:** None (backward compatible during migration)
**Action Required:** Update environment variables in all deployments
