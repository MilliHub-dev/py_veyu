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

def test_email_connection() -> Dict[str, Any]:
    """
    Test email connection with current settings and return detailed results.
    """
    result = {
        'success': False,
        'backend': getattr(settings, 'EMAIL_BACKEND', 'Not configured'),
        'message': '',
        'connection_time': 0,
        'error': None
    }
    
    try:
        if 'smtp' not in result['backend'].lower():
            result['message'] = f"Not using SMTP backend: {result['backend']}"
            result['success'] = True
            return result
        
        # Test SMTP connection with timeout
        import smtplib
        import socket
        
        host = getattr(settings, 'EMAIL_HOST', '')
        port = getattr(settings, 'EMAIL_PORT', 587)
        timeout = getattr(settings, 'EMAIL_TIMEOUT', 15)
        use_tls = getattr(settings, 'EMAIL_USE_TLS', False)
        use_ssl = getattr(settings, 'EMAIL_USE_SSL', False)
        username = getattr(settings, 'EMAIL_HOST_USER', '')
        password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        
        if not host:
            result['error'] = 'EMAIL_HOST not configured'
            return result
        
        start_time = time.time()
        
        try:
            # Create SSL context with more lenient certificate verification
            import ssl
            context = ssl.create_default_context()
            
            # For SendGrid and other providers with certificate issues
            if 'sendgrid' in host.lower():
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            
            if use_ssl:
                smtp = smtplib.SMTP_SSL(host, port, timeout=timeout, context=context)
            else:
                smtp = smtplib.SMTP(host, port, timeout=timeout)
            
            if use_tls and not use_ssl:
                smtp.starttls(context=context)
            
            if username and password:
                smtp.login(username, password)
            
            smtp.quit()
            
            result['connection_time'] = time.time() - start_time
            result['success'] = True
            result['message'] = f"SMTP connection successful in {result['connection_time']:.2f}s"
            
        except socket.timeout:
            result['error'] = f"Connection timeout after {timeout}s"
        except smtplib.SMTPAuthenticationError as e:
            result['error'] = f"Authentication failed: {str(e)}"
        except smtplib.SMTPConnectError as e:
            result['error'] = f"Connection failed: {str(e)}"
        except Exception as e:
            result['error'] = f"SMTP error: {str(e)}"
        
        logger.info(f"Email connection test: {'SUCCESS' if result['success'] else 'FAILED'} - {result.get('message', result.get('error', ''))}")
        return result
        
    except Exception as e:
        logger.error(f"Error testing email connection: {str(e)}", exc_info=True)
        result['error'] = f"Test error: {str(e)}"
        return result

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
    Send an email with optional HTML template and enhanced error handling.
    
    Args:
        subject: Email subject
        recipients: List of recipient email addresses
        message: Plain text message (optional if template is provided)
        template: Template name (will be resolved automatically)
        context: Context variables for the template
        fail_silently: If True, exceptions will be caught and logged but not raised
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not recipients:
        logger.warning("No recipients provided for email")
        return False
        
    context = context or {}
    html_message = None
    
    try:
        logger.debug(f"Preparing email to {recipients} with subject: {subject}")
        
        # If template is provided, render it with enhanced template resolution
        if template:
            html_message, fallback_message = _render_email_template(template, context)
            # Use fallback message if no plain text message provided
            if not message:
                message = fallback_message
        
        # Ensure we have some message content
        if not message and not html_message:
            message = "This is a notification from Veyu."
            logger.warning("No message content provided, using default message")
        
        # Get email backend from kwargs or use default
        connection = kwargs.get('connection', None)
        
        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=message or "",
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@veyu.cc'),
            to=recipients,
            connection=connection,
            **{k: v for k, v in kwargs.items() if k not in ['connection']}
        )
        
        if html_message:
            email.attach_alternative(html_message, "text/html")
        
        # Log email details
        email_id = f"{int(time.time())}_{recipients[0].split('@')[0]}"
        logger.debug(f"[Email {email_id}] Sending email to {recipients}")
        
        # Send email with retry logic
        result = _send_email_with_retry(email, fail_silently)
        
        if result:
            logger.info(f"[Email {email_id}] Successfully sent to {recipients}")
            
            # If using file backend, log the file location
            if hasattr(settings, 'EMAIL_FILE_PATH') and settings.EMAIL_BACKEND.endswith('filebased.EmailBackend'):
                try:
                    email_files = [f for f in os.listdir(settings.EMAIL_FILE_PATH) 
                                 if f.endswith('.log') or f.endswith('.eml')]
                    if email_files:
                        latest_email = max(email_files, 
                                         key=lambda f: os.path.getmtime(os.path.join(settings.EMAIL_FILE_PATH, f)))
                        logger.debug(f"[Email {email_id}] Saved to {os.path.join(settings.EMAIL_FILE_PATH, latest_email)}")
                except Exception as e:
                    logger.debug(f"Could not log email file location: {str(e)}")
        
        return result
        
    except Exception as e:
        error_msg = f"Failed to prepare email: {str(e)}"
        logger.error(error_msg, exc_info=True)
        if not fail_silently:
            if isinstance(e, (BadHeaderError, ImproperlyConfigured)):
                raise
            raise Exception(error_msg) from e
        return False

