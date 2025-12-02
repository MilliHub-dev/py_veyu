"""
Fix script to generate inspection numbers for paid inspections that are missing them
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from inspections.models import VehicleInspection

print("=" * 60)
print("FIXING INSPECTION NUMBERS")
print("=" * 60)

# Find all paid inspections without inspection numbers
paid_without_numbers = VehicleInspection.objects.filter(
    payment_status='paid',
    inspection_number__isnull=True
)

print(f"\nFound {paid_without_numbers.count()} paid inspections without inspection numbers")

if paid_without_numbers.exists():
    print("\nGenerating inspection numbers...")
    for insp in paid_without_numbers:
        old_number = insp.inspection_number
        insp.inspection_number = insp._generate_inspection_number()
        insp.save()
        print(f"  ✓ Inspection ID {insp.id}: {old_number or 'None'} → {insp.inspection_number}")
    
    print(f"\n✓ Fixed {paid_without_numbers.count()} inspections")
else:
    print("\n✓ All paid inspections have inspection numbers")

print("\n" + "=" * 60)
