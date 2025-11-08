#!/usr/bin/env python
"""
Quick test script for email fixes.
Run this to test if the email timeout issues are resolved.
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from utils.mail import test_email_connection, send_email, validate_email_configuration
from django.conf import settings

def main():
    print("=== Email System Fix Test ===\n")
    
    # 1. Show current settings
    print("1. Current Email Settings:")
    print(f"   Backend: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
    print(f"   Host: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
    print(f"   Port: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
    print(f"   Timeout: {getattr(settings, 'EMAIL_TIMEOUT', 'Not set')}s")
    print(f"   Max Retries: {getattr(settings, 'EMAIL_MAX_RETRIES', 'Not set')}")
    print(f"   Fallback Enabled: {getattr(settings, 'EMAIL_FALLBACK_ENABLED', 'Not set')}")
    print()
    
    # 2. Validate configuration
    print("2. Validating Configuration:")
    try:
        validation = validate_email_configuration()
        if validation['valid']:
            print("   ✓ Configuration is valid")
        else:
            print("   ✗ Configuration has errors:")
            for error in validation['errors']:
                print(f"     - {error}")
        
        if validation['warnings']:
            print("   Warnings:")
            for warning in validation['warnings']:
                print(f"     - {warning}")
    except Exception as e:
        print(f"   ✗ Validation failed: {str(e)}")
    print()
    
    # 3. Test connection
    print("3. Testing SMTP Connection:")
    try:
        result = test_email_connection()
        if result['success']:
            print(f"   ✓ {result['message']}")
        else:
            print(f"   ✗ Connection failed: {result['error']}")
            
            # Suggest fixes
            if 'timeout' in str(result['error']).lower():
                print("   💡 Suggestion: Network connectivity issue or SMTP server is slow")
                print("      - Check if EMAIL_HOST is correct")
                print("      - Try reducing EMAIL_TIMEOUT further")
                print("      - Check firewall/network settings")
            elif 'authentication' in str(result['error']).lower():
                print("   💡 Suggestion: Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD")
    except Exception as e:
        print(f"   ✗ Connection test failed: {str(e)}")
    print()
    
    # 4. Test email sending (optional)
    test_email = input("Enter email address to send test email (or press Enter to skip): ").strip()
    if test_email:
        print(f"\n4. Sending Test Email to {test_email}:")
        try:
            success = send_email(
                subject='Email Fix Test - Veyu',
                recipients=[test_email],
                message='This is a test email to verify the timeout fixes are working correctly.',
                fail_silently=False
            )
            
            if success:
                print("   ✓ Test email sent successfully!")
            else:
                print("   ✗ Test email failed to send")
                
        except Exception as e:
            print(f"   ✗ Test email failed: {str(e)}")
    
    print("\n=== Test Complete ===")
    print("\nIf you're still experiencing issues:")
    print("1. Check your network connectivity")
    print("2. Verify SendGrid API key is correct")
    print("3. Try using console backend for development: EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend")
    print("4. Run: python manage.py test_email --help for more options")

if __name__ == '__main__':
    main()