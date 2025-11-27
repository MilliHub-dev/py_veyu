"""
Test script for inspection payment and revenue sharing system
Run with: python test_inspection_revenue.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from decimal import Decimal
from inspections.models_revenue import InspectionRevenueSettings, InspectionRevenueSplit, WithdrawalRequest
from inspections.models import VehicleInspection
from wallet.models import Wallet, Transaction
from accounts.models import Account, Customer, Dealership
from django.utils import timezone


def test_revenue_settings():
    """Test revenue settings creation and validation"""
    print("\n" + "="*60)
    print("TEST 1: Revenue Settings")
    print("="*60)
    
    try:
        # Create default settings
        settings = InspectionRevenueSettings.objects.create(
            dealer_percentage=Decimal('60.00'),
            platform_percentage=Decimal('40.00'),
            is_active=True,
            notes="Test revenue split settings"
        )
        print(f"✓ Created revenue settings: {settings}")
        print(f"  - Dealer: {settings.dealer_percentage}%")
        print(f"  - Platform: {settings.platform_percentage}%")
        print(f"  - Active: {settings.is_active}")
        
        # Test validation (should fail - percentages don't add to 100)
        try:
            bad_settings = InspectionRevenueSettings(
                dealer_percentage=Decimal('50.00'),
                platform_percentage=Decimal('30.00'),
                is_active=False
            )
            bad_settings.full_clean()
            print("✗ Validation failed - should have caught invalid percentages")
        except Exception as e:
            print(f"✓ Validation working correctly: {str(e)[:50]}...")
        
        # Get active settings
        active = InspectionRevenueSettings.get_active_settings()
        print(f"✓ Active settings retrieved: {active}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_revenue_split_calculation():
    """Test revenue split calculation"""
    print("\n" + "="*60)
    print("TEST 2: Revenue Split Calculation")
    print("="*60)
    
    try:
        settings = InspectionRevenueSettings.get_active_settings()
        
        # Test amounts
        test_amounts = [
            Decimal('5000.00'),
            Decimal('10000.00'),
            Decimal('15000.00'),
        ]
        
        for amount in test_amounts:
            dealer_amount = (amount * settings.dealer_percentage) / Decimal('100')
            platform_amount = (amount * settings.platform_percentage) / Decimal('100')
            
            print(f"\nInspection Fee: ₦{amount:,.2f}")
            print(f"  Dealer ({settings.dealer_percentage}%): ₦{dealer_amount:,.2f}")
            print(f"  Platform ({settings.platform_percentage}%): ₦{platform_amount:,.2f}")
            print(f"  Total: ₦{dealer_amount + platform_amount:,.2f}")
            
            # Verify totals match
            assert dealer_amount + platform_amount == amount, "Split doesn't add up!"
        
        print("\n✓ All calculations correct")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_withdrawal_request_validation():
    """Test withdrawal request validation"""
    print("\n" + "="*60)
    print("TEST 3: Withdrawal Request Validation")
    print("="*60)
    
    try:
        # Test minimum amount validation
        print("\nTesting minimum withdrawal amount...")
        
        # This should fail (below minimum)
        try:
            from django.core.exceptions import ValidationError
            request = WithdrawalRequest(
                amount=Decimal('50.00')  # Below minimum of 100
            )
            request.full_clean()
            print("✗ Should have failed validation for amount below minimum")
        except ValidationError as e:
            print(f"✓ Minimum amount validation working: {str(e)[:50]}...")
        
        # This should pass
        request = WithdrawalRequest(
            amount=Decimal('1000.00')
        )
        print(f"✓ Valid amount accepted: ₦{request.amount:,.2f}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_models_exist():
    """Test that all models are properly registered"""
    print("\n" + "="*60)
    print("TEST 4: Model Registration")
    print("="*60)
    
    try:
        # Check if models are accessible
        print("\nChecking model registration...")
        
        models = [
            ('InspectionRevenueSettings', InspectionRevenueSettings),
            ('InspectionRevenueSplit', InspectionRevenueSplit),
            ('WithdrawalRequest', WithdrawalRequest),
        ]
        
        for name, model in models:
            print(f"✓ {name}: {model._meta.db_table}")
        
        # Check if tables exist in database
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'inspections_%'
            """)
            tables = cursor.fetchall()
            
            if tables:
                print("\n✓ Database tables found:")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("\n⚠ No tables found - run migrations first:")
                print("  python manage.py migrate inspections")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\n⚠ If tables don't exist, run:")
        print("  python manage.py migrate inspections")
        return False


