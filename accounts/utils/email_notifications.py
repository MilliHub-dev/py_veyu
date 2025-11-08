import logging
import os
from typing import Optional, Dict, Any, List
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string, get_template
from django.template import TemplateDoesNotExist
from django.utils.html import strip_tags
from utils.mail import send_email

# Set up logging
logger = logging.getLogger(__name__)

User = get_user_model()

def get_template_path(template_name: str) -> str:
    """
    Get the correct template path, checking multiple possible locations.
    """
    possible_paths = [
        template_name,  # Direct path
        f'utils/templates/{template_name}',  # Utils templates
        f'templates/{template_name}',  # Root templates
        f'emails/{template_name}',  # Email specific folder
    ]
    
    for path in possible_paths:
        try:
            get_template(path)
            logger.debug(f"Found template at: {path}")
            return path
        except TemplateDoesNotExist:
            continue
    
    logger.warning(f"Template {template_name} not found in any location")
    return template_name  # Return original name as fallback

def render_email_template(template_name: str, context: Dict[str, Any]) -> tuple[str, str]:
    """
    Render email template with fallback to plain text.
    Returns tuple of (html_content, plain_text_content)
    """
    html_content = ""
    plain_text_content = ""
    
    try:
        template_path = get_template_path(template_name)
        html_content = render_to_string(template_path, context)
        # Create plain text version by stripping HTML tags
        plain_text_content = strip_tags(html_content)
        logger.debug(f"Successfully rendered template: {template_name}")
    except TemplateDoesNotExist as e:
        logger.error(f"Template {template_name} not found: {str(e)}")
        # Create fallback plain text content
        plain_text_content = create_fallback_content(template_name, context)
    except Exception as e:
        logger.error(f"Error rendering template {template_name}: {str(e)}", exc_info=True)
        plain_text_content = create_fallback_content(template_name, context)
    
    return html_content, plain_text_content

def create_fallback_content(template_name: str, context: Dict[str, Any]) -> str:
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

def send_verification_email(user, verification_code: str) -> bool:
    """Send email verification code to user."""
    subject = "Verify Your Email - Veyu"
    context = {
        "name": user.first_name or user.email,
        "email": user.email,
        "verification_code": verification_code,
        "support_email": getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@veyu.cc'),
        "app_name": "Veyu"
    }
    
    try:
        # Use the enhanced send_email function with template resolution and improved error handling
        success = send_email(
            subject=subject,
            recipients=[user.email],
            template='verification_email.html',
            context=context,
            fail_silently=False
        )
        
        if success:
            logger.info(f"Verification email sent successfully to {user.email}")
        else:
            logger.warning(f"Verification email failed to send to {user.email}")
            
        return success
        
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {str(e)}", exc_info=True)
        return False

def send_welcome_email(user) -> bool:
    """Send welcome email to new user."""
    subject = f"Welcome to Veyu, {user.first_name or 'there'}!"
    frontend_url = getattr(settings, 'FRONTEND_URL', 'https://veyu.cc')
    context = {
        "user_name": user.first_name or 'there',
        "buy_link": f"{frontend_url}/buy/",
        "rent_link": f"{frontend_url}/rent/",
        "mechanic_link": f"{frontend_url}/mechanics/",
        "support_email": getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@veyu.cc'),
        "app_name": "Veyu"
    }
    
    try:
        # Use the enhanced send_email function with template resolution
        return send_email(
            subject=subject,
            recipients=[user.email],
            template='welcome_email.html',
            context=context,
            fail_silently=False
        )
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}", exc_info=True)
        return False

def send_password_reset_email(user, reset_url: str, reset_token: str = None) -> bool:
    """
    Send password reset email with secure reset link.
    
    Args:
        user: User account requesting password reset
        reset_url: Complete reset URL with token
        reset_token: Reset token (optional, for logging)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    from datetime import datetime
    
    subject = "Reset Your Veyu Password"
    context = {
        "user": user,
        "user_name": user.first_name or 'there',
        "user_email": user.email,
        "reset_url": reset_url,
        "reset_link": reset_url,  # Backward compatibility
        "current_year": datetime.now().year,
        "site_name": "Veyu",
        "site_url": getattr(settings, 'FRONTEND_URL', 'https://veyu.com.ng'),
        "support_email": getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@veyu.cc'),
        "app_name": "Veyu"
    }
    
    try:
        # Use the enhanced send_email function with template resolution
        success = send_email(
            subject=subject,
            recipients=[user.email],
            template='password_reset.html',
            context=context,
            fail_silently=False
        )
        
        if success:
            logger.info(f"Password reset email sent successfully to {user.email}")
            if reset_token:
                logger.debug(f"Reset token sent: {reset_token[:8]}...")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}", exc_info=True)
        return False

def send_otp_email(user, otp_code: str, validity_minutes: int = 30) -> bool:
    """Send OTP code to user's email."""
    subject = "Your Verification Code - Veyu"
    context = {
        "otp": otp_code,
        "validity_minutes": validity_minutes,
        "support_email": getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@veyu.cc'),
        "app_name": "Veyu"
    }
    
    try:
        # Use the enhanced send_email function with template resolution
        return send_email(
            subject=subject,
            recipients=[user.email],
            template='otp_email.html',
            context=context,
            fail_silently=False
        )
    except Exception as e:
        logger.error(f"Failed to send OTP email to {user.email}: {str(e)}", exc_info=True)
        return False

