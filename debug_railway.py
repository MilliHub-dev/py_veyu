#!/usr/bin/env python3
"""
Railway deployment debugging script
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check environment variables and configuration"""
    logger.info("🔍 Environment Check")
    logger.info("=" * 50)
    
    # Check Python version
    logger.info(f"Python version: {sys.version}")
    
    # Check current directory
    logger.info(f"Current directory: {os.getcwd()}")
    
    # Check if manage.py exists
    manage_py = Path("manage.py")
    logger.info(f"manage.py exists: {manage_py.exists()}")
    
    # Check Django settings
    django_settings = os.environ.get('DJANGO_SETTINGS_MODULE', 'Not set')
    logger.info(f"DJANGO_SETTINGS_MODULE: {django_settings}")
    
    # Check critical environment variables
    critical_vars = [
        'DATABASE_URL',
        'DJANGO_SECRET_KEY',
        'PORT'
    ]
    
    logger.info("\n📋 Critical Environment Variables:")
    for var in critical_vars:
        value = os.environ.get(var)
        if value:
            # Mask sensitive values
            if 'SECRET' in var or 'PASSWORD' in var or 'KEY' in var:
                masked_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                logger.info(f"✅ {var}: {masked_value}")
            else:
                logger.info(f"✅ {var}: {value}")
        else:
            logger.error(f"❌ {var}: Not set")
    
    # Check optional variables
    optional_vars = [
        'REDIS_URL',
        'CLOUDINARY_URL',
        'EMAIL_HOST_USER',
        'DEBUG'
    ]
    
    logger.info("\n📋 Optional Environment Variables:")
    for var in optional_vars:
        value = os.environ.get(var)
        if value:
            if 'SECRET' in var or 'PASSWORD' in var or 'KEY' in var or 'URL' in var:
                masked_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                logger.info(f"✅ {var}: {masked_value}")
            else:
                logger.info(f"✅ {var}: {value}")
        else:
            logger.info(f"⚠️  {var}: Not set")

def test_django_import():
    """Test Django import and setup"""
    logger.info("\n🐍 Django Import Test")
    logger.info("=" * 50)
    
    try:
        # Set Django settings if not set
        if not os.environ.get('DJANGO_SETTINGS_MODULE'):
            os.environ['DJANGO_SETTINGS_MODULE'] = 'veyu.railway_settings'
            logger.info("Set DJANGO_SETTINGS_MODULE to veyu.railway_settings")
        
        import django
        logger.info(f"✅ Django imported successfully (version: {django.get_version()})")
        
        django.setup()
        logger.info("✅ Django setup completed")
        
        # Test settings import
        from django.conf import settings
        logger.info(f"✅ Settings imported - DEBUG: {settings.DEBUG}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Django import/setup failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_database_connection():
    """Test database connection"""
    logger.info("\n🗄️  Database Connection Test")
    logger.info("=" * 50)
    
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        logger.info(f"✅ Database connection successful: {result}")
        
        # Get database info
        db_settings = connection.settings_dict
        logger.info(f"Database engine: {db_settings.get('ENGINE', 'Unknown')}")
        logger.info(f"Database name: {db_settings.get('NAME', 'Unknown')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def test_health_endpoint():
    """Test health endpoint functionality"""
    logger.info("\n🏥 Health Endpoint Test")
    logger.info("=" * 50)
    
    try:
        from utils.views import health_check
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/health/')
        
        response = health_check(request)
        logger.info(f"✅ Health check function works - Status: {response.status_code}")
        
        if hasattr(response, 'content'):
            import json
            content = json.loads(response.content.decode())
            logger.info(f"Health check response: {content}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Health endpoint test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_static_files():
    """Test static files configuration"""
    logger.info("\n📁 Static Files Test")
    logger.info("=" * 50)
    
    try:
        from django.conf import settings
        
        logger.info(f"STATIC_URL: {settings.STATIC_URL}")
        logger.info(f"STATIC_ROOT: {settings.STATIC_ROOT}")
        
        static_root = Path(settings.STATIC_ROOT)
        logger.info(f"Static root exists: {static_root.exists()}")
        
        if static_root.exists():
            static_files = list(static_root.rglob('*'))
            logger.info(f"Static files count: {len(static_files)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Static files test failed: {e}")
        return False

def main():
    """Main diagnostic function"""
    logger.info("🚀 Railway Deployment Diagnostics")
    logger.info("=" * 60)
    
    tests = [
        ("Environment Check", check_environment),
        ("Django Import", test_django_import),
        ("Database Connection", test_database_connection),
        ("Health Endpoint", test_health_endpoint),
        ("Static Files", test_static_files),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n📊 Test Results Summary")
    logger.info("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} {test_name}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Railway deployment should work.")
    else:
        logger.error("⚠️  Some tests failed. Check the logs above for details.")
        sys.exit(1)

if __name__ == '__main__':
    main()