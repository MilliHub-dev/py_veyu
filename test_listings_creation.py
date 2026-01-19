import os
import django
import sys
from django.conf import settings

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
os.environ['DEBUG'] = 'True'
django.setup()

from rest_framework.test import APIClient
from accounts.models import Account, Dealership
from django.contrib.auth import get_user_model
from listings.models import Car, Plane, Boat, Bike, UAV

User = get_user_model()

def run_tests():
    print("Setting up test environment...")
    
    # Create test user
    email = "testdealer@veyu.cc"
    password = "testpassword123"
    try:
        user = User.objects.get(email=email)
        print(f"User {email} already exists. Deleting...")
        user.delete()
    except User.DoesNotExist:
        pass
    
    print(f"Creating user {email}...")
    user = User.objects.create_user(
        email=email,
        password=password,
        user_type='dealer',
        first_name='Test',
        last_name='Dealer'
    )
    
    # Update dealership profile
    print("Updating dealership profile...")
    dealership = Dealership.objects.get(user=user)
    dealership.phone_number = "+2348012345678"
    dealership.business_name = "Test Motors"
    dealership.save()
    
    # Authenticate
    client = APIClient()
    client.force_authenticate(user=user)
    
    url = '/api/v1/admin/dealership/listings/create/'
    
    # 1. Test Car
    print("\n--- Testing Car Listing ---")
    car_data = {
        'action': 'create-listing',
        'vehicle_type': 'car',
        'title': 'Test Car Listing',
        'brand': 'Toyota',
        'model': 'Camry',
        'condition': 'used-foreign',
        'listing_type': 'sale',
        'price': 5000000,
        'transmission': 'auto',
        'fuel_system': 'petrol',
        'drivetrain': 'FWD',
        'seats': 5,
        'doors': 4,
        'vin': 'TESTVIN123456',
        'color': 'Blue',
        'mileage': 10000
    }
    response = client.post(url, car_data, format='json')
    if response.status_code == 200:
        print("SUCCESS: Car listing created.")
        print(f"ID: {response.data['data']['id']}")
    else:
        print("FAILED: Car listing creation.")
        print(response.status_code)
        if hasattr(response, 'data'):
            print(response.data)
        elif response.status_code in [301, 302]:
            print(f"Redirect to: {response['Location']}")
        else:
            print(response.content)
        
    # 2. Test Plane
    print("\n--- Testing Plane Listing ---")
    plane_data = {
        'action': 'create-listing',
        'vehicle_type': 'plane',
        'title': 'Test Plane Listing',
        'brand': 'Cessna',
        'model': '172',
        'condition': 'used-foreign',
        'listing_type': 'sale',
        'price': 150000000,
        'registration_number': 'N12345',
        'aircraft_type': 'propeller',
        'engine_type': 'piston',
        'max_altitude': 14000,
        'wing_span': 11.0,
        'range': 1200
    }
    response = client.post(url, plane_data, format='json')
    if response.status_code == 200:
        print("SUCCESS: Plane listing created.")
        print(f"ID: {response.data['data']['id']}")
    else:
        print("FAILED: Plane listing creation.")
        print(response.status_code)
        print(response.data)

    # 3. Test Boat
    print("\n--- Testing Boat Listing ---")
    boat_data = {
        'action': 'create-listing',
        'vehicle_type': 'boat',
        'title': 'Test Boat Listing',
        'brand': 'Yamaha',
        'model': '242X',
        'condition': 'new',
        'listing_type': 'sale',
        'price': 45000000,
        'hull_material': 'fiberglass',
        'engine_count': 2,
        'propeller_type': 'inboard',
        'length': 24.0,
        'beam_width': 8.6,
        'draft': 1.5
    }
    response = client.post(url, boat_data, format='json')
    if response.status_code == 200:
        print("SUCCESS: Boat listing created.")
        print(f"ID: {response.data['data']['id']}")
    else:
        print("FAILED: Boat listing creation.")
        print(response.status_code)
        print(response.data)

    # 4. Test Bike
    print("\n--- Testing Bike Listing ---")
    bike_data = {
        'action': 'create-listing',
        'vehicle_type': 'bike',
        'title': 'Test Bike Listing',
        'brand': 'Ducati',
        'model': 'Panigale V4',
        'condition': 'new',
        'listing_type': 'sale',
        'price': 12000000,
        'engine_capacity': 1103,
        'bike_type': 'sport',
        'saddle_height': 830.0
    }
    response = client.post(url, bike_data, format='json')
    if response.status_code == 200:
        print("SUCCESS: Bike listing created.")
        print(f"ID: {response.data['data']['id']}")
    else:
        print("FAILED: Bike listing creation.")
        print(response.status_code)
        print(response.data)

    # 5. Test UAV
    print("\n--- Testing UAV Listing ---")
    uav_data = {
        'action': 'create-listing',
        'vehicle_type': 'uav',
        'title': 'Test UAV Listing',
        'brand': 'DJI',
        'model': 'Matrice 300 RTK',
        'condition': 'new',
        'listing_type': 'sale',
        'price': 8000000,
        'uav_type': 'quadcopter',
        'purpose': 'inspection',
        'max_flight_time': 55,
        'camera_resolution': '4K',
        'payload_capacity': 2.7,
        'weight': 6.3,
        'rotor_count': 4,
        'has_obstacle_avoidance': True,
        'has_gps': True,
        'has_return_to_home': True
    }
    response = client.post(url, uav_data, format='json')
    if response.status_code == 200:
        print("SUCCESS: UAV listing created.")
        print(f"ID: {response.data['data']['id']}")
    else:
        print("FAILED: UAV listing creation.")
        print(response.status_code)
        print(response.data)

    # Cleanup
    print("\nCleaning up...")
    user.delete()
    print("Done.")

if __name__ == "__main__":
    run_tests()
