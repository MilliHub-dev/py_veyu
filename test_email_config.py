import os
import sys
import django
from django.conf import settings

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

# Now we can import Django settings
from django.conf import settings

print("\n=== Email Configuration ===")
print(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
print(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
print(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
print(f"EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}")
print(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}")
print(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
print(f"SERVER_EMAIL: {getattr(settings, 'SERVER_EMAIL', 'Not set')}")
print("\n=== Environment Variables ===")
print(f"EMAIL_HOST_USER in env: {os.getenv('EMAIL_HOST_USER', 'Not set')}")
print(f"EMAIL_HOST_PASSWORD in env: {'Set' if os.getenv('EMAIL_HOST_PASSWORD') else 'Not set'}")
print(f"DEFAULT_FROM_EMAIL in env: {os.getenv('DEFAULT_FROM_EMAIL', 'Not set')}")

# Test SMTP connection
try:
    import smtplib
    print("\n=== Testing SMTP Connection ===")
    with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10) as server:
        server.starttls()
        print("Connected to SMTP server")
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        print("Successfully authenticated with SMTP server")
except Exception as e:
    print(f"\n=== SMTP Connection Error ===")
    print(f"Error: {str(e)}")
    print("\nTroubleshooting Tips:")
    print("1. Check your internet connection")
    print("2. Verify your Gmail credentials")
    print("3. Make sure 'Less secure app access' is enabled in your Google Account")
    print("   or use an App Password if you have 2FA enabled")
    print("4. Check if your firewall or antivirus is blocking the connection")
    print("5. Try using a different port (465 with SSL or 587 with TLS)")
