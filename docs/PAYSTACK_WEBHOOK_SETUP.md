# Paystack Webhook Setup Guide

## Overview

This guide explains how to set up and configure Paystack webhooks for automatic payment processing in the Veyu platform.

## What are Webhooks?

Webhooks allow Paystack to notify your application in real-time when events occur (e.g., successful payments, failed transfers). This enables automatic payment verification without manual intervention.

## Webhook Endpoint

**Production URL:** `https://veyu.cc/api/v1/hooks/payment-webhook/`
**Staging URL:** `https://staging.veyu.cc/api/v1/hooks/payment-webhook/`

## Supported Events

The webhook handler processes the following Paystack events:

### 1. `charge.success`
Triggered when a payment is successfully charged.

**Handles:**
- Wallet deposits
- Inspection payments
- Vehicle order payments
- Service booking payments

### 2. `transfer.success`
Triggered when a payout/transfer is successful.

**Handles:**
- Wallet withdrawal confirmations
- Payout completions

### 3. `transfer.failed`
Triggered when a transfer fails.

**Handles:**
- Automatic wallet refunds
- Transaction status updates

### 4. `transfer.reversed`
Triggered when a transfer is reversed.

**Handles:**
- Automatic wallet refunds
- Transaction reversal tracking

## Setup Instructions

### Step 1: Configure Webhook URL in Paystack Dashboard

