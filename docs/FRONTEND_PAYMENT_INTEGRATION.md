# Frontend Payment Integration Guide

## Overview
This guide explains how to integrate Paystack payments for inspection fees in the checkout flow.

## Payment Flow Options

### Option 1: Send Payment Reference (Recommended)
After Paystack payment succeeds, send the reference to the checkout endpoint.

```javascript
// In your Paystack onSuccess callback
const onPaystackSuccess = async (response) => {
  console.log('Payment successful:', response);
  
  try {
    // Create order with payment reference
    const orderResponse = await fetch(`/api/v1/listings/checkout/${listingId}/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        payment_option: 'pay-after-inspection',
        payment_reference: response.reference  // ← Send this!
      })
    });
    
    if (orderResponse.ok) {
      const order = await orderResponse.json();
      console.log('Order created:', order);
      // Redirect to success page
    } else {
      console.error('Order creation failed:', await orderResponse.json());
    }
  } catch (error) {
    console.error('Error creating order:', error);
  }
};
```

### Option 2: Let Webhook Handle It (Fallback)
If you don't send the reference, the backend will look for recent payments.

```javascript
// Just call checkout without reference
const orderResponse = await fetch(`/api/v1/listings/checkout/${listingId}/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    payment_option: 'pay-after-inspection'
    // No payment_reference - backend will find recent payment
  })
});
```

**Note**: This relies on timing (5-minute window) and is less reliable.

## Complete Integration Example

```javascript
import { PaystackButton } from 'react-paystack';

const CheckoutPage = () => {
  const [listing, setListing] = useState(null);
  const [checkoutData, setCheckoutData] = useState(null);
  
  // Fetch checkout data
  useEffect(() => {
    const fetchCheckout = async () => {
      const response = await api.get(`/listings/checkout/${listingId}/`);
      setCheckoutData(response.data);
    };
    fetchCheckout();
  }, [listingId]);
  
  // Paystack configuration
  const paystackConfig = {
    reference: `INSP-${Date.now()}`,
    email: user.email,
    amount: checkoutData?.fees?.inspection_fee * 100, // Convert to kobo
    publicKey: process.env.REACT_APP_PAYSTACK_PUBLIC_KEY,
    metadata: {
      purpose: 'inspection',  // ← Important for webhook
      user_id: user.id,
      vehicle_id: listing.vehicle.id,
      listing_id: listingId
    }
  };
  
  // Handle successful payment
  const handlePaystackSuccess = async (response) => {
    console.log('✅ Payment successful:', response);
    
    try {
      // Create order with payment reference
      const orderResponse = await api.post(
        `/listings/checkout/${listingId}/`,
        {
          payment_option: 'pay-after-inspection',
          payment_reference: response.reference
        }
      );
      
      if (orderResponse.data.error === false) {
        // Success! Redirect to order confirmation
        navigate(`/orders/${orderResponse.data.data.uuid}`);
      } else {
        // Handle error
        showError(orderResponse.data.message);
      }
    } catch (error) {
      console.error('❌ Order creation failed:', error);
      showError('Failed to create order. Please contact support.');
    }
  };
  
  // Handle payment close/cancel
  const handlePaystackClose = () => {
    console.log('Payment cancelled');
    showInfo('Payment was cancelled');
  };
  
  return (
    <div>
      <h2>Checkout</h2>
      
      {/* Show inspection fee */}
      <div>
        <p>Inspection Fee: ₦{checkoutData?.fees?.inspection_fee}</p>
        <p>Service Fee: ₦{checkoutData?.fees?.service_fee}</p>
        <p>Tax: ₦{checkoutData?.fees?.tax}</p>
        <hr />
        <p><strong>Total: ₦{checkoutData?.total}</strong></p>
      </div>
      
      {/* Paystack button */}
      <PaystackButton
        {...paystackConfig}
        text="Pay Inspection Fee"
        onSuccess={handlePaystackSuccess}
        onClose={handlePaystackClose}
        className="btn btn-primary"
      />
    </div>
  );
};
```

## Error Handling

### 402 Payment Required
```json
{
  "error": "Inspection payment required",
  "message": "You must pay for and complete a vehicle inspection...",
  "required_action": "pay_inspection",
  "vehicle_id": 123,
  "listing_id": "uuid"
}
```

**Action**: Show payment button to user.

### 400 Bad Request
```json
{
  "error": "Customer profile not found. Please complete your profile first."
}
```

**Action**: Redirect to profile completion page.

### 500 Internal Server Error
```json
{
  "error": "Payment verification error",
  "message": "Error verifying payment: ..."
}
```

**Action**: Show error message and suggest contacting support.

## Testing

### Test with Paystack Test Cards
```javascript
// Use Paystack test cards
const testCard = {
  number: '4084084084084081',
  cvv: '408',
  expiry: '12/25',
  pin: '0000'
};
```

### Test Checkout Flow
1. Navigate to listing page
2. Click "Buy Now"
3. Complete Paystack payment
4. Verify order is created
5. Check order status page

### Debug Checklist
- [ ] Paystack public key is correct
- [ ] Payment reference is sent to checkout
- [ ] Metadata includes `purpose: 'inspection'`
- [ ] User is authenticated (JWT token)
- [ ] Customer profile exists
- [ ] Webhook URL is configured in Paystack dashboard

## Webhook Configuration

Ensure Paystack webhook is configured:

**URL**: `https://dev.veyu.cc/api/v1/hooks/payment-webhook/`

**Events**:
- ✅ charge.success
- ✅ transfer.success
- ✅ transfer.failed

## Support

If you encounter issues:
1. Check browser console for errors
2. Check network tab for API responses
3. Check backend logs for payment processing
4. Contact backend team with payment reference

## API Reference

### GET /api/v1/listings/checkout/{listingId}/
Get checkout summary including fees and inspection status.

### POST /api/v1/listings/checkout/{listingId}/
Create order after payment.

**Body**:
```json
{
  "payment_option": "pay-after-inspection",
  "payment_reference": "T166503098007364"
}
```

### POST /api/v1/hooks/payment-webhook/
Paystack webhook endpoint (called by Paystack, not frontend).
