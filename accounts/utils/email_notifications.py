from typing import Optional, Dict, Any, List
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

User = get_user_model()

def send_verification_email(user, verification_code: str) -> bool:
    """Send email verification code to user."""
    subject = "Verify Your Email - Veyu"
    context = {
        "name": user.first_name or user.email,
        "verification_code": verification_code,
        "support_email": settings.DEFAULT_FROM_EMAIL,
        "app_name": "Veyu"
    }
    
    # Render HTML content
    html_message = render_to_string('verification_email.html', context)
    plain_message = f"Your verification code is: {verification_code}"
    
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
        logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        return False

def send_welcome_email(user) -> bool:
    """Send welcome email to new user."""
    subject = f"Welcome to Veyu, {user.first_name or 'there'}!"
    context = {
        "user_name": user.first_name or 'there',
        "buy_link": f"{settings.FRONTEND_URL}/buy/",
        "rent_link": f"{settings.FRONTEND_URL}/rent/",
        "mechanic_link": f"{settings.FRONTEND_URL}/mechanics/"
    }
    
    # Render HTML content
    html_message = render_to_string('welcome_email.html', context)
    plain_message = f"Welcome to Veyu! We're excited to have you on board, {user.first_name or 'there'}!"
    
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
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False

def send_password_reset_email(user, reset_link: str) -> bool:
    """Send password reset email with reset link."""
    subject = "Password Reset Request - Veyu"
    context = {
        "user_name": user.first_name or 'there',
        "reset_link": reset_link,
        "support_email": settings.DEFAULT_FROM_EMAIL,
        "app_name": "Veyu"
    }
    
    # Render HTML content
    html_message = render_to_string('password_reset.html', context)
    plain_message = f"Please click the following link to reset your password: {reset_link}"
    
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
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False

def send_otp_email(user, otp_code: str, validity_minutes: int = 30) -> bool:
    """Send OTP code to user's email."""
    subject = "Your Verification Code - Veyu"
    context = {
        "otp": otp_code,
        "validity_minutes": validity_minutes,
        "support_email": settings.DEFAULT_FROM_EMAIL,
        "app_name": "Veyu"
    }
    
    # Render HTML content
    html_message = render_to_string('otp_email.html', context)
    plain_message = f"Your verification code is: {otp_code}\nThis code is valid for {validity_minutes} minutes."
    
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
        logger.error(f"Failed to send OTP email to {user.email}: {str(e)}")
        return False

def send_business_verification_status(user, status: str, reason: str = "") -> bool:
    """Notify user about their business verification status."""
    subject = "Business Verification " + (
        "Approved" if status.lower() == "approved" else "Rejected"
    )
    
    # Render HTML content
    context = {
        'user_name': user.first_name or 'there',
        'status': status,
        'reason': reason,
        'support_email': settings.DEFAULT_FROM_EMAIL,
        'app_name': 'Veyu'
    }
    
    html_message = render_to_string('business_verification_status.html', context)
    plain_message = f"Your business verification has been {status}."
    if reason:
        plain_message += f" Reason: {reason}"
    
    try:
        send_mail(
            subject=f"{subject} - Veyu",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send business verification status email to {user.email}: {str(e)}")
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
