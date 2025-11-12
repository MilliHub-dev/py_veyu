#!/usr/bin/env python
"""
Comprehensive email diagnostic script for server troubleshooting.
"""
import os
import sys
import django
import socket
import smtplib
import ssl
import time
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from django.core.mail import send_mail, get_connection
from django.conf import settings
from utils.mail import test_email_connection

def test_network_connectivity():
    """Test basic network connectivity to Brevo servers."""
    print("=== Network Connectivity Test ===")
    
    host = settings.EMAIL_HOST
    port = settings.EMAIL_PORT
    
    print(f"Testing connection to {host}:{port}")
    
    try:
        # Test basic socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print("✅ Network connection successful")
            return True
        else:
            print(f"❌ Network connection failed (error code: {result})")
            return False
    except Exception as e:
        print(f"❌ Network test error: {e}")
        return False

def test_smtp_connection_detailed():
    """Test SMTP connection with detailed logging."""
    print("\n=== SMTP Connection Test ===")
    
    host = settings.EMAIL_HOST
    port = settings.EMAIL_PORT
    username = settings.EMAIL_HOST_USER
    password = settings.EMAIL_HOST_PASSWORD
    use_tls = settings.EMAIL_USE_TLS
    
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Username: {username}")
    print(f"Use TLS: {use_tls}")
    print(f"Password: {'*' * len(password) if password else 'Not set'}")
    
    try:
        # Create SSL context
        context = ssl.create_default_context()
        
        # For Brevo, we might need to be more lenient
        if 'brevo' in host.lower():
            print("Configuring SSL context for Brevo...")
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        
        print("Connecting to SMTP server...")
        smtp = smtplib.SMTP(host, port, timeout=30)
        
        # Enable debug output
        smtp.set_debuglevel(1)
        
        print("Starting TLS...")
        if use_tls:
            smtp.starttls(context=context)
        
        print("Authenticating...")
        if username and password:
            smtp.login(username, password)
            print("✅ Authentication successful")
        
        smtp.quit()
        print("✅ SMTP connection test successful")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        return False
    except smtplib.SMTPConnectError as e:
        print(f"❌ Connection failed: {e}")
        return False
    except socket.timeout:
        print("❌ Connection timeout")
        return False
    except Exception as e:
        print(f"❌ SMTP error: {e}")
        return False

def test_django_email_backend():
    """Test Django's email backend."""
    print("\n=== Django Email Backend Test ===")
    
    try:
        connection = get_connection()
        connection.open()
        print("✅ Django email backend connection opened successfully")
        connection.close()
        print("✅ Django email backend connection closed successfully")
        return True
    except Exception as e:
        print(f"❌ Django email backend error: {e}")
        return False

def test_actual_email_send():
    """Test sending an actual email."""
    print("\n=== Actual Email Send Test ===")
    
    try:
        print("Sending test email...")
        
        result = send_mail(
            subject='Server Email Test - Veyu Platform',
            message='This is a test email sent from the server to verify email functionality.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['ekeminieffiong22@gmail.com'],
            fail_silently=False
        )
        
        if result == 1:
            print("✅ Email sent successfully!")
            return True
        else:
            print("❌ Email failed to send (no exception but result != 1)")
            return False
            
    except Exception as e:
        print(f"❌ Email send error: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def test_utils_mail_function():
    """Test the custom utils.mail function."""
    print("\n=== Utils Mail Function Test ===")
    
    try:
        from utils.mail import send_email
        
        result = send_email(
            subject='Utils Mail Test - Veyu Platform',
            recipients=['ekeminieffiong22@gmail.com'],
            message='This is a test email sent using the custom utils.mail function.',
            fail_silently=False
        )
        
        if result:
            print("✅ Utils mail function successful!")
            return True
        else:
            print("❌ Utils mail function failed")
            return False
            
    except Exception as e:
        print(f"❌ Utils mail function error: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def check_server_environment():
    """Check server environment for potential issues."""
    print("\n=== Server Environment Check ===")
    
    # Check if we're in DEBUG mode
    print(f"DEBUG mode: {settings.DEBUG}")
    
    # Check email backend
    print(f"Email backend: {settings.EMAIL_BACKEND}")
    
    # Check if running on server vs local
    hostname = socket.gethostname()
    print(f"Hostname: {hostname}")
    
    # Check environment variables
    env_vars = ['EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD']
    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        if 'PASSWORD' in var and value != 'Not set':
            value = '*' * len(value)
        print(f"{var}: {value}")
    
    # Check for firewall/network restrictions
    print("\nChecking common email ports...")
    ports_to_check = [25, 465, 587, 2525]
    for port in ports_to_check:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((settings.EMAIL_HOST, port))
            sock.close()
            status = "✅ Open" if result == 0 else "❌ Blocked/Closed"
            print(f"Port {port}: {status}")
        except Exception as e:
            print(f"Port {port}: ❌ Error - {e}")

def main():
    """Run all diagnostic tests."""
    print("🔍 EMAIL DIAGNOSTIC TOOL - VEYU PLATFORM")
    print("=" * 50)
    
    tests = [
        ("Network Connectivity", test_network_connectivity),
        ("SMTP Connection", test_smtp_connection_detailed),
        ("Django Email Backend", test_django_email_backend),
        ("Actual Email Send", test_actual_email_send),
        ("Utils Mail Function", test_utils_mail_function),
    ]
    
    # Run environment check first
    check_server_environment()
    
    # Run all tests
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All tests passed! Email should be working.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        print("\nCommon server issues:")
        print("- Firewall blocking SMTP ports (587, 465, 25)")
        print("- Network restrictions on outbound connections")
        print("- Incorrect credentials or authentication method")
        print("- SSL/TLS certificate issues")
        print("- Server IP blocked by email provider")

if __name__ == "__main__":
    main()