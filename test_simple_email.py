#!/usr/bin/env python
"""
Simple email test script using the new straightforward email system.
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

from utils.simple_mail import (
    send_simple_email,
    send_verification_email,
    send_welcome_email,
    test_email_connection
)
from django.conf import settings

def main():
    print("🚀 SIMPLE EMAIL TEST - VEYU PLATFORM")
    print("=" * 50)
    
    # Show current settings
    print(f"Email Backend: {settings.EMAIL_BACKEND}")
    print(f"SMTP Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
    print(f"From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"Use TLS: {settings.EMAIL_USE_TLS}")
    print()
    
    # Test connection
    print("1. Testing email connection...")
    connection_result = test_email_connection()
    if connection_result['success']:
        print("✅ Connection test passed")
    else:
        print(f"❌ Connection test failed: {connection_result['message']}")
        return
    
    print()
    
    # Test simple email
    print("2. Testing simple email...")
    result = send_simple_email(
        subject="Simple Test Email - Veyu",
        recipients=["ekeminieffiong22@gmail.com"],
        message="This is a simple test email from the new straightforward email system."
    )
    
    if result:
        print("✅ Simple email sent successfully")
    else:
        print("❌ Simple email failed")
    
    print()
    
    # Test verification email
    print("3. Testing verification email...")
    result = send_verification_email(
        email="ekeminieffiong22@gmail.com",
        verification_code="123456",
        user_name="Test User"
    )
    
    if result:
        print("✅ Verification email sent successfully")
    else:
        print("❌ Verification email failed")
    
    print()
    
    # Test welcome email
    print("4. Testing welcome email...")
    result = send_welcome_email(
        email="ekeminieffiong22@gmail.com",
        user_name="Test User"
    )
    
    if result:
        print("✅ Welcome email sent successfully")
    else:
        print("❌ Welcome email failed")
    
    print()
    print("🎉 Email testing complete!")
    print("Check your inbox at ekeminieffiong22@gmail.com")

if __name__ == "__main__":
    main()