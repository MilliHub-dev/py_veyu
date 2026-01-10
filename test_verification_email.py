#!/usr/bin/env python3
"""
Test script to verify OTP creation and verification email sending
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.railway_settings')
django.setup()

from accounts.models import Account, OTP
from utils.async_email import send_verification_email_async
from django.utils import timezone
from datetime import timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_verification_email():
    """Test verification email sending"""
    
    # Find a test user (or create one)
    try:
        user = Account.objects.filter(email='veyultd@gmail.com').first()
        if not user:
            logger.error("Test user not found")
            return
        
        logger.info(f"Testing verification email for user: {user.email}")
        
        # Create OTP
        otp = OTP.objects.create(
            valid_for=user,
            channel='email',
            purpose='verification',
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        logger.info(f"Created OTP: {otp.code}")
        
        # Send verification email
        logger.info("Sending verification email...")
        send_verification_email_async(user, otp.code)
        
        logger.info("Verification email queued successfully")
        
        # Wait a bit for async processing
        import time
        time.sleep(5)
        
        logger.info("Test completed")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)

def check_existing_otps():
    """Check existing OTPs for the user"""
    try:
        user = Account.objects.filter(email='veyultd@gmail.com').first()
        if not user:
            logger.error("Test user not found")
            return
        
        otps = OTP.objects.filter(valid_for=user).order_by('-created_at')
        logger.info(f"Found {otps.count()} OTPs for user {user.email}")
        
        for otp in otps[:5]:  # Show last 5 OTPs
            logger.info(f"OTP: {otp.code}, Purpose: {otp.purpose}, Channel: {otp.channel}, Created: {otp.created_at}, Used: {otp.used}")
            
    except Exception as e:
        logger.error(f"Failed to check OTPs: {e}", exc_info=True)

if __name__ == '__main__':
    logger.info("🧪 Testing verification email system...")
    
    # Check existing OTPs first
    logger.info("\n1. Checking existing OTPs...")
    check_existing_otps()
    
    # Test verification email
    logger.info("\n2. Testing verification email sending...")
    test_verification_email()