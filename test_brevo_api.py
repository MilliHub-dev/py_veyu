#!/usr/bin/env python
"""
Test Brevo API email sending (fast and reliable).
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

from utils.brevo_api import send_email_via_brevo_api, send_template_email_via_api

def main():
    print("🚀 BREVO API EMAIL TEST (Fast & Reliable)")
    print("=" * 60)
    
    # Test 1: Simple API email
    print("\n1. Testing simple API email...")
    result = send_email_via_brevo_api(
        subject="Test Email via Brevo API",
        recipients=["ekeminieffiong22@gmail.com"],
        html_content="<h1>Hello!</h1><p>This email was sent via Brevo's HTTP API (not SMTP).</p>",
        text_content="Hello! This email was sent via Brevo's HTTP API."
    )
    
    if result['success']:
        print(f"✅ Simple email sent! Message ID: {result.get('message_id')}")
    else:
        print(f"❌ Simple email failed: {result.get('error')}")
    
    # Test 2: Template email via API
    print("\n2. Testing template email via API...")
    result = send_template_email_via_api(
        subject="Welcome to Veyu!",
        recipients=["ekeminieffiong22@gmail.com"],
        template_name="welcome_email.html",
        context={'user_name': 'Test User'}
    )
    
    if result:
        print("✅ Template email sent!")
    else:
        print("❌ Template email failed")
    
    # Test 3: Verification email via API
    print("\n3. Testing verification email via API...")
    result = send_template_email_via_api(
        subject="Verify Your Email - Veyu",
        recipients=["ekeminieffiong22@gmail.com"],
        template_name="verification_email.html",
        context={
            'name': 'Test User',
            'verification_code': '123456'
        }
    )
    
    if result:
        print("✅ Verification email sent!")
    else:
        print("❌ Verification email failed")
    
    print("\n" + "=" * 60)
    print("📬 Check your inbox at ekeminieffiong22@gmail.com")
    print("Emails sent via Brevo API (HTTP) - much faster than SMTP!")

if __name__ == "__main__":
    main()
