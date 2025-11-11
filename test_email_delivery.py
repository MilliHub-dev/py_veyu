"""
Test email delivery with current configuration
Run this script to diagnose email issues:
python manage.py shell < test_email_delivery.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
import smtplib
import ssl

print("=" * 60)
print("EMAIL CONFIGURATION TEST")
print("=" * 60)

# Print current configuration
print(f"\nEmail Backend: {settings.EMAIL_BACKEND}")
print(f"Email Host: {settings.EMAIL_HOST}")
print(f"Email Port: {settings.EMAIL_PORT}")
print(f"Email Use TLS: {settings.EMAIL_USE_TLS}")
print(f"Email Host User: {settings.EMAIL_HOST_USER}")
print(f"Email Host Password: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
print(f"Default From Email: {settings.DEFAULT_FROM_EMAIL}")

# Test SMTP connection
print("\n" + "=" * 60)
print("TESTING SMTP CONNECTION")
print("=" * 60)

try:
    context = ssl.create_default_context()
    with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10) as server:
        server.starttls(context=context)
        print("✓ TLS connection established")
        
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        print("✓ Authentication successful")
        
        print("\n✓ SMTP connection test PASSED")
        
except smtplib.SMTPAuthenticationError as e:
    print(f"\n✗ Authentication failed: {e}")
    print("\nPossible solutions:")
    print("1. Generate a new Gmail App Password at: https://myaccount.google.com/apppasswords")
    print("2. Ensure 2-Step Verification is enabled on the Gmail account")
    print("3. Update EMAIL_HOST_PASSWORD in settings.py with the new app password")
    
except Exception as e:
    print(f"\n✗ Connection failed: {e}")
    print("\nPossible solutions:")
    print("1. Check your internet connection")
    print("2. Verify EMAIL_HOST and EMAIL_PORT settings")
    print("3. Check if Gmail SMTP is accessible from your network")

# Test sending email
print("\n" + "=" * 60)
print("TESTING EMAIL SENDING")
print("=" * 60)

try:
    send_mail(
        subject='Test Email from Veyu',
        message='This is a test email to verify email configuration.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['test@example.com'],  # Change this to your email
        fail_silently=False,
    )
    print("✓ Email sent successfully")
    
except Exception as e:
    print(f"✗ Email sending failed: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
