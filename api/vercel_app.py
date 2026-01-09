"""
Vercel WSGI Entry Point for Django Application
Simplified version with better error handling
"""

import os
import sys
import logging
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.vercel_settings')

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def app(environ, start_response):
    """Main WSGI application for Vercel"""
    
    # Get request info
    method = environ.get('REQUEST_METHOD', 'GET')
    path = environ.get('PATH_INFO', '/')
    
    logger.info(f"Request: {method} {path}")
    
    # Handle health check directly
    if path == '/health':
        status = '200 OK'
        headers = [('Content-Type', 'application/json')]
        start_response(status, headers)
        return [b'{"status": "healthy", "service": "veyu-api"}']
    
    # Handle root path directly
    if path == '/' or path == '':
        status = '200 OK'
        headers = [('Content-Type', 'application/json')]
        start_response(status, headers)
        return [b'{"message": "Veyu API is running", "docs": "/api/docs/"}']
    
    try:
        # Initialize Django only when needed
        import django
        from django.core.wsgi import get_wsgi_application
        
        # Setup Django
        django.setup()
        
        # Get Django WSGI app
        django_app = get_wsgi_application()
        
        # Process with Django
        return django_app(environ, start_response)
        
    except Exception as e:
        logger.error(f"Django error: {str(e)}")
        
        # Return error response
        status = '500 Internal Server Error'
        headers = [('Content-Type', 'application/json')]
        start_response(status, headers)
        error_msg = f'{{"error": "Server Error", "message": "{str(e)}"}}'
        return [error_msg.encode()]
