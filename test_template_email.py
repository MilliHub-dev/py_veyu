#!/usr/bin/env python
"""
Test email templates with the simple email system.
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

from utils.simple_mail import send_template_email

def main():
    print("📧 TEMPLATE EMAIL TEST")
    print("=" * 50)
    
    # Test 1: Welcome email template
    print("\n1. Testing welcome email template...")
    result = send_template_email(
        subject="Welcome to Veyu!",
        recipients=["ekeminieffiong22@gmail.com"],
        template_name="welcome_email.html",
        context={
            'user_name': 'John Doe',
            'app_name': 'Veyu',
        }
    )
    print("✅ Welcome template sent" if result else "❌ Welcome template failed")
    
    # Test 2: OTP email template
    print("\n2. Testing OTP email template...")
    result = send_template_email(
        subject="Your Verification Code",
        recipients=["ekeminieffiong22@gmail.com"],
        template_name="otp_email.html",
        context={
            'otp': '123456',
            'user_name': 'John Doe',
            'validity_minutes': 30,
        }
    )
    print("✅ OTP template sent" if result else "❌ OTP template failed")
    
    # Test 3: Password reset template
    print("\n3. Testing password reset template...")
    result = send_template_email(
        subject="Reset Your Password",
        recipients=["ekeminieffiong22@gmail.com"],
        template_name="password_reset_email.html",
        context={
            'user_name': 'John Doe',
            'reset_link': 'https://veyu.cc/reset-password/abc123',
        }
    )
    print("✅ Password reset template sent" if result else "❌ Password reset template failed")
    
    # Test 4: Email confirmation template
    print("\n4. Testing email confirmation template...")
    result = send_template_email(
        subject="Confirm Your Email",
        recipients=["ekeminieffiong22@gmail.com"],
        template_name="email-confirmation.html",
        context={
            'user_name': 'John Doe',
            'confirmation_link': 'https://veyu.cc/confirm-email/xyz789',
        }
    )
    print("✅ Email confirmation template sent" if result else "❌ Email confirmation template failed")
    
    print("\n🎉 Template testing complete!")
    print("Check your inbox at ekeminieffiong22@gmail.com")

if __name__ == "__main__":
    main()