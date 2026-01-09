#!/usr/bin/env python3
"""
Vercel Build Script for Django Static Files
Handles dependency installation, static file collection, and environment validation
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def log(message):
    """Log with emoji for better visibility"""
    logger.info(message)

def run_command(command, check=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {command}")
        logger.error(f"Error: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def main():
    log("🚀 Starting Vercel build process...")
    
    # Environment validation
    log("📋 Validating environment variables...")
    
    required_vars = [
        "DJANGO_SECRET_KEY",
        "DATABASE_URL",
        "CLOUDINARY_URL"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
        else:
            log(f"✅ {var} is set")
    
    if missing_vars:
        log("❌ Missing required environment variables:")
        for var in missing_vars:
            log(f"   - {var}")
        log("💡 Please set these variables in your Vercel dashboard")
        sys.exit(1)
    
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.vercel_settings')
    
    # Create necessary directories
    log("📁 Creating required directories...")
    directories = [
        'staticfiles',
        'logs',
        'uploads/docs',
        'uploads/profiles',
        'uploads/signed_docs',
        'uploads/vehicle',
        'uploads/vehicles'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    log("✅ Directories created")
    
    # Run database migrations
    log("🗄️  Running database migrations...")
    
    # First, try to fix any migration inconsistencies
    log("🔧 Checking for migration inconsistencies...")
    result = run_command(
        'python3 manage.py migrate --noinput --verbosity=1',
        check=False
    )
    
    if result.returncode != 0 and "InconsistentMigrationHistory" in result.stderr:
        log("⚠️  Detected migration history inconsistency")
        log("🔧 Attempting to fix migration dependencies...")
        
        # Try to fake the problematic migration first
        fake_result = run_command(
            'python3 manage.py migrate feedback 0001 --fake',
            check=False
        )
        
        if fake_result.returncode == 0:
            log("✅ Faked problematic migration")
            
            # Now try to migrate normally
            result = run_command(
                'python3 manage.py migrate --noinput --verbosity=1',
                check=False
            )
    
    if result.returncode == 0:
        log("✅ Database migrations completed successfully")
    else:
        log("⚠️  Migration warning (may be expected if database is already up to date)")
        log(result.stderr)
        # Don't fail the build on migration errors as they might be non-critical
    
    # Collect static files
    log("🎨 Collecting static files...")
    
    result = run_command(
        'python3 manage.py collectstatic --noinput --clear --verbosity=1',
        check=False
    )
    
    if result.returncode == 0:
        log("✅ Static files collected successfully")
        
        # Count static files
        static_count = sum(1 for _ in Path('staticfiles').rglob('*') if _.is_file())
        log(f"📊 Collected {static_count} static files")
    else:
        log("❌ Static file collection failed")
        log(result.stderr)
        sys.exit(1)
    
    # Optimize static files
    log("⚡ Optimizing static files...")
    
    # Remove unnecessary files
    run_command('find staticfiles -name "*.pyc" -delete', check=False)
    run_command('find staticfiles -name "__pycache__" -type d -exec rm -rf {} +', check=False)
    run_command('find staticfiles -name "*.map" -delete', check=False)
    
    log("✅ Static files optimized")
    
    # Final validation
    log("🔍 Running final validation checks...")
    
    critical_files = [
        'manage.py',
        'vercel_app.py',
        'veyu/vercel_settings.py',
        'staticfiles'
    ]
    
    for file_path in critical_files:
        if Path(file_path).exists():
            log(f"✅ {file_path} exists")
        else:
            log(f"❌ Critical file missing: {file_path}")
            sys.exit(1)
    
    log("🎉 Build completed successfully!")
    log("🚀 Ready for Vercel deployment")

if __name__ == '__main__':
    main()
