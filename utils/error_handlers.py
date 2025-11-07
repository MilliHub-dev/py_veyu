"""
Error handling decorators and utilities for the Veyu platform.

This module provides decorators and utilities for consistent error handling
across API views, including logging, response formatting, and trace ID generation.
"""

import logging
import traceback
import uuid
from functools import wraps
from typing import Any, Dict, Optional, Callable

from django.http import JsonResponse
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.response import Response

from .exceptions import (
    VeyuException, 
    APIError, 
    ValidationError, 
    DatabaseError,
    ErrorCodes
)

# Configure logger for error handling
logger = logging.getLogger('veyu.error_handler')


def get_client_ip(request) -> str:
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_request_context(request) -> Dict[str, Any]:
    """Extract relevant context from request for logging"""
    return {
        'method': request.method,
        'path': request.path,
        'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
        'user_email': getattr(request.user, 'email', None) if hasattr(request, 'user') else None,
        'ip_address': get_client_ip(request),
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'content_type': request.META.get('CONTENT_TYPE', ''),
    }


def log_error(
    error: Exception, 
    context: Dict[str, Any], 
    trace_id: str,
    level: str = 'error'
) -> None:
    """
    Log error with context information
    
    Args:
        error: The exception that occurred
        context: Request context information
        trace_id: Unique identifier for this error occurrence
        level: Log level (error, warning, info)
    """
    error_data = {
        'trace_id': trace_id,
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context,
    }
    
    # Add VeyuException specific data
    if isinstance(error, VeyuException):
        error_data.update({
            'error_code': error.error_code,
            'details': error.details,
        })
    
    # Add traceback for non-VeyuException errors
    if not isinstance(error, VeyuException):
        error_data['traceback'] = traceback.format_exc()
    
    # Log based on level
    log_method = getattr(logger, level, logger.error)
    log_method(f"Error occurred: {error}", extra=error_data)


def handle_api_exception(func: Callable) -> Callable:
    """
    Decorator for consistent API error handling in views.
    
    This decorator catches exceptions, logs them with context,
    and returns properly formatted error responses.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract request from args (assumes it's the second argument after self)
        request = None
        if len(args) >= 2:
            request = args[1]
        elif 'request' in kwargs:
            request = kwargs['request']
        
        trace_id = str(uuid.uuid4())
        
        try:
            return func(*args, **kwargs)
            
        except VeyuException as e:
            # Handle known Veyu exceptions
            e.trace_id = trace_id
            
            if request:
                context = get_request_context(request)
                log_error(e, context, trace_id, 'warning')
            
            return Response(
                e.to_dict(),
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except DjangoValidationError as e:
            # Handle Django validation errors
            validation_error = ValidationError(
                message=str(e),
                details={'django_validation_error': True}
            )
            validation_error.trace_id = trace_id
            
            if request:
                context = get_request_context(request)
                log_error(validation_error, context, trace_id, 'warning')
            
            return Response(
                validation_error.to_dict(),
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            # Handle unexpected exceptions
            api_error = APIError(
                message=f"Unexpected error: {str(e)}",
                error_code=ErrorCodes.API_INTERNAL_ERROR,
                details={'original_error': type(e).__name__}
            )
            api_error.trace_id = trace_id
            
            if request:
                context = get_request_context(request)
                log_error(e, context, trace_id, 'error')
            
            return Response(
                api_error.to_dict(),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return wrapper


def handle_database_errors(func: Callable) -> Callable:
    """
    Decorator for handling database-related errors with transaction rollback.
    
    This decorator wraps database operations in transactions and handles
    database-specific errors appropriately.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            with transaction.atomic():
                return func(*args, **kwargs)
                
        except Exception as e:
            # Convert database errors to DatabaseError
            if 'database' in str(e).lower() or 'connection' in str(e).lower():
                raise DatabaseError(
                    message=f"Database operation failed: {str(e)}",
                    details={'original_error': type(e).__name__}
                )
            # Re-raise other exceptions
            raise
    
    return wrapper


