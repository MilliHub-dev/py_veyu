# Withdrawal System with Paystack Account Verification

## Overview

The withdrawal system has been updated to include bank account details directly in the withdrawal request and support Paystack account verification before submission.

## Key Changes

### Before
- Withdrawal requests referenced `PayoutInformation` model
- No account verification
- Bank details stored separately

### After
- ✅ Bank account details stored directly in withdrawal request
- ✅ Paystack account verification endpoint
- ✅ Frontend can verify account before submission
- ✅ Verification status tracked in database

## New Fields in WithdrawalRequest

```python
# Bank account details
account_name = models.CharField(max_length=200)
account_number = models.CharField(max_length=20)
bank_name = models.CharField(max_length=200)
bank_code = models.CharField(max_length=10)

# Paystack verification
paystack_verified = models.BooleanField(default=False)
paystack_recipient_code = models.CharField(max_length=100, blank=True, null=True)
```

## API Endpoints

### 1. Verify Account Number

Verify bank account details with Paystack before creating withdrawal request.

**Endpoint:** `POST /api/v1/wallet/withdrawal-requests/verify-account/`

**Request:**
```json
{
  "account_number": "0123456789",
  "bank_code": "058"
}
```

**Response (Success):**
```json
{
  "success": true,
  "verified": true,
  "data": {
    "account_name": "JOHN DOE",
    "account_number": "0123456789",
    "bank_code": "058"
  },
  "message": "Account verified successfully"
}
```

**Response (Failed):**
```json
{
  "success": false,
  "verified": false,
  "error": "Account verification failed",
  "message": "Invalid account number or bank code"
}
```

### 2. Create Withdrawal Request

Create a withdrawal request with verified bank account details.

**Endpoint:** `POST /api/v1/wallet/withdrawal-requests/`

**Request:**
```json
{
  "amount": 10000.00,
  "account_name": "JOHN DOE",
  "account_number": "0123456789",
  "bank_name": "GTBank",
  "bank_code": "058",
  "paystack_verified": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "amount": 10000.00,
    "account_name": "JOHN DOE",
    "account_number": "0123456789",
    "bank_name": "GTBank",
    "bank_code": "058",
    "paystack_verified": true,
    "status": "pending",
    "date_created": "2025-11-27T12:00:00Z"
  },
  "message": "Withdrawal request submitted successfully. It will be reviewed by our team."
}
```

## Frontend Integration

### Complete Workflow

```javascript
// 1. Get list of banks
async function getBanks() {
  const response = await fetch('/api/v1/wallet/banks/', {
    headers: {
      'Authorization': `Token ${token}`
    }
  });
  return await response.json();
}

// 2. Verify account number
async function verifyAccount(accountNumber, bankCode) {
  const response = await fetch(
    '/api/v1/wallet/withdrawal-requests/verify-account/',
    {
      method: 'POST',
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        account_number: accountNumber,
        bank_code: bankCode
      })
    }
  );
  
  const data = await response.json();
  
  if (data.verified) {
    // Show verified account name
    console.log('Account Name:', data.data.account_name);
    return data.data;
  } else {
    // Show error
    alert(data.message);
    return null;
  }
}

// 3. Create withdrawal request
async function createWithdrawal(amount, accountDetails) {
  const response = await fetch(
    '/api/v1/wallet/withdrawal-requests/',
    {
      method: 'POST',
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        amount: amount,
        account_name: accountDetails.account_name,
        account_number: accountDetails.account_number,
        bank_name: accountDetails.bank_name,
        bank_code: accountDetails.bank_code,
        paystack_verified: true
      })
    }
  );
  
  return await response.json();
}

// Complete flow
async function handleWithdrawal() {
  // Step 1: Get banks
  const banks = await getBanks();
  showBankSelector(banks);
  
  // Step 2: User enters account number and selects bank
  const accountNumber = document.getElementById('account_number').value;
  const bankCode = document.getElementById('bank_code').value;
  
  // Step 3: Verify account
  const accountDetails = await verifyAccount(accountNumber, bankCode);
  
  if (!accountDetails) {
    return; // Verification failed
  }
  
  // Step 4: Show verified account name
  document.getElementById('account_name').value = accountDetails.account_name;
  document.getElementById('account_name').disabled = true;
  
  // Step 5: User enters amount and submits
  const amount = document.getElementById('amount').value;
  
  // Step 6: Create withdrawal request
  const result = await createWithdrawal(amount, {
    ...accountDetails,
    bank_name: getBankName(bankCode, banks)
  });
  
  if (result.success) {
    alert('Withdrawal request submitted successfully!');
    showWithdrawalConfirmation(result.data);
  }
}
```

