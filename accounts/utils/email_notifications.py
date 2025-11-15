"""
Email notifications for Veyu platform.
Uses the simple_mail system for reliable email delivery.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from django.contrib.auth import get_user_model
from django.conf import settings
from utils.simple_mail import send_template_email, send_simple_email

logger = logging.getLogger(__name__)

User = get_user_model()


def send_verification_email(user, verification_code: str) -> bool:
    """Send email verification code to user using unified template."""
    subject = "Verify Your Email - Veyu"
    context = {
        "name": user.first_name or user.email,
        "user_name": user.first_name or 'there',
        "email": user.email,
        "verification_code": verification_code,
        "otp": verification_code,  # Support both variable names
        "validity_minutes": 30,  # Default validity
        "purpose": "signup",  # Distinguish from login verification
        "support_email": getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@veyu.cc'),
        "app_name": "Veyu"
    }
    
    try:
        success = send_template_email(
            subject=subject,
            recipients=[user.email],
            template_name='verification_email.html',
            context=context
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
        success = send_template_email(
            subject=subject,
            recipients=[user.email],
            template_name='welcome_email.html',
            context=context
        )
        
        if success:
            logger.info(f"Welcome email sent successfully to {user.email}")
        
        return success
        
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
    subject = "Reset Your Veyu Password"
    context = {
        "user": user,
        "user_name": user.first_name or 'there',
        "user_email": user.email,
        "reset_url": reset_url,
        "reset_link": reset_url,  # Backward compatibility
        "current_year": datetime.now().year,
        "site_name": "Veyu",
        "site_url": getattr(settings, 'FRONTEND_URL', 'https://veyu.cc'),
        "support_email": getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@veyu.cc'),
        "app_name": "Veyu"
    }
    
    try:
        success = send_template_email(
            subject=subject,
            recipients=[user.email],
            template_name='password_reset.html',
            context=context
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
    """Send OTP code to user's email using unified verification template."""
    subject = "Verify Your Email - Veyu"  # Unified subject line
    context = {
        "otp": otp_code,
        "verification_code": otp_code,  # Support both variable names
        "name": user.first_name or user.email,
        "user_name": user.first_name or 'there',
        "email": user.email,
        "validity_minutes": validity_minutes,
        "purpose": "login",  # Distinguish from signup verification
        "support_email": getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@veyu.cc'),
        "app_name": "Veyu"
    }
    
    try:
        success = send_template_email(
            subject=subject,
            recipients=[user.email],
            template_name='verification_email.html',  # Use unified template
            context=context
        )
        
        if success:
            logger.info(f"OTP email sent successfully to {user.email}")
        
        return success
        
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
        'verified': 'Approved',
        'rejected': 'Rejected'
    }
    
    status_display = status_messages.get(status.lower(), status.title())
    
    if status.lower() in ['approved', 'verified']:
        subject = f"Business Verification Approved - {business_name or 'Your Business'}"
    elif status.lower() == 'rejected':
        subject = f"Business Verification Update - {business_name or 'Your Business'}"
    else:
        subject = f"Business Verification {status_display} - {business_name or 'Your Business'}"
    
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
        success = send_template_email(
            subject=subject,
            recipients=[user.email],
            template_name='business_verification_status.html',
            context=context
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
    
    try:
        success = send_template_email(
            subject=subject,
            recipients=[user.email],
            template_name='new_booking.html',
            context=context
        )
        
        if success:
            logger.info(f"Booking confirmation email sent to {user.email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to send booking confirmation email to {user.email}: {str(e)}", exc_info=True)
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
    
    try:
        success = send_template_email(
            subject=subject,
            recipients=[user.email],
            template_name='inspection_scheduled.html',
            context=context
        )
        
        if success:
            logger.info(f"Inspection scheduled email sent to {user.email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to send inspection scheduled email to {user.email}: {str(e)}", exc_info=True)
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
    
    try:
        success = send_template_email(
            subject=subject,
            recipients=[user.email],
            template_name='order_confirmation.html',
            context=context
        )
        
        if success:
            logger.info(f"Order confirmation email sent to {user.email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to send order confirmation email to {user.email}: {str(e)}", exc_info=True)
        return False


def send_listing_published(user, listing_details: Dict[str, Any]) -> bool:
    """Send notification when listing is published."""
    subject = f"Your Listing is Now Live - {listing_details.get('title', '')}"
    context = {
        "user_name": user.first_name or 'there',
        **listing_details,
        "support_email": settings.DEFAULT_FROM_EMAIL,
        "app_name": "Veyu",
        "frontend_url": getattr(settings, 'FRONTEND_URL', 'https://veyu.cc')
    }
    
    try:
        success = send_template_email(
            subject=subject,
            recipients=[user.email],
            template_name='listing_published.html',
            context=context
        )
        
        if success:
            logger.info(f"Listing published email sent to {user.email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to send listing published email to {user.email}: {str(e)}", exc_info=True)
        return False


def send_purchase_confirmation(user, purchase_details: Dict[str, Any]) -> bool:
    """Send purchase confirmation email."""
    subject = f"Purchase Confirmation - {purchase_details.get('order_number', '')}"
    context = {
        "user_name": user.first_name or 'there',
        **purchase_details,
        "support_email": settings.DEFAULT_FROM_EMAIL,
        "app_name": "Veyu"
    }
    
    try:
        success = send_template_email(
            subject=subject,
            recipients=[user.email],
            template_name='purchase_confirmation.html',
            context=context
        )
        
        if success:
            logger.info(f"Purchase confirmation email sent to {user.email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to send purchase confirmation email to {user.email}: {str(e)}", exc_info=True)
        return False


def send_wallet_transaction(user, transaction_details: Dict[str, Any]) -> bool:
    """Send wallet transaction notification."""
    subject = f"Wallet Transaction - {transaction_details.get('transaction_type', 'Update')}"
    context = {
        "user_name": user.first_name or 'there',
        **transaction_details,
        "support_email": settings.DEFAULT_FROM_EMAIL,
        "app_name": "Veyu"
    }
    
    try:
        success = send_template_email(
            subject=subject,
            recipients=[user.email],
            template_name='wallet_transaction.html',
            context=context
        )
        
        if success:
            logger.info(f"Wallet transaction email sent to {user.email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to send wallet transaction email to {user.email}: {str(e)}", exc_info=True)
        return False


def send_security_alert(user, alert_details: Dict[str, Any]) -> bool:
    """Send security alert email."""
    subject = "Security Alert - Veyu Account"
    context = {
        "user_name": user.first_name or 'there',
        **alert_details,
        "support_email": settings.DEFAULT_FROM_EMAIL,
        "app_name": "Veyu"
    }
    
    try:
        success = send_template_email(
            subject=subject,
            recipients=[user.email],
            template_name='security_email.html',
            context=context
        )
        
        if success:
            logger.info(f"Security alert email sent to {user.email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to send security alert email to {user.email}: {str(e)}", exc_info=True)
        return False


def send_rental_confirmation(user, rental_details: Dict[str, Any]) -> bool:
    """Send rental confirmation email."""
    subject = f"Rental Confirmation - {rental_details.get('rental_reference', '')}"
    context = {
        "user_name": user.first_name or 'there',
        **rental_details,
        "support_email": settings.DEFAULT_FROM_EMAIL,
        "app_name": "Veyu"
    }
    
    try:
        success = send_template_email(
            subject=subject,
            recipients=[user.email],
            template_name='new_rental.html',
            context=context
        )
        
        if success:
            logger.info(f"Rental confirmation email sent to {user.email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to send rental confirmation email to {user.email}: {str(e)}", exc_info=True)
        return False


def send_promotion_email(user, promotion_details: Dict[str, Any]) -> bool:
    """Send promotional email."""
    subject = promotion_details.get('subject', 'Special Offer from Veyu')
    context = {
        "user_name": user.first_name or 'there',
        **promotion_details,
        "support_email": settings.DEFAULT_FROM_EMAIL,
        "app_name": "Veyu"
    }
    
    try:
        success = send_template_email(
            subject=subject,
            recipients=[user.email],
            template_name='promotion.html',
            context=context
        )
        
        if success:
            logger.info(f"Promotion email sent to {user.email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to send promotion email to {user.email}: {str(e)}", exc_info=True)
        return False


def send_reminder_email(user, reminder_details: Dict[str, Any]) -> bool:
    """Send reminder email."""
    subject = reminder_details.get('subject', 'Reminder from Veyu')
    context = {
        "user_name": user.first_name or 'there',
        **reminder_details,
        "support_email": settings.DEFAULT_FROM_EMAIL,
        "app_name": "Veyu"
    }
    
    try:
        success = send_template_email(
            subject=subject,
            recipients=[user.email],
            template_name='reminder.html',
            context=context
        )
        
        if success:
            logger.info(f"Reminder email sent to {user.email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to send reminder email to {user.email}: {str(e)}", exc_info=True)
        return False
