import logging
import uuid
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.db import DatabaseError as DjangoDatabaseError
from accounts.models import Mechanic, Dealer, Customer, Account
from bookings import define_request
from .exceptions import VeyuException, APIError, ErrorCodes
from .error_handlers import log_error, get_request_context, ErrorResponseFormatter

# Configure logger for middleware
logger = logging.getLogger('veyu.middleware')

class UserTypeMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.customer = None
        request.mechanic = None
        request.dealer = None

        define_request(request)

        if request.user.is_authenticated:
            try:
                if request.user.user_type == 'customer':
                    request.customer = Customer.objects.get(user=request.user)
                elif request.user.user_type == 'dealer':
                    request.dealer = Dealer.objects.get(user=request.user)
                elif request.user.user_type == 'mechanic':
                    request.mechanic = Mechanic.objects.get(user=request.user)
            except:
                pass


class GlobalExceptionMiddleware(MiddlewareMixin):
    """
    Global exception handling middleware for the Veyu platform.
    
    This middleware catches unhandled exceptions and converts them to
    properly formatted JSON responses with logging and trace IDs.
    """
    
    def process_exception(self, request, exception):
        """
        Process unhandled exceptions and return formatted JSON responses
        
        Args:
            request: The Django request object
            exception: The unhandled exception
            
        Returns:
            JsonResponse with formatted error or None to continue normal processing
        """
        # Generate trace ID for this error
        trace_id = str(uuid.uuid4())
        
        # Get request context for logging
        context = get_request_context(request)
        
        # Handle VeyuException instances
        if isinstance(exception, VeyuException):
            exception.trace_id = trace_id
            log_error(exception, context, trace_id, 'warning')
            
            return JsonResponse(
                exception.to_dict(),
                status=self._get_status_code_for_exception(exception)
            )
        
        # Handle Django's built-in exceptions
        elif isinstance(exception, PermissionDenied):
            error = APIError(
                message="Permission denied",
                error_code=ErrorCodes.PERMISSION_DENIED,
                user_message="You don't have permission to access this resource."
            )
            error.trace_id = trace_id
            log_error(exception, context, trace_id, 'warning')
            
            return JsonResponse(error.to_dict(), status=403)
        
        elif isinstance(exception, DjangoValidationError):
            error = APIError(
                message=f"Validation error: {str(exception)}",
                error_code=ErrorCodes.VALIDATION_ERROR,
                user_message="Please check your input and try again."
            )
            error.trace_id = trace_id
            log_error(exception, context, trace_id, 'warning')
            
            return JsonResponse(error.to_dict(), status=400)
        
        elif isinstance(exception, DjangoDatabaseError):
            error = APIError(
                message="Database error occurred",
                error_code=ErrorCodes.DATABASE_CONNECTION_ERROR,
                user_message="A database error occurred. Please try again later."
            )
            error.trace_id = trace_id
            log_error(exception, context, trace_id, 'error')
            
            return JsonResponse(error.to_dict(), status=500)
        
        # Handle other unexpected exceptions
        else:
            # Only handle API requests (JSON responses)
            if self._is_api_request(request):
                error = APIError(
                    message=f"Unexpected error: {str(exception)}",
                    error_code=ErrorCodes.API_INTERNAL_ERROR,
                    details={'exception_type': type(exception).__name__}
                )
                error.trace_id = trace_id
                log_error(exception, context, trace_id, 'error')
                
                return JsonResponse(error.to_dict(), status=500)
        
        # Return None to continue with Django's default exception handling
        # (for non-API requests like admin interface)
        return None
    
    def _is_api_request(self, request):
        """
        Determine if this is an API request that should return JSON
        
        Args:
            request: The Django request object
            
        Returns:
            bool: True if this appears to be an API request
        """
        # Check if request accepts JSON
        accept_header = request.META.get('HTTP_ACCEPT', '')
        if 'application/json' in accept_header:
            return True
        
        # Check if request path starts with API prefix
        api_prefixes = ['/api/', '/accounts/api/', '/bookings/api/', '/chat/api/', '/feedback/api/']
        for prefix in api_prefixes:
            if request.path.startswith(prefix):
                return True
        
        # Check if request content type is JSON
        content_type = request.META.get('CONTENT_TYPE', '')
        if 'application/json' in content_type:
            return True
        
        return False
    
    def _get_status_code_for_exception(self, exception):
        """
        Get appropriate HTTP status code for VeyuException
        
        Args:
            exception: VeyuException instance
            
        Returns:
            int: HTTP status code
        """
        error_code_to_status = {
            ErrorCodes.VALIDATION_ERROR: 400,
            ErrorCodes.AUTHENTICATION_FAILED: 401,
            ErrorCodes.TOKEN_INVALID: 401,
            ErrorCodes.TOKEN_EXPIRED: 401,
            ErrorCodes.PERMISSION_DENIED: 403,
            ErrorCodes.NOT_FOUND: 404,
            ErrorCodes.API_RATE_LIMIT_EXCEEDED: 429,
            ErrorCodes.EMAIL_DELIVERY_FAILED: 500,
            ErrorCodes.DATABASE_CONNECTION_ERROR: 500,
            ErrorCodes.API_INTERNAL_ERROR: 500,
        }
        
        return error_code_to_status.get(exception.error_code, 400)


class CorrelationIdMiddleware(MiddlewareMixin):
    """
    Middleware to add correlation IDs to requests for tracking across services.
    
    This middleware adds a unique correlation ID to each request that can be
    used for tracking requests across different components and logs.
    """
    
    def process_request(self, request):
        """Add correlation ID to request"""
        # Check if correlation ID is provided in headers
        correlation_id = request.META.get('HTTP_X_CORRELATION_ID')
        
        # Generate new correlation ID if not provided
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Add correlation ID to request
        request.correlation_id = correlation_id
        
        # Add to response headers in process_response
        return None
    
    def process_response(self, request, response):
        """Add correlation ID to response headers"""
        if hasattr(request, 'correlation_id'):
            response['X-Correlation-ID'] = request.correlation_id
        
        return response


