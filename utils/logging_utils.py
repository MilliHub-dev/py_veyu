"""
Logging utilities for the Veyu platform.

This module provides utilities for structured logging, correlation ID tracking,
and consistent log formatting across the application.
"""

import logging
import uuid
import json
from typing import Dict, Any, Optional
from datetime import datetime
from django.conf import settings


class CorrelationIdFilter(logging.Filter):
    """
    Logging filter to add correlation IDs to log records.
    
    This filter adds correlation IDs from the current request context
    to all log records, enabling request tracking across services.
    """
    
    def filter(self, record):
        """Add correlation ID to log record if available"""
        # Try to get correlation ID from thread-local storage or request
        correlation_id = getattr(record, 'correlation_id', None)
        
        if not correlation_id:
            # Try to get from current request (if available)
            try:
                from django.core.context_processors import request
                if hasattr(request, 'correlation_id'):
                    correlation_id = request.correlation_id
            except:
                pass
        
        # Set correlation ID or generate new one
        record.correlation_id = correlation_id or str(uuid.uuid4())
        return True


class StructuredLogger:
    """
    Utility class for structured logging with consistent formatting.
    
    This class provides methods for logging with structured data,
    correlation IDs, and consistent formatting across the application.
    """
    
    def __init__(self, name: str):
        """
        Initialize structured logger
        
        Args:
            name: Logger name (usually __name__)
        """
        self.logger = logging.getLogger(name)
    
    def _log_with_context(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        **kwargs
    ):
        """
        Log message with structured context
        
        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Log message
            context: Additional context data
            correlation_id: Correlation ID for request tracking
            **kwargs: Additional keyword arguments
        """
        # Prepare log data
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'message': message,
            'correlation_id': correlation_id or str(uuid.uuid4()),
        }
        
        # Add context data
        if context:
            log_data['context'] = context
        
        # Add any additional kwargs
        log_data.update(kwargs)
        
        # Get log method
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        
        # Log with extra data
        log_method(message, extra=log_data)
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log debug message with context"""
        self._log_with_context('debug', message, context, **kwargs)
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log info message with context"""
        self._log_with_context('info', message, context, **kwargs)
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log warning message with context"""
        self._log_with_context('warning', message, context, **kwargs)
    
    def error(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log error message with context"""
        self._log_with_context('error', message, context, **kwargs)
    
    def critical(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log critical message with context"""
        self._log_with_context('critical', message, context, **kwargs)
    
    def log_api_request(
        self,
        request,
        response_status: int,
        duration_ms: Optional[float] = None,
        **kwargs
    ):
        """
        Log API request with structured data
        
        Args:
            request: Django request object
            response_status: HTTP response status code
            duration_ms: Request duration in milliseconds
            **kwargs: Additional context data
        """
        context = {
            'method': request.method,
            'path': request.path,
            'status_code': response_status,
            'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        if duration_ms is not None:
            context['duration_ms'] = duration_ms
        
        # Add any additional context
        context.update(kwargs)
        
        # Determine log level based on status code
        if response_status >= 500:
            level = 'error'
        elif response_status >= 400:
            level = 'warning'
        else:
            level = 'info'
        
        message = f"{request.method} {request.path} - {response_status}"
        self._log_with_context(level, message, context)
    
    def log_email_event(
        self,
        event_type: str,
        recipient: str,
        subject: str,
        success: bool = True,
        error_message: Optional[str] = None,
        **kwargs
    ):
        """
        Log email-related events
        
        Args:
            event_type: Type of email event (sent, failed, bounced, etc.)
            recipient: Email recipient
            subject: Email subject
            success: Whether the operation was successful
            error_message: Error message if operation failed
            **kwargs: Additional context data
        """
        context = {
            'event_type': event_type,
            'recipient': recipient,
            'subject': subject,
            'success': success,
        }
        
        if error_message:
            context['error_message'] = error_message
        
        # Add any additional context
        context.update(kwargs)
        
        level = 'info' if success else 'error'
        message = f"Email {event_type}: {subject} to {recipient}"
        
        self._log_with_context(level, message, context)
    
    def log_authentication_event(
        self,
        event_type: str,
        user_email: Optional[str] = None,
        user_id: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        **kwargs
    ):
        """
        Log authentication-related events
        
        Args:
            event_type: Type of auth event (login, logout, signup, etc.)
            user_email: User email address
            user_id: User ID
            success: Whether the operation was successful
            error_message: Error message if operation failed
            **kwargs: Additional context data
        """
        context = {
            'event_type': event_type,
            'success': success,
        }
        
        if user_email:
            context['user_email'] = user_email
        if user_id:
            context['user_id'] = user_id
        if error_message:
            context['error_message'] = error_message
        
        # Add any additional context
        context.update(kwargs)
        
        level = 'info' if success else 'warning'
        message = f"Authentication {event_type}"
        if user_email:
            message += f" for {user_email}"
        
        self._log_with_context(level, message, context)
    
    def log_business_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[int] = None,
        **kwargs
    ):
        """
        Log business logic events
        
        Args:
            event_type: Type of business event
            entity_type: Type of entity (booking, listing, verification, etc.)
            entity_id: Entity identifier
            user_id: User ID associated with the event
            **kwargs: Additional context data
        """
        context = {
            'event_type': event_type,
            'entity_type': entity_type,
        }
        
        if entity_id:
            context['entity_id'] = entity_id
        if user_id:
            context['user_id'] = user_id
        
        # Add any additional context
        context.update(kwargs)
        
        message = f"{entity_type.title()} {event_type}"
        if entity_id:
            message += f" (ID: {entity_id})"
        
        self._log_with_context('info', message, context)
    
    @staticmethod
    def _get_client_ip(request) -> str:
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LoggingMixin:
    """
    Mixin class to add structured logging capabilities to views and other classes.
    
    This mixin provides a structured logger instance and common logging methods
    that can be used in Django views, serializers, and other classes.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = StructuredLogger(self.__class__.__module__)
    
    def log_info(self, message: str, **kwargs):
        """Log info message with class context"""
        kwargs.setdefault('class_name', self.__class__.__name__)
        self.logger.info(message, **kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message with class context"""
        kwargs.setdefault('class_name', self.__class__.__name__)
        self.logger.warning(message, **kwargs)
    
    def log_error(self, message: str, **kwargs):
        """Log error message with class context"""
        kwargs.setdefault('class_name', self.__class__.__name__)
        self.logger.error(message, **kwargs)


# Convenience functions for common logging scenarios
def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance"""
    return StructuredLogger(name)


def log_performance(func_name: str, duration_ms: float, **kwargs):
    """Log performance metrics for a function or operation"""
    logger = StructuredLogger('veyu.performance')
    context = {
        'function_name': func_name,
        'duration_ms': duration_ms,
        'performance_metric': True,
    }
    context.update(kwargs)
    
    # Determine log level based on duration
    if duration_ms > 5000:  # > 5 seconds
        level = 'warning'
    elif duration_ms > 1000:  # > 1 second
        level = 'info'
    else:
        level = 'debug'
    
    message = f"Performance: {func_name} took {duration_ms:.2f}ms"
    logger._log_with_context(level, message, context)


def log_security_event(event_type: str, severity: str = 'medium', **kwargs):
    """Log security-related events"""
    logger = StructuredLogger('veyu.security')
    context = {
        'event_type': event_type,
        'severity': severity,
        'security_event': True,
    }
    context.update(kwargs)
    
    # Determine log level based on severity
    level_map = {
        'low': 'info',
        'medium': 'warning',
        'high': 'error',
        'critical': 'critical',
    }
    level = level_map.get(severity.lower(), 'warning')
    
    message = f"Security event: {event_type}"
    logger._log_with_context(level, message, context)


# Create logs directory if it doesn't exist
import os
logs_dir = os.path.join(settings.BASE_DIR, 'logs')
os.makedirs(logs_dir, exist_ok=True)