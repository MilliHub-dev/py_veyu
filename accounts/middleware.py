"""
Security Middleware for Veyu Platform

This module provides security middleware for rate limiting, account lockout,
and security headers to enhance the platform's security posture.
"""

import logging
import time
from typing import Dict, Any, Optional
from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import hashlib
import json

logger = logging.getLogger(__name__)
User = get_user_model()


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to all responses.
    """
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Add security headers to response."""
        
        # Content Security Policy
        if not response.get('Content-Security-Policy'):
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https: blob:; "
                "connect-src 'self' https: wss: ws:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
            response['Content-Security-Policy'] = csp_policy
        
        # X-Frame-Options (clickjacking protection)
        if not response.get('X-Frame-Options'):
            response['X-Frame-Options'] = 'DENY'
        
        # X-Content-Type-Options (MIME type sniffing protection)
        if not response.get('X-Content-Type-Options'):
            response['X-Content-Type-Options'] = 'nosniff'
        
        # X-XSS-Protection (XSS protection)
        if not response.get('X-XSS-Protection'):
            response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer Policy
        if not response.get('Referrer-Policy'):
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy (formerly Feature Policy)
        if not response.get('Permissions-Policy'):
            permissions_policy = (
                "geolocation=(self), "
                "microphone=(), "
                "camera=(), "
                "payment=(self), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "speaker=(self)"
            )
            response['Permissions-Policy'] = permissions_policy
        
        # Strict Transport Security (HTTPS only)
        if request.is_secure() and not response.get('Strict-Transport-Security'):
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # Cross-Origin Embedder Policy
        if not response.get('Cross-Origin-Embedder-Policy'):
            response['Cross-Origin-Embedder-Policy'] = 'require-corp'
        
        # Cross-Origin Opener Policy
        if not response.get('Cross-Origin-Opener-Policy'):
            response['Cross-Origin-Opener-Policy'] = 'same-origin'
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Middleware for rate limiting API requests with different limits for different endpoints.
    """
    
    # Rate limit configurations (requests per minute)
    RATE_LIMITS = {
        'auth': {
            'login': 5,      # 5 login attempts per minute
            'signup': 3,     # 3 signup attempts per minute
            'password_reset': 2,  # 2 password reset requests per minute
            'verify': 10,    # 10 verification attempts per minute
        },
        'api': {
            'default': 60,   # 60 requests per minute for general API
            'upload': 10,    # 10 file uploads per minute
            'search': 30,    # 30 search requests per minute
        }
    }
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Check rate limits for incoming requests."""
        
        # Skip rate limiting for certain conditions
        if self._should_skip_rate_limiting(request):
            return None
        
        # Determine rate limit based on endpoint
        limit_key, limit_value = self._get_rate_limit(request)
        
        if limit_value is None:
            return None  # No rate limiting for this endpoint
        
        # Get client identifier
        client_id = self._get_client_identifier(request)
        
        # Check rate limit
        if self._is_rate_limited(client_id, limit_key, limit_value):
            logger.warning(f"Rate limit exceeded for {client_id} on {request.path}")
            return JsonResponse({
                'error': True,
                'message': 'Rate limit exceeded. Please try again later.',
                'code': 'RATE_LIMIT_EXCEEDED',
                'retry_after': 60
            }, status=429)
        
        # Update rate limit counter
        self._update_rate_limit(client_id, limit_key)
        
        return None
    
    def _should_skip_rate_limiting(self, request: HttpRequest) -> bool:
        """Determine if rate limiting should be skipped."""
        # Skip for admin users
        if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_staff:
            return True
        
        # Skip for health checks
        if request.path in ['/health/', '/api/health/', '/ping/']:
            return True
        
        # Skip for static files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return True
        
        return False
    
    def _get_rate_limit(self, request: HttpRequest) -> tuple:
        """Get rate limit configuration for the request."""
        path = request.path.lower()
        
        # Authentication endpoints
        if '/login' in path:
            return 'auth_login', self.RATE_LIMITS['auth']['login']
        elif '/signup' in path:
            return 'auth_signup', self.RATE_LIMITS['auth']['signup']
        elif '/password' in path and '/reset' in path:
            return 'auth_password_reset', self.RATE_LIMITS['auth']['password_reset']
        elif '/verify' in path:
            return 'auth_verify', self.RATE_LIMITS['auth']['verify']
        
        # API endpoints
        elif '/upload' in path:
            return 'api_upload', self.RATE_LIMITS['api']['upload']
        elif '/search' in path:
            return 'api_search', self.RATE_LIMITS['api']['search']
        elif path.startswith('/api/'):
            return 'api_default', self.RATE_LIMITS['api']['default']
        
        return 'unknown', None
    
    def _get_client_identifier(self, request: HttpRequest) -> str:
        """Get unique identifier for the client."""
        # Use user ID if authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f"user_{request.user.id}"
        
        # Use IP address for anonymous users
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        return f"ip_{ip}"
    
    def _is_rate_limited(self, client_id: str, limit_key: str, limit_value: int) -> bool:
        """Check if client has exceeded rate limit."""
        cache_key = f"rate_limit:{limit_key}:{client_id}"
        current_count = cache.get(cache_key, 0)
        return current_count >= limit_value
    
    def _update_rate_limit(self, client_id: str, limit_key: str) -> None:
        """Update rate limit counter."""
        cache_key = f"rate_limit:{limit_key}:{client_id}"
        current_count = cache.get(cache_key, 0)
        cache.set(cache_key, current_count + 1, timeout=60)  # 1 minute window


