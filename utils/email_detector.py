"""
Email backend detector that automatically chooses the best available backend.
"""
import socket
import logging
from django.conf import settings
from django.core.mail.backends.console import EmailBackend as ConsoleBackend
from django.core.mail.backends.filebased import EmailBackend as FileBackend

logger = logging.getLogger('utils.mail')


def detect_network_connectivity():
    """
    Test if the server has internet connectivity for SMTP.
    """
    try:
        # Try to connect to common DNS servers
        test_hosts = [
            ('8.8.8.8', 53),  # Google DNS
            ('1.1.1.1', 53),  # Cloudflare DNS
        ]
        
        for host, port in test_hosts:
            try:
                sock = socket.create_connection((host, port), timeout=5)
                sock.close()
                logger.debug(f"Network connectivity confirmed via {host}:{port}")
                return True
            except (socket.timeout, socket.error, OSError):
                continue
        
        logger.warning("No network connectivity detected")
        return False
        
    except Exception as e:
        logger.error(f"Error testing network connectivity: {e}")
        return False


# Cache for backend detection to avoid repeated checks
_backend_cache = None
_cache_timestamp = 0
_cache_duration = 300  # 5 minutes

def get_optimal_email_backend():
    """
    Determine the best email backend based on environment and connectivity.
    Uses caching to avoid repeated network checks.
    """
    global _backend_cache, _cache_timestamp
    
    import time
    current_time = time.time()
    
    # Return cached result if still valid
    if _backend_cache and (current_time - _cache_timestamp) < _cache_duration:
        return _backend_cache
    
    # If explicitly set to console, use it
    if getattr(settings, 'USE_CONSOLE_EMAIL', False):
        logger.info("Using console email backend (explicitly configured)")
        _backend_cache = 'django.core.mail.backends.console.EmailBackend'
        _cache_timestamp = current_time
        return _backend_cache
    
    # In DEBUG mode, prefer console unless SMTP is explicitly requested
    if getattr(settings, 'DEBUG', False):
        if not getattr(settings, 'USE_SMTP_IN_DEV', False):
            logger.info("Using console email backend (DEBUG mode)")
            _backend_cache = 'django.core.mail.backends.console.EmailBackend'
            _cache_timestamp = current_time
            return _backend_cache
    
    # Test network connectivity
    if not detect_network_connectivity():
        logger.warning("No network connectivity - falling back to console backend")
        _backend_cache = 'django.core.mail.backends.console.EmailBackend'
        _cache_timestamp = current_time
        return _backend_cache
    
    # Test SMTP connectivity
    try:
        email_host = getattr(settings, 'EMAIL_HOST', '')
        email_port = getattr(settings, 'EMAIL_PORT', 587)
        
        if email_host:
            sock = socket.create_connection((email_host, email_port), timeout=10)
            sock.close()
            logger.info(f"SMTP connectivity confirmed to {email_host}:{email_port}")
            _backend_cache = 'utils.email_backends.ReliableSMTPBackend'
            _cache_timestamp = current_time
            return _backend_cache
        else:
            logger.warning("No EMAIL_HOST configured - using console backend")
            _backend_cache = 'django.core.mail.backends.console.EmailBackend'
            _cache_timestamp = current_time
            return _backend_cache
            
    except (socket.timeout, socket.error, OSError) as e:
        logger.warning(f"SMTP connectivity failed ({e}) - falling back to console backend")
        _backend_cache = 'django.core.mail.backends.console.EmailBackend'
        _cache_timestamp = current_time
        return _backend_cache
    except Exception as e:
        logger.error(f"Error testing SMTP connectivity: {e}")
        _backend_cache = 'django.core.mail.backends.console.EmailBackend'
        _cache_timestamp = current_time
        return _backend_cache


class AdaptiveEmailBackend:
    """
    Email backend that automatically adapts to the environment.
    """
    
    def __init__(self, *args, **kwargs):
        self.backend_class = None
        self.backend_instance = None
        self._setup_backend()
    
    def _setup_backend(self):
        """Setup the appropriate backend based on environment."""
        backend_path = get_optimal_email_backend()
        
        try:
            from django.utils.module_loading import import_string
            self.backend_class = import_string(backend_path)
            self.backend_instance = self.backend_class()
            logger.info(f"Initialized email backend: {backend_path}")
        except Exception as e:
            logger.error(f"Failed to initialize backend {backend_path}: {e}")
            # Fallback to console
            self.backend_class = ConsoleBackend
            self.backend_instance = ConsoleBackend()
            logger.info("Fallback to console email backend")
    
    def send_messages(self, email_messages):
        """Send messages using the configured backend."""
        if not self.backend_instance:
            logger.error("No email backend available")
            return 0
        
        try:
            return self.backend_instance.send_messages(email_messages)
        except Exception as e:
            logger.error(f"Email backend failed: {e}")
            # Try console backend as last resort
            try:
                console_backend = ConsoleBackend()
                result = console_backend.send_messages(email_messages)
                logger.info(f"Fallback console backend sent {result} messages")
                return result
            except Exception as fallback_error:
                logger.error(f"Even console backend failed: {fallback_error}")
                return 0
    
    def open(self):
        """Open connection if supported by backend."""
        if hasattr(self.backend_instance, 'open'):
            return self.backend_instance.open()
        return True
    
    def close(self):
        """Close connection if supported by backend."""
        if hasattr(self.backend_instance, 'close'):
            self.backend_instance.close()