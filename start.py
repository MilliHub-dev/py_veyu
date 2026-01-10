#!/usr/bin/env python3
"""
Railway startup script with better error handling and debugging
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def run_command(command, description, required=True):
    """Run a command with proper error handling"""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        logger.info(f"✅ {description} completed successfully")
        if result.stdout:
            logger.info(f"Output: {result.stdout}")
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"❌ {description} timed out after 5 minutes")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {description} failed with exit code {e.returncode}")
        logger.error(f"Error output: {e.stderr}")
        if e.stdout:
            logger.error(f"Standard output: {e.stdout}")
        if required:
            return False
        else:
            logger.warning(f"⚠️  {description} failed but continuing...")
            return True
    except Exception as e:
        logger.error(f"❌ Unexpected error during {description}: {e}")
        return False

def check_environment():
    """Check required environment variables"""
    logger.info("🔍 Checking environment variables...")
    
    # Check Python version
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current directory: {os.getcwd()}")
    
    required_vars = [
        'DATABASE_URL',
        'DJANGO_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing_vars.append(var)
        else:
            # Mask sensitive values for logging
            if 'SECRET' in var or 'PASSWORD' in var:
                masked_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                logger.info(f"✅ {var}: {masked_value}")
            else:
                logger.info(f"✅ {var}: {value}")
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        return False
    
    # Check optional vars
    optional_vars = ['CLOUDINARY_URL', 'REDIS_URL', 'EMAIL_HOST_USER', 'PORT']
    for var in optional_vars:
        value = os.environ.get(var)
        if value:
            if 'URL' in var and len(value) > 20:
                masked_value = f"{value[:15]}...{value[-10:]}"
                logger.info(f"✅ {var}: {masked_value}")
            else:
                logger.info(f"✅ {var}: {value}")
        else:
            logger.warning(f"⚠️  {var} is not set (optional)")
    
    return True

def test_django_setup():
    """Test Django setup"""
    try:
        logger.info("🔧 Testing Django setup...")
        
        # Set Django settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.railway_settings')
        logger.info(f"DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
        
        import django
        django.setup()
        logger.info(f"✅ Django {django.get_version()} setup successful")
        
        # Test settings import
        from django.conf import settings
        logger.info(f"✅ Settings loaded - DEBUG: {settings.DEBUG}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Django setup failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_database_connection():
    """Test database connection"""
    try:
        logger.info("🗄️  Testing database connection...")
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        logger.info(f"✅ Database connection successful: {result}")
        
        # Get database info
        db_settings = connection.settings_dict
        logger.info(f"Database engine: {db_settings.get('ENGINE', 'Unknown')}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def main():
    """Main startup function"""
    logger.info("🚀 Starting Railway deployment...")
    logger.info("=" * 60)
    
    # Check environment
    if not check_environment():
        logger.error("❌ Environment check failed")
        sys.exit(1)
    
    # Test Django setup
    if not test_django_setup():
        logger.error("❌ Django setup failed")
        sys.exit(1)
    
    # Test database connection
    if not test_database_connection():
        logger.error("❌ Database connection failed")
        sys.exit(1)
    
    # Collect static files (non-critical)
    logger.info("📁 Collecting static files...")
    run_command('python manage.py collectstatic --noinput --clear', 'Static files collection', required=False)
    
    # Run migrations
    logger.info("🔄 Running database migrations...")
    if not run_command('python manage.py migrate --verbosity=1', 'Database migrations'):
        logger.error("❌ Database migrations failed")
        sys.exit(1)
    
    # Test health endpoint
    try:
        logger.info("🏥 Testing health endpoint...")
        from utils.views import health_check
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/health/')
        response = health_check(request)
        
        logger.info(f"✅ Health endpoint test successful - Status: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Health endpoint test failed: {e}")
        # Don't exit here, just log the error
    
    # Start Gunicorn
    port = os.environ.get('PORT', '8000')
    workers = os.environ.get('WEB_CONCURRENCY', '2')
    
    gunicorn_cmd = [
        'gunicorn',
        'veyu.wsgi:application',
        '--bind', f'0.0.0.0:{port}',
        '--workers', str(workers),
        '--timeout', '120',
        '--keep-alive', '5',
        '--max-requests', '1000',
        '--max-requests-jitter', '100',
        '--access-logfile', '-',
        '--error-logfile', '-',
        '--log-level', 'info'
    ]
    
    logger.info(f"🌐 Starting Gunicorn server on port {port} with {workers} workers...")
    logger.info(f"Command: {' '.join(gunicorn_cmd)}")
    
    # Execute Gunicorn (this will replace the current process)
    try:
        os.execvp('gunicorn', gunicorn_cmd)
    except Exception as e:
        logger.error(f"❌ Failed to start Gunicorn: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()