#!/usr/bin/env python
"""
Test Gmail SMTP connectivity specifically.
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

import socket
import smtplib
import ssl
from django.conf import settings

def test_gmail_smtp():
    """Test Gmail SMTP with detailed diagnostics."""
    print("=== Gmail SMTP Connectivity Test ===")
    
    # Get settings
    host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
    port = getattr(settings, 'EMAIL_PORT', 587)
    username = getattr(settings, 'EMAIL_HOST_USER', '')
    password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
    use_tls = getattr(settings, 'EMAIL_USE_TLS', True)
    
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password) if password else 'NOT SET'}")
    print(f"Use TLS: {use_tls}")
    print()
    
    # Test 1: Basic connectivity
    print("1. Testing basic connectivity...")
    try:
        sock = socket.create_connection((host, port), timeout=10)
        sock.close()
        print("✓ Can connect to Gmail SMTP server")
    except Exception as e:
        print(f"✗ Cannot connect to Gmail SMTP server: {e}")
        return False
    
    # Test 2: SMTP handshake
    print("\n2. Testing SMTP handshake...")
    try:
        smtp = smtplib.SMTP(host, port, timeout=10)
        response = smtp.ehlo()
        print(f"✓ SMTP handshake successful: {response}")
        smtp.quit()
    except Exception as e:
        print(f"✗ SMTP handshake failed: {e}")
        return False
    
    # Test 3: TLS connection
    if use_tls:
        print("\n3. Testing TLS connection...")
        try:
            smtp = smtplib.SMTP(host, port, timeout=10)
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            print("✓ TLS connection successful")
            smtp.quit()
        except Exception as e:
            print(f"✗ TLS connection failed: {e}")
            return False
    
    # Test 4: Authentication
    if username and password:
        print("\n4. Testing authentication...")
        try:
            smtp = smtplib.SMTP(host, port, timeout=10)
            smtp.ehlo()
            if use_tls:
                smtp.starttls()
                smtp.ehlo()
            smtp.login(username, password)
            print("✓ Authentication successful")
            smtp.quit()
        except smtplib.SMTPAuthenticationError as e:
            print(f"✗ Authentication failed: {e}")
            print("  Possible issues:")
            print("  - Incorrect Gmail app password")
            print("  - 2FA not enabled on Gmail account")
            print("  - App password expired")
            return False
        except Exception as e:
            print(f"✗ Authentication error: {e}")
            return False
    else:
        print("\n4. Skipping authentication test (no credentials)")
    
    # Test 5: Send test email
    print("\n5. Testing email send...")
    try:
        smtp = smtplib.SMTP(host, port, timeout=10)
        smtp.ehlo()
        if use_tls:
            smtp.starttls()
            smtp.ehlo()
        if username and password:
            smtp.login(username, password)
        
        # Create test message
        from email.mime.text import MIMEText
        msg = MIMEText("This is a test email from Veyu SMTP test.")
        msg['Subject'] = "SMTP Test - Veyu"
        msg['From'] = username or 'test@veyu.cc'
        msg['To'] = 'test@example.com'
        
        # Send (but to a fake address so it doesn't actually deliver)
        smtp.send_message(msg)
        print("✓ Email send test successful")
        smtp.quit()
        
    except Exception as e:
        print(f"✗ Email send test failed: {e}")
        return False
    
    print("\n=== All tests passed! Gmail SMTP should work. ===")
    return True

def test_alternative_ports():
    """Test alternative SMTP ports."""
    print("\n=== Testing Alternative Ports ===")
    
    ports_to_test = [
        (587, "TLS"),
        (465, "SSL"),
        (25, "Plain (usually blocked)")
    ]
    
    for port, description in ports_to_test:
        print(f"\nTesting port {port} ({description})...")
        try:
            sock = socket.create_connection(('smtp.gmail.com', port), timeout=5)
            sock.close()
            print(f"✓ Port {port} is accessible")
        except Exception as e:
            print(f"✗ Port {port} blocked: {e}")

if __name__ == "__main__":
    success = test_gmail_smtp()
    
    if not success:
        test_alternative_ports()
        
        print("\n=== Troubleshooting Tips ===")
        print("1. Check Gmail app password:")
        print("   - Go to Google Account settings")
        print("   - Enable 2-factor authentication")
        print("   - Generate new app password")
        print("   - Use app password, not regular password")
        print()
        print("2. Check network/firewall:")
        print("   - SMTP ports might be blocked")
        print("   - Contact hosting provider")
        print("   - Try different ports (587, 465)")
        print()
        print("3. Alternative solutions:")
        print("   - Use Gmail API instead of SMTP")
        print("   - Use different email provider")
        print("   - Set up local mail relay")