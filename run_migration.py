#!/usr/bin/env python
"""
Script to run Django migrations on Vercel/production database.
This ensures the PlatformFeeSettings table is created.
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.vercel_settings')

# Initialize Django
django.setup()

from django.core.management import call_command

def run_migrations():
    """Run Django migrations."""
    print("Running Django migrations...")
    try:
        call_command('migrate', '--noinput', verbosity=2)
        print("\n✓ Migrations completed successfully!")
        return True
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        return False

if __name__ == '__main__':
    success = run_migrations()
    sys.exit(0 if success else 1)
