"""
Test script to verify JWT authentication is working
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework_simplejwt.authentication import JWTAuthentication
from accounts.models import Account
from listings.api.dealership_views import CreateListingView

# Get a dealer user
try:
    dealer_user = Account.objects.filter(user_type='dealer').first()
    if not dealer_user:
        print("No dealer user found in database")
        exit(1)
    
    print(f"Testing with user: {dealer_user.email} (ID: {dealer_user.id})")
    
    # Create a request factory
    factory = APIRequestFactory()
    
    # Create a mock POST request
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
    
    # Add the Authorization header with the token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzYzNjUxNzAxLCJpYXQiOjE3NjM2NDcxMDMsImp0aSI6Ijg4MmI1MzU1MDNjZTQ2OTNiOWIzZjkyNjQ5Y2IwMWQwIiwidXNlcl9pZCI6NjksInVzZXJfdHlwZSI6ImRlYWxlciIsImVtYWlsIjoiZGV2b3BzLm1pbGxpaHViQGdtYWlsLmNvbSIsInByb3ZpZGVyIjoidmV5dSIsImlzcyI6InZleS11LXBsYXRmb3JtIn0.NfihR9jRQL2kmUb31mdT0bMfFiGbkXQGYQxEoXoBy5A"
    request.META['HTTP_AUTHORIZATION'] = f'Bearer {token}'
    
    # Test JWT authentication
    print("\nTesting JWT Authentication...")
    jwt_auth = JWTAuthentication()
    try:
        result = jwt_auth.authenticate(request)
        if result:
            user, validated_token = result
            print(f"✓ JWT Authentication successful!")
            print(f"  User: {user.email}")
            print(f"  User ID: {user.id}")
            print(f"  User Type: {user.user_type}")
        else:
            print("✗ JWT Authentication returned None (no credentials provided)")
    except Exception as e:
        print(f"✗ JWT Authentication failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test the view
    print("\nTesting CreateListingView...")
    view = CreateListingView.as_view()
    try:
        response = view(request)
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
    except Exception as e:
        print(f"View error: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
