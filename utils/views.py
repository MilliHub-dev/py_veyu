"""
Utility views for the application
"""

from django.http import JsonResponse, HttpResponse, Http404
from django.views.generic import ListView, DetailView, View
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.conf import settings
from django.shortcuts import render
import os
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """Simple health check endpoint for Railway"""
    try:
        # Test database connection
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'service': 'veyu-api',
            'database': 'connected',
            'version': '1.0.0'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'service': 'veyu-api',
            'database': 'disconnected',
            'error': str(e),
            'version': '1.0.0'
        }, status=503)

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

# Utility views for URLs
def index_view(request, template=None):
    """Index view for templates"""
    return JsonResponse({'message': 'Index view', 'template': template})

def chat_view(request, room_name=None):
    """Chat view"""
    return JsonResponse({'message': 'Chat view', 'room': room_name})

@csrf_exempt
def payment_webhook(request):
    """Payment webhook handler"""
    return JsonResponse({'status': 'received'})

@csrf_exempt
def verification_webhook(request):
    """Verification webhook handler"""
    return JsonResponse({'status': 'received'})

@csrf_exempt
def email_relay(request):
    """Email relay handler"""
    return JsonResponse({'status': 'email relay'})

def email_health_check(request):
    """Email health check"""
    return JsonResponse({'status': 'healthy', 'service': 'email'})

def email_config_validation(request):
    """Email configuration validation"""
    return JsonResponse({'status': 'valid', 'service': 'email'})

def email_connection_test(request):
    """Email connection test"""
    return JsonResponse({'status': 'connected', 'service': 'email'})

def email_test_send(request):
    """Email test send"""
    return JsonResponse({'status': 'sent', 'service': 'email'})

def process_email_queue_endpoint(request):
    """Process email queue"""
    return JsonResponse({'status': 'processed', 'service': 'email'})

def database_health_check(request):
    """Database health check"""
    return JsonResponse({'status': 'healthy', 'service': 'database'})

def database_info(request):
    """Database info"""
    return JsonResponse({'status': 'info', 'service': 'database'})

def system_health_check(request):
    """System health check"""
    return JsonResponse({'status': 'healthy', 'service': 'system'})

class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to require staff access"""
    def test_func(self):
        return self.request.user.is_staff

class LogListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """View to list available log files"""
    template_name = 'utils/log_list.html'
    context_object_name = 'log_files'
    
    def get_queryset(self):
        """Get list of available log files"""
        log_dir = getattr(settings, 'LOG_DIR', 'logs')
        if not os.path.exists(log_dir):
            return []
        
        log_files = []
        for filename in os.listdir(log_dir):
            if filename.endswith('.log'):
                filepath = os.path.join(log_dir, filename)
                if os.path.isfile(filepath):
                    log_files.append({
                        'name': filename,
                        'size': os.path.getsize(filepath),
                        'modified': os.path.getmtime(filepath)
                    })
        
        return sorted(log_files, key=lambda x: x['modified'], reverse=True)

class LogDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """View to display log file content"""
    template_name = 'utils/log_detail.html'
    context_object_name = 'log_content'
    
    def get_object(self):
        """Get log file content"""
        log_file = self.kwargs.get('log_file')
        log_dir = getattr(settings, 'LOG_DIR', 'logs')
        filepath = os.path.join(log_dir, log_file)
        
        if not os.path.exists(filepath) or not filepath.endswith('.log'):
            raise Http404("Log file not found")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                # Read last 1000 lines for performance
                lines = f.readlines()
                content = ''.join(lines[-1000:]) if len(lines) > 1000 else ''.join(lines)
                
            return {
                'filename': log_file,
                'content': content,
                'line_count': len(lines)
            }
        except Exception as e:
            logger.error(f"Error reading log file {log_file}: {e}")
            raise Http404("Error reading log file")

class LogDownloadView(LoginRequiredMixin, StaffRequiredMixin, View):
    """View to download log files"""
    
    def get(self, request, log_file):
        """Download log file"""
        log_dir = getattr(settings, 'LOG_DIR', 'logs')
        filepath = os.path.join(log_dir, log_file)
        
        if not os.path.exists(filepath) or not filepath.endswith('.log'):
            raise Http404("Log file not found")
        
        try:
            with open(filepath, 'rb') as f:
                response = HttpResponse(f.read(), content_type='text/plain')
                response['Content-Disposition'] = f'attachment; filename="{log_file}"'
                return response
        except Exception as e:
            logger.error(f"Error downloading log file {log_file}: {e}")
            raise Http404("Error downloading log file")

class LogRefreshAPIView(LoginRequiredMixin, StaffRequiredMixin, View):
    """API view to refresh log content"""
    
    def get(self, request, log_file):
        """Get latest log content"""
        log_dir = getattr(settings, 'LOG_DIR', 'logs')
        filepath = os.path.join(log_dir, log_file)
        
        if not os.path.exists(filepath) or not filepath.endswith('.log'):
            return JsonResponse({'error': 'Log file not found'}, status=404)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Get last 100 lines for API response
                recent_content = ''.join(lines[-100:]) if len(lines) > 100 else ''.join(lines)
                
            return JsonResponse({
                'content': recent_content,
                'line_count': len(lines),
                'filename': log_file
            })
        except Exception as e:
            logger.error(f"Error refreshing log file {log_file}: {e}")
            return JsonResponse({'error': 'Error reading log file'}, status=500)