class AccountLockoutMiddleware(MiddlewareMixin):
    """
    Middleware for account lockout after failed authentication attempts.
    """
    
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Check for account lockout on authentication endpoints."""
        
        # Only check lockout for authentication endpoints
        if not self._is_auth_endpoint(request):
            return None
        
        # Get email from request data
        email = self._get_email_from_request(request)
        if not email:
            return None
        
        # Check if account is locked
        if self._is_account_locked(email):
            lockout_info = self._get_lockout_info(email)
            logger.warning(f"Locked account access attempt: {email}")
            
            return JsonResponse({
                'error': True,
                'message': 'Account temporarily locked due to multiple failed login attempts.',
                'code': 'ACCOUNT_LOCKED',
                'details': {
                    'locked_until': lockout_info.get('locked_until'),
                    'attempts_remaining': 0,
                    'lockout_duration_minutes': self.LOCKOUT_DURATION_MINUTES
                }
            }, status=423)  # 423 Locked
        
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Handle failed authentication attempts."""
        
        # Only process authentication endpoints
        if not self._is_auth_endpoint(request):
            return response
        
        # Get email from request
        email = self._get_email_from_request(request)
        if not email:
            return response
        
        # Check if authentication failed
        if self._is_auth_failure(response):
            self._record_failed_attempt(email)
            
            # Check if account should be locked
            failed_attempts = self._get_failed_attempts(email)
            if failed_attempts >= self.MAX_FAILED_ATTEMPTS:
                self._lock_account(email)
                logger.warning(f"Account locked due to failed attempts: {email}")
                
                # Update response to indicate lockout
                if hasattr(response, 'data'):
                    response.data['account_locked'] = True
                    response.data['lockout_duration_minutes'] = self.LOCKOUT_DURATION_MINUTES
        
        elif self._is_auth_success(response):
            # Clear failed attempts on successful authentication
            self._clear_failed_attempts(email)
        
        return response
    
    def _is_auth_endpoint(self, request: HttpRequest) -> bool:
        """Check if request is to an authentication endpoint."""
        path = request.path.lower()
        return '/login' in path or '/token' in path
    
    def _get_email_from_request(self, request: HttpRequest) -> Optional[str]:
        """Extract email from request data."""
        try:
            if hasattr(request, 'data') and 'email' in request.data:
                return request.data['email'].lower()
            
            # Try to parse JSON body
            if request.content_type == 'application/json':
                data = json.loads(request.body.decode('utf-8'))
                return data.get('email', '').lower()
        except (json.JSONDecodeError, AttributeError, KeyError):
            pass
        
        return None
    
    def _is_auth_failure(self, response: HttpResponse) -> bool:
        """Check if response indicates authentication failure."""
        return response.status_code in [401, 403]
    
    def _is_auth_success(self, response: HttpResponse) -> bool:
        """Check if response indicates authentication success."""
        return response.status_code == 200
    
    def _get_lockout_cache_key(self, email: str) -> str:
        """Get cache key for account lockout."""
        email_hash = hashlib.sha256(email.encode()).hexdigest()
        return f"account_lockout:{email_hash}"
    
    def _get_failed_attempts_cache_key(self, email: str) -> str:
        """Get cache key for failed attempts."""
        email_hash = hashlib.sha256(email.encode()).hexdigest()
        return f"failed_attempts:{email_hash}"
    
    def _is_account_locked(self, email: str) -> bool:
        """Check if account is currently locked."""
        cache_key = self._get_lockout_cache_key(email)
        lockout_data = cache.get(cache_key)
        
        if not lockout_data:
            return False
        
        # Check if lockout has expired
        locked_until = lockout_data.get('locked_until')
        if locked_until and timezone.now() > locked_until:
            # Lockout expired, clear it
            cache.delete(cache_key)
            self._clear_failed_attempts(email)
            return False
        
        return True
    
    def _get_lockout_info(self, email: str) -> Dict[str, Any]:
        """Get lockout information for account."""
        cache_key = self._get_lockout_cache_key(email)
        return cache.get(cache_key, {})
    
    def _record_failed_attempt(self, email: str) -> None:
        """Record a failed authentication attempt."""
        cache_key = self._get_failed_attempts_cache_key(email)
        attempts = cache.get(cache_key, 0) + 1
        
        # Store for 1 hour
        cache.set(cache_key, attempts, timeout=3600)
        
        logger.info(f"Failed authentication attempt {attempts} for {email}")
    
    def _get_failed_attempts(self, email: str) -> int:
        """Get number of failed attempts for account."""
        cache_key = self._get_failed_attempts_cache_key(email)
        return cache.get(cache_key, 0)
    
    def _lock_account(self, email: str) -> None:
        """Lock account for specified duration."""
        lockout_until = timezone.now() + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
        
        lockout_data = {
            'locked_at': timezone.now().isoformat(),
            'locked_until': lockout_until.isoformat(),
            'reason': 'multiple_failed_attempts'
        }
        
        cache_key = self._get_lockout_cache_key(email)
        cache.set(cache_key, lockout_data, timeout=self.LOCKOUT_DURATION_MINUTES * 60)
    
    def _clear_failed_attempts(self, email: str) -> None:
        """Clear failed attempts counter."""
        cache_key = self._get_failed_attempts_cache_key(email)
        cache.delete(cache_key)


