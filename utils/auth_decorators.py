"""
Authentication decorators for the Veyu application.
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
import logging
from utils.log_security import security_logger, get_request_metadata

# Set up security logging
django_security_logger = logging.getLogger('security')


def admin_required(view_func):
    """
    Decorator that requires user to be authenticated and have admin privileges.
    
    Admin privileges are determined by either:
    - is_staff = True
    - user_type = 'admin'
    
    For unauthenticated users: redirects to login page
    For non-admin users: returns 403 Forbidden response
    
    Works with both function-based views and class-based views.
    
    Requirements: 4.1, 4.2, 4.3, 4.4
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        # Handle both function-based views and class-based views
        if len(args) >= 1:
            # Check if first argument is a request object (function-based view)
            # or if it's a view instance (class-based view)
            first_arg = args[0]
            
            # For class-based views, the first argument is 'self' (view instance)
            # and the second argument is the request
            if hasattr(first_arg, 'request') or (len(args) >= 2 and hasattr(args[1], 'user')):
                # This is a class-based view - request is the second argument
                request = args[1] if len(args) >= 2 else first_arg.request
            elif hasattr(first_arg, 'user'):
                # This is a function-based view - request is the first argument
                request = first_arg
            else:
                # Fallback - assume it's a function-based view
                request = first_arg
        else:
            raise ValueError("admin_required decorator requires at least one argument")
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            # Log unauthenticated access attempt
            security_logger.log_invalid_request(
                user_email='anonymous',
                request_details=f"Unauthenticated access attempt to {request.path}",
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                additional_data=get_request_metadata(request)
            )
            
            django_security_logger.warning(
                f"Unauthenticated access attempt to {request.path} from IP {request.META.get('REMOTE_ADDR', 'unknown')}"
            )
            # Redirect to login page for unauthenticated users
            return redirect('admin:login')
        
        # Check if user has admin privileges
        user = request.user
        is_admin = user.is_staff or (hasattr(user, 'user_type') and user.user_type == 'admin')
        
        if not is_admin:
            # Log permission denied event
            additional_data = get_request_metadata(request)
            additional_data.update({
                'user_type': getattr(user, 'user_type', 'unknown'),
                'is_staff': user.is_staff
            })
            
            security_logger.log_permission_denied(
                user_email=user.email,
                log_file=request.path,
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                reason='insufficient_admin_privileges',
                additional_data=additional_data
            )
            
            django_security_logger.warning(
                f"Access denied for user {user.email} (user_type: {getattr(user, 'user_type', 'unknown')}, "
                f"is_staff: {user.is_staff}) to {request.path} from IP {request.META.get('REMOTE_ADDR', 'unknown')}"
            )
            # Return 403 for non-admin users
            return HttpResponseForbidden(
                "Access denied. Administrative privileges required to access this resource."
            )
        
        # Log successful access (only for Django logging, detailed logging is done in views)
        django_security_logger.info(
            f"Admin access granted to user {user.email} for {request.path} from IP {request.META.get('REMOTE_ADDR', 'unknown')}"
        )
        
        return view_func(*args, **kwargs)
    
    return wrapper