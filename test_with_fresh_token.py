"""
Test with a freshly generated token
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.authentication import JWTAuthentication
from accounts.models import Account
from accounts.authentication import TokenManager
from listings.api.dealership_views import CreateListingView

# Get the dealer user
user = Account.objects.get(id=69)
print(f"Testing with user: {user.email}")

# Generate a fresh token
tokens = TokenManager.create_tokens_for_user(user)
fresh_token = tokens['access']

print(f"\nUsing fresh token: {fresh_token[:50]}...")

# Create a request
factory = APIRequestFactory()
request = factory.post('/api/v1/admin/dealership/listings/create/', {
    'action': 'create-listing',
    'title': 'Test Vehicle',
    'brand': 'Toyota',
    'model': 'Camry',
    'condition': 'used-foreign',
    'transmission': 'auto',
    'fuel_system': 'petrol',
    'drivetrain': 'FWD',
    'seats': 5,
    'doors': 4,
    'vin': 'TEST123456789',
    'listing_type': 'sale',
    'price': 5000000
}, format='json')

# Add the Authorization header
request.META['HTTP_AUTHORIZATION'] = f'Bearer {fresh_token}'

# Test JWT authentication
print("\nTesting JWT Authentication with fresh token...")
jwt_auth = JWTAuthentication()
try:
    result = jwt_auth.authenticate(request)
    if result:
        auth_user, validated_token = result
        print(f"✓ JWT Authentication SUCCESSFUL!")
        print(f"  Authenticated as: {auth_user.email}")
        print(f"  User ID: {auth_user.id}")
        print(f"  User Type: {auth_user.user_type}")
        
        # Now test the view
        print("\n✓ Testing CreateListingView with authenticated request...")
        view = CreateListingView.as_view()
        response = view(request)
        print(f"  Response status: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✓ SUCCESS! Listing created")
            print(f"  Response: {response.data}")
        else:
            print(f"  Response data: {response.data}")
    else:
        print("✗ Authentication returned None")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