1. Log in to your [Paystack Dashboard](https://dashboard.paystack.com/)
2. Navigate to **Settings** → **Webhooks**
3. Add webhook URL:
   - **Test Mode:** `https://staging.veyu.cc/api/v1/hooks/payment-webhook/`
   - **Live Mode:** `https://veyu.cc/api/v1/hooks/payment-webhook/`
4. Click **Save**

### Step 2: Select Events to Listen To

In the Paystack webhook settings, select these events:
- ✅ `charge.success`
- ✅ `transfer.success`
- ✅ `transfer.failed`
- ✅ `transfer.reversed`

### Step 3: Verify Secret Key Configuration

Ensure your environment variables are set:

```bash
# Test Environment
PAYSTACK_TEST_PUBLIC_KEY=pk_test_xxxxxxxxxxxxx
PAYSTACK_TEST_SECRET_KEY=sk_test_xxxxxxxxxxxxx

# Live Environment
PAYSTACK_LIVE_PUBLIC_KEY=pk_live_xxxxxxxxxxxxx
PAYSTACK_LIVE_SECRET_KEY=sk_live_xxxxxxxxxxxxx
```

## Payment Metadata Structure

When initiating payments, include metadata to help the webhook identify the payment purpose:

### Wallet Deposit
```json
{
  "purpose": "wallet_deposit",
  "user_id": 123
}
```

### Inspection Payment
```json
{
  "purpose": "inspection",
  "related_id": 456,
  "user_id": 123
}
```

### Order Payment
```json
{
  "purpose": "order",
  "related_id": 789,
  "user_id": 123
}
```

### Booking Payment
```json
{
  "purpose": "booking",
  "related_id": 321,
  "user_id": 123
}
```

## Testing Webhooks

### Using Paystack Test Mode

1. Use test cards from [Paystack Test Cards](https://paystack.com/docs/payments/test-payments/)
2. Initiate a test payment
3. Check your application logs for webhook processing

### Manual Webhook Testing

You can manually trigger webhooks using curl:

```bash
# Generate signature
SECRET_KEY="your_secret_key"
PAYLOAD='{"event":"charge.success","data":{"reference":"test_ref_123","amount":500000,"customer":{"email":"test@example.com"},"metadata":{"purpose":"wallet_deposit","user_id":1}}}'

SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha512 -hmac "$SECRET_KEY" | awk '{print $2}')

# Send webhook
curl -X POST https://staging.veyu.cc/api/v1/hooks/payment-webhook/ \
  -H "Content-Type: application/json" \
  -H "X-Paystack-Signature: $SIGNATURE" \
  -d "$PAYLOAD"
```

## Security

### Signature Verification

All webhook requests are verified using HMAC SHA512 signature:

1. Paystack signs the payload with your secret key
2. The signature is sent in the `X-Paystack-Signature` header
3. Our webhook handler verifies the signature before processing

**Never disable signature verification in production!**

### IP Whitelisting (Optional)

For additional security, you can whitelist Paystack's IP addresses in your firewall:
- `52.31.139.75`
- `52.49.173.169`
- `52.214.14.220`

## Monitoring and Debugging

### Check Webhook Logs

View webhook activity in your application logs:

```bash
# View recent webhook logs
tail -f logs/django.log | grep "Paystack webhook"
```

### Common Issues

#### 1. Signature Verification Failed
**Cause:** Wrong secret key or payload tampering
**Solution:** Verify `PAYSTACK_SECRET_KEY` matches your dashboard

#### 2. User Not Found
**Cause:** Invalid `user_id` in metadata
**Solution:** Ensure correct user ID is passed in payment metadata

#### 3. Transaction Already Processed
**Cause:** Duplicate webhook delivery (normal behavior)
**Solution:** No action needed - system handles duplicates automatically

#### 4. Related Object Not Found
**Cause:** Invalid `related_id` in metadata
**Solution:** Verify the inspection/order/booking ID exists

## Transaction History

### Admin Dashboard

View all transactions in Django Admin:
- URL: `/admin/wallet/transaction/`
- Features:
  - Filter by type, status, source, date
  - Search by reference, email, narration
  - Color-coded status badges
  - Transaction summaries

### User API Endpoint

Users can view their transaction history:

**Endpoint:** `GET /api/v1/wallet/transactions/`

**Query Parameters:**
- `type` - Filter by transaction type
- `status` - Filter by status
- `source` - Filter by source (wallet/bank)
- `start_date` - Filter from date (YYYY-MM-DD)
- `end_date` - Filter to date (YYYY-MM-DD)
- `limit` - Number of results (default: 50)
- `offset` - Pagination offset (default: 0)

**Example Request:**
```bash
curl -X GET "https://veyu.cc/api/v1/wallet/transactions/?type=deposit&limit=20" \
  -H "Authorization: Token your_auth_token"
```

**Example Response:**
```json
{
  "error": false,
  "summary": {
    "total_deposits": 50000.00,
    "total_withdrawals": 10000.00,
    "total_payments": 15000.00,
    "total_received": 5000.00,
    "total_sent": 3000.00,
    "current_balance": 27000.00,
    "ledger_balance": 27000.00
  },
  "pagination": {
    "total": 45,
    "limit": 20,
    "offset": 0,
    "has_more": true
  },
  "transactions": [
    {
      "id": 123,
      "sender_name": "John Doe",
      "sender_email": "john@example.com",
      "recipient_name": "Veyu",
      "recipient_email": null,
      "amount": 5000.00,
      "formatted_amount": "₦5,000.00",
      "type": "deposit",
      "type_display": "Deposit",
      "status": "completed",
      "status_display": "Completed",
      "source": "bank",
      "source_display": "Bank",
      "tx_ref": "PSK_123456789",
      "narration": "Wallet deposit via Paystack",
      "transaction_direction": "Incoming",
      "days_old": 2,
      "is_successful": true,
      "is_pending": false,
      "date_created": "2025-11-25T10:30:00Z",
      "last_updated": "2025-11-25T10:30:05Z",
      "related_order_id": null,
      "related_booking_id": null,
      "related_inspection_id": null
    }
  ]
}
```

## Email Notifications

The webhook automatically sends email notifications for:

### Wallet Deposits
- **Template:** `wallet_deposit_success`
- **Recipient:** User who made the deposit
- **Content:** Amount, new balance, reference

### Inspection Payments
- **Template:** `inspection_payment_success`
- **Recipient:** User who paid
- **Content:** Inspection details, amount, reference

## Best Practices

1. **Always include metadata** - Helps identify payment purpose
2. **Use unique references** - Prevents duplicate processing
3. **Monitor webhook logs** - Catch issues early
4. **Test in staging first** - Verify webhook behavior before going live
5. **Handle idempotency** - System automatically handles duplicate webhooks
6. **Keep secret keys secure** - Never commit to version control

## Support

For webhook-related issues:
1. Check application logs: `logs/django.log`
2. Verify Paystack dashboard webhook logs
3. Contact Paystack support: support@paystack.com
4. Review this documentation

## Related Documentation

- [Paystack Webhook Documentation](https://paystack.com/docs/payments/webhooks/)
- [Inspection Payment Flow](./INSPECTION_PAYMENT_SUMMARY.md)
- [Wallet API Documentation](./WALLET_API.md)
