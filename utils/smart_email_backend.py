"""
Smart email backend that automatically chooses the best available option.
"""
import socket
import logging
from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from django.core.mail.backends.console import EmailBackend as ConsoleBackend

logger = logging.getLogger('utils.mail')


class SmartEmailBackend:
    """
    Smart email backend that automatically detects what works and uses it.
    
    Priority order:
    1. Gmail SMTP (if accessible)
    2. Console backend (fallback)
    """
    
    def __init__(self, *args, **kwargs):
        self.backend = None
        self.backend_type = None
        self._detect_best_backend()
    
    def _detect_best_backend(self):
        """Detect and initialize the best available email backend."""
        
        # Test Gmail SMTP connectivity
        if self._test_gmail_smtp():
            logger.info("Gmail SMTP is accessible - using SMTP backend")
            self.backend = SMTPBackend()
            self.backend_type = 'smtp'
            return
        
        # Fall back to console backend
        logger.warning("Gmail SMTP not accessible - falling back to console backend")
        self.backend = ConsoleBackend()
        self.backend_type = 'console'
    
    def _test_gmail_smtp(self):
        """Test if Gmail SMTP is accessible."""
        try:
            host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
            port = getattr(settings, 'EMAIL_PORT', 587)
            
            # Quick connectivity test
            sock = socket.create_connection((host, port), timeout=5)
            sock.close()
            
            logger.debug(f"Gmail SMTP connectivity test passed: {host}:{port}")
            return True
            
        except (socket.timeout, socket.error, OSError) as e:
            logger.debug(f"Gmail SMTP connectivity test failed: {e}")
            return False
        except Exception as e:
            logger.debug(f"Unexpected error testing Gmail SMTP: {e}")
            return False
    
    def send_messages(self, email_messages):
        """Send messages using the detected backend."""
        if not self.backend:
            logger.error("No email backend available")
            return 0
        
        try:
            result = self.backend.send_messages(email_messages)
            
            if self.backend_type == 'smtp':
                logger.info(f"Successfully sent {result} emails via Gmail SMTP")
            else:
                logger.info(f"Successfully logged {result} emails to console (SMTP not available)")
            
            return result
            
        except Exception as e:
            logger.error(f"Email backend ({self.backend_type}) failed: {e}")
            
            # If SMTP failed, try console as last resort
            if self.backend_type == 'smtp':
                logger.info("SMTP failed, trying console backend as fallback")
                try:
                    console_backend = ConsoleBackend()
                    result = console_backend.send_messages(email_messages)
                    logger.info(f"Fallback console backend processed {result} emails")
                    return result
                except Exception as fallback_error:
                    logger.error(f"Even console backend failed: {fallback_error}")
            
            return 0
    
    def open(self):
        """Open connection if supported by backend."""
        if hasattr(self.backend, 'open'):
            return self.backend.open()
        return True
    
    def close(self):
        """Close connection if supported by backend."""
        if hasattr(self.backend, 'close'):
            self.backend.close()


# For backwards compatibility
class AutoDetectEmailBackend(SmartEmailBackend):
    """Alias for SmartEmailBackend."""
    pass