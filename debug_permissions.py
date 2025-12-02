"""
Debug permission checking
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from inspections.models import VehicleInspection

inspection = VehicleInspection.objects.first()
user = inspection.customer.user

print("=" * 60)
print("PERMISSION DEBUG")
print("=" * 60)

print(f"\nInspection Customer: {inspection.customer}")
print(f"  User: {inspection.customer.user}")
print(f"  Email: {inspection.customer.user.email}")

print(f"\nTest User: {user}")
print(f"  Email: {user.email}")
print(f"  Has 'customer' attr: {hasattr(user, 'customer')}")

if hasattr(user, 'customer'):
    print(f"  user.customer: {user.customer}")
    print(f"  user.customer == inspection.customer: {user.customer == inspection.customer}")
else:
    print("  ✗ User does not have 'customer' attribute!")

print(f"\nHas 'dealership' attr: {hasattr(user, 'dealership')}")
print(f"Is inspector: {user == inspection.inspector}")
print(f"Is staff: {user.is_staff}")

print("\n" + "=" * 60)
