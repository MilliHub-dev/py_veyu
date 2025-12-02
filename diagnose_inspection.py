"""
Diagnostic script to check inspection data
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from inspections.models import VehicleInspection

print("=" * 60)
print("INSPECTION DIAGNOSTICS")
print("=" * 60)

# Check all inspections
all_inspections = VehicleInspection.objects.all()
print(f"\nTotal inspections in database: {all_inspections.count()}")

if all_inspections.exists():
    print("\nInspection Details:")
    print("-" * 60)
    for insp in all_inspections:
        print(f"ID: {insp.id}")
        print(f"  Inspection Number: {insp.inspection_number or 'NOT GENERATED'}")
        print(f"  Vehicle: {insp.vehicle.name}")
        print(f"  Status: {insp.get_status_display()}")
        print(f"  Payment Status: {insp.get_payment_status_display()}")
        print(f"  Is Paid: {insp.is_paid}")
        print(f"  Paid At: {insp.paid_at or 'Not paid'}")
        print(f"  Created: {insp.date_created}")
        print("-" * 60)

# Check for inspection with ID 8
print("\nChecking for Inspection ID 8:")
try:
    insp_8 = VehicleInspection.objects.get(id=8)
    print(f"✓ Found Inspection ID 8")
    print(f"  Inspection Number: {insp_8.inspection_number or 'NOT GENERATED'}")
    print(f"  Status: {insp_8.get_status_display()}")
    print(f"  Payment Status: {insp_8.get_payment_status_display()}")
    print(f"  Is Paid: {insp_8.is_paid}")
    
    if not insp_8.inspection_number:
        print("\n⚠ ISSUE: Inspection ID 8 exists but has no inspection_number!")
        print("  This happens when the inspection hasn't been paid yet.")
        print("  The inspection_number is generated in the mark_paid() method.")
except VehicleInspection.DoesNotExist:
    print("✗ Inspection ID 8 does not exist in the database")

# Check for inspection with number INSP-8
print("\nChecking for Inspection Number 'INSP-8':")
try:
    insp_num = VehicleInspection.objects.get(inspection_number='INSP-8')
    print(f"✓ Found Inspection with number INSP-8")
    print(f"  ID: {insp_num.id}")
    print(f"  Vehicle: {insp_num.vehicle.name}")
    print(f"  Status: {insp_num.get_status_display()}")
except VehicleInspection.DoesNotExist:
    print("✗ No inspection with number 'INSP-8' exists")

print("\n" + "=" * 60)
