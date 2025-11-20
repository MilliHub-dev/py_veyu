#!/usr/bin/env python
"""
Generate a new Django SECRET_KEY
"""
from django.core.management.utils import get_random_secret_key

print("=" * 70)
print("NEW DJANGO SECRET KEY")
print("=" * 70)
new_key = get_random_secret_key()
print(f"\n{new_key}\n")
print("=" * 70)
print("\nIMPORTANT:")
print("1. Update your .env file: DJANGO_SECRET_KEY=" + new_key)
print("2. Update Vercel environment variables with this same key")
print("3. Redeploy your application")
print("4. All users will need to re-login")
print("=" * 70)