### UI Example

```html
<form id="withdrawal-form">
  <h2>Request Withdrawal</h2>
  
  <!-- Amount -->
  <div class="form-group">
    <label>Amount (₦)</label>
    <input type="number" id="amount" min="100" step="0.01" required>
    <small>Minimum: ₦100</small>
  </div>
  
  <!-- Bank Selection -->
  <div class="form-group">
    <label>Bank</label>
    <select id="bank_code" required>
      <option value="">Select Bank</option>
      <!-- Populated from API -->
    </select>
  </div>
  
  <!-- Account Number -->
  <div class="form-group">
    <label>Account Number</label>
    <input type="text" id="account_number" maxlength="10" required>
    <button type="button" onclick="verifyAccount()">Verify Account</button>
  </div>
  
  <!-- Account Name (auto-filled after verification) -->
  <div class="form-group">
    <label>Account Name</label>
    <input type="text" id="account_name" disabled>
    <span id="verification-status"></span>
  </div>
  
  <!-- Submit -->
  <button type="submit" id="submit-btn" disabled>Submit Withdrawal Request</button>
</form>

<script>
async function verifyAccount() {
  const accountNumber = document.getElementById('account_number').value;
  const bankCode = document.getElementById('bank_code').value;
  
  if (!accountNumber || !bankCode) {
    alert('Please enter account number and select bank');
    return;
  }
  
  // Show loading
  document.getElementById('verification-status').innerHTML = 
    '<span style="color: orange;">Verifying...</span>';
  
  const result = await verifyAccountAPI(accountNumber, bankCode);
  
  if (result.verified) {
    // Show success
    document.getElementById('account_name').value = result.data.account_name;
    document.getElementById('verification-status').innerHTML = 
      '<span style="color: green;">✓ Verified</span>';
    document.getElementById('submit-btn').disabled = false;
  } else {
    // Show error
    document.getElementById('verification-status').innerHTML = 
      '<span style="color: red;">✗ Verification failed</span>';
    alert(result.message);
  }
}
</script>
```

## Bank Codes (Nigerian Banks)

Common bank codes for Paystack:

```javascript
const NIGERIAN_BANKS = [
  { name: 'Access Bank', code: '044' },
  { name: 'Citibank', code: '023' },
  { name: 'Ecobank Nigeria', code: '050' },
  { name: 'Fidelity Bank', code: '070' },
  { name: 'First Bank of Nigeria', code: '011' },
  { name: 'First City Monument Bank', code: '214' },
  { name: 'Guaranty Trust Bank', code: '058' },
  { name: 'Heritage Bank', code: '030' },
  { name: 'Keystone Bank', code: '082' },
  { name: 'Polaris Bank', code: '076' },
  { name: 'Providus Bank', code: '101' },
  { name: 'Stanbic IBTC Bank', code: '221' },
  { name: 'Standard Chartered Bank', code: '068' },
  { name: 'Sterling Bank', code: '232' },
  { name: 'Union Bank of Nigeria', code: '032' },
  { name: 'United Bank for Africa', code: '033' },
  { name: 'Unity Bank', code: '215' },
  { name: 'Wema Bank', code: '035' },
  { name: 'Zenith Bank', code: '057' }
];
```

## Admin Panel

### Withdrawal Request Display

