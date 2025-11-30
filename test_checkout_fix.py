"""
Test script to verify the checkout payment fix
Run this after deploying the fix to test the payment flow
"""

import requests
import json

# Configuration
BASE_URL = "https://dev.veyu.cc"  # Change to your deployment URL
AUTH_TOKEN = "your_jwt_token_here"  # Replace with actual token
LISTING_ID = "c87678f6-c930-11f0-a5b2-cdce16ffe435"  # Replace with actual listing ID

def test_checkout_with_payment():
    """Test checkout endpoint with payment reference"""
    
    url = f"{BASE_URL}/api/v1/listings/checkout/{LISTING_ID}/"
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Simulate successful Paystack payment
    payload = {
        "payment_option": "pay-after-inspection",
        "payment_reference": "T166503098007364"  # Replace with actual reference from Paystack
    }
    
    print(f"Testing checkout endpoint: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, headers=headers, json=payload)
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Body: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("\n✅ SUCCESS: Order created successfully!")
        return True
    elif response.status_code == 402:
        print("\n❌ FAILED: Payment verification failed")
        return False
    else:
        print(f"\n❌ FAILED: Unexpected status code {response.status_code}")
        return False

def test_webhook_endpoint():
    """Test that webhook endpoint is accessible"""
    
    url = f"{BASE_URL}/api/v1/hooks/payment-webhook/"
    
    print(f"\nTesting webhook endpoint: {url}")
    
    # Send a test request (will fail signature check but should not 404)
    response = requests.post(url, json={"test": "data"})
    
    print(f"Response Status: {response.status_code}")
    
    if response.status_code == 404:
        print("❌ FAILED: Webhook endpoint not found (404)")
        return False
    elif response.status_code in [400, 401, 403]:
        print("✅ SUCCESS: Webhook endpoint exists (auth/validation error expected)")
        return True
    else:
        print(f"⚠️  WARNING: Unexpected status code {response.status_code}")
        return True

if __name__ == "__main__":
    print("=" * 60)
    print("CHECKOUT PAYMENT FIX - TEST SUITE")
    print("=" * 60)
    
    # Test 1: Webhook endpoint accessibility
    print("\n[TEST 1] Webhook Endpoint Accessibility")
    print("-" * 60)
    webhook_ok = test_webhook_endpoint()
    
    # Test 2: Checkout with payment reference
    print("\n[TEST 2] Checkout with Payment Reference")
    print("-" * 60)
    print("⚠️  NOTE: Update AUTH_TOKEN and LISTING_ID before running")
    # checkout_ok = test_checkout_with_payment()  # Uncomment when ready
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Webhook Endpoint: {'✅ PASS' if webhook_ok else '❌ FAIL'}")
    # print(f"Checkout Flow: {'✅ PASS' if checkout_ok else '❌ FAIL'}")  # Uncomment when ready
    print("=" * 60)