class CSRFExemptionMiddleware(MiddlewareMixin):
    """
    Middleware to handle CSRF exemption for API endpoints while maintaining
    CSRF protection for web forms.
    """
    
    def process_request(self, request: HttpRequest) -> None:
        """Exempt API endpoints from CSRF validation."""
        
        # Exempt API endpoints from CSRF
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        
        # Exempt webhook endpoints
        elif any(webhook in request.path for webhook in ['/webhook/', '/callback/']):
            setattr(request, '_dont_enforce_csrf_checks', True)


class SecurityLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for logging security-related events.
    """
    
    def process_request(self, request: HttpRequest) -> None:
        """Log security-relevant request information."""
        
        # Log authentication attempts
        if self._is_security_relevant_endpoint(request):
            client_ip = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
            
            logger.info(
                f"Security event: {request.method} {request.path} "
                f"from {client_ip} with {user_agent[:100]}"
            )
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Log security-relevant response information."""
        
        # Log failed authentication attempts
        if self._is_security_relevant_endpoint(request) and response.status_code in [401, 403, 423]:
            client_ip = self._get_client_ip(request)
            logger.warning(
                f"Security alert: Failed authentication from {client_ip} "
                f"to {request.path} (Status: {response.status_code})"
            )
        
        return response
    
    def _is_security_relevant_endpoint(self, request: HttpRequest) -> bool:
        """Check if endpoint is security-relevant."""
        security_paths = ['/login', '/signup', '/password', '/token', '/verify', '/admin']
        return any(path in request.path.lower() for path in security_paths)
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'Unknown')