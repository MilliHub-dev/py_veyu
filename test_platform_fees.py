#!/usr/bin/env python
"""
Quick test script for Platform Fee Settings
Run with: python test_platform_fees.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from listings.models import PlatformFeeSettings
from decimal import Decimal

def test_fee_calculations():
    print("Testing Platform Fee Settings...")
    print("=" * 50)
    
    # Get or create active settings
    settings = PlatformFeeSettings.get_active_settings()
    print(f"\nActive Settings: {settings}")
    print(f"Service Fee: {settings.service_fee_percentage}% + ₦{settings.service_fee_fixed}")
    print(f"Inspection Fee: {settings.inspection_fee_percentage}% (min: ₦{settings.inspection_fee_minimum}, max: ₦{settings.inspection_fee_maximum})")
    print(f"Tax: {settings.tax_percentage}%")
    
    # Test with a sample listing price
    test_prices = [1000000, 5000000, 10000000, 50000]
    
    print("\n" + "=" * 50)
    print("Fee Calculations for Different Listing Prices:")
    print("=" * 50)
    
    for price in test_prices:
        print(f"\nListing Price: ₦{price:,}")
        
        service_fee = settings.calculate_service_fee(price)
        inspection_fee = settings.calculate_inspection_fee(price)
        tax = settings.calculate_tax(price)
        total = price + service_fee + inspection_fee + tax
        
        print(f"  Service Fee:    ₦{service_fee:,.2f}")
        print(f"  Inspection Fee: ₦{inspection_fee:,.2f}")
        print(f"  Tax:            ₦{tax:,.2f}")
        print(f"  {'─' * 40}")
        print(f"  TOTAL:          ₦{total:,.2f}")
    
    print("\n" + "=" * 50)
    print("✅ All calculations completed successfully!")

if __name__ == "__main__":
    test_fee_calculations()
