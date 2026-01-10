"""
WSGI config for veyu project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.railway_settings')

try:
    from django.core.wsgi import get_wsgi_application
    logger.info("Initializing Django WSGI application...")
    
    application = get_wsgi_application()
    logger.info("Django WSGI application initialized successfully")
    
except Exception as e:
    logger.error(f"Failed to initialize Django WSGI application: {e}")
    raise