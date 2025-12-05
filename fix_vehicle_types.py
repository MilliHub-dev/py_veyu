"""
Script to fix incorrectly saved vehicle types
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from listings.models import Vehicle, Car, Plane, Boat, Bike
from django.db import transaction


def fix_cessna_planes():
    """Fix Cessna vehicles that were saved as Cars"""
    print("=" * 60)
    print("FIXING CESSNA PLANES")
    print("=" * 60)
    
    # Find all Cars with Cessna brand (likely planes)
    cessna_cars = Car.objects.filter(brand__iexact='Cessna')
    
    print(f"\nFound {cessna_cars.count()} Cessna vehicles saved as Cars")
    
    if cessna_cars.count() == 0:
        print("No Cessna cars to fix")
        return
    
    fixed_count = 0
    
    for car in cessna_cars:
        print(f"\nFixing: {car.name} (ID: {car.id})")
        
        try:
            with transaction.atomic():
                # Get the base vehicle
                vehicle = Vehicle.objects.get(pk=car.pk)
                
                # Create a new Plane with the same data
                plane = Plane(
                    id=vehicle.id,  # Use same ID
                    uuid=vehicle.uuid,
                    date_created=vehicle.date_created,
                    last_updated=vehicle.last_updated,
                    dealer=vehicle.dealer,
                    name=vehicle.name,
                    slug=vehicle.slug,
                    brand=vehicle.brand,
                    model=vehicle.model,
                    condition=vehicle.condition,
                    fuel_system=vehicle.fuel_system,
                    transmission=vehicle.transmission,
                    color=vehicle.color,
                    mileage=vehicle.mileage,
                    for_sale=vehicle.for_sale,
                    for_rent=vehicle.for_rent,
                    available=vehicle.available,
                    video=vehicle.video,
                    tags=vehicle.tags,
                    features=vehicle.features,
                    custom_duty=vehicle.custom_duty,
                    last_rental=vehicle.last_rental,
                    current_rental=vehicle.current_rental,
                    # Plane-specific fields (can be set later)
                    registration_number=None,
                    engine_type=None,
                    aircraft_type='jet',  # Default
                    max_altitude=None,
                    wing_span=None,
                    range=None,
                )
                
                # Delete the Car entry
                Car.objects.filter(pk=car.pk).delete()
                
                # Save as Plane
                plane.save()
                
                print(f"  ✓ Converted to Plane (ID: {plane.id})")
                fixed_count += 1
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"\n✓ Fixed {fixed_count} vehicle(s)")


def show_summary():
    """Show summary of vehicle types"""
    print("\n" + "=" * 60)
    print("VEHICLE TYPE SUMMARY")
    print("=" * 60)
    
    print(f"\nCars: {Car.objects.count()}")
    print(f"Planes: {Plane.objects.count()}")
    print(f"Boats: {Boat.objects.count()}")
    print(f"Bikes: {Bike.objects.count()}")
    
    if Plane.objects.exists():
        print("\nPlanes:")
        for plane in Plane.objects.all():
            print(f"  - {plane.name} ({plane.brand})")


def main():
    print("\n" + "=" * 60)
    print("VEHICLE TYPE FIX SCRIPT")
    print("=" * 60)
    
    try:
        fix_cessna_planes()
        show_summary()
        
        print("\n" + "=" * 60)
        print("FIX COMPLETE")
        print("=" * 60)
        print("\nIMPORTANT: When creating listings, always specify vehicle_type:")
        print("  - vehicle_type='car' for cars")
        print("  - vehicle_type='plane' for planes")
        print("  - vehicle_type='boat' for boats")
        print("  - vehicle_type='bike' for bikes")
        print("  - vehicle_type='uav' for drones")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
