import os
import sys
import django
from django.conf import settings
from django.core.mail import send_mail

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

# Test email configuration
print("Testing ZeptoMail configuration...")
print(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
print(f"ZEPTOMAIL_API_KEY: {'Set' if hasattr(settings, 'ZEPTOMAIL_API_KEY') and settings.ZEPTOMAIL_API_KEY else 'Not set'}")
print(f"ZEPTOMAIL_SENDER_EMAIL: {getattr(settings, 'ZEPTOMAIL_SENDER_EMAIL', 'Not set')}")
print(f"ZEPTOMAIL_SENDER_NAME: {getattr(settings, 'ZEPTOMAIL_SENDER_NAME', 'Not set')}")

# Send test email
try:
    print("\nSending test email...")
    result = send_mail(
        'Test Email from Veyu',
        'This is a test email from Veyu using ZeptoMail.',
        settings.ZEPTOMAIL_SENDER_EMAIL,
        ['ekeminieffiong22@gmail.com'],
        fail_silently=False,
        html_message='<h1>Test Email</h1><p>This is a test email from Veyu using ZeptoMail.</p>'
    )
    print(f"Email sent successfully! Result: {result}")
except Exception as e:
    print(f"Error sending email: {str(e)}")
    
    # Print detailed error information
    import traceback
    traceback.print_exc()

print("\nTest completed.")
