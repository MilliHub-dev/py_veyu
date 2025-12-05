"""
Test that fixed vehicles return correct kind
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from listings.models import Vehicle, Car, Plane
from listings.api.serializers import VehicleSerializer
from rest_framework.test import APIRequestFactory


def test_vehicle_kind():
    """Test that vehicle.kind returns correct type"""
    print("=" * 60)
    print("TESTING VEHICLE.KIND AFTER FIX")
    print("=" * 60)
    
    factory = APIRequestFactory()
    request = factory.get('/')
    
    # Test Cars
    print("\nCars:")
    for car in Car.objects.all():
        kind = car.__class__.__name__.lower()
        serializer = VehicleSerializer(car, context={'request': request})
        serializer_kind = serializer.data.get('kind')
        
        status = "✓" if kind == 'car' and serializer_kind == 'car' else "✗"
        print(f"{status} {car.name}: kind='{kind}', serializer='{serializer_kind}'")
    
    # Test Planes
    print("\nPlanes:")
    for plane in Plane.objects.all():
        kind = plane.__class__.__name__.lower()
        serializer = VehicleSerializer(plane, context={'request': request})
        serializer_kind = serializer.data.get('kind')
        
        status = "✓" if kind == 'plane' and serializer_kind == 'plane' else "✗"
        print(f"{status} {plane.name}: kind='{kind}', serializer='{serializer_kind}'")
    
    # Test via base Vehicle query
    print("\nVia Vehicle.objects.all():")
    for vehicle in Vehicle.objects.all():
        kind = vehicle.__class__.__name__.lower()
        
        # Check if it's actually a specific type
        actual_type = "vehicle"
        if Car.objects.filter(pk=vehicle.pk).exists():
            actual_type = "car"
        elif Plane.objects.filter(pk=vehicle.pk).exists():
            actual_type = "plane"
        
        status = "✓" if kind == actual_type else "✗"
        print(f"{status} {vehicle.name} ({vehicle.brand}): kind='{kind}', actual='{actual_type}'")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    test_vehicle_kind()
