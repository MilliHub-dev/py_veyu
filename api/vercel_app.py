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
    
    # Optimize database connections for serverless
    from django.db import connections
    
    def close_old_connections():
        """Close database connections to prevent connection pooling issues in serverless"""
        for conn in connections.all():
            conn.close()
    
    # Get WSGI application
    application = get_wsgi_application()
    
    # Wrap application with connection cleanup
    def serverless_application(environ, start_response):
        """WSGI application wrapper with serverless optimizations"""
        try:
            # Log request info
            method = environ.get('REQUEST_METHOD', 'UNKNOWN')
            path = environ.get('PATH_INFO', '/')
            logger.info(f"Processing {method} request to {path}")
            
            # Process request
            response = application(environ, start_response)
            
            # Clean up connections after request
            close_old_connections()
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            
            # Clean up connections on error
            close_old_connections()
            
            # Return 500 error response
            status = '500 Internal Server Error'
            headers = [('Content-Type', 'text/plain')]
            start_response(status, headers)
            return [b'Internal Server Error']
    
    # Export the wrapped application
    app = serverless_application
    
    logger.info("Django WSGI application initialized successfully for Vercel")
    
except ImportError as e:
    logger.error(f"Failed to import Django: {e}")
    raise
except Exception as e:
    logger.error(f"Failed to initialize Django application: {e}", exc_info=True)
    raise

# Health check endpoint for monitoring
def health_check(environ, start_response):
    """Simple health check endpoint"""
    if environ.get('PATH_INFO') == '/health':
        status = '200 OK'
        headers = [('Content-Type', 'application/json')]
        start_response(status, headers)
        return [b'{"status": "healthy", "service": "veyu-django"}']
    
    # Pass to main application
    return app(environ, start_response)

# Final application with health check - this is what Vercel will call
handler = health_check