def require_authentication(func: Callable) -> Callable:
    """
    Decorator to ensure user is authenticated before accessing the view.
    
    Returns 401 Unauthorized if user is not authenticated.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract request from args
        request = None
        if len(args) >= 2:
            request = args[1]
        elif 'request' in kwargs:
            request = kwargs['request']
        
        if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
            from .exceptions import AuthenticationError
            raise AuthenticationError(
                message="Authentication required",
                error_code=ErrorCodes.AUTHENTICATION_FAILED,
                user_message="Please log in to access this resource."
            )
        
        return func(*args, **kwargs)
    
    return wrapper


def validate_request_data(required_fields: list = None, optional_fields: list = None):
    """
    Decorator to validate request data before processing.
    
    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names (for documentation)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract request from args
            request = None
            if len(args) >= 2:
                request = args[1]
            elif 'request' in kwargs:
                request = kwargs['request']
            
            if not request:
                return func(*args, **kwargs)
            
            # Get request data
            data = getattr(request, 'data', {})
            
            # Check required fields
            if required_fields:
                missing_fields = []
                for field in required_fields:
                    if field not in data or data[field] is None or data[field] == '':
                        missing_fields.append(field)
                
                if missing_fields:
                    raise ValidationError(
                        message=f"Missing required fields: {', '.join(missing_fields)}",
                        field_errors={field: "This field is required." for field in missing_fields}
                    )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class ErrorResponseFormatter:
    """Utility class for formatting error responses consistently"""
    
    @staticmethod
    def format_error_response(
        error: Exception,
        trace_id: Optional[str] = None,
        status_code: int = 500
    ) -> JsonResponse:
        """
        Format an error as a JSON response
        
        Args:
            error: The exception to format
            trace_id: Optional trace ID for tracking
            status_code: HTTP status code
            
        Returns:
            JsonResponse with formatted error
        """
        if isinstance(error, VeyuException):
            response_data = error.to_dict()
            if trace_id:
                response_data['trace_id'] = trace_id
        else:
            response_data = {
                'error': True,
                'message': 'An unexpected error occurred',
                'code': ErrorCodes.API_INTERNAL_ERROR,
                'details': {'error_type': type(error).__name__},
                'trace_id': trace_id or str(uuid.uuid4())
            }
        
        return JsonResponse(response_data, status=status_code)
    
    @staticmethod
    def format_validation_error(
        field_errors: Dict[str, str],
        message: str = "Validation failed"
    ) -> JsonResponse:
        """
        Format validation errors as a JSON response
        
        Args:
            field_errors: Dictionary of field names to error messages
            message: General error message
            
        Returns:
            JsonResponse with formatted validation error
        """
        validation_error = ValidationError(
            message=message,
            field_errors=field_errors
        )
        
        return JsonResponse(
            validation_error.to_dict(),
            status=400
        )


# Utility functions for common error scenarios
def handle_permission_denied(user_message: str = "Permission denied") -> Response:
    """Create a standardized permission denied response"""
    error = APIError(
        message="User does not have permission to perform this action",
        error_code=ErrorCodes.PERMISSION_DENIED,
        user_message=user_message
    )
    return Response(error.to_dict(), status=status.HTTP_403_FORBIDDEN)


def handle_not_found(resource_name: str = "Resource") -> Response:
    """Create a standardized not found response"""
    error = APIError(
        message=f"{resource_name} not found",
        error_code=ErrorCodes.NOT_FOUND,
        user_message=f"The requested {resource_name.lower()} was not found."
    )
    return Response(error.to_dict(), status=status.HTTP_404_NOT_FOUND)


def handle_rate_limit_exceeded(limit: int, window: int) -> Response:
    """Create a standardized rate limit exceeded response"""
    from .exceptions import RateLimitError
    error = RateLimitError(limit=limit, window=window)
    return Response(error.to_dict(), status=status.HTTP_429_TOO_MANY_REQUESTS)