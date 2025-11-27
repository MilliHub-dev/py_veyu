"""
Script to create missing user profiles for existing accounts.

This script creates Customer, Dealership, or Mechanic profiles for users
who don't have them yet, based on their user_type.

Run this after deploying the profile auto-creation signal to fix existing users.

Usage:
    python manage.py shell < scripts/create_missing_profiles.py

Or:
    python scripts/create_missing_profiles.py
"""

import os
import sys
import django

# Setup Django environment if running as standalone script
if __name__ == '__main__':
    # Add project root to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
    django.setup()

from accounts.models import Account, Customer, Dealership, Mechanic

def create_missing_profiles():
    """Create missing profiles for all existing users."""
    
    print("=" * 60)
    print("CREATING MISSING USER PROFILES")
    print("=" * 60)
    
    stats = {
        'customer': {'total': 0, 'created': 0, 'existing': 0},
        'dealer': {'total': 0, 'created': 0, 'existing': 0},
        'mechanic': {'total': 0, 'created': 0, 'existing': 0},
        'other': {'total': 0},
    }
    
    # Process customers
    print("\n1. Processing Customers...")
    print("-" * 60)
    customers = Account.objects.filter(user_type='customer')
    stats['customer']['total'] = customers.count()
    
    for user in customers:
        try:
            # Check if profile exists
            if hasattr(user, 'customer_profile'):
                stats['customer']['existing'] += 1
                print(f"  ✓ {user.email} - Profile exists")
            else:
                # Create profile
                Customer.objects.create(user=user)
                stats['customer']['created'] += 1
                print(f"  + {user.email} - Profile created")
        except Exception as e:
            print(f"  ✗ {user.email} - Error: {e}")
    
    # Process dealerships
    print("\n2. Processing Dealerships...")
    print("-" * 60)
    dealers = Account.objects.filter(user_type='dealer')
    stats['dealer']['total'] = dealers.count()
    
    for user in dealers:
        try:
            # Check if profile exists
            if hasattr(user, 'dealership_profile'):
                stats['dealer']['existing'] += 1
                print(f"  ✓ {user.email} - Profile exists")
            else:
                # Create profile
                Dealership.objects.create(user=user)
                stats['dealer']['created'] += 1
                print(f"  + {user.email} - Profile created")
        except Exception as e:
            print(f"  ✗ {user.email} - Error: {e}")
    
    # Process mechanics
    print("\n3. Processing Mechanics...")
    print("-" * 60)
    mechanics = Account.objects.filter(user_type='mechanic')
    stats['mechanic']['total'] = mechanics.count()
    
    for user in mechanics:
        try:
            # Check if profile exists
            if hasattr(user, 'mechanic_profile'):
                stats['mechanic']['existing'] += 1
                print(f"  ✓ {user.email} - Profile exists")
            else:
                # Create profile
                Mechanic.objects.create(user=user)
                stats['mechanic']['created'] += 1
                print(f"  + {user.email} - Profile created")
        except Exception as e:
            print(f"  ✗ {user.email} - Error: {e}")
    
    # Count other user types (admin, staff)
    stats['other']['total'] = Account.objects.filter(
        user_type__in=['admin', 'staff']
    ).count()
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    print(f"\nCustomers:")
    print(f"  Total: {stats['customer']['total']}")
    print(f"  Existing profiles: {stats['customer']['existing']}")
    print(f"  Created profiles: {stats['customer']['created']}")
    
    print(f"\nDealerships:")
    print(f"  Total: {stats['dealer']['total']}")
    print(f"  Existing profiles: {stats['dealer']['existing']}")
    print(f"  Created profiles: {stats['dealer']['created']}")
    
    print(f"\nMechanics:")
    print(f"  Total: {stats['mechanic']['total']}")
    print(f"  Existing profiles: {stats['mechanic']['existing']}")
    print(f"  Created profiles: {stats['mechanic']['created']}")
    
    print(f"\nOther (admin/staff): {stats['other']['total']}")
    
    total_created = (
        stats['customer']['created'] + 
        stats['dealer']['created'] + 
        stats['mechanic']['created']
    )
    
    print(f"\n✅ Total profiles created: {total_created}")
    print("=" * 60)
    
    return stats

if __name__ == '__main__':
    create_missing_profiles()
