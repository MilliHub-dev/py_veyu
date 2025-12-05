"""
Diagnostic script to check vehicle type issues
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from listings.models import Vehicle, Car, Boat, Plane, Bike, Listing
from accounts.models import Dealership
from django.contrib.contenttypes.models import ContentType


def check_vehicle_types():
    """Check all vehicles and their actual types"""
    print("=" * 60)
    print("VEHICLE TYPE DIAGNOSIS")
    print("=" * 60)
    
    all_vehicles = Vehicle.objects.all()
    
    print(f"\nTotal vehicles in database: {all_vehicles.count()}")
    print("\nVehicle Details:")
    print("-" * 60)
    
    for vehicle in all_vehicles:
        # Get the actual class
        actual_class = vehicle.__class__.__name__
        
        # Check if it's a specific type
        is_car = hasattr(vehicle, 'car')
        is_boat = hasattr(vehicle, 'boat')
        is_plane = hasattr(vehicle, 'plane')
        is_bike = hasattr(vehicle, 'bike')
        
        # Try to get specific instance
        specific_type = "Vehicle (base)"
        try:
            if Car.objects.filter(pk=vehicle.pk).exists():
                specific_type = "Car"
            elif Boat.objects.filter(pk=vehicle.pk).exists():
                specific_type = "Boat"
            elif Plane.objects.filter(pk=vehicle.pk).exists():
                specific_type = "Plane"
            elif Bike.objects.filter(pk=vehicle.pk).exists():
                specific_type = "Bike"
        except Exception as e:
            specific_type = f"Error: {e}"
        
        print(f"\nID: {vehicle.id}")
        print(f"  Name: {vehicle.name}")
        print(f"  Brand: {vehicle.brand}")
        print(f"  Class: {actual_class}")
        print(f"  Specific Type: {specific_type}")
        print(f"  Has car attr: {is_car}")
        print(f"  Has boat attr: {is_boat}")
        print(f"  Has plane attr: {is_plane}")
        print(f"  Has bike attr: {is_bike}")


def check_listings():
    """Check listings and their vehicle types"""
    print("\n" + "=" * 60)
    print("LISTING VEHICLE TYPES")
    print("=" * 60)
    
    listings = Listing.objects.select_related('vehicle').all()
    
    print(f"\nTotal listings: {listings.count()}")
    print("\nListing Details:")
    print("-" * 60)
    
    for listing in listings:
        vehicle = listing.vehicle
        actual_class = vehicle.__class__.__name__
        
        # Check specific type
        specific_type = "Unknown"
        if Car.objects.filter(pk=vehicle.pk).exists():
            specific_type = "Car"
        elif Boat.objects.filter(pk=vehicle.pk).exists():
            specific_type = "Boat"
        elif Plane.objects.filter(pk=vehicle.pk).exists():
            specific_type = "Plane"
        elif Bike.objects.filter(pk=vehicle.pk).exists():
            specific_type = "Bike"
        
        print(f"\nListing: {listing.title}")
        print(f"  Vehicle: {vehicle.name}")
        print(f"  Class: {actual_class}")
        print(f"  Specific Type: {specific_type}")
        print(f"  Listing Type: {listing.listing_type}")


def check_specific_models():
    """Check each specific model table"""
    print("\n" + "=" * 60)
    print("SPECIFIC MODEL COUNTS")
    print("=" * 60)
    
    print(f"\nCars: {Car.objects.count()}")
    print(f"Boats: {Boat.objects.count()}")
    print(f"Planes: {Plane.objects.count()}")
    print(f"Bikes: {Bike.objects.count()}")
    
    print("\nCar Details:")
    for car in Car.objects.all():
        print(f"  - {car.name} (ID: {car.id})")
    
    print("\nPlane Details:")
    for plane in Plane.objects.all():
        print(f"  - {plane.name} (ID: {plane.id})")
    
    print("\nBoat Details:")
    for boat in Boat.objects.all():
        print(f"  - {boat.name} (ID: {boat.id})")
    
    print("\nBike Details:")
    for bike in Bike.objects.all():
        print(f"  - {bike.name} (ID: {bike.id})")


def check_dealership_vehicles():
    """Check vehicles in dealership relationships"""
    print("\n" + "=" * 60)
    print("DEALERSHIP VEHICLE RELATIONSHIPS")
    print("=" * 60)
    
    dealers = Dealership.objects.all()
    
    for dealer in dealers:
        print(f"\nDealer: {dealer.business_name}")
        print(f"  Owned vehicles (FK): {dealer.owned_vehicles.count()}")
        print(f"  M2M vehicles: {dealer.vehicles.count()}")
        
        print("\n  Owned vehicles (via FK):")
        for vehicle in dealer.owned_vehicles.all():
            actual_class = vehicle.__class__.__name__
            print(f"    - {vehicle.name} ({actual_class})")
        
        print("\n  M2M vehicles:")
        for vehicle in dealer.vehicles.all():
            actual_class = vehicle.__class__.__name__
            print(f"    - {vehicle.name} ({actual_class})")


def main():
    try:
        check_specific_models()
        check_vehicle_types()
        check_listings()
        check_dealership_vehicles()
        
        print("\n" + "=" * 60)
        print("DIAGNOSIS COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError during diagnosis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