The admin panel now shows:
- ✅ Account name
- ✅ Account number
- ✅ Bank name
- ✅ Bank code
- ✅ Paystack verification status (✓ Verified / ⚠ Not Verified)
- ✅ Paystack recipient code (if available)

### Verification Badge

Verified accounts show a green badge:
```
GTBank ✓ Verified
JOHN DOE - 0123456789
```

Unverified accounts show an orange warning:
```
GTBank ⚠ Not Verified
JOHN DOE - 0123456789
```

## Migration

### Apply Migration

```bash
python manage.py migrate inspections
```

This will:
1. Remove `payout_info` foreign key
2. Add `account_name` field
3. Add `account_number` field
4. Add `bank_name` field
5. Add `bank_code` field
6. Add `paystack_verified` field
7. Add `paystack_recipient_code` field

### Migration File

`inspections/migrations/0004_add_bank_details_to_withdrawal.py`

## Validation

### Account Number Validation

```python
# Must be 10 digits
# Must be numeric only
# Spaces and dashes removed automatically

def validate_account_number(account_number):
    clean = account_number.replace(' ', '').replace('-', '')
    
    if not clean.isdigit():
        raise ValidationError('Account number must contain only digits')
    
    if len(clean) != 10:
        raise ValidationError('Account number must be 10 digits')
    
    return clean
```

### Amount Validation

```python
# Minimum: ₦100
# Must not exceed wallet balance

def validate_amount(amount, wallet_balance):
    if amount < 100:
        raise ValidationError('Minimum withdrawal amount is ₦100')
    
    if amount > wallet_balance:
        raise ValidationError(
            f'Insufficient balance. Available: ₦{wallet_balance:,.2f}'
        )
    
    return amount
```

## Security

### Paystack Verification

- ✅ Account details verified with Paystack API
- ✅ Prevents typos and errors
- ✅ Ensures account exists and is active
- ✅ Returns correct account name

### Server-Side Validation

- ✅ Amount validated against wallet balance
- ✅ Account number format validated
- ✅ Only business accounts can request withdrawals
- ✅ Admin approval required

### Audit Trail

- ✅ All withdrawal requests logged
- ✅ Verification status tracked
- ✅ Paystack recipient code stored
- ✅ Complete history maintained

## Testing

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

### Test Withdrawal Request

```bash
curl -X POST "http://localhost:8000/api/v1/wallet/withdrawal-requests/" \
  -H "Authorization: Token {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 10000.00,
    "account_name": "JOHN DOE",
    "account_number": "0123456789",
    "bank_name": "GTBank",
    "bank_code": "058",
    "paystack_verified": true
  }'
```

## Files Modified

1. **inspections/models_revenue.py**
   - Updated `WithdrawalRequest` model with bank account fields
   - Removed `payout_info` foreign key
   - Added Paystack verification fields

2. **wallet/serializers.py**
   - Updated `WithdrawalRequestSerializer` with new fields
   - Updated `WithdrawalRequestCreateSerializer` with validation

3. **wallet/views_withdrawal.py**
   - Added `verify_account_number` endpoint
   - Updated withdrawal creation logic

4. **wallet/urls.py**
   - Added verification endpoint URL

5. **inspections/admin_revenue.py**
   - Updated admin display with new fields
   - Added verification status badge

6. **inspections/migrations/0004_add_bank_details_to_withdrawal.py**
   - Migration to update database schema

## Summary

✅ **Bank account details stored directly in withdrawal request**
✅ **Paystack account verification endpoint**
✅ **Frontend can verify before submission**
✅ **Verification status tracked**
✅ **Admin panel shows verification badge**
✅ **Complete audit trail**

The withdrawal system now provides a better user experience with account verification and stores all necessary bank details directly in the withdrawal request.

---

**Implementation Date:** November 27, 2025
**Status:** ✅ COMPLETE
**Migration Required:** Yes (`0004_add_bank_details_to_withdrawal.py`)
**Frontend Integration:** Required
