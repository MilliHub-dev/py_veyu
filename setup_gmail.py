#!/usr/bin/env python
"""
Interactive script to help set up Gmail SMTP configuration.
"""
import os
import sys
from pathlib import Path

def main():
    print("=== Gmail SMTP Setup for Veyu ===\n")
    
    print("This script will help you configure Gmail SMTP for email delivery.")
    print("You'll need:")
    print("1. A Gmail account")
    print("2. Two-factor authentication enabled")
    print("3. A Gmail App Password (we'll help you create one)\n")
    
    # Check if user has 2FA enabled
    has_2fa = input("Do you have 2-factor authentication enabled on your Gmail account? (y/n): ").lower().strip()
    
    if has_2fa != 'y':
        print("\n❌ You need to enable 2-factor authentication first!")
        print("1. Go to: https://myaccount.google.com/security")
        print("2. Under 'Signing in to Google', click '2-Step Verification'")
        print("3. Follow the setup process")
        print("4. Come back and run this script again")
        return
    
    print("\n✅ Great! Now let's set up your App Password.")
    print("\nSteps to create a Gmail App Password:")
    print("1. Go to: https://myaccount.google.com/security")
    print("2. Under 'Signing in to Google', click 'App passwords'")
    print("3. Select 'Mail' as the app")
    print("4. Select 'Other (Custom name)' as the device")
    print("5. Enter 'Veyu Platform' as the custom name")
    print("6. Click 'Generate'")
    print("7. Copy the 16-character password (format: abcd efgh ijkl mnop)")
    
    input("\nPress Enter when you have your App Password ready...")
    
    # Get user inputs
    gmail_address = input("\nEnter your Gmail address: ").strip()
    app_password = input("Enter your 16-character App Password (spaces will be removed): ").strip().replace(' ', '')
    
    # Validate inputs
    if not gmail_address or '@gmail.com' not in gmail_address:
        print("❌ Please enter a valid Gmail address")
        return
    
    if len(app_password) != 16:
        print("❌ App Password should be exactly 16 characters (without spaces)")
        return
    
    # Update .env file
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found. Please make sure you're in the project root directory.")
        return
    
    # Read current .env content
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update email configuration lines
    updated_lines = []
    email_configs = {
        'EMAIL_HOST': 'smtp.gmail.com',
        'EMAIL_PORT': '587',
        'EMAIL_USE_TLS': 'True',
        'EMAIL_USE_SSL': 'False',
        'EMAIL_HOST_USER': gmail_address,
        'EMAIL_HOST_PASSWORD': app_password,
        'DEFAULT_FROM_EMAIL': gmail_address,
        'SERVER_EMAIL': gmail_address,
        'EMAIL_SSL_VERIFY': 'True'
    }
    
    updated_configs = set()
    
    for line in lines:
        line_updated = False
        for key, value in email_configs.items():
            if line.startswith(f'{key}='):
                updated_lines.append(f'{key}={value}\n')
                updated_configs.add(key)
                line_updated = True
                break
        
        if not line_updated:
            updated_lines.append(line)
    
    # Add any missing configurations
    for key, value in email_configs.items():
        if key not in updated_configs:
            updated_lines.append(f'{key}={value}\n')
    
    # Write updated .env file
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)
    
    print(f"\n✅ Gmail configuration updated successfully!")
    print(f"   Email: {gmail_address}")
    print(f"   Host: smtp.gmail.com:587")
    print(f"   SSL Verify: Enabled")
    
    # Test the configuration
    print("\n🧪 Testing the configuration...")
    
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
        django.setup()
        
        from utils.mail import test_email_connection, validate_email_configuration
        
        # Validate configuration
        config_result = validate_email_configuration()
        if config_result['valid']:
            print("✅ Configuration is valid")
        else:
            print("❌ Configuration issues:")
            for error in config_result['errors']:
                print(f"   - {error}")
        
        # Test connection
        connection_result = test_email_connection()
        if connection_result['success']:
            print(f"✅ SMTP connection successful ({connection_result.get('connection_time', 0):.2f}s)")
        else:
            print(f"❌ SMTP connection failed: {connection_result.get('error', 'Unknown error')}")
            return
        
        # Offer to send test email
        send_test = input("\nWould you like to send a test email? (y/n): ").lower().strip()
        if send_test == 'y':
            test_email = input("Enter email address to send test to: ").strip()
            if test_email:
                from utils.mail import send_email
                
                success = send_email(
                    subject="Gmail SMTP Test - Veyu Platform",
                    recipients=[test_email],
                    message=f"""
Hello!

This is a test email from the Veyu platform using Gmail SMTP.

Configuration:
- From: {gmail_address}
- Host: smtp.gmail.com:587
- SSL Verification: Enabled

If you received this email, Gmail SMTP is working correctly!

Best regards,
Veyu Team
                    """.strip()
                )
                
                if success:
                    print("✅ Test email sent successfully!")
                else:
                    print("❌ Test email failed to send")
        
        print("\n🎉 Gmail SMTP setup complete!")
        print("\nYou can now use the following commands:")
        print("- python manage.py test_email --check-only  # Test configuration")
        print("- python manage.py test_email --to email@example.com  # Send test email")
        
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")
        print("Please run: python manage.py test_email --check-only")

if __name__ == "__main__":
    main()