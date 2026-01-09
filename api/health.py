"""
Simple health check endpoint for Vercel
"""

def app(environ, start_response):
    """Simple health check WSGI application"""
    
    # Get the request path
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    if path == '/health' and method == 'GET':
        # Health check response
        status = '200 OK'
        headers = [
            ('Content-Type', 'application/json'),
            ('Access-Control-Allow-Origin', '*')
        ]
        start_response(status, headers)
        return [b'{"status": "healthy", "service": "veyu-api"}']
    
    # For any other path, return 404
    status = '404 Not Found'
    headers = [('Content-Type', 'text/plain')]
    start_response(status, headers)
    return [b'Health endpoint only']