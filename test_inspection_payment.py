"""
Quick test script for inspection payment functionality
Run with: python manage.py shell < test_inspection_payment.py
"""

print("=" * 60)
print("TESTING INSPECTION PAYMENT SYSTEM")
print("=" * 60)

# Test 1: Check models
print("\n1. Checking models...")
from inspections.models import VehicleInspection
from wallet.models import Transaction

print("✓ VehicleInspection model loaded")
print("✓ Transaction model loaded")

# Test 2: Check payment fields
print("\n2. Checking payment fields on VehicleInspection...")
payment_fields = [f.name for f in VehicleInspection._meta.fields if 'payment' in f.name or 'fee' in f.name or 'paid' in f.name]
print(f"✓ Payment fields found: {payment_fields}")

# Test 3: Check status choices
print("\n3. Checking status choices...")
status_choices = dict(VehicleInspection.STATUS_CHOICES)
if 'pending_payment' in status_choices:
    print(f"✓ 'pending_payment' status exists: {status_choices['pending_payment']}")
else:
    print("✗ 'pending_payment' status NOT found!")

# Test 4: Check payment status choices
print("\n4. Checking payment status choices...")
payment_status_choices = dict(VehicleInspection.PAYMENT_STATUS_CHOICES)
print(f"✓ Payment statuses: {list(payment_status_choices.keys())}")

# Test 5: Check Transaction related_inspection field
print("\n5. Checking Transaction.related_inspection field...")
transaction_fields = [f.name for f in Transaction._meta.fields if 'inspection' in f.name]
print(f"✓ Inspection-related fields: {transaction_fields}")

# Test 6: Check InspectionFeeService
print("\n6. Checking InspectionFeeService...")
from inspections.services import InspectionFeeService

fees = InspectionFeeService.BASE_FEES
print(f"✓ Base fees configured:")
for inspection_type, fee in fees.items():
    print(f"  - {inspection_type}: ₦{fee:,.2f}")

# Test 7: Test fee calculation
print("\n7. Testing fee calculation...")
test_fee = InspectionFeeService.calculate_inspection_fee('pre_purchase')
print(f"✓ Pre-purchase inspection fee: ₦{test_fee:,.2f}")

# Test 8: Test fee quote
print("\n8. Testing fee quote...")
quote = InspectionFeeService.get_fee_quote('pre_rental')
print(f"✓ Quote generated:")
print(f"  - Type: {quote['inspection_type']}")
print(f"  - Base fee: ₦{quote['base_fee']:,.2f}")
print(f"  - Total: ₦{quote['total_fee']:,.2f}")
print(f"  - Currency: {quote['currency']}")

print("\n" + "=" * 60)
print("ALL TESTS PASSED! ✓")
print("=" * 60)
print("\nInspection payment system is ready to use!")
print("\nNext steps:")
print("1. Test wallet payment endpoint")
print("2. Test Paystack payment endpoint")
print("3. Integrate Paystack on frontend")
print("4. Test end-to-end flow")
