import logging
import os
import time
from functools import wraps
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from django.core.mail import EmailMessage, EmailMultiAlternatives, BadHeaderError, get_connection
from django.template.loader import render_to_string
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger('utils.mail')

# Ensure the email directory exists
if hasattr(settings, 'EMAIL_FILE_PATH'):
    os.makedirs(settings.EMAIL_FILE_PATH, exist_ok=True)

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
    fail_silently: bool = False,
    **kwargs
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
        logger.debug(f"Preparing email to {recipients} with subject: {subject}")
        
        # If template is provided, render it
        if template:
            try:
                template_path = str(settings.BASE_DIR / template)
                logger.debug(f"Rendering template: {template_path}")
                html_message = render_to_string(template_path, context or {})
                message = message or ""  # Fallback empty message if none provided
            except Exception as e:
                error_msg = f"Error rendering email template {template}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                if not fail_silently:
                    raise ValueError(error_msg) from e
                return False
        else:
            html_message = None
        
        # Get email backend from kwargs or use default
        connection = kwargs.get('connection', None)
        
        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=message or "",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
            connection=connection,
            **{k: v for k, v in kwargs.items() if k not in ['connection']}
        )
        
        if html_message:
            email.attach_alternative(html_message, "text/html")
        
        # Log email details
        email_id = f"{int(time.time())}_{recipients[0]}"
        logger.debug(f"[Email {email_id}] Sending email to {recipients}")
        
        # Send email with retry logic
        result = _send_email_with_retry(email, fail_silently)
        
        if result:
            logger.info(f"[Email {email_id}] Successfully sent to {recipients}")
            
            # If using file backend, log the file location
            if hasattr(settings, 'EMAIL_FILE_PATH') and settings.EMAIL_BACKEND.endswith('filebased.EmailBackend'):
                email_files = [f for f in os.listdir(settings.EMAIL_FILE_PATH) 
                             if f.endswith('.log') or f.endswith('.eml')]
                if email_files:
                    latest_email = max(email_files, 
                                     key=lambda f: os.path.getmtime(os.path.join(settings.EMAIL_FILE_PATH, f)))
                    logger.debug(f"[Email {email_id}] Saved to {os.path.join(settings.EMAIL_FILE_PATH, latest_email)}")
        
        return result
        
    except Exception as e:
        error_msg = f"Failed to prepare email: {str(e)}"
        logger.error(error_msg)
        if not fail_silently:
            if isinstance(e, (BadHeaderError, ImproperlyConfigured)):
                raise
            raise Exception(error_msg) from e
        return False

def _send_email_with_retry(email: EmailMultiAlternatives, fail_silently: bool, max_retries: int = 3, delay: int = 1) -> bool:
    """Internal function to send email with retry logic."""
    last_exception = None
    
    for attempt in range(1, max_retries + 1):
        try:
            email.send(fail_silently=False)
            logger.debug(f"Email sent successfully to {email.to} (attempt {attempt}/{max_retries})")
            return True
            
        except Exception as e:
            last_exception = e
            error_msg = f"Attempt {attempt}/{max_retries} failed to send email to {email.to}: {str(e)}"
            logger.warning(error_msg)
            
            if attempt < max_retries:
                sleep_time = delay * (2 ** (attempt - 1))  # Exponential backoff
                logger.debug(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
    
    # If we get here, all retries failed
    error_msg = f"Failed to send email to {email.to} after {max_retries} attempts. Last error: {str(last_exception)}"
    logger.error(error_msg, exc_info=True)
    
    if not fail_silently and last_exception:
        raise last_exception from None
        
    return False








