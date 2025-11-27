# Transaction History API Documentation

## Overview

This document describes the transaction history and analytics endpoints available in the Veyu platform.

## Base URL

- **Production:** `https://veyu.cc/api/v1/wallet/`
- **Staging:** `https://staging.veyu.cc/api/v1/wallet/`

## Authentication

All endpoints require authentication using Token Authentication:

```
Authorization: Token your_auth_token_here
```

---

## Endpoints

### 1. Get Transaction History

Retrieve paginated transaction history with filtering options.

**Endpoint:** `GET /wallet/transactions/`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | No | Filter by transaction type: `deposit`, `withdraw`, `transfer_in`, `transfer_out`, `payment`, `charge` |
| `status` | string | No | Filter by status: `pending`, `completed`, `failed`, `reversed`, `locked` |
| `source` | string | No | Filter by source: `wallet`, `bank` |
| `start_date` | string | No | Filter from date (format: YYYY-MM-DD) |
| `end_date` | string | No | Filter to date (format: YYYY-MM-DD) |
| `limit` | integer | No | Number of results per page (default: 50, max: 100) |
| `offset` | integer | No | Pagination offset (default: 0) |

**Example Request:**

```bash
curl -X GET "https://veyu.cc/api/v1/wallet/transactions/?type=deposit&status=completed&limit=20" \
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
      "related_inspection_id": 45
    }
  ]
}
```

---

### 2. Get Transaction Summary

Get a quick summary of user's transaction statistics.

**Endpoint:** `GET /wallet/transactions/summary/`

**Example Request:**

```bash
curl -X GET "https://veyu.cc/api/v1/wallet/transactions/summary/" \
  -H "Authorization: Token your_auth_token"
```

**Example Response:**

```json
{
  "error": false,
  "wallet": {
    "balance": 27000.00,
    "ledger_balance": 27000.00,
    "locked_amount": 0.00,
    "currency": "NGN"
  },
  "summary": {
    "total_deposits": 50000.00,
    "total_withdrawals": 10000.00,
    "total_payments": 15000.00,
    "total_received": 5000.00,
    "total_sent": 3000.00,
    "total_transactions": 45,
    "pending_transactions": 2
  },
  "recent_transactions": [
    {
      "id": 123,
      "sender_name": "John Doe",
      "recipient_name": "Veyu",
      "amount": 5000.00,
      "type": "deposit",
      "status": "completed",
      "date_created": "2025-11-25T10:30:00Z"
    }
  ]
}
```

---

### 3. Get Transaction Analytics (Admin Only)

Get comprehensive transaction analytics and statistics. Requires admin/staff privileges.

**Endpoint:** `GET /wallet/analytics/`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `days` | integer | No | Number of days to analyze (default: 30) |

**Example Request:**

```bash
curl -X GET "https://veyu.cc/api/v1/wallet/analytics/?days=30" \
  -H "Authorization: Token admin_auth_token"
```

**Example Response:**

```json
{
  "error": false,
  "summary": {
    "period": {
      "start_date": "2025-10-27T00:00:00Z",
      "end_date": "2025-11-27T00:00:00Z",
      "days": 30
    },
    "totals": {
      "deposits": {
        "count": 150,
        "amount": 2500000.00
      },
      "withdrawals": {
        "count": 45,
        "amount": 500000.00
      },
      "payments": {
        "count": 200,
        "amount": 1800000.00
      },
      "transfers": {
        "count": 80,
        "amount": 300000.00
      }
    },
    "status": {
      "pending": 5,
      "completed": 470,
      "failed": 10
    },
    "sources": {
      "bank": {
        "count": 250,
        "amount": 3200000.00
      },
      "wallet": {
        "count": 235,
        "amount": 900000.00
      }
    },
    "total_transaction_count": 485,
    "total_transaction_volume": 5100000.00
  },
  "daily_stats": [
    {
      "date": "2025-11-20",
      "count": 25,
      "total_amount": 180000.00,
      "deposits": 10,
      "withdrawals": 3,
      "payments": 12
    }
  ],
  "wallet_statistics": {
    "total_wallets": 1250,
    "active_wallets": 890,
    "total_balance": 15000000.00,
    "average_balance": 12000.00,
    "top_wallet_balance": 500000.00,
    "top_wallet_user": "topuser@example.com"
  },
  "success_rate": {
    "period_days": 30,
    "total_transactions": 485,
    "completed": 470,
    "failed": 10,
    "pending": 5,
    "success_rate": 96.91,
    "failure_rate": 2.06
  },
  "top_users": [
    {
      "user_id": 123,
      "user_email": "user@example.com",
      "user_name": "John Doe",
      "balance": 50000.00,
      "total_transactions": 45,
      "total_volume": 250000.00
    }
  ]
}
```

