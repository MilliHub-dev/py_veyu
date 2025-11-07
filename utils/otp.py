import secrets
import string
import logging
from datetime import datetime, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

def make_random_otp(length=6):
    """Generate a cryptographically secure random OTP of specified length.
    
    Args:
        length (int): Length of the OTP. Defaults to 6.
        
    Returns:
        str: A cryptographically secure random numeric OTP of the specified length.
    """
    # Use secrets module for cryptographically secure random generation
    otp = ''.join(secrets.choice(string.digits) for _ in range(length))
    logger.info(f"Generated OTP of length {length}")
    return otp

def is_otp_expired(otp_created_time, expiry_minutes=10):
    """Check if an OTP has expired based on creation time.
    
    Args:
        otp_created_time (datetime): When the OTP was created
        expiry_minutes (int): Expiry time in minutes. Defaults to 10.
        
    Returns:
        bool: True if OTP has expired, False otherwise.
    """
    if not otp_created_time:
        return True
    
    expiry_time = otp_created_time + timedelta(minutes=expiry_minutes)
    return timezone.now() > expiry_time

def validate_otp_format(otp_code):
    """Validate OTP format (numeric and correct length).
    
    Args:
        otp_code (str): The OTP code to validate
        
    Returns:
        bool: True if format is valid, False otherwise.
    """
    if not otp_code:
        return False
    
    # Check if it's numeric and has correct length (4-8 digits)
    return otp_code.isdigit() and 4 <= len(otp_code) <= 8
