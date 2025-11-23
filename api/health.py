"""
Simple health check endpoint for Vercel deployment diagnostics
"""

import os
import sys
import json
from pathlib import Path

def app(environ, start_response):
    """
    Minimal WSGI health check that doesn't require Django
    Useful for diagnosing deployment issues
    """
    
    path = environ.get('PATH_INFO', '/')
    
    if path == '/health' or path == '/api/health':
        # Basic health check
        status = '200 OK'
        headers = [('Content-Type', 'application/json')]
        
        health_data = {
            'status': 'healthy',
            'service': 'veyu-django',
            'environment': {
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'has_django_secret': bool(os.environ.get('DJANGO_SECRET_KEY')),
                'has_database_url': bool(os.environ.get('DATABASE_URL')),
                'has_cloudinary_url': bool(os.environ.get('CLOUDINARY_URL')),
                'has_email_config': bool(os.environ.get('EMAIL_HOST_USER')),
            }
        }
        
        start_response(status, headers)
        return [json.dumps(health_data, indent=2).encode()]
    
    elif path == '/api/health/django':
        # Django-specific health check
        try:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.vercel_settings')
            
            import django
            django.setup()
            
            from django.conf import settings
            from django.db import connection
            
            # Test database connection
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                db_status = 'connected'
            except Exception as e:
                db_status = f'error: {str(e)}'
            
            health_data = {
                'status': 'healthy',
                'django': {
                    'version': django.get_version(),
                    'debug': settings.DEBUG,
                    'allowed_hosts': settings.ALLOWED_HOSTS,
                    'database': db_status,
                    'static_root': str(settings.STATIC_ROOT),
                    'static_url': settings.STATIC_URL,
                }
            }
            
            status = '200 OK'
            headers = [('Content-Type', 'application/json')]
            start_response(status, headers)
            return [json.dumps(health_data, indent=2).encode()]
            
        except Exception as e:
            status = '500 Internal Server Error'
            headers = [('Content-Type', 'application/json')]
            
            error_data = {
                'status': 'error',
                'error': str(e),
                'error_type': type(e).__name__,
            }
            
            start_response(status, headers)
            return [json.dumps(error_data, indent=2).encode()]
    
    else:
        # Not a health check endpoint
        status = '404 Not Found'
        headers = [('Content-Type', 'text/plain')]
        start_response(status, headers)
        return [b'Health check endpoints: /health or /api/health/django']