---

## Transaction Types

| Type | Description | Direction |
|------|-------------|-----------|
| `deposit` | Deposit into wallet from bank | Incoming |
| `withdraw` | Withdrawal from wallet to bank | Outgoing |
| `transfer_in` | Transfer received from another wallet | Incoming |
| `transfer_out` | Transfer sent to another wallet | Outgoing |
| `payment` | Payment for services/products | Outgoing |
| `charge` | System charges/fees | Outgoing |

## Transaction Status

| Status | Description |
|--------|-------------|
| `pending` | Transaction is being processed |
| `completed` | Transaction completed successfully |
| `failed` | Transaction failed |
| `reversed` | Transaction was reversed/refunded |
| `locked` | Transaction is locked (e.g., escrow) |

## Transaction Sources

| Source | Description |
|--------|-------------|
| `wallet` | Transaction from user's wallet balance |
| `bank` | Transaction via bank/card (Paystack) |

---

## Filtering Examples

### Get all deposits in the last 7 days

```bash
curl -X GET "https://veyu.cc/api/v1/wallet/transactions/?type=deposit&start_date=2025-11-20" \
  -H "Authorization: Token your_auth_token"
```

### Get all failed transactions

```bash
curl -X GET "https://veyu.cc/api/v1/wallet/transactions/?status=failed" \
  -H "Authorization: Token your_auth_token"
```

### Get all bank transactions

```bash
curl -X GET "https://veyu.cc/api/v1/wallet/transactions/?source=bank" \
  -H "Authorization: Token your_auth_token"
```

### Get transactions for a specific date range

```bash
curl -X GET "https://veyu.cc/api/v1/wallet/transactions/?start_date=2025-11-01&end_date=2025-11-30" \
  -H "Authorization: Token your_auth_token"
```

### Paginate through results

```bash
# First page
curl -X GET "https://veyu.cc/api/v1/wallet/transactions/?limit=20&offset=0" \
  -H "Authorization: Token your_auth_token"

# Second page
curl -X GET "https://veyu.cc/api/v1/wallet/transactions/?limit=20&offset=20" \
  -H "Authorization: Token your_auth_token"
```

---

## Admin Dashboard

### Viewing All Transactions

Admins can view all transactions in the Django admin panel:

**URL:** `/admin/wallet/transaction/`

**Features:**
- Filter by type, status, source, date
- Search by reference, email, narration
- Color-coded status badges
- Transaction details and summaries
- Bulk actions (mark as completed/failed)

### Transaction Analytics Dashboard

Access comprehensive analytics:

**URL:** `/admin/wallet/wallet/`

**Features:**
- Wallet statistics
- Transaction summaries
- Top users by volume
- Success/failure rates

---

## Error Responses

### 400 Bad Request

```json
{
  "error": "Invalid date format. Use YYYY-MM-DD"
}
```

### 401 Unauthorized

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden (Admin endpoints)

```json
{
  "error": "Permission denied. Admin access required."
}
```

### 404 Not Found

```json
{
  "error": "Wallet not found for user"
}
```

---

## Best Practices

1. **Use pagination** - Always use `limit` and `offset` for large result sets
2. **Filter by date** - Use date filters to reduce response size
3. **Cache results** - Cache transaction summaries on the frontend
4. **Monitor pending** - Regularly check for pending transactions
5. **Handle errors** - Always handle error responses gracefully

---

## Related Documentation

- [Paystack Webhook Setup](./PAYSTACK_WEBHOOK_SETUP.md)
- [Wallet API Documentation](./WALLET_API.md)
- [Inspection Payment Flow](./INSPECTION_PAYMENT_SUMMARY.md)

---

## Support

For API-related issues:
- Check application logs
- Review error responses
- Contact support: support@veyu.cc