def send_business_verification_status(user, status: str, reason: str = "", business_name: str = "") -> bool:
    """
    Notify user about their business verification status.
    
    Args:
        user: User account to notify
        status: Verification status ('submitted', 'approved', 'rejected', 'pending')
        reason: Reason for rejection or additional information
        business_name: Name of the business being verified
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    status_messages = {
        'submitted': 'Submitted for Review',
        'pending': 'Under Review',
        'approved': 'Approved',
        'verified': 'Approved',  # Handle both 'approved' and 'verified'
        'rejected': 'Rejected'
    }
    
    status_display = status_messages.get(status.lower(), status.title())
    
    if status.lower() in ['approved', 'verified']:
        subject = f"Business Verification Approved - {business_name or 'Your Business'}"
    elif status.lower() == 'rejected':
        subject = f"Business Verification Update - {business_name or 'Your Business'}"
    else:
        subject = f"Business Verification {status_display} - {business_name or 'Your Business'}"
    
    # Enhanced context for template
    context = {
        'user': user,
        'user_name': user.first_name or 'there',
        'status': status.lower(),
        'status_display': status_display,
        'reason': reason,
        'business_name': business_name,
        'support_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@veyu.cc'),
        'app_name': 'Veyu',
        'frontend_url': getattr(settings, 'FRONTEND_URL', 'https://veyu.cc'),
        'dashboard_url': f"{getattr(settings, 'FRONTEND_URL', 'https://veyu.cc')}/dashboard/"
    }
    
    try:
        # Use the enhanced send_email function with template resolution
        success = send_email(
            subject=subject,
            recipients=[user.email],
            template='business_verification_status.html',
            context=context,
            fail_silently=False
        )
        
        if success:
            logger.info(f"Business verification status email sent to {user.email} - Status: {status}")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to send business verification status email to {user.email}: {str(e)}", exc_info=True)
        return False

def send_booking_confirmation(user, booking_details: Dict[str, Any]) -> bool:
    """Send booking confirmation email."""
    subject = f"Booking Confirmation - {booking_details.get('booking_reference', '')}"
    context = {
        "user_name": user.first_name or 'there',
        **booking_details,
        "support_email": settings.DEFAULT_FROM_EMAIL,
        "app_name": "Veyu"
    }
    
    # Render HTML content
    html_message = render_to_string('booking_confirmation.html', context)
    plain_message = f"Your booking has been confirmed. Reference: {booking_details.get('booking_reference', '')}"
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send booking confirmation email to {user.email}: {str(e)}")
        return False

def send_inspection_scheduled(user, inspection_details: Dict[str, Any]) -> bool:
    """Send inspection scheduled notification."""
    subject = f"Inspection Scheduled - {inspection_details.get('inspection_reference', '')}"
    context = {
        "user_name": user.first_name or 'there',
        **inspection_details,
        "support_email": settings.DEFAULT_FROM_EMAIL,
        "app_name": "Veyu"
    }
    
    # Render HTML content
    html_message = render_to_string('inspection_scheduled.html', context)
    plain_message = f"Your inspection has been scheduled. Reference: {inspection_details.get('inspection_reference', '')}"
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send inspection scheduled email to {user.email}: {str(e)}")
        return False

def send_order_confirmation(user, order_details: Dict[str, Any]) -> bool:
    """Send order confirmation email."""
    subject = f"Order Confirmation - {order_details.get('order_number', '')}"
    context = {
        "user_name": user.first_name or 'there',
        **order_details,
        "support_email": settings.DEFAULT_FROM_EMAIL,
        "app_name": "Veyu"
    }
    
    # Render HTML content
    html_message = render_to_string('order_confirmation.html', context)
    plain_message = f"Thank you for your order! Order Number: {order_details.get('order_number', '')}"
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send order confirmation email to {user.email}: {str(e)}")
        return False
