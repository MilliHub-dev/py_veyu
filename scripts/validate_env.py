#!/usr/bin/env python3
"""
Environment Variable Validation Script for Vercel Deployment

This script validates that all critical environment variables are set
and provides helpful error messages for missing or invalid configurations.

Usage:
    python scripts/validate_env.py
    python scripts/validate_env.py --generate-secret-key
    
Exit codes:
    0: All critical variables are valid
    1: One or more critical variables are missing or invalid
"""

import os
import sys
import argparse
from urllib.parse import urlparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def generate_secret_key():
    """Generate a new Django secret key."""
    try:
        from django.core.management.utils import get_random_secret_key
        return get_random_secret_key()
    except ImportError:
        # Fallback if Django is not available
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
        return ''.join(secrets.choice(alphabet) for _ in range(50))

def validate_database_url(url):
    """Validate DATABASE_URL format and connectivity requirements."""
    if not url:
        return False, "DATABASE_URL is not set"
    
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ['postgresql', 'postgres', 'sqlite']:
            return False, f"Unsupported database scheme: {parsed.scheme}"
        
        if parsed.scheme in ['postgresql', 'postgres']:
            if not parsed.hostname:
                return False, "PostgreSQL DATABASE_URL missing hostname"
            if not parsed.username:
                return False, "PostgreSQL DATABASE_URL missing username"
            if not parsed.password:
                return False, "PostgreSQL DATABASE_URL missing password"
            if not parsed.path or parsed.path == '/':
                return False, "PostgreSQL DATABASE_URL missing database name"
        
        return True, "DATABASE_URL format is valid"
    except Exception as e:
        return False, f"Invalid DATABASE_URL format: {str(e)}"

def validate_cloudinary_url(url):
    """Validate CLOUDINARY_URL format."""
    if not url:
        return False, "CLOUDINARY_URL is not set"
    
    try:
        parsed = urlparse(url)
        if parsed.scheme != 'cloudinary':
            return False, f"Invalid Cloudinary URL scheme: {parsed.scheme}"
        
        if '@' not in parsed.netloc:
            return False, "Cloudinary URL missing credentials"
        
        credentials, cloud_name = parsed.netloc.split('@', 1)
        if ':' not in credentials:
            return False, "Cloudinary URL missing API key or secret"
        
        api_key, api_secret = credentials.split(':', 1)
        if not api_key or not api_secret or not cloud_name:
            return False, "Cloudinary URL missing required components"
        
        return True, "CLOUDINARY_URL format is valid"
    except Exception as e:
        return False, f"Invalid CLOUDINARY_URL format: {str(e)}"

def validate_email_config():
    """Validate email configuration."""
    errors = []
    
    email_host = os.getenv('EMAIL_HOST')
    email_user = os.getenv('EMAIL_HOST_USER')
    email_password = os.getenv('EMAIL_HOST_PASSWORD')
    
    if not email_host:
        errors.append("EMAIL_HOST is not set")
    
    if not email_user:
        errors.append("EMAIL_HOST_USER is not set")
    
    if not email_password:
        errors.append("EMAIL_HOST_PASSWORD is not set")
    
    # Validate email addresses
    default_from = os.getenv('DEFAULT_FROM_EMAIL')
    if default_from and '@' not in default_from:
        errors.append("DEFAULT_FROM_EMAIL is not a valid email address")
    
    return len(errors) == 0, errors

def validate_sms_config():
    """Validate SMS configuration."""
    errors = []
    warnings = []
    
    sms_api_key = os.getenv('AFRICAS_TALKING_API_KEY')
    if not sms_api_key:
        errors.append("AFRICAS_TALKING_API_KEY is not set - required for OTP functionality")
    elif sms_api_key in ['your-africas-talking-api-key', 'your-api-key']:
        warnings.append("AFRICAS_TALKING_API_KEY appears to be using default/example value")
    
    return len(errors) == 0, errors, warnings

def validate_security_settings():
    """Validate security-related settings."""
    warnings = []
    
    debug = os.getenv('DEBUG', 'False').lower()
    if debug in ['true', '1', 'yes', 'on']:
        warnings.append("DEBUG is enabled - should be False in production")
    
    secret_key = os.getenv('DJANGO_SECRET_KEY')
    if not secret_key:
        return False, ["DJANGO_SECRET_KEY is not set"]
    
    if secret_key in ['your-secret-key-here', 'your-unique-secret-key-here-change-this-in-production']:
        warnings.append("DJANGO_SECRET_KEY appears to be using default/example value")
    
    if len(secret_key) < 50:
        warnings.append("DJANGO_SECRET_KEY should be at least 50 characters long")
    
    return True, warnings

def validate_django_settings_compatibility():
    """Validate that environment variables are compatible with Django settings."""
    warnings = []
    
    # Check if we can import Django settings
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.vercel_settings')
        import django
        django.setup()
        from django.conf import settings
        
        # Validate that critical settings are properly configured
        if not hasattr(settings, 'SECRET_KEY') or not settings.SECRET_KEY:
            warnings.append("Django SECRET_KEY not properly configured")
        
        if not hasattr(settings, 'DATABASES') or not settings.DATABASES.get('default'):
            warnings.append("Django DATABASES not properly configured")
        
        # Check email configuration
        if not hasattr(settings, 'EMAIL_HOST_USER') or not settings.EMAIL_HOST_USER:
            warnings.append("Django EMAIL_HOST_USER not properly configured")
        
        # Check Cloudinary configuration
        if not hasattr(settings, 'CLOUDINARY_STORAGE') or not settings.CLOUDINARY_STORAGE:
            warnings.append("Django CLOUDINARY_STORAGE not properly configured")
        
        return True, warnings
        
    except Exception as e:
        return False, [f"Failed to validate Django settings: {str(e)}"]

