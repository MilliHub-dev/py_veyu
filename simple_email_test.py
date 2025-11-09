#!/usr/bin/env python
"""
Simple Gmail SMTP test - no custom backends, just Django's built-in SMTP.
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

from django.core.mail import send_mail
from django.conf import settings

def test_simple_email():
    print("=== Simple Gmail SMTP Test ===")
    print(f"Backend: {settings.EMAIL_BACKEND}")
    print(f"Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
    print(f"User: {settings.EMAIL_HOST_USER}")
    print(f"TLS: {settings.EMAIL_USE_TLS}")
    print()
    
    try:
        print("Sending test email...")
        
        result = send_mail(
            subject='Simple Test Email - Veyu',
            message='This is a simple test email sent directly via Django SMTP backend.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['ekeminieffiong22@gmail.com'],
            fail_silently=False
        )
        
        if result == 1:
            print("✅ Email sent successfully!")
            print("Check your inbox at ekeminieffiong22@gmail.com")
        else:
            print("❌ Email failed to send")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    test_simple_email()