def _render_email_template(template_name: str, context: Dict[str, Any]) -> tuple[str, str]:
    """
    Render email template with fallback handling.
    Returns tuple of (html_content, plain_text_content)
    """
    from django.template import TemplateDoesNotExist
    from django.template.loader import get_template
    
    html_content = ""
    plain_text_content = ""
    
    # Possible template locations
    possible_paths = [
        template_name,  # Direct path
        f'utils/templates/{template_name}',  # Utils templates
        f'templates/{template_name}',  # Root templates
        f'emails/{template_name}',  # Email specific folder
    ]
    
    # Try to find and render the template
    template_found = False
    for path in possible_paths:
        try:
            get_template(path)
            html_content = render_to_string(path, context)
            # Create plain text version by stripping HTML tags
            from django.utils.html import strip_tags
            plain_text_content = strip_tags(html_content)
            logger.debug(f"Successfully rendered template: {path}")
            template_found = True
            break
        except TemplateDoesNotExist:
            continue
        except Exception as e:
            logger.warning(f"Error rendering template {path}: {str(e)}")
            continue
    
    # If no template found, create fallback content
    if not template_found:
        logger.warning(f"Template {template_name} not found in any location, using fallback")
        plain_text_content = _create_fallback_content(template_name, context)
    
    return html_content, plain_text_content

def _create_fallback_content(template_name: str, context: Dict[str, Any]) -> str:
    """Create fallback plain text content when template rendering fails."""
    app_name = context.get('app_name', 'Veyu')
    
    if 'verification' in template_name:
        return f"""
Hello {context.get('name', 'there')},

Your verification code for {app_name} is: {context.get('verification_code', 'N/A')}

This code will expire in 30 minutes.

If you didn't request this, please ignore this email.

Best regards,
The {app_name} Team
        """.strip()
    
    elif 'welcome' in template_name:
        return f"""
Welcome to {app_name}, {context.get('user_name', 'there')}!

We're excited to have you join our community. Start exploring our platform to discover amazing vehicles and services.

Best regards,
The {app_name} Team
        """.strip()
    
    elif 'password_reset' in template_name:
        return f"""
Hello {context.get('user_name', 'there')},

We received a request to reset your password for {app_name}.

Reset link: {context.get('reset_link', 'N/A')}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
The {app_name} Team
        """.strip()
    
    elif 'otp' in template_name:
        return f"""
Your verification code for {app_name} is: {context.get('otp', 'N/A')}

This code is valid for {context.get('validity_minutes', 30)} minutes.

Do not share this code with anyone.

Best regards,
The {app_name} Team
        """.strip()
    
    else:
        return f"""
Hello,

This is a notification from {app_name}.

Best regards,
The {app_name} Team
        """.strip()

