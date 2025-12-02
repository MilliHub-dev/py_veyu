"""
Test inspection slip endpoint with the correct user
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from django.test import RequestFactory
from inspections.views import InspectionSlipRetrievalView
from inspections.models import VehicleInspection
from rest_framework.test import force_authenticate

print("=" * 60)
print("TESTING WITH CORRECT USER")
print("=" * 60)

# Get the inspection and its customer
inspection = VehicleInspection.objects.first()
if not inspection:
    print("✗ No inspections found")
    exit(1)

print(f"\nInspection Details:")
print(f"  ID: {inspection.id}")
print(f"  Number: {inspection.inspection_number}")
print(f"  Customer: {inspection.customer.user.email}")

# Create request with the correct user
factory = RequestFactory()
user = inspection.customer.user

print(f"\n✓ Testing with customer user: {user.email}")

# Test with valid slip number
print("\n" + "-" * 60)
print(f"Test: Accessing {inspection.inspection_number} as owner")
print("-" * 60)

request = factory.get(f'/api/v1/inspections/slips/{inspection.inspection_number}/')
force_authenticate(request, user=user)
view = InspectionSlipRetrievalView.as_view()
response = view(request, slip_number=inspection.inspection_number)

print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    print("✓ SUCCESS: Customer can access their own inspection slip")
    print(f"\nResponse data:")
    data = response.data.get('data', {})
    print(f"  Inspection Number: {data.get('inspection_number')}")
    print(f"  Vehicle: {data.get('vehicle', {}).get('name')}")
    print(f"  Status: {data.get('inspection_status')}")
    print(f"  Payment Status: {data.get('payment_status')}")
else:
    print(f"✗ FAILED: Expected 200, got {response.status_code}")
    print(f"Response: {response.data}")

print("\n" + "=" * 60)
