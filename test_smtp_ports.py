#!/usr/bin/env python
"""
Test SMTP port connectivity for different email providers.
"""
import socket
import sys
from datetime import datetime

def test_smtp_port(host, port, timeout=10):
    """Test if a specific SMTP port is reachable."""
    try:
        start_time = datetime.now()
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        return True, f"✓ Connected in {duration:.2f}s"
    except socket.timeout:
        return False, f"✗ Timeout after {timeout}s"
    except socket.gaierror as e:
        return False, f"✗ DNS resolution failed: {e}"
    except ConnectionRefusedError:
        return False, f"✗ Connection refused (port blocked)"
    except OSError as e:
        if e.errno == 101:
            return False, f"✗ Network unreachable"
        else:
            return False, f"✗ OS Error: {e}"
    except Exception as e:
        return False, f"✗ Error: {e}"

def main():
    print("=== SMTP Port Connectivity Test ===")
    print(f"Test started at: {datetime.now()}")
    print()
    
    # Test different SMTP providers and ports
    smtp_tests = [
        # Gmail
        ("Gmail SMTP (TLS)", "smtp.gmail.com", 587),
        ("Gmail SMTP (SSL)", "smtp.gmail.com", 465),
        ("Gmail SMTP (Plain)", "smtp.gmail.com", 25),
        
        # Alternative providers
        ("Outlook/Hotmail", "smtp-mail.outlook.com", 587),
        ("Yahoo", "smtp.mail.yahoo.com", 587),
        ("SendGrid", "smtp.sendgrid.net", 587),
        
        # Generic test
        ("Google DNS", "8.8.8.8", 53),  # Should work if internet is available
    ]
    
    results = []
    
    for name, host, port in smtp_tests:
        print(f"Testing {name} ({host}:{port})...")
        success, message = test_smtp_port(host, port)
        results.append((name, host, port, success, message))
        print(f"  {message}")
        print()
    
    # Summary
    print("=== Summary ===")
    working_smtp = []
    blocked_smtp = []
    
    for name, host, port, success, message in results:
        if "DNS" in name:  # Skip DNS test in summary
            continue
            
        if success:
            working_smtp.append(f"{name} ({host}:{port})")
        else:
            blocked_smtp.append(f"{name} ({host}:{port}) - {message}")
    
    if working_smtp:
        print("✓ Working SMTP servers:")
        for smtp in working_smtp:
            print(f"  - {smtp}")
    else:
        print("✗ No SMTP servers are reachable")
    
    if blocked_smtp:
        print("\n✗ Blocked/Failed SMTP servers:")
        for smtp in blocked_smtp:
            print(f"  - {smtp}")
    
    # Recommendations
    print("\n=== Recommendations ===")
    if not working_smtp:
        print("• All SMTP ports appear to be blocked")
        print("• Contact your hosting provider about SMTP access")
        print("• Consider using an HTTP-based email API instead of SMTP")
        print("• Alternative: Use a local mail relay or email service")
    elif len(working_smtp) < len(blocked_smtp):
        print("• Some SMTP ports are blocked, but others work")
        print("• Use the working SMTP servers for email delivery")
    else:
        print("• SMTP connectivity looks good!")
        print("• The issue might be with authentication or configuration")

if __name__ == "__main__":
    main()