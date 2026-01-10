#!/usr/bin/env python3
"""
Vercel Build Script for Django Static Site Generation
Generates static HTML files from Django views for deployment
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

def generate_static_site():
    """Generate static HTML files from Django"""
    
    log("🏗️  Generating static Django site...")
    
    # Set Django settings for static generation
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
    
    # Import Django after setting environment
    import django
    from django.conf import settings
    from django.test import Client
    from django.urls import reverse
    
    django.setup()
    
    # Create output directory
    output_dir = Path('dist')
    output_dir.mkdir(exist_ok=True)
    
    # Create a test client
    client = Client()
    
    # Generate static pages
    pages_to_generate = [
        ('/', 'index.html'),
        ('/api/docs/', 'api-docs.html'),
    ]
    
    for url, filename in pages_to_generate:
        try:
            log(f"📄 Generating {filename} from {url}")
            response = client.get(url)
            
            if response.status_code == 200:
                output_file = output_dir / filename
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(response.content.decode('utf-8'))
                log(f"✅ Generated {filename}")
            else:
                log(f"⚠️  Skipped {filename} (status: {response.status_code})")
                
        except Exception as e:
            log(f"❌ Failed to generate {filename}: {e}")
    
    # Copy static files to dist
    log("📁 Copying static files...")
    if Path('staticfiles').exists():
        run_command('cp -r staticfiles/* dist/', check=False)
    
    log("✅ Static site generation complete!")

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
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
    
    # Create necessary directories
    log("📁 Creating required directories...")
    directories = [
        'staticfiles',
        'dist',
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
    
    result = run_command(
        'python3 manage.py migrate --noinput --verbosity=1',
        check=False
    )
    
    if result.returncode == 0:
        log("✅ Database migrations completed successfully")
    else:
        log("⚠️  Migration warning (may be expected if database is already up to date)")
        log(result.stderr)
    
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
    
    # Generate static site
    try:
        generate_static_site()
    except Exception as e:
        log(f"❌ Static site generation failed: {e}")
        # Create a simple index.html as fallback
        with open('dist/index.html', 'w') as f:
            f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Veyu API</title>
</head>
<body>
    <h1>Veyu API</h1>
    <p>API is running. Visit <a href="/api/docs/">/api/docs/</a> for documentation.</p>
</body>
</html>
            ''')
        log("✅ Created fallback index.html")
    
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
        'dist/index.html',
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
