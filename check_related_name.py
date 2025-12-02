"""
Check the actual related name for Customer
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from accounts.models import Account, Customer

# Get a customer
customer = Customer.objects.first()
if not customer:
    print("No customers found")
    exit(1)

user = customer.user

print("=" * 60)
print("RELATED NAME CHECK")
print("=" * 60)

print(f"\nCustomer: {customer}")
print(f"User: {user}")

print(f"\nChecking attributes on user:")
print(f"  hasattr(user, 'customer'): {hasattr(user, 'customer')}")
print(f"  hasattr(user, 'customer_profile'): {hasattr(user, 'customer_profile')}")

if hasattr(user, 'customer_profile'):
    print(f"  user.customer_profile: {user.customer_profile}")
    print(f"  user.customer_profile == customer: {user.customer_profile == customer}")

print("\n" + "=" * 60)
