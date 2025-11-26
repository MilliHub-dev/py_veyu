# Paystack Integration for Inspection Payments

## Overview

Inspection payments support Paystack for bank payments (card, bank transfer, USSD, QR code). This guide shows how to integrate Paystack on the frontend.

## Payment Flow

```
1. Customer initiates payment
   ↓
2. Backend creates pending transaction & returns reference
   ↓
3. Frontend opens Paystack checkout with reference
   ↓
4. Customer completes payment on Paystack
   ↓
5. Frontend receives success callback
   ↓
6. Frontend calls verify endpoint with reference
   ↓
7. Backend verifies with Paystack & marks inspection as paid
```

## Backend Endpoints

### 1. Initiate Payment

**Endpoint:** `POST /api/v1/inspections/{inspection_id}/pay/`

**Request:**
```json
{
  "payment_method": "bank",
  "amount": 50000.00
}
```

**Response:**
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

### 2. Verify Payment

**Endpoint:** `POST /api/v1/inspections/{inspection_id}/verify-payment/`

**Request:**
```json
{
  "reference": "veyu-inspection-1-abc123def456"
}
```

**Response:**
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

## Frontend Integration

### Option 1: Paystack Popup (Recommended)

#### Step 1: Include Paystack Script

```html
<script src="https://js.paystack.co/v1/inline.js"></script>
```

#### Step 2: Initialize Payment

```javascript
async function payForInspection(inspectionId, amount) {
  try {
    // 1. Initiate payment on backend
    const response = await fetch(`/api/v1/inspections/${inspectionId}/pay/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        payment_method: 'bank',
        amount: amount
      })
    });
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.error || 'Payment initiation failed');
    }
    
    // 2. Open Paystack popup
    const paystack = PaystackPop.setup({
      key: 'YOUR_PAYSTACK_PUBLIC_KEY', // Replace with your public key
      email: data.data.email,
      amount: data.data.amount * 100, // Convert to kobo
      ref: data.data.reference,
      currency: data.data.currency,
      
      onSuccess: async (transaction) => {
        console.log('Payment successful:', transaction);
        
        // 3. Verify payment on backend
        await verifyPayment(inspectionId, transaction.reference);
      },
      
      onCancel: () => {
        console.log('Payment cancelled by user');
        alert('Payment was cancelled');
      }
    });
    
    paystack.openIframe();
    
  } catch (error) {
    console.error('Payment error:', error);
    alert('Payment failed: ' + error.message);
  }
}

