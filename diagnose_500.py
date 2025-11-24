"""
Diagnostic script to identify the cause of 500 Internal Server Error on Vercel
"""

import os
import sys
from pathlib import Path

# Add project to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

print("=" * 60)
print("VERCEL 500 ERROR DIAGNOSTIC")
print("=" * 60)

# Check 1: Environment Variables
print("\n1. CHECKING ENVIRONMENT VARIABLES:")
print("-" * 60)

required_vars = [
    'DJANGO_SECRET_KEY',
    'DATABASE_URL',
    'CLOUDINARY_URL',
    'EMAIL_HOST_USER',
    'EMAIL_HOST_PASSWORD',
]

missing_vars = []
for var in required_vars:
    value = os.environ.get(var)
    if value:
        # Mask sensitive values
        if len(value) > 20:
            masked = value[:10] + "..." + value[-5:]
        else:
            masked = "***"
        print(f"✓ {var}: {masked}")
    else:
        print(f"✗ {var}: NOT SET")
        missing_vars.append(var)

if missing_vars:
    print(f"\n⚠️  MISSING VARIABLES: {', '.join(missing_vars)}")
    print("\nThese must be set in Vercel Dashboard:")
    print("Settings → Environment Variables")
else:
    print("\n✓ All required environment variables are set")

# Check 2: Django Settings Import
print("\n2. CHECKING DJANGO SETTINGS:")
print("-" * 60)

try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.vercel_settings')
    import django
    django.setup()
    print("✓ Django settings imported successfully")
    
    from django.conf import settings
    print(f"✓ DEBUG mode: {settings.DEBUG}")
    print(f"✓ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    
except Exception as e:
    print(f"✗ Failed to import Django settings: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check 3: Database Connection
print("\n3. CHECKING DATABASE CONNECTION:")
print("-" * 60)

try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
    print("✓ Database connection successful")
    print(f"✓ Database: {connection.settings_dict['NAME']}")
    
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    import traceback
    traceback.print_exc()

# Check 4: Cloudinary Configuration
print("\n4. CHECKING CLOUDINARY:")
print("-" * 60)

try:
    import cloudinary
    config = cloudinary.config()
    if config.cloud_name:
        print(f"✓ Cloudinary configured: {config.cloud_name}")
    else:
        print("✗ Cloudinary not configured")
except Exception as e:
    print(f"✗ Cloudinary check failed: {e}")

# Check 5: WSGI Application
print("\n5. CHECKING WSGI APPLICATION:")
print("-" * 60)

try:
    from django.core.wsgi import get_wsgi_application
    app = get_wsgi_application()
    print("✓ WSGI application created successfully")
    
    # Test a simple request
    from io import BytesIO
    
    def start_response(status, headers):
        print(f"✓ Response status: {status}")
    
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/health',
        'wsgi.input': BytesIO(),
        'wsgi.errors': sys.stderr,
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '8000',
        'wsgi.url_scheme': 'http',
    }
    
    response = app(environ, start_response)
    print("✓ Test request processed successfully")
    
except Exception as e:
    print(f"✗ WSGI application failed: {e}")
    import traceback
    traceback.print_exc()

# Check 6: Installed Apps
print("\n6. CHECKING INSTALLED APPS:")
print("-" * 60)

try:
    from django.conf import settings
    problematic_apps = ['daphne', 'channels']
    found_problematic = [app for app in settings.INSTALLED_APPS if app in problematic_apps]
    
    if found_problematic:
        print(f"⚠️  Found problematic apps for serverless: {found_problematic}")
        print("   These should be removed in vercel_settings.py")
    else:
        print("✓ No problematic apps found")
        
    print(f"\nInstalled apps ({len(settings.INSTALLED_APPS)}):")
    for app in settings.INSTALLED_APPS:
        print(f"  - {app}")
        
except Exception as e:
    print(f"✗ Failed to check installed apps: {e}")

# Summary
print("\n" + "=" * 60)
print("DIAGNOSTIC SUMMARY")
print("=" * 60)

if missing_vars:
    print("\n❌ ACTION REQUIRED:")
    print(f"   Set these variables in Vercel: {', '.join(missing_vars)}")
    print("\n   Steps:")
    print("   1. Go to Vercel Dashboard → Your Project")
    print("   2. Settings → Environment Variables")
    print("   3. Add each missing variable")
    print("   4. Redeploy")
else:
    print("\n✓ All checks passed!")
    print("  If still getting 500 errors, check Vercel function logs")

print("\n" + "=" * 60)
