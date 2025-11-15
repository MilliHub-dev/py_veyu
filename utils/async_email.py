"""
Asynchronous email sending using Brevo API (fast and reliable).
Uses HTTP API instead of SMTP to avoid network/firewall issues.
"""

import logging
import threading
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def send_email_async(email_function, *args, **kwargs):
    """
    Send email in a background thread to avoid blocking the main request.
    
    Args:
        email_function: The email function to call
        *args: Positional arguments for the email function
        **kwargs: Keyword arguments for the email function
    """
    def _send():
        try:
            result = email_function(*args, **kwargs)
            if result:
                logger.info(f"✅ Async email sent successfully via {email_function.__name__}")
            else:
                logger.warning(f"⚠️ Async email failed via {email_function.__name__}")
        except Exception as e:
            logger.error(f"❌ Async email error in {email_function.__name__}: {e}", exc_info=True)
    
    # Start email sending in background thread
    thread = threading.Thread(target=_send, daemon=True)
    thread.start()
    logger.info(f"📧 Email queued for async sending via {email_function.__name__}")


def send_verification_email_async(user, verification_code: str):
    """Send verification email asynchronously using Brevo API."""
    def _send_verification():
        from utils.brevo_api import send_template_email_via_api
        from django.conf import settings
        
        context = {
            "name": user.first_name or user.email,
            "user_name": user.first_name or 'there',
            "email": user.email,
            "verification_code": verification_code,
            "otp": verification_code,  # Support both variable names
            "validity_minutes": 30,
            "purpose": "signup",
            "support_email": getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@veyu.cc'),
            "app_name": "Veyu"
        }
        
        return send_template_email_via_api(
            subject="Verify Your Email - Veyu",
            recipients=[user.email],
            template_name='verification_email.html',
            context=context
        )
    
    send_email_async(_send_verification)


def send_welcome_email_async(user):
    """Send welcome email asynchronously using Brevo API."""
    def _send_welcome():
        from utils.brevo_api import send_template_email_via_api
        from django.conf import settings
        
        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://veyu.cc')
        context = {
            "user_name": user.first_name or 'there',
            "buy_link": f"{frontend_url}/buy/",
            "rent_link": f"{frontend_url}/rent/",
            "mechanic_link": f"{frontend_url}/mechanics/",
            "support_email": getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@veyu.cc'),
            "app_name": "Veyu"
        }
        
        return send_template_email_via_api(
            subject=f"Welcome to Veyu, {user.first_name or 'there'}!",
            recipients=[user.email],
            template_name='welcome_email.html',
            context=context
        )
    
    send_email_async(_send_welcome)


def send_otp_email_async(user, otp_code: str, validity_minutes: int = 30):
    """Send OTP email asynchronously using unified verification template."""
    def _send_otp():
        from utils.brevo_api import send_template_email_via_api
        from django.conf import settings
        
        context = {
            "otp": otp_code,
            "verification_code": otp_code,  # Support both variable names
            "name": user.first_name or user.email,
            "user_name": user.first_name or 'there',
            "email": user.email,
            "validity_minutes": validity_minutes,
            "purpose": "login",
            "support_email": getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@veyu.cc'),
            "app_name": "Veyu"
        }
        
        return send_template_email_via_api(
            subject="Verify Your Email - Veyu",  # Unified subject
            recipients=[user.email],
            template_name='verification_email.html',  # Use unified template
            context=context
        )
    
    send_email_async(_send_otp)


def send_password_reset_email_async(user, reset_url: str, reset_token: str = None):
    """Send password reset email asynchronously."""
    from accounts.utils.email_notifications import send_password_reset_email
    send_email_async(send_password_reset_email, user, reset_url, reset_token)


def send_wallet_transaction_async(user, transaction_details: Dict[str, Any]):
    """Send wallet transaction email asynchronously."""
    from accounts.utils.email_notifications import send_wallet_transaction
    send_email_async(send_wallet_transaction, user, transaction_details)


def send_order_confirmation_async(user, order_details: Dict[str, Any]):
    """Send order confirmation email asynchronously."""
    from accounts.utils.email_notifications import send_order_confirmation
    send_email_async(send_order_confirmation, user, order_details)


def send_booking_confirmation_async(user, booking_details: Dict[str, Any]):
    """Send booking confirmation email asynchronously."""
    from accounts.utils.email_notifications import send_booking_confirmation
    send_email_async(send_booking_confirmation, user, booking_details)
