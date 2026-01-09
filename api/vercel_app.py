import os
import sys
from pathlib import Path
import json

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.vercel_settings')

def handler(request):
    """Vercel function handler"""
    
    # Get request path and method
    path = getattr(request, 'path', '/')
    method = getattr(request, 'method', 'GET')
    
    # Handle health check
    if path == '/health':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'status': 'ok', 'service': 'veyu-api'})
        }
    
    # Handle root path
    if path == '/' or path == '':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Veyu API is running',
                'docs': '/api/docs/',
                'health': '/health'
            })
        }
    
    try:
        # Initialize Django
        import django
        django.setup()
        
        from django.test import RequestFactory
        from django.core.handlers.wsgi import WSGIHandler
        
        # Create Django request
        factory = RequestFactory()
        
        if method.upper() == 'POST':
            django_request = factory.post(path)
        else:
            django_request = factory.get(path)
        
        # Process with Django
        wsgi_handler = WSGIHandler()
        response = wsgi_handler.get_response(django_request)
        
        # Convert Django response to Vercel format
        headers = {}
        for header, value in response.items():
            headers[header] = value
        
        return {
            'statusCode': response.status_code,
            'headers': headers,
            'body': response.content.decode('utf-8') if response.content else ''
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Server Error',
                'message': str(e)
            })
        }
