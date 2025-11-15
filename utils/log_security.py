"""
Security logging utilities for the log viewer system.
Provides centralized security event logging with structured data.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from django.utils import timezone
from django.conf import settings
from pathlib import Path


class LogViewerSecurityLogger:
    """
    Centralized security logging for log viewer operations.
    
    Logs all security-relevant events to security.log with structured data
    for monitoring and audit purposes.
    
    Requirements: 4.5
    """
    
    def __init__(self):
        """Initialize the security logger."""
        self.logger = logging.getLogger('log_viewer_security')
        
        # Ensure security log file exists and is writable
        self.security_log_path = self._get_security_log_path()
        self._ensure_log_file_exists()
    
    def _get_security_log_path(self) -> Path:
        """Get the path to the security log file."""
        logs_directory = getattr(settings, 'LOG_DIRECTORY', Path(settings.BASE_DIR) / 'logs')
        if isinstance(logs_directory, str):
            logs_directory = Path(logs_directory)
        
        return logs_directory / 'security.log'
    
    def _ensure_log_file_exists(self) -> None:
        """Ensure the security log file exists and is writable."""
        try:
            # Create logs directory if it doesn't exist
            self.security_log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create security log file if it doesn't exist
            if not self.security_log_path.exists():
                self.security_log_path.touch()
                
        except (OSError, PermissionError):
            # If we can't create the log file, we'll fall back to Django logging
            pass
    
    def log_access_attempt(
        self, 
        user_email: str, 
        log_file: str, 
        ip_address: str, 
        success: bool = True,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log log viewer access attempts.
        
        Args:
            user_email: Email of the user attempting access
            log_file: Name of the log file being accessed
            ip_address: IP address of the request
            success: Whether the access was successful
            additional_data: Additional context data
        """
        event_data = {
            'event_type': 'log_access_attempt',
            'timestamp': timezone.now().isoformat(),
            'user_email': user_email,
            'log_file': log_file,
            'ip_address': ip_address,
            'success': success,
            'user_agent': additional_data.get('user_agent', '') if additional_data else '',
            'search_query': additional_data.get('search_query', '') if additional_data else '',
            'level_filter': additional_data.get('level_filter', '') if additional_data else ''
        }
        
        level = 'info' if success else 'warning'
        message = f"Log access {'successful' if success else 'failed'}: {user_email} -> {log_file}"
        
        self._write_security_log(level, message, event_data)
    
    def log_permission_denied(
        self, 
        user_email: str, 
        log_file: str, 
        ip_address: str,
        reason: str = 'insufficient_privileges',
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log permission denied events.
        
        Args:
            user_email: Email of the user denied access
            log_file: Name of the log file access was denied for
            ip_address: IP address of the request
            reason: Reason for denial
            additional_data: Additional context data
        """
        event_data = {
            'event_type': 'permission_denied',
            'timestamp': timezone.now().isoformat(),
            'user_email': user_email,
            'log_file': log_file,
            'ip_address': ip_address,
            'reason': reason,
            'user_agent': additional_data.get('user_agent', '') if additional_data else '',
            'user_type': additional_data.get('user_type', '') if additional_data else '',
            'is_staff': additional_data.get('is_staff', False) if additional_data else False
        }
        
        message = f"Permission denied: {user_email} -> {log_file} (reason: {reason})"
        
        self._write_security_log('warning', message, event_data)
    
    def log_file_access_error(
        self, 
        user_email: str, 
        log_file: str, 
        error_type: str,
        error_message: str,
        ip_address: str,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log file access errors and invalid requests.
        
        Args:
            user_email: Email of the user who encountered the error
            log_file: Name of the log file that caused the error
            error_type: Type of error (file_not_found, permission_error, etc.)
            error_message: Detailed error message
            ip_address: IP address of the request
            additional_data: Additional context data
        """
        event_data = {
            'event_type': 'file_access_error',
            'timestamp': timezone.now().isoformat(),
            'user_email': user_email,
            'log_file': log_file,
            'error_type': error_type,
            'error_message': error_message,
            'ip_address': ip_address,
            'user_agent': additional_data.get('user_agent', '') if additional_data else '',
            'request_path': additional_data.get('request_path', '') if additional_data else ''
        }
        
        message = f"File access error: {user_email} -> {log_file} ({error_type}: {error_message})"
        
        self._write_security_log('error', message, event_data)
    
    def log_invalid_request(
        self, 
        user_email: str, 
        request_details: str,
        ip_address: str,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log invalid or suspicious requests.
        
        Args:
            user_email: Email of the user making the request
            request_details: Details of the invalid request
            ip_address: IP address of the request
            additional_data: Additional context data
        """
        event_data = {
            'event_type': 'invalid_request',
            'timestamp': timezone.now().isoformat(),
            'user_email': user_email,
            'request_details': request_details,
            'ip_address': ip_address,
            'user_agent': additional_data.get('user_agent', '') if additional_data else '',
            'request_path': additional_data.get('request_path', '') if additional_data else '',
            'request_method': additional_data.get('request_method', '') if additional_data else ''
        }
        
        message = f"Invalid request: {user_email} -> {request_details}"
        
        self._write_security_log('warning', message, event_data)
    
    def log_download_attempt(
        self, 
        user_email: str, 
        log_file: str, 
        ip_address: str,
        success: bool = True,
        file_size: Optional[int] = None,
        is_filtered: bool = False,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log log file download attempts.
        
        Args:
            user_email: Email of the user downloading the file
            log_file: Name of the log file being downloaded
            ip_address: IP address of the request
            success: Whether the download was successful
            file_size: Size of the downloaded file in bytes
            is_filtered: Whether this was a filtered download
            additional_data: Additional context data
        """
        event_data = {
            'event_type': 'download_attempt',
            'timestamp': timezone.now().isoformat(),
            'user_email': user_email,
            'log_file': log_file,
            'ip_address': ip_address,
            'success': success,
            'file_size': file_size,
            'is_filtered': is_filtered,
            'user_agent': additional_data.get('user_agent', '') if additional_data else '',
            'search_query': additional_data.get('search_query', '') if additional_data else '',
            'level_filter': additional_data.get('level_filter', '') if additional_data else ''
        }
        
        download_type = 'filtered' if is_filtered else 'complete'
        size_info = f" ({file_size} bytes)" if file_size else ""
        message = f"Download {'successful' if success else 'failed'}: {user_email} -> {log_file} ({download_type}){size_info}"
        
        level = 'info' if success else 'warning'
        self._write_security_log(level, message, event_data)
    
    def log_api_access(
        self, 
        user_email: str, 
        log_file: str, 
        ip_address: str,
        endpoint: str,
        success: bool = True,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log API endpoint access for real-time updates.
        
        Args:
            user_email: Email of the user accessing the API
            log_file: Name of the log file being accessed via API
            ip_address: IP address of the request
            endpoint: API endpoint being accessed
            success: Whether the API call was successful
            additional_data: Additional context data
        """
        event_data = {
            'event_type': 'api_access',
            'timestamp': timezone.now().isoformat(),
            'user_email': user_email,
            'log_file': log_file,
            'ip_address': ip_address,
            'endpoint': endpoint,
            'success': success,
            'user_agent': additional_data.get('user_agent', '') if additional_data else '',
            'is_manual_refresh': additional_data.get('is_manual_refresh', False) if additional_data else False
        }
        
        message = f"API access {'successful' if success else 'failed'}: {user_email} -> {endpoint} ({log_file})"
        
        level = 'info' if success else 'warning'
        self._write_security_log(level, message, event_data)
    
    def _write_security_log(self, level: str, message: str, event_data: Dict[str, Any]) -> None:
        """
        Write security event to log file and Django logging system.
        
        Args:
            level: Log level (info, warning, error)
            message: Human-readable message
            event_data: Structured event data
        """
        # Format log entry with timestamp and structured data
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {level.upper()}: LOG_VIEWER: {message}"
        
        # Add structured data as JSON on the next line for parsing
        structured_data = json.dumps(event_data, default=str, separators=(',', ':'))
        full_log_entry = f"{log_entry}\n    DATA: {structured_data}\n"
        
        # Write to security log file
        try:
            with open(self.security_log_path, 'a', encoding='utf-8') as f:
                f.write(full_log_entry)
        except (OSError, PermissionError):
            # If we can't write to the security log file, fall back to Django logging
            pass
        
        # Also log to Django logging system
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(message, extra={'event_data': event_data})


# Global instance for easy access
security_logger = LogViewerSecurityLogger()


def get_request_metadata(request) -> Dict[str, Any]:
    """
    Extract metadata from Django request for security logging.
    
    Args:
        request: Django HttpRequest object
        
    Returns:
        Dict containing request metadata
    """
    return {
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'request_path': request.path,
        'request_method': request.method,
        'user_type': getattr(request.user, 'user_type', '') if hasattr(request.user, 'user_type') else '',
        'is_staff': request.user.is_staff if hasattr(request.user, 'is_staff') else False
    }