def _send_email_with_retry(email: EmailMultiAlternatives, fail_silently: bool, max_retries: int = 3, delay: int = 1) -> bool:
    """Internal function to send email with retry logic and comprehensive logging."""
    import socket
    import ssl
    from smtplib import SMTPException, SMTPServerDisconnected
    
    last_exception = None
    email_id = f"{int(time.time())}_{email.to[0].split('@')[0] if email.to else 'unknown'}"
    
    logger.info(f"[Email {email_id}] Starting email delivery to {email.to} (max {max_retries} attempts)")
    
    for attempt in range(1, max_retries + 1):
        try:
            # Create a fresh connection for each attempt to avoid connection reuse issues
            if hasattr(email, 'connection') and email.connection:
                try:
                    email.connection.close()
                except:
                    pass
                email.connection = None
            
            start_time = time.time()
            email.send(fail_silently=False)
            delivery_time = time.time() - start_time
            
            logger.info(f"[Email {email_id}] Successfully delivered on attempt {attempt}/{max_retries} "
                       f"in {delivery_time:.2f}s to {email.to}")
            
            # Log delivery status for monitoring
            _log_email_delivery_status(email_id, email.to[0], 'delivered', attempt, delivery_time)
            return True
            
        except (socket.timeout, TimeoutError) as e:
            last_exception = e
            error_msg = f"TimeoutError: timed out"
            
            if attempt < max_retries:
                sleep_time = delay * (2 ** (attempt - 1))  # Exponential backoff
                logger.warning(f"[Email {email_id}] Attempt {attempt}/{max_retries} failed: {error_msg}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                logger.error(f"[Email {email_id}] Attempt {attempt}/{max_retries} failed: {error_msg}")
                # Try fallback backend on final timeout
                if _try_fallback_email(email, email_id):
                    return True
                    
        except ssl.SSLError as e:
            last_exception = e
            error_msg = f"SSLCertVerificationError: {str(e)}"
            
            if attempt < max_retries:
                sleep_time = delay * (2 ** (attempt - 1))  # Exponential backoff
                logger.warning(f"[Email {email_id}] Attempt {attempt}/{max_retries} failed: {error_msg}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                logger.error(f"[Email {email_id}] Attempt {attempt}/{max_retries} failed: {error_msg}")
                # Try fallback backend on SSL failure
                if _try_fallback_email(email, email_id):
                    return True
                    
        except SMTPServerDisconnected as e:
            last_exception = e
            error_msg = f"SMTPServerDisconnected: {str(e) if str(e) else 'Server not connected'}"
            
            if attempt < max_retries:
                sleep_time = delay * (2 ** (attempt - 1))  # Exponential backoff
                logger.warning(f"[Email {email_id}] Attempt {attempt}/{max_retries} failed: {error_msg}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                logger.error(f"[Email {email_id}] Attempt {attempt}/{max_retries} failed: {error_msg}")
                # Try fallback backend on disconnection
                if _try_fallback_email(email, email_id):
                    return True
                    
        except SMTPException as e:
            last_exception = e
            error_type = type(e).__name__
            error_msg = f"{error_type}: {str(e)}"
            
            if attempt < max_retries:
                sleep_time = delay * (2 ** (attempt - 1))  # Exponential backoff
                logger.warning(f"[Email {email_id}] Attempt {attempt}/{max_retries} failed: {error_msg}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                logger.error(f"[Email {email_id}] Attempt {attempt}/{max_retries} failed: {error_msg}")
                # Try fallback backend on final SMTP failure
                if _try_fallback_email(email, email_id):
                    return True
                    
        except OSError as e:
            last_exception = e
            if e.errno == 101:  # Network is unreachable
                error_msg = f"OSError: [Errno 101] Network is unreachable"
                logger.error(f"[Email {email_id}] Network unreachable - attempting fallback immediately")
                # Don't retry network unreachable errors, go straight to fallback
                if _try_fallback_email(email, email_id):
                    return True
                break  # Exit retry loop for network errors
            else:
                error_msg = f"OSError: {str(e)}"
                
            if attempt < max_retries:
                sleep_time = delay * (2 ** (attempt - 1))  # Exponential backoff
                logger.warning(f"[Email {email_id}] Attempt {attempt}/{max_retries} failed: {error_msg}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                logger.error(f"[Email {email_id}] Attempt {attempt}/{max_retries} failed: {error_msg}")
                
        except Exception as e:
            last_exception = e
            error_type = type(e).__name__
            error_msg = f"{error_type}: {str(e)}"
            
            if attempt < max_retries:
                sleep_time = delay * (2 ** (attempt - 1))  # Exponential backoff
                logger.warning(f"[Email {email_id}] Attempt {attempt}/{max_retries} failed: {error_msg}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                logger.error(f"[Email {email_id}] Attempt {attempt}/{max_retries} failed: {error_msg}")
    
    # If we get here, all retries failed
    final_error = f"[Email {email_id}] All {max_retries} delivery attempts failed. Last error: {str(last_exception)}"
    logger.error(final_error)
    
    # Log failed delivery for monitoring
    _log_email_delivery_status(email_id, email.to[0] if email.to else 'unknown', 'failed', max_retries, 0, str(last_exception))
    
    # Queue for retry if configured
    if hasattr(settings, 'EMAIL_RETRY_QUEUE_ENABLED') and settings.EMAIL_RETRY_QUEUE_ENABLED:
        _queue_failed_email(email, last_exception)
    
    if not fail_silently and last_exception:
        raise last_exception from None
        
    return False

def _try_fallback_email(email: EmailMultiAlternatives, email_id: str) -> bool:
    """Try to send email using fallback backend when primary fails."""
    try:
        # Check if fallback is enabled
        if not getattr(settings, 'EMAIL_FALLBACK_ENABLED', True):
            logger.debug(f"[Email {email_id}] Fallback email disabled")
            return False
            
        fallback_backend = getattr(settings, 'EMAIL_FALLBACK_BACKEND', 'django.core.mail.backends.console.EmailBackend')
        
        logger.info(f"[Email {email_id}] Attempting fallback delivery using {fallback_backend}")
        
        # Create new connection with fallback backend
        from django.core.mail import get_connection
        fallback_connection = get_connection(backend=fallback_backend)
        
        # Create new email with fallback connection
        fallback_email = EmailMultiAlternatives(
            subject=email.subject,
            body=email.body,
            from_email=email.from_email,
            to=email.to,
            cc=email.cc,
            bcc=email.bcc,
            connection=fallback_connection,
            headers=email.extra_headers
        )
        
        # Copy alternatives (HTML content)
        for content, mimetype in email.alternatives:
            fallback_email.attach_alternative(content, mimetype)
        
        # Copy attachments
        for attachment in email.attachments:
            fallback_email.attach(attachment)
        
        # Send using fallback
        start_time = time.time()
        fallback_email.send(fail_silently=False)
        delivery_time = time.time() - start_time
        
        logger.info(f"[Email {email_id}] Successfully delivered via fallback in {delivery_time:.2f}s")
        _log_email_delivery_status(email_id, email.to[0], 'delivered_fallback', 1, delivery_time)
        
        return True
        
    except Exception as e:
        logger.error(f"[Email {email_id}] Fallback delivery also failed: {str(e)}", exc_info=True)
        return False

def _log_email_delivery_status(email_id: str, recipient: str, status: str, attempts: int, 
                              delivery_time: float = 0, error_message: str = None):
    """Log email delivery status for monitoring and analytics."""
    log_data = {
        'email_id': email_id,
        'recipient': recipient,
        'status': status,
        'attempts': attempts,
        'delivery_time': delivery_time,
        'timestamp': time.time()
    }
    
    if error_message:
        log_data['error'] = error_message
    
    # Log to dedicated email logger
    email_logger = logging.getLogger('utils.mail.delivery')
    email_logger.info(f"Email delivery status: {log_data}")

def _queue_failed_email(email: EmailMultiAlternatives, exception: Exception):
    """Queue failed email for later retry."""
    try:
        import json
        from django.core.serializers.json import DjangoJSONEncoder
        
        # Create email queue directory if it doesn't exist
        queue_dir = getattr(settings, 'EMAIL_QUEUE_DIR', os.path.join(settings.BASE_DIR, 'email_queue'))
        os.makedirs(queue_dir, exist_ok=True)
        
        # Serialize email data
        email_data = {
            'subject': email.subject,
            'body': email.body,
            'from_email': email.from_email,
            'to': email.to,
            'cc': email.cc,
            'bcc': email.bcc,
            'attachments': [],  # We'll skip attachments for now
            'alternatives': [(alt[0], alt[1]) for alt in email.alternatives],
            'headers': dict(email.extra_headers),
            'failed_at': time.time(),
            'error': str(exception),
            'retry_count': 0
        }
        
        # Save to queue file
        queue_file = os.path.join(queue_dir, f"email_{int(time.time())}_{email.to[0].split('@')[0]}.json")
        with open(queue_file, 'w') as f:
            json.dump(email_data, f, cls=DjangoJSONEncoder, indent=2)
        
        logger.info(f"Queued failed email for later retry: {queue_file}")
        
    except Exception as e:
        logger.error(f"Failed to queue email for retry: {str(e)}", exc_info=True)

def process_email_queue(max_retry_count: int = 5) -> Dict[str, int]:
    """
    Process queued emails and attempt to send them.
    
    Args:
        max_retry_count: Maximum number of retry attempts for queued emails
        
    Returns:
        Dict with processing statistics
    """
    import json
    import glob
    
    stats = {'processed': 0, 'sent': 0, 'failed': 0, 'skipped': 0}
    
    try:
        queue_dir = getattr(settings, 'EMAIL_QUEUE_DIR', os.path.join(settings.BASE_DIR, 'email_queue'))
        
        if not os.path.exists(queue_dir):
            logger.debug("Email queue directory does not exist")
            return stats
        
        # Get all queued email files
        queue_files = glob.glob(os.path.join(queue_dir, "email_*.json"))
        
        if not queue_files:
            logger.debug("No queued emails found")
            return stats
        
        logger.info(f"Processing {len(queue_files)} queued emails")
        
        for queue_file in queue_files:
            stats['processed'] += 1
            
            try:
                with open(queue_file, 'r') as f:
                    email_data = json.load(f)
                
                # Check retry count
                retry_count = email_data.get('retry_count', 0)
                if retry_count >= max_retry_count:
                    logger.warning(f"Skipping email {queue_file}: max retry count reached ({retry_count})")
                    stats['skipped'] += 1
                    continue
                
                # Recreate email message
                email = EmailMultiAlternatives(
                    subject=email_data['subject'],
                    body=email_data['body'],
                    from_email=email_data['from_email'],
                    to=email_data['to'],
                    cc=email_data.get('cc', []),
                    bcc=email_data.get('bcc', []),
                    headers=email_data.get('headers', {})
                )
                
                # Add alternatives (HTML content)
                for content, mimetype in email_data.get('alternatives', []):
                    email.attach_alternative(content, mimetype)
                
                # Try to send
                if _send_email_with_retry(email, fail_silently=True, max_retries=2):
                    # Success - remove from queue
                    os.remove(queue_file)
                    stats['sent'] += 1
                    logger.info(f"Successfully sent queued email: {queue_file}")
                else:
                    # Failed - update retry count
                    email_data['retry_count'] = retry_count + 1
                    email_data['last_retry_at'] = time.time()
                    
                    with open(queue_file, 'w') as f:
                        json.dump(email_data, f, indent=2)
                    
                    stats['failed'] += 1
                    logger.warning(f"Failed to send queued email: {queue_file} (retry {retry_count + 1})")
                
            except Exception as e:
                logger.error(f"Error processing queued email {queue_file}: {str(e)}", exc_info=True)
                stats['failed'] += 1
        
        logger.info(f"Email queue processing complete: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error processing email queue: {str(e)}", exc_info=True)
        return stats

def get_email_queue_status() -> Dict[str, Any]:
    """Get status of the email queue."""
    import json
    import glob
    
    try:
        queue_dir = getattr(settings, 'EMAIL_QUEUE_DIR', os.path.join(settings.BASE_DIR, 'email_queue'))
        
        if not os.path.exists(queue_dir):
            return {'total': 0, 'by_retry_count': {}, 'oldest': None, 'newest': None}
        
        queue_files = glob.glob(os.path.join(queue_dir, "email_*.json"))
        
        if not queue_files:
            return {'total': 0, 'by_retry_count': {}, 'oldest': None, 'newest': None}
        
        retry_counts = {}
        oldest_time = None
        newest_time = None
        
        for queue_file in queue_files:
            try:
                with open(queue_file, 'r') as f:
                    email_data = json.load(f)
                
                retry_count = email_data.get('retry_count', 0)
                retry_counts[retry_count] = retry_counts.get(retry_count, 0) + 1
                
                failed_at = email_data.get('failed_at', 0)
                if oldest_time is None or failed_at < oldest_time:
                    oldest_time = failed_at
                if newest_time is None or failed_at > newest_time:
                    newest_time = failed_at
                    
            except Exception as e:
                logger.warning(f"Error reading queue file {queue_file}: {str(e)}")
        
        return {
            'total': len(queue_files),
            'by_retry_count': retry_counts,
            'oldest': oldest_time,
            'newest': newest_time
        }
        
    except Exception as e:
        logger.error(f"Error getting email queue status: {str(e)}", exc_info=True)
        return {'error': str(e)}

def validate_email_configuration() -> Dict[str, Any]:
    """
    Validate email configuration and return detailed status.
    
    Returns:
        Dict with validation results and recommendations
    """
    validation_result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'config': {},
        'recommendations': []
    }
    
    try:
        # Check required settings
        required_settings = [
            'EMAIL_BACKEND',
            'DEFAULT_FROM_EMAIL'
        ]
        
        for setting in required_settings:
            if hasattr(settings, setting):
                validation_result['config'][setting] = getattr(settings, setting)
            else:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Missing required setting: {setting}")
        
        # Validate email backend specific settings
        email_backend = getattr(settings, 'EMAIL_BACKEND', '')
        
        if 'smtp' in email_backend.lower():
            smtp_settings = ['EMAIL_HOST', 'EMAIL_PORT']
            for setting in smtp_settings:
                if hasattr(settings, setting):
                    validation_result['config'][setting] = getattr(settings, setting)
                else:
                    validation_result['valid'] = False
                    validation_result['errors'].append(f"Missing SMTP setting: {setting}")
            
            # Check optional SMTP settings
            optional_smtp = ['EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD', 'EMAIL_USE_TLS', 'EMAIL_USE_SSL']
            for setting in optional_smtp:
                if hasattr(settings, setting):
                    # Mask password in config display
                    if 'PASSWORD' in setting:
                        validation_result['config'][setting] = '***' if getattr(settings, setting) else None
                    else:
                        validation_result['config'][setting] = getattr(settings, setting)
        
        elif 'filebased' in email_backend.lower():
            if hasattr(settings, 'EMAIL_FILE_PATH'):
                validation_result['config']['EMAIL_FILE_PATH'] = settings.EMAIL_FILE_PATH
                # Check if directory exists and is writable
                if not os.path.exists(settings.EMAIL_FILE_PATH):
                    validation_result['warnings'].append(f"Email file path does not exist: {settings.EMAIL_FILE_PATH}")
                elif not os.access(settings.EMAIL_FILE_PATH, os.W_OK):
                    validation_result['errors'].append(f"Email file path is not writable: {settings.EMAIL_FILE_PATH}")
                    validation_result['valid'] = False
            else:
                validation_result['errors'].append("EMAIL_FILE_PATH required for filebased backend")
                validation_result['valid'] = False
        
        elif 'console' in email_backend.lower():
            validation_result['warnings'].append("Using console backend - emails will be printed to console")
        
        # Validate DEFAULT_FROM_EMAIL format
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '')
        if from_email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, from_email):
                validation_result['errors'].append(f"Invalid DEFAULT_FROM_EMAIL format: {from_email}")
                validation_result['valid'] = False
        
        # Check for common configuration issues
        if hasattr(settings, 'EMAIL_USE_TLS') and hasattr(settings, 'EMAIL_USE_SSL'):
            if settings.EMAIL_USE_TLS and settings.EMAIL_USE_SSL:
                validation_result['warnings'].append("Both EMAIL_USE_TLS and EMAIL_USE_SSL are enabled - this may cause issues")
        
        # Add recommendations
        if validation_result['valid']:
            validation_result['recommendations'].append("Configuration appears valid")
            
            if 'console' in email_backend.lower():
                validation_result['recommendations'].append("Consider using SMTP backend for production")
            
            if not hasattr(settings, 'EMAIL_TIMEOUT'):
                validation_result['recommendations'].append("Consider setting EMAIL_TIMEOUT for better error handling")
        
        logger.info(f"Email configuration validation completed: {'VALID' if validation_result['valid'] else 'INVALID'}")
        return validation_result
        
    except Exception as e:
        logger.error(f"Error validating email configuration: {str(e)}", exc_info=True)
        return {
            'valid': False,
            'errors': [f"Validation error: {str(e)}"],
            'warnings': [],
            'config': {},
            'recommendations': []
        }

def test_smtp_connection() -> Dict[str, Any]:
    """
    Test SMTP connection and return detailed results.
    
    Returns:
        Dict with connection test results
    """
    test_result = {
        'success': False,
        'message': '',
        'details': {},
        'error': None
    }
    
    try:
        email_backend = getattr(settings, 'EMAIL_BACKEND', '')
        
        if 'smtp' not in email_backend.lower():
            test_result['message'] = f"Not using SMTP backend: {email_backend}"
            test_result['success'] = True  # Not an error, just different backend
            return test_result
        
        # Get SMTP settings
        host = getattr(settings, 'EMAIL_HOST', '')
        port = getattr(settings, 'EMAIL_PORT', 587)
        username = getattr(settings, 'EMAIL_HOST_USER', '')
        password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        use_tls = getattr(settings, 'EMAIL_USE_TLS', False)
        use_ssl = getattr(settings, 'EMAIL_USE_SSL', False)
        timeout = getattr(settings, 'EMAIL_TIMEOUT', 30)
        
        if not host:
            test_result['error'] = "EMAIL_HOST not configured"
            return test_result
        
        # Test connection
        import smtplib
        import socket
        
        start_time = time.time()
        
        try:
            # Create SSL context with more lenient certificate verification
            import ssl
            context = ssl.create_default_context()
            
            # For SendGrid and other providers with certificate issues
            if 'sendgrid' in host.lower():
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            
            # Choose SMTP class based on SSL setting
            if use_ssl:
                smtp = smtplib.SMTP_SSL(host, port, timeout=timeout, context=context)
            else:
                smtp = smtplib.SMTP(host, port, timeout=timeout)
            
            # Enable TLS if configured
            if use_tls and not use_ssl:
                smtp.starttls(context=context)
            
            # Authenticate if credentials provided
            if username and password:
                smtp.login(username, password)
                test_result['details']['authenticated'] = True
            else:
                test_result['details']['authenticated'] = False
            
            # Test completed successfully
            connection_time = time.time() - start_time
            smtp.quit()
            
            test_result['success'] = True
            test_result['message'] = f"SMTP connection successful in {connection_time:.2f}s"
            test_result['details'].update({
                'host': host,
                'port': port,
                'use_tls': use_tls,
                'use_ssl': use_ssl,
                'connection_time': connection_time
            })
            
        except smtplib.SMTPAuthenticationError as e:
            test_result['error'] = f"SMTP authentication failed: {str(e)}"
        except smtplib.SMTPConnectError as e:
            test_result['error'] = f"SMTP connection failed: {str(e)}"
        except socket.timeout:
            test_result['error'] = f"SMTP connection timeout after {timeout}s"
        except Exception as e:
            test_result['error'] = f"SMTP error: {str(e)}"
        
        logger.info(f"SMTP connection test: {'SUCCESS' if test_result['success'] else 'FAILED'}")
        return test_result
        
    except Exception as e:
        logger.error(f"Error testing SMTP connection: {str(e)}", exc_info=True)
        test_result['error'] = f"Test error: {str(e)}"
        return test_result

def get_email_backend_health() -> Dict[str, Any]:
    """
    Get comprehensive email backend health status.
    
    Returns:
        Dict with health check results
    """
    health_status = {
        'healthy': True,
        'backend': getattr(settings, 'EMAIL_BACKEND', 'Not configured'),
        'configuration': {},
        'connection': {},
        'queue': {},
        'last_check': time.time(),
        'issues': []
    }
    
    try:
        # Validate configuration
        config_validation = validate_email_configuration()
        health_status['configuration'] = config_validation
        
        if not config_validation['valid']:
            health_status['healthy'] = False
            health_status['issues'].extend(config_validation['errors'])
        
        # Test connection for SMTP backends
        if 'smtp' in health_status['backend'].lower():
            connection_test = test_smtp_connection()
            health_status['connection'] = connection_test
            
            if not connection_test['success']:
                health_status['healthy'] = False
                health_status['issues'].append(f"Connection test failed: {connection_test.get('error', 'Unknown error')}")
        
        # Check email queue status
        queue_status = get_email_queue_status()
        health_status['queue'] = queue_status
        
        if queue_status.get('total', 0) > 100:  # Arbitrary threshold
            health_status['issues'].append(f"Large email queue: {queue_status['total']} emails")
        
        # Overall health assessment
        if not health_status['issues']:
            health_status['status'] = 'healthy'
        elif health_status['healthy']:
            health_status['status'] = 'warning'
        else:
            health_status['status'] = 'unhealthy'
        
        logger.info(f"Email backend health check: {health_status['status'].upper()}")
        return health_status
        
    except Exception as e:
        logger.error(f"Error checking email backend health: {str(e)}", exc_info=True)
        return {
            'healthy': False,
            'status': 'error',
            'error': str(e),
            'last_check': time.time()
        }