async function verifyPayment(inspectionId, reference) {
  try {
    const response = await fetch(`/api/v1/inspections/${inspectionId}/verify-payment/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        reference: reference
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      alert('Payment verified! Inspection can now begin.');
      // Redirect to inspection page or update UI
      window.location.href = `/inspections/${inspectionId}`;
    } else {
      alert('Payment verification failed: ' + data.error);
    }
    
  } catch (error) {
    console.error('Verification error:', error);
    alert('Payment verification failed');
  }
}
```

#### Step 3: Trigger Payment

```html
<button onclick="payForInspection(1, 50000)">
  Pay ₦50,000 for Inspection
</button>
```

### Option 2: React/Vue Integration

#### React Example

```jsx
import { useState } from 'react';
import { PaystackButton } from 'react-paystack';

function InspectionPayment({ inspectionId, amount, email }) {
  const [paymentData, setPaymentData] = useState(null);
  const publicKey = 'YOUR_PAYSTACK_PUBLIC_KEY';
  
  // Initialize payment
  const initiatePayment = async () => {
    try {
      const response = await fetch(`/api/v1/inspections/${inspectionId}/pay/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          payment_method: 'bank',
          amount: amount
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setPaymentData(data.data);
      }
    } catch (error) {
      console.error('Payment initiation failed:', error);
    }
  };
  
  // Verify payment
  const verifyPayment = async (reference) => {
    try {
      const response = await fetch(`/api/v1/inspections/${inspectionId}/verify-payment/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ reference })
      });
      
      const data = await response.json();
      
      if (data.success) {
        alert('Payment successful!');
        // Navigate to inspection page
      }
    } catch (error) {
      console.error('Verification failed:', error);
    }
  };
  
  const componentProps = {
    email: paymentData?.email || email,
    amount: (paymentData?.amount || amount) * 100,
    reference: paymentData?.reference,
    publicKey,
    text: 'Pay Now',
    onSuccess: (reference) => verifyPayment(reference.reference),
    onClose: () => alert('Payment cancelled'),
  };
  
  return (
    <div>
      <button onClick={initiatePayment}>Initialize Payment</button>
      
      {paymentData && (
        <PaystackButton {...componentProps} />
      )}
    </div>
  );
}
```

#### Vue Example

```vue
<template>
  <div>
    <button @click="initiatePayment">Pay ₦{{ amount }}</button>
    
    <paystack
      v-if="paymentData"
      :amount="paymentData.amount * 100"
      :email="paymentData.email"
      :paystackkey="publicKey"
      :reference="paymentData.reference"
      :callback="verifyPayment"
      :close="onClose"
    >
      Complete Payment
    </paystack>
  </div>
</template>

<script>
import Paystack from 'vue-paystack';

export default {
  components: {
    Paystack
  },
  data() {
    return {
      publicKey: 'YOUR_PAYSTACK_PUBLIC_KEY',
      paymentData: null
    };
  },
  props: {
    inspectionId: Number,
    amount: Number
  },
  methods: {
    async initiatePayment() {
      try {
        const response = await fetch(`/api/v1/inspections/${this.inspectionId}/pay/`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.authToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            payment_method: 'bank',
            amount: this.amount
          })
        });
        
        const data = await response.json();
        
        if (data.success) {
          this.paymentData = data.data;
        }
      } catch (error) {
        console.error('Payment initiation failed:', error);
      }
    },
    
    async verifyPayment(response) {
      try {
        const result = await fetch(`/api/v1/inspections/${this.inspectionId}/verify-payment/`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.authToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            reference: response.reference
          })
        });
        
        const data = await result.json();
        
        if (data.success) {
          this.$router.push(`/inspections/${this.inspectionId}`);
        }
      } catch (error) {
        console.error('Verification failed:', error);
      }
    },
    
    onClose() {
      console.log('Payment cancelled');
    }
  }
};
</script>
```

## Environment Variables

Make sure these are set in your environment:

```bash
# Test Keys (for development)
PAYSTACK_TEST_PUBLIC_KEY=pk_test_xxxxxxxxxxxxx
PAYSTACK_TEST_SECRET_KEY=sk_test_xxxxxxxxxxxxx

# Live Keys (for production)
PAYSTACK_LIVE_PUBLIC_KEY=pk_live_xxxxxxxxxxxxx
PAYSTACK_LIVE_SECRET_KEY=sk_live_xxxxxxxxxxxxx
```

## Testing

### Test Cards

Use these test cards on Paystack:

| Card Number | CVV | Expiry | PIN | OTP | Result |
|-------------|-----|--------|-----|-----|--------|
| 4084084084084081 | 408 | 12/30 | 0000 | 123456 | Success |
| 5060666666666666666 | 123 | 12/30 | 1234 | 123456 | Success |
| 4084084084084081 | 408 | 12/30 | 0000 | 000000 | Failed |

### Test Flow

```bash
# 1. Get quote
curl -X POST "https://veyu.cc/api/v1/inspections/quote/" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"inspection_type": "pre_purchase"}'

# 2. Create inspection
curl -X POST "https://veyu.cc/api/v1/inspections/" \
  -H "Authorization: Bearer TOKEN" \
  -d '{...}'

# 3. Initiate payment
curl -X POST "https://veyu.cc/api/v1/inspections/1/pay/" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"payment_method": "bank", "amount": 50000.00}'

# 4. Complete payment on Paystack popup (frontend)

# 5. Verify payment
curl -X POST "https://veyu.cc/api/v1/inspections/1/verify-payment/" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"reference": "veyu-inspection-1-abc123def456"}'
```

## Error Handling

### Common Errors

**Payment Initiation Failed:**
```json
{
  "error": "Inspection has already been paid for"
}
```

**Verification Failed:**
```json
{
  "success": false,
  "error": "Payment verification failed",
  "message": "Transaction not found"
}
```

**Insufficient Balance (Wallet):**
```json
{
  "error": "Insufficient wallet balance",
  "available_balance": 30000.00,
  "required_amount": 50000.00
}
```

## Security Notes

1. **Never expose secret keys** on the frontend
2. **Always verify payments** on the backend
3. **Use HTTPS** in production
4. **Validate amounts** on both frontend and backend
5. **Check payment status** before allowing inspection to proceed

## Webhook Integration (Optional)

For automatic payment verification, you can set up Paystack webhooks:

```python
# Add to views.py
from django.views.decorators.csrf import csrf_exempt
import hmac
import hashlib

@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def paystack_webhook(request):
    """
    Handle Paystack webhook for payment notifications
    """
    # Verify webhook signature
    signature = request.headers.get('x-paystack-signature')
    secret = os.environ.get('PAYSTACK_SECRET_KEY')
    
    computed_signature = hmac.new(
        secret.encode('utf-8'),
        request.body,
        hashlib.sha512
    ).hexdigest()
    
    if signature != computed_signature:
        return Response({'error': 'Invalid signature'}, status=400)
    
    # Process webhook
    event = request.data
    
    if event['event'] == 'charge.success':
        reference = event['data']['reference']
        
        # Find and update transaction
        try:
            transaction = Transaction.objects.get(tx_ref=reference, status='pending')
            transaction.status = 'completed'
            transaction.save()
            
            # Mark inspection as paid
            if transaction.related_inspection:
                transaction.related_inspection.mark_paid(transaction, 'bank')
        except Transaction.DoesNotExist:
            pass
    
    return Response({'status': 'success'})
```

## Support

For Paystack-specific issues:
- Documentation: https://paystack.com/docs
- Support: support@paystack.com

For Veyu integration issues:
- Check transaction logs
- Verify environment variables
- Contact development team
