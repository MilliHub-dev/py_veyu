"""
Vercel WSGI Entry Point for Django Application
Optimized for serverless deployment with proper error handling and logging.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project directory to Python path (parent of api directory)
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings module for Vercel
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.vercel_settings')

# Configure logging for serverless environment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

try:
    # Initialize Django
    import django
    from django.conf import settings
    from django.core.wsgi import get_wsgi_application
    
    # Setup Django
    django.setup()
    
    # Get WSGI application
    django_app = get_wsgi_application()
    
    logger.info("Django WSGI application initialized successfully for Vercel")
    
    # Export for Vercel - this is the main entry point
    def app(environ, start_response):
        """Main WSGI application for Vercel"""
        try:
            # Log request details for debugging
            method = environ.get('REQUEST_METHOD', 'UNKNOWN')
            path = environ.get('PATH_INFO', '/')
            query = environ.get('QUERY_STRING', '')
            logger.info(f"Vercel request: {method} {path}?{query}")
            
            return django_app(environ, start_response)
        except Exception as e:
            logger.error(f"Error in WSGI app: {str(e)}", exc_info=True)
            status = '500 Internal Server Error'
            headers = [('Content-Type', 'application/json')]
            start_response(status, headers)
            return [f'{{"error": "Application Error", "message": "{str(e)}"}}'.encode()]
    
except Exception as e:
    logger.error(f"Failed to initialize Django: {e}", exc_info=True)
    
    # Fallback error handler
    def app(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-Type', 'text/plain')]
        start_response(status, headers)
        return [f'Django Initialization Error: {str(e)}'.encode()]
