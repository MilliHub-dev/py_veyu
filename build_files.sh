#!/bin/bash

# Vercel Build Script for Django Static Files
# This script handles dependency installation, static file collection, and environment validation

set -e  # Exit on any error

echo "🚀 Starting Vercel build process..."

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Environment validation
log "📋 Validating environment variables..."

# Critical environment variables for Django
REQUIRED_VARS=(
    "DJANGO_SECRET_KEY"
    "DATABASE_URL"
    "CLOUDINARY_URL"
)

# Optional but recommended variables
OPTIONAL_VARS=(
    "EMAIL_HOST_USER"
    "EMAIL_HOST_PASSWORD"
    "DEFAULT_FROM_EMAIL"
    "FRONTEND_URL"
)

# Check required variables
missing_vars=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    else
        log "✅ $var is set"
    fi
done

# Report missing required variables
if [ ${#missing_vars[@]} -ne 0 ]; then
    log "❌ Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        log "   - $var"
    done
    log "💡 Please set these variables in your Vercel dashboard or .env file"
    exit 1
fi

# Check optional variables (warn but don't fail)
for var in "${OPTIONAL_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        log "⚠️  Optional variable $var is not set"
    else
        log "✅ $var is set"
    fi
done

# Python version check
log "🐍 Checking Python version..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    log "✅ Python version: $PYTHON_VERSION"
else
    log "❌ Python3 not found"
    exit 1
fi

# Pip version check
log "📦 Checking pip version..."
if command_exists pip3; then
    PIP_VERSION=$(pip3 --version 2>&1 | cut -d' ' -f2)
    log "✅ Pip version: $PIP_VERSION"
else
    log "❌ Pip3 not found"
    exit 1
fi

# Install Python dependencies
log "📥 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    log "📋 Found requirements.txt, installing packages..."
    
    # Upgrade pip first
    pip3 install --upgrade pip
    
    # Install requirements with optimizations for Vercel
    pip3 install -r requirements.txt --no-cache-dir --disable-pip-version-check
    
    log "✅ Dependencies installed successfully"
else
    log "❌ requirements.txt not found"
    exit 1
fi

# Django setup check
log "🔧 Validating Django configuration..."

# Set Django settings module for Vercel
export DJANGO_SETTINGS_MODULE="veyu.vercel_settings"

# Check if Django can import settings
if python3 -c "import django; django.setup()" 2>/dev/null; then
    log "✅ Django configuration is valid"
else
    log "❌ Django configuration error"
    python3 -c "import django; django.setup()" # Show the actual error
    exit 1
fi

# Create necessary directories
log "📁 Creating required directories..."
mkdir -p staticfiles
mkdir -p logs
mkdir -p uploads/docs
mkdir -p uploads/profiles
mkdir -p uploads/signed_docs
mkdir -p uploads/vehicle
mkdir -p uploads/vehicles

log "✅ Directories created"

# Collect static files
log "🎨 Collecting static files..."

# Run Django's collectstatic command
python3 manage.py collectstatic --noinput --clear --verbosity=1

if [ $? -eq 0 ]; then
    log "✅ Static files collected successfully"
    
    # Show static files summary
    STATIC_COUNT=$(find staticfiles -type f | wc -l)
    STATIC_SIZE=$(du -sh staticfiles | cut -f1)
    log "📊 Collected $STATIC_COUNT static files ($STATIC_SIZE total)"
else
    log "❌ Static file collection failed"
    exit 1
fi

# Optimize static files for CDN
log "⚡ Optimizing static files for CDN..."

# Remove unnecessary files that might have been collected
find staticfiles -name "*.pyc" -delete 2>/dev/null || true
find staticfiles -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find staticfiles -name "*.map" -delete 2>/dev/null || true

# Compress CSS and JS files if tools are available
if command_exists gzip; then
    log "🗜️  Pre-compressing static files..."
    find staticfiles -type f \( -name "*.css" -o -name "*.js" -o -name "*.html" -o -name "*.json" \) -exec gzip -k {} \;
    log "✅ Static files pre-compressed"
fi

# Database migration check (but don't run migrations in build)
log "🗄️  Checking database migrations..."
python3 manage.py showmigrations --plan > /dev/null 2>&1
if [ $? -eq 0 ]; then
    log "✅ Database migration check passed"
else
    log "⚠️  Database migration check failed (this is normal if DB is not accessible during build)"
fi

# Final validation
log "🔍 Running final validation checks..."

# Check if critical files exist
CRITICAL_FILES=(
    "manage.py"
    "vercel_app.py"
    "veyu/vercel_settings.py"
    "staticfiles"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ -e "$file" ]; then
        log "✅ $file exists"
    else
        log "❌ Critical file missing: $file"
        exit 1
    fi
done

# Check Django apps can be imported
log "🧪 Testing Django app imports..."
python3 -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.vercel_settings')
django.setup()

# Test importing all apps
apps = ['accounts', 'bookings', 'chat', 'feedback', 'listings', 'wallet', 'utils', 'analytics', 'docs', 'inspections']
for app in apps:
    try:
        __import__(app)
        print(f'✅ {app} imported successfully')
    except ImportError as e:
        print(f'❌ Failed to import {app}: {e}')
        exit(1)
"

if [ $? -eq 0 ]; then
    log "✅ All Django apps can be imported"
else
    log "❌ Django app import test failed"
    exit 1
fi

# Build summary
log "📈 Build Summary:"
log "   - Python version: $PYTHON_VERSION"
log "   - Pip version: $PIP_VERSION"
log "   - Static files: $STATIC_COUNT files ($STATIC_SIZE)"
log "   - Django apps: All apps validated"
log "   - Environment: All required variables set"

log "🎉 Build completed successfully!"
log "🚀 Ready for Vercel deployment"

# Set build success flag
touch .build_success

exit 0