def main():
    """Main validation function."""
    print("🔍 Validating environment variables for Vercel deployment...")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # Critical variables validation
    critical_vars = {
        'DJANGO_SECRET_KEY': 'Django secret key for cryptographic signing',
        'DATABASE_URL': 'Database connection string',
        'EMAIL_HOST_USER': 'SMTP username for email sending',
        'EMAIL_HOST_PASSWORD': 'SMTP password for email sending',
        'CLOUDINARY_URL': 'Cloudinary credentials for media storage',
        'AFRICAS_TALKING_API_KEY': 'SMS API key for OTP and notifications',
    }
    
    print("📋 Checking critical environment variables...")
    for var, description in critical_vars.items():
        value = os.getenv(var)
        if not value:
            errors.append(f"❌ {var}: {description} - NOT SET")
        else:
            print(f"✅ {var}: Set")
    
    # Detailed validation
    print("\n🔧 Performing detailed validation...")
    
    # Database validation
    db_valid, db_message = validate_database_url(os.getenv('DATABASE_URL'))
    if not db_valid:
        errors.append(f"❌ DATABASE_URL: {db_message}")
    else:
        print(f"✅ DATABASE_URL: {db_message}")
    
    # Cloudinary validation
    cloudinary_valid, cloudinary_message = validate_cloudinary_url(os.getenv('CLOUDINARY_URL'))
    if not cloudinary_valid:
        errors.append(f"❌ CLOUDINARY_URL: {cloudinary_message}")
    else:
        print(f"✅ CLOUDINARY_URL: {cloudinary_message}")
    
    # Email validation
    email_valid, email_errors = validate_email_config()
    if not email_valid:
        for error in email_errors:
            errors.append(f"❌ Email Config: {error}")
    else:
        print("✅ Email configuration: Valid")
    
    # SMS validation
    sms_valid, sms_errors, sms_warnings = validate_sms_config()
    if not sms_valid:
        for error in sms_errors:
            errors.append(f"❌ SMS Config: {error}")
    else:
        print("✅ SMS configuration: Valid")
        for warning in sms_warnings:
            warnings.append(f"⚠️  SMS: {warning}")
    
    # Security validation
    security_valid, security_messages = validate_security_settings()
    if not security_valid:
        for error in security_messages:
            errors.append(f"❌ Security: {error}")
    else:
        print("✅ Security configuration: Valid")
        for warning in security_messages:
            warnings.append(f"⚠️  Security: {warning}")
    
    # Django settings compatibility check
    print("\n� Valcidating Django settings compatibility...")
    django_valid, django_messages = validate_django_settings_compatibility()
    if not django_valid:
        for error in django_messages:
            errors.append(f"❌ Django Settings: {error}")
    else:
        print("✅ Django settings: Compatible")
        for warning in django_messages:
            warnings.append(f"⚠️  Django Settings: {warning}")
    
    # Optional but recommended variables
    print("\n📝 Checking recommended optional variables...")
    recommended_vars = {
        'SENTRY_DSN': 'Error tracking and monitoring',
        'FRONTEND_URL': 'Frontend URL for email links',
        'GOOGLE_MAPS_API_KEY': 'Location services integration',
    }
    
    for var, description in recommended_vars.items():
        value = os.getenv(var)
        if not value:
            warnings.append(f"⚠️  {var}: {description} - Not set (recommended)")
        else:
            print(f"✅ {var}: Set")
    
    # Print results
    print("\n" + "=" * 60)
    print("📊 VALIDATION RESULTS")
    print("=" * 60)
    
    if errors:
        print(f"\n❌ CRITICAL ERRORS ({len(errors)}):")
        for error in errors:
            print(f"   {error}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"   {warning}")
    
    if not errors and not warnings:
        print("\n🎉 All environment variables are properly configured!")
        print("✅ Ready for Vercel deployment!")
    elif not errors:
        print(f"\n✅ All critical variables are set!")
        print(f"⚠️  {len(warnings)} warnings - review recommended settings")
        print("🚀 Ready for Vercel deployment with warnings")
    else:
        print(f"\n💥 Deployment will FAIL - {len(errors)} critical errors found")
        print("🔧 Fix the errors above before deploying to Vercel")
        print("\n📋 QUICK FIX GUIDE:")
        print("1. Generate Django secret key: python scripts/validate_env.py --generate-secret-key")
        print("2. Copy .env.example to .env: copy .env.example .env")
        print("3. Edit .env file with your actual values")
        print("4. For Vercel deployment, set these in Vercel dashboard or CLI:")
        print("   vercel env add DJANGO_SECRET_KEY")
        print("   vercel env add DATABASE_URL")
        print("   vercel env add EMAIL_HOST_USER")
        print("   vercel env add EMAIL_HOST_PASSWORD")
        print("   vercel env add CLOUDINARY_URL")
        print("   vercel env add AFRICAS_TALKING_API_KEY")
        print("5. Re-run this script to validate: python scripts/validate_env.py")
    
    # Exit with appropriate code
    sys.exit(1 if errors else 0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Validate environment variables for Vercel deployment')
    parser.add_argument('--generate-secret-key', action='store_true', 
                       help='Generate a new Django secret key')
    
    args = parser.parse_args()
    
    if args.generate_secret_key:
        print("🔑 Generating new Django secret key...")
        secret_key = generate_secret_key()
        print(f"DJANGO_SECRET_KEY={secret_key}")
        print("\n💡 Copy this value to your .env file or Vercel environment variables")
        sys.exit(0)
    
    main()