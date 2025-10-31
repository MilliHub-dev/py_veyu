import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    try:
        print("Testing email configuration...")
        print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
        print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        
        # Test sending an email
        send_mail(
            'Test Email from Veyu',
            'This is a test email from Veyu.',
            settings.DEFAULT_FROM_EMAIL,
            ['info.veyu@gmail.com'],  # Send to yourself for testing
            fail_silently=False,
        )
        print("Email sent successfully!")
        
        # If using file backend, show where emails are saved
        if settings.EMAIL_BACKEND == 'django.core.mail.backends.filebased.EmailBackend':
            email_file = os.path.join(settings.EMAIL_FILE_PATH, os.listdir(settings.EMAIL_FILE_PATH)[-1])
            print(f"Email saved to: {email_file}")
            
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Check your internet connection")
        print("2. Verify Gmail app password is correct")
        print("3. Check if Gmail's 'Less secure app access' is enabled")
        print("4. Check if your firewall is blocking the connection")
        print("5. Try using a different port (465 with SSL or 587 with TLS)")

if __name__ == "__main__":
    test_email()
