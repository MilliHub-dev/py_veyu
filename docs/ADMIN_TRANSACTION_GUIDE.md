# Admin Transaction Management Guide

## Overview

This guide explains how to use the enhanced transaction management features in the Django admin panel.

## Accessing the Admin Panel

**URL:** `https://veyu.cc/admin/`

**Login:** Use your admin credentials

---

## Transaction Management

### Viewing All Transactions

**URL:** `/admin/wallet/transaction/`

#### Features

1. **List View Columns:**
   - Transaction ID
   - Type Badge (color-coded)
   - Sender Information (name + email)
   - Recipient Information (name + email)
   - Amount (with +/- indicators)
   - Status Badge (color-coded)
   - Source (wallet/bank)
   - Transaction Reference
   - Date Created

2. **Color Coding:**
   - **Green badges:** Deposits, Completed status
   - **Red badges:** Withdrawals, Failed status
   - **Blue badges:** Payments
   - **Yellow badges:** Transfers Out, Pending status
   - **Cyan badges:** Transfers In
   - **Gray badges:** Charges, Reversed status
   - **Orange badges:** Locked status

3. **Filtering Options:**
   - Filter by Type (deposit, withdraw, transfer, payment, charge)
   - Filter by Status (pending, completed, failed, reversed, locked)
   - Filter by Source (wallet, bank)
   - Filter by Date (using date hierarchy)

4. **Search Functionality:**
   Search by:
   - Sender name
   - Recipient name
   - Transaction reference
   - Sender email
   - Recipient email
   - Narration/description

5. **Bulk Actions:**
   - Mark selected as completed
   - Mark selected as failed

#### How to Use

**Find a specific transaction:**
1. Use the search box to search by email, reference, or name
2. Or use filters on the right sidebar
3. Click on a transaction to view full details

**Filter by date:**
1. Use the date hierarchy at the top
2. Click on year → month → day to drill down

**Update transaction status:**
1. Select transactions using checkboxes
2. Choose action from dropdown (Mark as completed/failed)
3. Click "Go"

**View transaction details:**
1. Click on any transaction ID
2. View complete transaction information including:
   - All transaction fields
   - Related objects (orders, bookings, inspections)
   - Transaction metadata
   - Timestamps

---

## Wallet Management

### Viewing All Wallets

**URL:** `/admin/wallet/wallet/`

#### Features

1. **List View Columns:**
   - User Email
   - User Name
   - Ledger Balance (total balance)
   - Available Balance (unlocked balance)
   - Locked Amount (pending transactions)
   - Total Transactions
   - Currency
   - Date Created

2. **Color Coding:**
   - **Green:** Positive available balance
   - **Red:** Zero or negative balance
   - **Orange:** Locked amounts

3. **Filtering Options:**
   - Filter by Currency
   - Filter by Date Created

4. **Search Functionality:**
   Search by:
   - User email
   - User first name
   - User last name

#### Wallet Detail View

When you click on a wallet, you'll see:

1. **Basic Information:**
   - User details
   - Balance information
   - Currency

2. **Transaction Summary:**
   - Total Deposits
   - Total Withdrawals
   - Total Payments
   - Pending Transactions count

---

## Common Admin Tasks

### 1. Investigate a Failed Payment

**Steps:**
1. Go to `/admin/wallet/transaction/`
2. Filter by Status: "Failed"
3. Sort by Date (newest first)
4. Click on the transaction to view details
5. Check:
   - Transaction reference
   - Error message in narration
   - Related user email
   - Amount and type

**Actions:**
- Contact user if needed
- Check Paystack dashboard for more details
- Mark as completed if payment actually succeeded

### 2. Find User's Transaction History

**Steps:**
1. Go to `/admin/wallet/transaction/`
2. Search for user's email in search box
3. View all transactions for that user
4. Use filters to narrow down (e.g., only deposits)

### 3. Monitor Pending Transactions

**Steps:**
1. Go to `/admin/wallet/transaction/`
2. Filter by Status: "Pending"
3. Check how long they've been pending (days_old)
4. Investigate transactions pending > 24 hours

**Actions:**
- Check Paystack dashboard
- Contact payment provider if needed
- Mark as failed if payment won't complete

