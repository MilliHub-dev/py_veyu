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
    html_message = render_to_string('emails/verification_email.html', context)
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
    html_message = render_to_string('emails/welcome_email.html', context)
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
    html_message = render_to_string('emails/password_reset.html', context)
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
    html_message = render_to_string('emails/otp_email.html', context)
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
    
    return send_email(
        subject=f"{subject} - Veyu",
        recipients=[user.email],
        template="utils/templates/business_verification_status.html",
        context={
            "user_name": user.first_name or 'there',
            "status": status,
            "reason": reason,
            "support_email": settings.DEFAULT_FROM_EMAIL,
            "app_name": "Veyu"
        }
    )

def send_booking_confirmation(user, booking_details: Dict[str, Any]) -> bool:
    """Send booking confirmation email."""
    return send_email(
        subject=f"Booking Confirmation - {booking_details.get('booking_reference', '')}",
        recipients=[user.email],
        template="utils/templates/booking_confirmation.html",
        context={
            "user_name": user.first_name or 'there',
            **booking_details,
            "support_email": settings.DEFAULT_FROM_EMAIL,
            "app_name": "Veyu"
        }
    )

def send_inspection_scheduled(user, inspection_details: Dict[str, Any]) -> bool:
    """Send inspection scheduled notification."""
    return send_email(
        subject=f"Inspection Scheduled - {inspection_details.get('inspection_reference', '')}",
        recipients=[user.email],
        template="utils/templates/inspection_scheduled.html",
        context={
            "user_name": user.first_name or 'there',
            **inspection_details,
            "support_email": settings.DEFAULT_FROM_EMAIL,
            "app_name": "Veyu"
        }
    )

def send_order_confirmation(user, order_details: Dict[str, Any]) -> bool:
    """Send order confirmation email."""
    return send_email(
        subject=f"Order Confirmation - {order_details.get('order_number', '')}",
        recipients=[user.email],
        template="utils/templates/order_confirmation.html",
        context={
            "user_name": user.first_name or 'there',
            **order_details,
            "support_email": settings.DEFAULT_FROM_EMAIL,
            "app_name": "Veyu"
        }
    )
