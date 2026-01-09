"""
Utility views for the application
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'veyu-api',
        'version': '1.0.0'
    })

@csrf_exempt  
@require_http_methods(["GET"])
def root_handler(request):
    """Root path handler"""
    return JsonResponse({
        'message': 'Veyu API is running',
        'docs': '/api/docs/',
        'health': '/health',
        'version': '1.0.0'
    })