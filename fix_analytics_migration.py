#!/usr/bin/env python
"""
Script to fix missing analytics tables in production database.
This will run the analytics migrations on your production database.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.vercel_settings')
django.setup()

from django.core.management import call_command
from django.db import connection

def check_table_exists(table_name):
    """Check if a table exists in the database"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
        """, [table_name])
        return cursor.fetchone()[0]

def main():
    print("=" * 60)
    print("Analytics Migration Fix Script")
    print("=" * 60)
    
    # Check if analytics tables exist
    tables_to_check = [
        'analytics_listinganalytics',
        'analytics_mechanicanalytics'
    ]
    
    print("\nChecking for missing tables...")
    missing_tables = []
    for table in tables_to_check:
        exists = check_table_exists(table)
        status = "✓ EXISTS" if exists else "✗ MISSING"
        print(f"  {table}: {status}")
        if not exists:
            missing_tables.append(table)
    
    if not missing_tables:
        print("\n✓ All analytics tables exist!")
        return
    
    print(f"\n⚠ Found {len(missing_tables)} missing table(s)")
    print("\nRunning migrations to create missing tables...")
    
    try:
        # Run migrations for analytics app
        call_command('migrate', 'analytics', verbosity=2)
        print("\n✓ Migrations completed successfully!")
        
        # Verify tables were created
        print("\nVerifying tables...")
        all_created = True
        for table in missing_tables:
            exists = check_table_exists(table)
            status = "✓ CREATED" if exists else "✗ STILL MISSING"
            print(f"  {table}: {status}")
            if not exists:
                all_created = False
        
        if all_created:
            print("\n✓ All tables created successfully!")
            print("\nYou can now delete listings from the admin panel.")
        else:
            print("\n✗ Some tables were not created. Check the error messages above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Error running migrations: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
