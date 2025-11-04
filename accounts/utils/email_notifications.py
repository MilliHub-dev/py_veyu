from typing import Optional, Dict, Any, List
from django.conf import settings
from django.contrib.auth import get_user_model
from utils.mail import send_email

User = get_user_model()

def send_verification_email(user, verification_code: str) -> bool:
    """Send email verification code to user."""
    return send_email(
        subject="Verify Your Email - Veyu",
        recipients=[user.email],
        template="utils/templates/verification_email.html",
        context={
            "name": user.first_name or user.email,
            "verification_code": verification_code,
            "support_email": settings.DEFAULT_FROM_EMAIL,
            "app_name": "Veyu"
        }
    )

def send_welcome_email(user) -> bool:
    """Send welcome email to new user."""
    return send_email(
        subject=f"Welcome to Veyu, {user.first_name or 'there'}!",
        recipients=[user.email],
        template="utils/templates/welcome_email.html",
        context={
            "user_name": user.first_name or 'there',
            "buy_link": f"{settings.FRONTEND_URL}/buy/",
            "rent_link": f"{settings.FRONTEND_URL}/rent/",
            "mechanic_link": f"{settings.FRONTEND_URL}/mechanics/"
        }
    )

def send_password_reset_email(user, reset_link: str) -> bool:
    """Send password reset email with reset link."""
    return send_email(
        subject="Password Reset Request - Veyu",
        recipients=[user.email],
        template="utils/templates/password_reset.html",
        context={
            "user_name": user.first_name or 'there',
            "reset_link": reset_link,
            "support_email": settings.DEFAULT_FROM_EMAIL,
            "app_name": "Veyu"
        }
    )

def send_otp_email(user, otp_code: str, validity_minutes: int = 30) -> bool:
    """Send OTP code to user's email."""
    return send_email(
        subject="Your Verification Code - Veyu",
        recipients=[user.email],
        template="utils/templates/otp_email.html",
        context={
            "otp": otp_code,
            "validity_minutes": validity_minutes,
            "support_email": settings.DEFAULT_FROM_EMAIL,
            "app_name": "Veyu"
        }
    )

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
