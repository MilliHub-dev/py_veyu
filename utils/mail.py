import logging
import time
from functools import wraps
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from django.core.mail import EmailMessage, EmailMultiAlternatives, BadHeaderError
from django.template.loader import render_to_string
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

def retry_on_failure(max_retries=3, delay=1):
    """Decorator to retry a function call with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            last_exception = None
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    retries += 1
                    if retries < max_retries:
                        sleep_time = delay * (2 ** (retries - 1))  # Exponential backoff
                        logger.warning(
                            f"Attempt {retries} failed: {str(e)}. "
                            f"Retrying in {sleep_time} seconds..."
                        )
                        time.sleep(sleep_time)
            
            # If we've exhausted all retries, log the error and raise
            logger.error(
                f"All {max_retries} attempts failed. Last error: {str(last_exception)}"
            )
            raise last_exception
        return wrapper
    return decorator

def send_email(
    subject: str, 
    recipients: List[str], 
    message: Optional[str] = None, 
    template: Optional[Union[str, Path]] = None, 
    context: Optional[Dict[str, Any]] = None,
    fail_silently: bool = False
) -> bool:
    """
    Send an email with optional HTML template.
    
    Args:
        subject: Email subject
        recipients: List of recipient email addresses
        message: Plain text message (optional if template is provided)
        template: Path to template file (relative to settings.BASE_DIR)
        context: Context variables for the template
        fail_silently: If True, exceptions will be caught and logged but not raised
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not recipients:
        logger.warning("No recipients provided for email")
        return False
        
    context = context or {}
    
    try:
        # If template is provided, render it
        if template:
            try:
                template_path = str(settings.BASE_DIR / template)
                html_message = render_to_string(template_path, context)
                message = message or ""  # Fallback empty message if none provided
            except Exception as e:
                error_msg = f"Error rendering email template {template}: {str(e)}"
                logger.error(error_msg)
                if not fail_silently:
                    raise ValueError(error_msg)
                return False
        else:
            html_message = None
        
        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=message or "",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        
        if html_message:
            email.attach_alternative(html_message, "text/html")
        
        # Send email with retry logic
        return _send_email_with_retry(email, fail_silently)
        
    except Exception as e:
        error_msg = f"Failed to prepare email: {str(e)}"
        logger.error(error_msg)
        if not fail_silently:
            if isinstance(e, (BadHeaderError, ImproperlyConfigured)):
                raise
            raise Exception(error_msg) from e
        return False

@retry_on_failure(max_retries=3, delay=1)
def _send_email_with_retry(email: EmailMultiAlternatives, fail_silently: bool) -> bool:
    """Internal function to send email with retry logic."""
    try:
        email.send(fail_silently=False)
        logger.info(f"Email sent successfully to {email.to}")
        return True
    except Exception as e:
        error_msg = f"Failed to send email to {email.to}: {str(e)}"
        logger.error(error_msg)
        if not fail_silently:
            raise
        return False








