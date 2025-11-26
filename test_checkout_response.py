#!/usr/bin/env python
"""
Test the checkout endpoint response locally to debug the issue.
"""
import os
import sys
import django
import json

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.vercel_settings')

# Initialize Django
django.setup()

from listings.models import Listing, PlatformFeeSettings
from listings.api.serializers import ListingSerializer
from decimal import Decimal

def test_checkout_calculation():
    """Test checkout calculation logic."""
    print("=" * 60)
    print("TESTING CHECKOUT CALCULATION")
    print("=" * 60)
    
    # Get a listing
    print("\n1. Finding a listing...")
    try:
        listing = Listing.objects.first()
        if not listing:
            print("   ✗ No listings found in database")
            return False
        print(f"   ✓ Found listing: {listing.title}")
        print(f"   - UUID: {listing.uuid}")
        print(f"   - Price: ₦{listing.price:,.2f}")
    except Exception as e:
        print(f"   ✗ Error finding listing: {e}")
        return False
    
    # Get fee settings
    print("\n2. Getting fee settings...")
    try:
        fee_settings = PlatformFeeSettings.get_active_settings()
        print(f"   ✓ Active settings found (ID: {fee_settings.id})")
        print(f"   - Service Fee: {fee_settings.service_fee_percentage}%")
        print(f"   - Inspection Fee: {fee_settings.inspection_fee_percentage}%")
        print(f"   - Tax: {fee_settings.tax_percentage}%")
    except Exception as e:
        print(f"   ✗ Error getting fee settings: {e}")
        return False
    
    # Calculate fees
    print("\n3. Calculating fees...")
    try:
        listing_price = float(listing.price) if listing.price else 0
        tax = fee_settings.calculate_tax(listing_price) if listing_price else 0
        inspection_fee = fee_settings.calculate_inspection_fee(listing_price) if listing_price else 0
        service_fee = fee_settings.calculate_service_fee(listing_price) if listing_price else 0
        total = listing_price + tax + inspection_fee + service_fee
        
        print(f"   ✓ Calculations complete:")
        print(f"   - Listing Price: ₦{listing_price:,.2f}")
        print(f"   - Service Fee: ₦{service_fee:,.2f}")
        print(f"   - Inspection Fee: ₦{inspection_fee:,.2f}")
        print(f"   - Tax: ₦{tax:,.2f}")
        print(f"   - Total: ₦{total:,.2f}")
    except Exception as e:
        print(f"   ✗ Error calculating fees: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Build response data
    print("\n4. Building response data...")
    try:
        data = {
            'error': False,
            'listing_price': listing_price,
            'fees': {
                'tax': round(tax, 2),
                'inspection_fee': round(inspection_fee, 2),
                'service_fee': round(service_fee, 2),
            },
            'total': round(total, 2),
            'listing': {'uuid': str(listing.uuid), 'title': listing.title}  # Simplified
        }
        
        print("   ✓ Response data structure:")
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"   ✗ Error building response: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("✓ TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print("\nIf the endpoint is not returning these values, check:")
    print("1. Is the Vercel deployment using the latest code?")
    print("2. Are there any errors in Vercel logs?")
    print("3. Is the PlatformFeeSettings table accessible on production?")
    
    return True

if __name__ == '__main__':
    success = test_checkout_calculation()
    sys.exit(0 if success else 1)
