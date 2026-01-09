from http.server import BaseHTTPRequestHandler
import os
import sys
from pathlib import Path
import json

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.vercel_settings')

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        
        # Health check
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
            return
        
        # Root path
        if self.path == '/' or self.path == '':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'message': 'Veyu API is running',
                'docs': '/api/docs/'
            }).encode())
            return
        
        try:
            # Initialize Django
            import django
            django.setup()
            
            from django.test import RequestFactory
            from django.core.handlers.wsgi import WSGIHandler
            
            # Create Django request
            factory = RequestFactory()
            request = factory.get(self.path)
            
            # Process with Django
            wsgi_handler = WSGIHandler()
            response = wsgi_handler.get_response(request)
            
            self.send_response(response.status_code)
            for header, value in response.items():
                self.send_header(header, value)
            self.end_headers()
            
            if hasattr(response, 'content'):
                self.wfile.write(response.content)
            else:
                self.wfile.write(b'')
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'Server Error',
                'message': str(e)
            }).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        self.do_GET()  # For now, handle POST same as GET
