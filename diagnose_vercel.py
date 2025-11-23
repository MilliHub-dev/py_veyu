#!/usr/bin/env python3
"""
Vercel Deployment Diagnostic Script
Helps identify common issues causing 500 errors on Vercel
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Check critical environment variables"""
    print("=" * 60)
    print("ENVIRONMENT VARIABLES CHECK")
    print("=" * 60)
    
    required_vars = {
        'DJANGO_SECRET_KEY': 'Django secret key for cryptographic signing',
        'DATABASE_URL': 'PostgreSQL connection string',
        'CLOUDINARY_URL': 'Cloudinary media storage URL',
        'EMAIL_HOST_USER': 'SMTP email username',
        'EMAIL_HOST_PASSWORD': 'SMTP email password',
    }
    
    missing = []
    for var, description in required_vars.items():
        value = os.environ.get(var)
        if value:
            # Show partial value for security
            display_value = value[:10] + '...' if len(value) > 10 else value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: MISSING - {description}")
            missing.append(var)
    
    print()
    return missing

def check_django_setup():
    """Try to initialize Django and catch errors"""
    print("=" * 60)
    print("DJANGO INITIALIZATION CHECK")
    print("=" * 60)
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.vercel_settings')
        
        import django
        print("✅ Django imported successfully")
        
        django.setup()
        print("✅ Django setup completed")
        
        from django.conf import settings
        print(f"✅ Settings module loaded: {settings.SETTINGS_MODULE}")
        print(f"✅ Debug mode: {settings.DEBUG}")
        print(f"✅ Allowed hosts: {settings.ALLOWED_HOSTS}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Check that all dependencies are installed")
        return False
        
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def check_database():
    """Test database connection"""
    print("\n" + "=" * 60)
    print("DATABASE CONNECTION CHECK")
    print("=" * 60)
    
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        print("✅ Database connection successful")
        print(f"✅ Database backend: {connection.settings_dict['ENGINE']}")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

def check_static_files():
    """Check static files configuration"""
    print("\n" + "=" * 60)
    print("STATIC FILES CHECK")
    print("=" * 60)
    
    try:
        from django.conf import settings
        
        print(f"✅ STATIC_URL: {settings.STATIC_URL}")
        print(f"✅ STATIC_ROOT: {settings.STATIC_ROOT}")
        
        static_root = Path(settings.STATIC_ROOT)
        if static_root.exists():
            file_count = sum(1 for _ in static_root.rglob('*') if _.is_file())
            print(f"✅ Static files directory exists with {file_count} files")
        else:
            print(f"⚠️  Static files directory doesn't exist: {static_root}")
            print("   Run: python manage.py collectstatic")
        
        return True
        
    except Exception as e:
        print(f"❌ Static files check failed: {e}")
        return False

def check_wsgi_app():
    """Test WSGI application loading"""
    print("\n" + "=" * 60)
    print("WSGI APPLICATION CHECK")
    print("=" * 60)
    
    try:
        # Check api/vercel_app.py
        sys.path.insert(0, str(Path(__file__).parent))
        
        from api.vercel_app import app
        print("✅ WSGI application loaded from api/vercel_app.py")
        print(f"✅ Application type: {type(app)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import WSGI app: {e}")
        return False
        
    except Exception as e:
        print(f"❌ WSGI app check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_cloudinary():
    """Test Cloudinary configuration"""
    print("\n" + "=" * 60)
    print("CLOUDINARY CHECK")
    print("=" * 60)
    
    try:
        import cloudinary
        from django.conf import settings
        
        if hasattr(settings, 'CLOUDINARY_STORAGE'):
            config = settings.CLOUDINARY_STORAGE
            print(f"✅ Cloudinary configured")
            print(f"✅ Cloud name: {config.get('CLOUD_NAME', 'Not set')}")
            print(f"✅ Secure: {config.get('SECURE', False)}")
        else:
            print("⚠️  Cloudinary storage not configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Cloudinary check failed: {e}")
        return False

def main():
    """Run all diagnostic checks"""
    print("\n" + "=" * 60)
    print("VERCEL DEPLOYMENT DIAGNOSTICS")
    print("=" * 60)
    print()
    
    results = {
        'Environment Variables': check_environment(),
        'Django Setup': check_django_setup(),
        'Database': check_database(),
        'Static Files': check_static_files(),
        'WSGI App': check_wsgi_app(),
        'Cloudinary': check_cloudinary(),
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for check, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{check}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All checks passed! Deployment should work.")
    else:
        print("❌ Some checks failed. Fix the issues above.")
        print("\nCommon fixes:")
        print("1. Set missing environment variables in Vercel dashboard")
        print("2. Run: python manage.py collectstatic")
        print("3. Check DATABASE_URL format and connectivity")
        print("4. Verify all dependencies in requirements.txt")
    print("=" * 60)
    
    sys.exit(0 if all_passed else 1)

if __name__ == '__main__':
    main()
