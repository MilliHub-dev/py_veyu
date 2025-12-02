"""
Test script to verify the inspection slip endpoint fix
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from django.test import RequestFactory
from inspections.views import InspectionSlipRetrievalView
from accounts.models import Account
from rest_framework.test import force_authenticate

print("=" * 60)
print("TESTING INSPECTION SLIP ENDPOINT")
print("=" * 60)

# Create a request factory
factory = RequestFactory()

# Get a user for authentication
try:
    user = Account.objects.first()
    if not user:
        print("✗ No users found in database. Cannot test authenticated endpoint.")
        exit(1)
    
    print(f"\n✓ Using user: {user.email}")
    
    # Test 1: Valid inspection slip (INSP-1)
    print("\n" + "-" * 60)
    print("Test 1: Valid inspection slip (INSP-1)")
    print("-" * 60)
    request = factory.get('/api/v1/inspections/slips/INSP-1/')
    force_authenticate(request, user=user)
    view = InspectionSlipRetrievalView.as_view()
    response = view(request, slip_number='INSP-1')
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.data}")
    
    if response.status_code == 200:
        print("✓ Test 1 PASSED: Valid slip returns 200")
    elif response.status_code == 403:
        print("⚠ Test 1 PARTIAL: Valid slip exists but user lacks permission")
    else:
        print(f"✗ Test 1 FAILED: Expected 200 or 403, got {response.status_code}")
    
    # Test 2: Invalid inspection slip (INSP-8)
    print("\n" + "-" * 60)
    print("Test 2: Invalid inspection slip (INSP-8)")
    print("-" * 60)
    request = factory.get('/api/v1/inspections/slips/INSP-8/')
    force_authenticate(request, user=user)
    view = InspectionSlipRetrievalView.as_view()
    response = view(request, slip_number='INSP-8')
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.data}")
    
    if response.status_code == 404:
        print("✓ Test 2 PASSED: Invalid slip returns 404")
        if 'success' in response.data and response.data['success'] == False:
            print("✓ Response includes success: false flag")
        if 'message' in response.data:
            print(f"✓ Response includes helpful message: {response.data['message']}")
    else:
        print(f"✗ Test 2 FAILED: Expected 404, got {response.status_code}")
    
    print("\n" + "=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Error during testing: {str(e)}")
    import traceback
    traceback.print_exc()
