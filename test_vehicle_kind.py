"""
Test script to verify vehicle.kind returns correct vehicle type
and can be used for counting/grouping vehicles by type.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from listings.models import Vehicle, Car, Boat, Plane, Bike, UAV, Listing
from django.db.models import Count, Q
from collections import Counter


def test_vehicle_kind():
    """Test that vehicle.kind returns the correct class name"""
    print("=" * 60)
    print("TEST 1: Vehicle Kind Detection")
    print("=" * 60)
    
    # Get sample vehicles of each type
    vehicles = []
    
    car = Car.objects.first()
    if car:
        vehicles.append(('Car', car))
        print(f"✓ Car found: {car.name}")
        print(f"  kind = '{car.__class__.__name__.lower()}'")
    
    boat = Boat.objects.first()
    if boat:
        vehicles.append(('Boat', boat))
        print(f"✓ Boat found: {boat.name}")
        print(f"  kind = '{boat.__class__.__name__.lower()}'")
    
    plane = Plane.objects.first()
    if plane:
        vehicles.append(('Plane', plane))
        print(f"✓ Plane found: {plane.name}")
        print(f"  kind = '{plane.__class__.__name__.lower()}'")
    
    bike = Bike.objects.first()
    if bike:
        vehicles.append(('Bike', bike))
        print(f"✓ Bike found: {bike.name}")
        print(f"  kind = '{bike.__class__.__name__.lower()}'")
    
    uav = UAV.objects.first()
    if uav:
        vehicles.append(('UAV', uav))
        print(f"✓ UAV found: {uav.name}")
        print(f"  kind = '{uav.__class__.__name__.lower()}'")
    
    if not vehicles:
        print("⚠ No vehicles found in database")
        return False
    
    print()
    return True


def test_vehicle_count_by_kind():
    """Test counting vehicles by kind"""
    print("=" * 60)
    print("TEST 2: Count Vehicles by Kind")
    print("=" * 60)
    
    # Method 1: Direct model queries
    print("\nMethod 1: Direct Model Queries")
    print("-" * 40)
    car_count = Car.objects.count()
    boat_count = Boat.objects.count()
    plane_count = Plane.objects.count()
    bike_count = Bike.objects.count()
    uav_count = UAV.objects.count()
    
    print(f"Cars:   {car_count}")
    print(f"Boats:  {boat_count}")
    print(f"Planes: {plane_count}")
    print(f"Bikes:  {bike_count}")
    print(f"UAVs:   {uav_count}")
    print(f"TOTAL:  {car_count + boat_count + plane_count + bike_count + uav_count}")
    
    # Method 2: Using vehicle.kind in Python
    print("\nMethod 2: Using vehicle.__class__.__name__.lower()")
    print("-" * 40)
    all_vehicles = Vehicle.objects.all()
    kind_counter = Counter()
    
    for vehicle in all_vehicles:
        kind = vehicle.__class__.__name__.lower()
        kind_counter[kind] += 1
    
    for kind, count in sorted(kind_counter.items()):
        print(f"{kind.capitalize()}s: {count}")
    print(f"TOTAL: {sum(kind_counter.values())}")
    
    return True


def test_listing_count_by_vehicle_kind():
    """Test counting listings by vehicle kind"""
    print("\n" + "=" * 60)
    print("TEST 3: Count Listings by Vehicle Kind")
    print("=" * 60)
    
    # Get all listings
    listings = Listing.objects.select_related('vehicle').all()
    
    if not listings.exists():
        print("⚠ No listings found in database")
        return False
    
    # Count by vehicle kind
    kind_counter = Counter()
    
    for listing in listings:
        kind = listing.vehicle.__class__.__name__.lower()
        kind_counter[kind] += 1
    
    print("\nListings by Vehicle Type:")
    print("-" * 40)
    for kind, count in sorted(kind_counter.items()):
        print(f"{kind.upper()}: {count} listing(s)")
    
    print(f"\nTOTAL LISTINGS: {sum(kind_counter.values())}")
    
    # Show breakdown by listing type
    print("\n" + "-" * 40)
    print("Breakdown by Listing Type:")
    print("-" * 40)
    
    for listing_type in ['sale', 'rental']:
        type_listings = listings.filter(listing_type=listing_type)
        type_counter = Counter()
        
        for listing in type_listings:
            kind = listing.vehicle.__class__.__name__.lower()
            type_counter[kind] += 1
        
        print(f"\n{listing_type.upper()} Listings:")
        for kind, count in sorted(type_counter.items()):
            print(f"  {kind}: {count}")
    
    return True


def test_serializer_kind_field():
    """Test that serializer returns kind field correctly"""
    print("\n" + "=" * 60)
    print("TEST 4: Serializer Kind Field")
    print("=" * 60)
    
    from listings.api.serializers import VehicleSerializer
    from rest_framework.test import APIRequestFactory
    
    factory = APIRequestFactory()
    request = factory.get('/')
    
    # Test each vehicle type
    vehicle_types = [
        (Car, 'car'),
        (Boat, 'boat'),
        (Plane, 'plane'),
        (Bike, 'bike'),
        (UAV, 'uav'),
    ]
    
    print("\nTesting Serializer Output:")
    print("-" * 40)
    
    for model, expected_kind in vehicle_types:
        vehicle = model.objects.first()
        if vehicle:
            serializer = VehicleSerializer(vehicle, context={'request': request})
            actual_kind = serializer.data.get('kind')
            
            status = "✓" if actual_kind == expected_kind else "✗"
            print(f"{status} {model.__name__}: kind='{actual_kind}' (expected: '{expected_kind}')")
        else:
            print(f"⚠ No {model.__name__} found to test")
    
    return True


def test_filter_by_kind():
    """Test filtering listings by vehicle kind"""
    print("\n" + "=" * 60)
    print("TEST 5: Filter Listings by Vehicle Kind")
    print("=" * 60)
    
    from listings.api.filters import CarSaleFilter
    from django.http import QueryDict
    
    # Test filtering for UAVs
    print("\nTest: Filter for UAVs only")
    print("-" * 40)
    
    queryset = Listing.objects.all()
    query_params = QueryDict('vehicle_type=uav')
    
    filter_instance = CarSaleFilter(query_params, queryset=queryset)
    filtered_qs = filter_instance.qs
    
    print(f"Total listings: {queryset.count()}")
    print(f"UAV listings: {filtered_qs.count()}")
    
    # Verify all results are UAVs
    if filtered_qs.exists():
        all_uavs = all(
            listing.vehicle.__class__.__name__.lower() == 'uav' 
            for listing in filtered_qs
        )
        print(f"All results are UAVs: {'✓ Yes' if all_uavs else '✗ No'}")
    
    # Test filtering for multiple types
    print("\nTest: Filter for Cars and UAVs")
    print("-" * 40)
    
    query_params = QueryDict('vehicle_type=car,uav')
    filter_instance = CarSaleFilter(query_params, queryset=queryset)
    filtered_qs = filter_instance.qs
    
    print(f"Car + UAV listings: {filtered_qs.count()}")
    
    # Count by kind
    kind_counter = Counter()
    for listing in filtered_qs:
        kind = listing.vehicle.__class__.__name__.lower()
        kind_counter[kind] += 1
    
    for kind, count in sorted(kind_counter.items()):
        print(f"  {kind}: {count}")
    
    # Test 'drone' alias
    print("\nTest: Filter using 'drone' alias")
    print("-" * 40)
    
    query_params = QueryDict('vehicle_type=drone')
    filter_instance = CarSaleFilter(query_params, queryset=queryset)
    filtered_qs = filter_instance.qs
    
    print(f"Drone listings: {filtered_qs.count()}")
    
    return True


def create_sample_data():
    """Create sample vehicles for testing if none exist"""
    print("\n" + "=" * 60)
    print("Creating Sample Data")
    print("=" * 60)
    
    from accounts.models import Dealership
    
    dealer = Dealership.objects.first()
    if not dealer:
        print("⚠ No dealership found. Cannot create sample data.")
        return False
    
    created = []
    
    # Create Car if none exists
    if not Car.objects.exists():
        car = Car.objects.create(
            dealer=dealer,
            name="Toyota Camry 2023",
            brand="Toyota",
            model="Camry",
            condition="new",
            color="Black",
            doors=4,
            seats=5,
            drivetrain="FWD"
        )
        created.append(f"Car: {car.name}")
    
    # Create UAV if none exists
    if not UAV.objects.exists():
        uav = UAV.objects.create(
            dealer=dealer,
            name="DJI Mavic 3",
            brand="DJI",
            model="Mavic 3",
            condition="new",
            color="Gray",
            uav_type="quadcopter",
            purpose="photography",
            max_flight_time=46,
            max_range=30,
            camera_resolution="5.1K",
            rotor_count=4,
            has_gps=True,
            has_obstacle_avoidance=True
        )
        created.append(f"UAV: {uav.name}")
    
    if created:
        print("\nCreated sample vehicles:")
        for item in created:
            print(f"  ✓ {item}")
    else:
        print("\nSample vehicles already exist")
    
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("VEHICLE KIND TESTING SUITE")
    print("=" * 60)
    
    try:
        # Check if we have data
        vehicle_count = Vehicle.objects.count()
        print(f"\nTotal vehicles in database: {vehicle_count}")
        
        if vehicle_count == 0:
            print("\n⚠ No vehicles found. Creating sample data...")
            create_sample_data()
        
        # Run tests
        tests = [
            test_vehicle_kind,
            test_vehicle_count_by_kind,
            test_listing_count_by_vehicle_kind,
            test_serializer_kind_field,
            test_filter_by_kind,
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append((test.__name__, result))
            except Exception as e:
                print(f"\n✗ {test.__name__} failed with error:")
                print(f"  {str(e)}")
                results.append((test.__name__, False))
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status}: {test_name}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠ {total - passed} test(s) failed")
        
    except Exception as e:
        print(f"\n✗ Test suite failed with error:")
        print(f"  {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
