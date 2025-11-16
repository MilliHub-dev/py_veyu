"""
Welcome email utility for first-time login functionality.
"""

import logging
from typing import Optional
from django.utils import timezone
from django.db import transaction
from accounts.models import Account
from utils.async_email import send_welcome_email_async

logger = logging.getLogger(__name__)


def send_welcome_email_on_first_login(user: Account) -> bool:
    """
    Send welcome email if this is user's first login.
    
    This function implements race condition prevention and proper error handling
    as specified in the requirements.
    
    Args:
        user: Account instance to check and send welcome email for
        
    Returns:
        bool: True if welcome email was sent, False if already sent or failed
        
    Requirements:
        - 1.1: Send welcome email on first successful login
        - 1.2: Prevent duplicate welcome emails
        - 3.1: Use asynchronous email delivery
        - 3.4: Prevent race conditions
    """
    try:
        # Use atomic transaction to prevent race conditions
        with transaction.atomic():
            # Select for update to lock the row and prevent race conditions
            user_locked = Account.objects.select_for_update().get(id=user.id)
            
            # Check if welcome email has already been sent
            if user_locked.welcome_email_sent_at is not None:
                logger.info(f"Welcome email already sent for user {user.email} at {user_locked.welcome_email_sent_at}")
                return False
            
            # Send welcome email asynchronously (non-blocking)
            send_welcome_email_async(user_locked)
            
            # Mark as sent to prevent duplicates
            user_locked.welcome_email_sent_at = timezone.now()
            user_locked.save(update_fields=['welcome_email_sent_at'])
            
            logger.info(f"Welcome email sent successfully for user {user.email} on first login")
            return True
            
    except Account.DoesNotExist:
        logger.error(f"User {user.id} not found when sending welcome email")
        return False
    except Exception as e:
        logger.error(f"Failed to send welcome email for user {user.email}: {str(e)}", exc_info=True)
        # Don't raise exception to avoid blocking login process
        return False


def check_welcome_email_status(user: Account) -> dict:
    """
    Check welcome email status for a user.
    
    Args:
        user: Account instance to check
        
    Returns:
        dict: Status information about welcome email
    """
    return {
        'welcome_email_sent': user.has_received_welcome_email,
        'welcome_email_sent_at': user.welcome_email_sent_at,
    }