### 4. Verify a Specific Payment

**Steps:**
1. Get the transaction reference from user
2. Go to `/admin/wallet/transaction/`
3. Search for the reference
4. Verify:
   - Status is "Completed"
   - Amount matches
   - User received funds (check wallet balance)

### 5. Check Top Users by Transaction Volume

**API Method:**
```bash
curl -X GET "https://veyu.cc/api/v1/wallet/analytics/?days=30" \
  -H "Authorization: Token admin_token"
```

Look for the `top_users` section in the response.

### 6. Generate Transaction Report

**Steps:**
1. Go to `/admin/wallet/transaction/`
2. Apply desired filters (date range, type, status)
3. Select all transactions (checkbox at top)
4. Export using Django admin export feature (if installed)

Or use the API:
```bash
curl -X GET "https://veyu.cc/api/v1/wallet/analytics/?days=30" \
  -H "Authorization: Token admin_token" > report.json
```

---

## Transaction Analytics (API)

### Get Analytics Dashboard Data

**Endpoint:** `GET /api/v1/wallet/analytics/?days=30`

**What you get:**
- Transaction summary (deposits, withdrawals, payments, transfers)
- Daily transaction statistics
- Wallet statistics (total wallets, balances)
- Success/failure rates
- Top 10 users by transaction volume

**Example:**
```bash
curl -X GET "https://veyu.cc/api/v1/wallet/analytics/?days=7" \
  -H "Authorization: Token your_admin_token"
```

---

## Troubleshooting

### Transaction Not Showing Up

**Possible causes:**
1. Webhook not received from Paystack
2. Webhook signature verification failed
3. User ID mismatch in metadata

**How to check:**
1. Check application logs: `logs/django.log`
2. Check Paystack dashboard webhook logs
3. Verify environment variables are set correctly

### Duplicate Transactions

**Don't worry!** The system automatically handles duplicate webhooks. If you see the same reference twice, only one will be processed.

### Balance Mismatch

**Steps to investigate:**
1. Go to user's wallet in admin
2. Check "Transaction Summary" section
3. Verify:
   - Ledger Balance = sum of all completed transactions
   - Available Balance = Ledger Balance - Locked Amount
4. Check for pending/locked transactions

### Failed Transfer Not Refunded

**Steps:**
1. Find the failed transaction
2. Check if status is "failed" or "reversed"
3. Verify wallet balance was updated
4. If not, manually update:
   - Change status to "failed"
   - Update wallet ledger_balance

---

## Best Practices

1. **Regular Monitoring:**
   - Check pending transactions daily
   - Review failed transactions weekly
   - Monitor success rates monthly

2. **User Support:**
   - Always verify transaction reference
   - Check both admin panel and Paystack dashboard
   - Provide clear status updates to users

3. **Security:**
   - Never share transaction references publicly
   - Verify user identity before discussing transactions
   - Keep admin credentials secure

4. **Data Integrity:**
   - Don't manually edit completed transactions
   - Use bulk actions carefully
   - Always verify before marking as completed/failed

---

## Quick Reference

### Transaction Types
- **Deposit:** Money coming into wallet from bank
- **Withdraw:** Money going out to bank account
- **Transfer In:** Money received from another wallet
- **Transfer Out:** Money sent to another wallet
- **Payment:** Payment for services/products
- **Charge:** System fees/charges

### Transaction Status
- **Pending:** Being processed
- **Completed:** Successfully completed
- **Failed:** Transaction failed
- **Reversed:** Transaction was reversed/refunded
- **Locked:** Funds locked (e.g., escrow)

### Transaction Sources
- **Bank:** Payment via Paystack (card/bank transfer)
- **Wallet:** Payment from wallet balance

---

## Support

For admin-related issues:
- Check logs: `logs/django.log`
- Review Paystack dashboard
- Contact technical support
- Refer to: `docs/PAYSTACK_WEBHOOK_SETUP.md`

---

## Related Documentation

- [Paystack Webhook Setup](./PAYSTACK_WEBHOOK_SETUP.md)
- [Transaction History API](./TRANSACTION_HISTORY_API.md)
- [Implementation Summary](../PAYSTACK_WEBHOOK_IMPLEMENTATION.md)
