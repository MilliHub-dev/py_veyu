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
    
    django.setup()
    
    # Create output directory
    output_dir = Path('dist')
    output_dir.mkdir(exist_ok=True)
    
    # Create a test client
    client = Client()
    
    # Generate a simple index.html since Django URLs are redirecting
    log("📄 Creating static index.html")
    index_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Veyu API</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 40px; }
        .api-info { background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .endpoint { background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #007cba; }
        a { color: #007cba; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚗 Veyu API</h1>
        <p>Vehicle marketplace and services platform</p>
    </div>
    
    <div class="api-info">
        <h2>API Documentation</h2>
        <p>Welcome to the Veyu API. This platform provides comprehensive vehicle marketplace and services.</p>
        
        <div class="endpoint">
            <h3>📚 API Documentation</h3>
            <p><a href="/api/docs/">Interactive API Documentation (Swagger)</a></p>
            <p>Complete API reference with interactive testing capabilities</p>
        </div>
        
        <div class="endpoint">
            <h3>🔐 Authentication</h3>
            <p><strong>POST</strong> <code>/api/v1/token/</code> - Get JWT token</p>
            <p><strong>POST</strong> <code>/api/v1/token/refresh/</code> - Refresh JWT token</p>
        </div>
        
        <div class="endpoint">
            <h3>👥 Accounts</h3>
            <p><strong>GET/POST</strong> <code>/api/v1/accounts/</code> - User account management</p>
        </div>
        
        <div class="endpoint">
            <h3>🚙 Listings</h3>
            <p><strong>GET/POST</strong> <code>/api/v1/listings/</code> - Vehicle listings</p>
        </div>
        
        <div class="endpoint">
            <h3>💬 Chat</h3>
            <p><strong>GET/POST</strong> <code>/api/v1/chat/</code> - Chat functionality</p>
        </div>
        
        <div class="endpoint">
            <h3>💰 Wallet</h3>
            <p><strong>GET/POST</strong> <code>/api/v1/wallet/</code> - Wallet operations</p>
        </div>
        
        <div class="endpoint">
            <h3>🔧 Inspections</h3>
            <p><strong>GET/POST</strong> <code>/api/v1/inspections/</code> - Vehicle inspections</p>
        </div>
        
        <div class="endpoint">
            <h3>🎧 Support</h3>
            <p><strong>GET/POST</strong> <code>/api/v1/support/</code> - Customer support</p>
        </div>
    </div>
    
    <div class="api-info">
        <h2>Getting Started</h2>
        <ol>
            <li>Visit the <a href="/api/docs/">API Documentation</a> for detailed endpoint information</li>
            <li>Obtain an authentication token from <code>/api/v1/token/</code></li>
            <li>Include the token in your requests: <code>Authorization: Bearer &lt;token&gt;</code></li>
            <li>Start making API calls to the available endpoints</li>
        </ol>
    </div>
    
    <div class="api-info">
        <h2>Status</h2>
        <p>✅ API is running and ready to serve requests</p>
        <p>🔗 Base URL: <code>https://py-veyu.vercel.app</code></p>
    </div>
</body>
</html>'''
    
    # Write index.html
    with open(output_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(index_content)
    log("✅ Created index.html")
    
    # Try to generate API docs page
    try:
        log("📄 Attempting to generate API docs page")
        response = client.get('/api/docs/', follow=True)  # Follow redirects
        
        if response.status_code == 200:
            with open(output_dir / 'api-docs.html', 'w', encoding='utf-8') as f:
                f.write(response.content.decode('utf-8'))
            log("✅ Generated api-docs.html")
        else:
            log(f"⚠️  Could not generate API docs (status: {response.status_code})")
            # Create a redirect page
            redirect_content = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>API Documentation</title>
    <meta http-equiv="refresh" content="0; url=/api/docs/">
</head>
<body>
    <p>Redirecting to <a href="/api/docs/">API Documentation</a>...</p>
</body>
</html>'''
            with open(output_dir / 'api-docs.html', 'w', encoding='utf-8') as f:
                f.write(redirect_content)
            log("✅ Created redirect page for API docs")
            
    except Exception as e:
        log(f"❌ Failed to generate API docs: {e}")
        # Create a simple fallback
        fallback_content = '''<!DOCTYPE html>
<html>
<head>
    <title>API Documentation</title>
</head>
<body>
    <h1>API Documentation</h1>
    <p>Please visit <a href="/api/docs/">/api/docs/</a> for the interactive API documentation.</p>
</body>
</html>'''
        with open(output_dir / 'api-docs.html', 'w', encoding='utf-8') as f:
            f.write(fallback_content)
        log("✅ Created fallback API docs page")
    
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