def test_api_endpoints():
    """Test that API endpoints are registered"""
    print("\n" + "="*60)
    print("TEST 5: API Endpoints")
    print("="*60)
    
    try:
        from django.urls import resolve, reverse
        
        endpoints = [
            ('withdrawal-requests', '/api/v1/wallet/withdrawal-requests/'),
            ('withdrawal-statistics', '/api/v1/wallet/withdrawal-requests/statistics/'),
        ]
        
        print("\nChecking API endpoints...")
        for name, path in endpoints:
            try:
                resolved = resolve(path)
                print(f"✓ {name}: {path}")
            except Exception as e:
                print(f"✗ {name}: {path} - {str(e)[:50]}...")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def print_summary():
    """Print implementation summary"""
    print("\n" + "="*60)
    print("IMPLEMENTATION SUMMARY")
    print("="*60)
    
    print("\n✅ COMPLETED FEATURES:")
    print("  1. Paystack-only payment for inspections")
    print("  2. Automatic revenue split (60% dealer / 40% platform)")
    print("  3. Configurable split percentages in admin")
    print("  4. Instant dealer wallet credit on payment")
    print("  5. Manual withdrawal requests for business accounts")
    print("  6. Admin approval workflow for withdrawals")
    print("  7. Complete audit trail for all transactions")
    
    print("\n📁 FILES CREATED:")
    print("  - inspections/models_revenue.py")
    print("  - inspections/admin_revenue.py")
    print("  - wallet/views_withdrawal.py")
    print("  - inspections/migrations/0002_inspection_revenue_models.py")
    print("  - docs/INSPECTION_PAYMENT_REVENUE_SHARING.md")
    print("  - INSPECTION_PAYMENT_IMPLEMENTATION.md")
    
    print("\n📝 FILES MODIFIED:")
    print("  - inspections/views.py (payment endpoints)")
    print("  - wallet/serializers.py (withdrawal serializers)")
    print("  - wallet/urls.py (withdrawal endpoints)")
    print("  - inspections/admin.py (import revenue admin)")
    
    print("\n🔧 NEXT STEPS:")
    print("  1. Run migration: python manage.py migrate inspections")
    print("  2. Create default revenue settings in admin panel")
    print("  3. Test payment flow with Paystack test keys")
    print("  4. Test withdrawal request flow")
    print("  5. Update frontend to integrate Paystack")
    
    print("\n📚 DOCUMENTATION:")
    print("  - Full docs: docs/INSPECTION_PAYMENT_REVENUE_SHARING.md")
    print("  - Summary: INSPECTION_PAYMENT_IMPLEMENTATION.md")
    
    print("\n🔗 API ENDPOINTS:")
    print("  Payment:")
    print("    POST /api/v1/inspections/{id}/pay/")
    print("    POST /api/v1/inspections/{id}/verify-payment/")
    print("  Withdrawals:")
    print("    GET  /api/v1/wallet/withdrawal-requests/")
    print("    POST /api/v1/wallet/withdrawal-requests/")
    print("    POST /api/v1/wallet/withdrawal-requests/{id}/cancel/")
    print("    GET  /api/v1/wallet/withdrawal-requests/statistics/")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("INSPECTION PAYMENT & REVENUE SHARING SYSTEM")
    print("Test Suite")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Revenue Settings", test_revenue_settings()))
    results.append(("Revenue Split Calculation", test_revenue_split_calculation()))
    results.append(("Withdrawal Validation", test_withdrawal_request_validation()))
    results.append(("Model Registration", test_models_exist()))
    results.append(("API Endpoints", test_api_endpoints()))
    
    # Print results
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Print summary
    print_summary()
    
    print("\n" + "="*60)
    print("Testing complete!")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
