"""
Simple, reliable email utility for Veyu platform.
No complex retry logic, just straightforward SMTP email sending.
"""

import logging
from typing import List, Optional
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def send_simple_email(
    subject: str,
    recipients: List[str],
    message: str = None,
    html_message: str = None,
    from_email: str = None,
    timeout: int = None
) -> bool:
    """
    Send a simple email using Django's built-in send_mail.
    
    Args:
        subject: Email subject
        recipients: List of recipient email addresses
        message: Plain text message
        html_message: HTML message (optional)
        from_email: From email address (optional, uses DEFAULT_FROM_EMAIL)
        timeout: SMTP timeout in seconds (optional, uses EMAIL_TIMEOUT from settings)
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        if not recipients:
            logger.warning("No recipients provided for email")
            return False
        
        if not message and not html_message:
            logger.warning("No message content provided")
            return False
        
        from_email = from_email or settings.DEFAULT_FROM_EMAIL
        
        # Create connection with custom timeout if provided
        from django.core.mail import get_connection
        connection = None
        if timeout:
            connection = get_connection(timeout=timeout)
        
        # Use Django's simple send_mail function
        result = send_mail(
            subject=subject,
            message=message or strip_tags(html_message),
            from_email=from_email,
            recipient_list=recipients,
            html_message=html_message,
            fail_silently=False,
            connection=connection
        )
        
        if result == 1:
            logger.info(f"Email sent successfully to {recipients}")
            return True
        else:
            logger.error(f"Email failed to send to {recipients}")
            return False
            
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return False


def send_template_email(
    subject: str,
    recipients: List[str],
    template_name: str,
    context: dict = None,
    from_email: str = None
) -> bool:
    """
    Send an email using a template.
    
    Args:
        subject: Email subject
        recipients: List of recipient email addresses
        template_name: Template file name (e.g., 'welcome_email.html')
        context: Template context variables
        from_email: From email address (optional)
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        if not recipients:
            logger.warning("No recipients provided for template email")
            return False
        
        context = context or {}
        from_email = from_email or settings.DEFAULT_FROM_EMAIL
        
        # Add default context variables including logo URL
        context.setdefault('logo_url', 'https://dev.veyu.cc/static/veyu/logo.png')
        context.setdefault('app_name', 'Veyu')
        context.setdefault('support_email', settings.DEFAULT_FROM_EMAIL)
        context.setdefault('frontend_url', getattr(settings, 'FRONTEND_URL', 'https://veyu.cc'))
        
        # Try to render the template from multiple possible locations
        template_paths = [
            template_name,  # Direct path
            f'{template_name}',  # Just the name
            f'emails/{template_name}',  # emails subfolder
        ]
        
        html_message = None
        plain_message = None
        
        for template_path in template_paths:
            try:
                html_message = render_to_string(template_path, context)
                plain_message = strip_tags(html_message)
                logger.info(f"Successfully rendered template: {template_path}")
                break
            except Exception as e:
                logger.debug(f"Template not found at {template_path}: {e}")
                continue
        
        # If no template found, use fallback
        if not html_message:
            logger.warning(f"Template {template_name} not found in any location, using fallback")
            plain_message = f"Hello,\n\nThis is a notification from Veyu.\n\nBest regards,\nThe Veyu Team"
            html_message = None
        
        return send_simple_email(
            subject=subject,
            recipients=recipients,
            message=plain_message,
            html_message=html_message,
            from_email=from_email
        )
        
    except Exception as e:
        logger.error(f"Template email send error: {e}")
        return False


def send_verification_email(email: str, verification_code: str, user_name: str = None) -> bool:
    """
    Send email verification code.
    
    Args:
        email: Recipient email address
        verification_code: Verification code
        user_name: User's name (optional)
    
    Returns:
        bool: True if email was sent successfully
    """
    subject = "Verify Your Email - Veyu"
    message = f"""
Hello {user_name or 'there'},

Your verification code for Veyu is: {verification_code}

This code will expire in 30 minutes.

If you didn't request this, please ignore this email.

Best regards,
The Veyu Team
    """.strip()
    
    return send_simple_email(
        subject=subject,
        recipients=[email],
        message=message
    )


def send_password_reset_email(email: str, reset_link: str, user_name: str = None) -> bool:
    """
    Send password reset email.
    
    Args:
        email: Recipient email address
        reset_link: Password reset link
        user_name: User's name (optional)
    
    Returns:
        bool: True if email was sent successfully
    """
    subject = "Reset Your Password - Veyu"
    message = f"""
Hello {user_name or 'there'},

We received a request to reset your password for Veyu.

Reset your password: {reset_link}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
The Veyu Team
    """.strip()
    
    return send_simple_email(
        subject=subject,
        recipients=[email],
        message=message
    )


def send_welcome_email(email: str, user_name: str = None) -> bool:
    """
    Send welcome email to new users.
    
    Args:
        email: Recipient email address
        user_name: User's name (optional)
    
    Returns:
        bool: True if email was sent successfully
    """
    subject = "Welcome to Veyu!"
    message = f"""
Welcome to Veyu, {user_name or 'there'}!

We're excited to have you join our community. Start exploring our platform to discover amazing vehicles and services.

Get started:
- Browse vehicles in our marketplace
- Find trusted mechanics near you
- Connect with other users

If you have any questions, feel free to contact our support team.

Best regards,
The Veyu Team
    """.strip()
    
    return send_simple_email(
        subject=subject,
        recipients=[email],
        message=message
    )


def test_email_connection() -> dict:
    """
    Test email connection and return results.
    
    Returns:
        dict: Test results with success status and details
    """
    try:
        # Try to send a test email to a dummy address (won't actually send)
        from django.core.mail import get_connection
        
        connection = get_connection()
        connection.open()
        connection.close()
        
        return {
            'success': True,
            'message': 'Email connection test successful',
            'backend': settings.EMAIL_BACKEND,
            'host': settings.EMAIL_HOST,
            'port': settings.EMAIL_PORT
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Email connection test failed: {str(e)}',
            'backend': settings.EMAIL_BACKEND,
            'host': settings.EMAIL_HOST,
            'port': settings.EMAIL_PORT
        }