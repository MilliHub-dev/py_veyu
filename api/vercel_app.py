import os
import sys
from pathlib import Path

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.vercel_settings')

# Initialize Django
import django
django.setup()

# Get Django WSGI application
from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
