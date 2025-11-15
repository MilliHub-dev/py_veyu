"""
Unified Email Verification Service for Veyu Platform

This service consolidates all email verification functionality to eliminate
duplicate emails and provide consistent verification handling.
"""

import logging
from typing import Dict, Any, Optional
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model

from accounts.models import Account, OTP
from accounts.utils.email_notifications import send_verification_email
from utils.otp import make_random_otp

logger = logging.getLogger(__name__)

User = get_user_model()


class EmailVerificationService:
    """
    Unified service for handling email verification across the platform.
    
    This service consolidates verification functionality to:
    - Send single verification emails (no duplicates)
    - Handle both authenticated and unauthenticated verification
    - Provide rate limiting for resend requests
    - Maintain consistent OTP management
    """
    
    # Rate limiting settings
    RATE_LIMIT_WINDOW = 60  # seconds
    MAX_REQUESTS_PER_WINDOW = 3
    RESEND_COOLDOWN = 60  # seconds between resend requests
    
    def __init__(self):
        self.logger = logger
    
    def send_verification_code(self, user: Account, purpose: str = 'verification') -> Dict[str, Any]:
        """
        Send verification code to user's email.
        
        This method consolidates all verification email sending to prevent duplicates.
        It invalidates previous unused OTPs and sends a single verification email.
        
        Args:
            user: Account instance to send verification to
            purpose: Purpose of the OTP ('verification', 'password_reset', etc.)
            
        Returns:
            Dict containing success status, message, and OTP details
        """
        try:
            # Check rate limiting
            rate_limit_check = self._check_rate_limit(user.email, 'send')
            if not rate_limit_check['allowed']:
                return {
                    'success': False,
                    'error': 'rate_limited',
                    'message': rate_limit_check['message'],
                    'retry_after': rate_limit_check.get('retry_after', self.RATE_LIMIT_WINDOW)
                }
            
            # Invalidate previous unused verification OTPs for this user
            self._invalidate_previous_otps(user, purpose)
            
            # Create new OTP
            otp = OTP.objects.create(
                valid_for=user,
                channel='email',
                purpose=purpose,
                expires_at=timezone.now() + timedelta(minutes=10)
            )
            
            # Send verification email using existing function
            email_sent = send_verification_email(user, otp.code)
            
            if email_sent:
                # Update rate limiting cache
                self._update_rate_limit_cache(user.email, 'send')
                
                self.logger.info(f"Verification code sent successfully to {user.email} for {purpose}")
                return {
                    'success': True,
                    'message': 'Verification code sent successfully',
                    'otp_id': otp.id,
                    'expires_at': otp.expires_at,
                    'code_length': len(otp.code)
                }
            else:
                # Mark OTP as used if email failed to prevent orphaned OTPs
                otp.used = True
                otp.save()
                
                self.logger.error(f"Failed to send verification email to {user.email}")
                return {
                    'success': False,
                    'error': 'email_send_failed',
                    'message': 'Failed to send verification email. Please try again.'
                }
                
        except Exception as e:
            self.logger.error(f"Error sending verification code to {user.email}: {str(e)}")
            return {
                'success': False,
                'error': 'system_error',
                'message': 'System error occurred. Please try again later.'
            }
    
    def verify_code(self, email: str, code: str, mark_verified: bool = True) -> Dict[str, Any]:
        """
        Verify email verification code without requiring authentication.
        
        This method allows unauthenticated users to verify their email addresses
        using the verification code sent to their email.
        
        Args:
            email: Email address to verify
            code: Verification code provided by user
            mark_verified: Whether to mark the email as verified upon success
            
        Returns:
            Dict containing verification result and user information
        """
        try:
            # Check rate limiting for verification attempts
            rate_limit_check = self._check_rate_limit(email, 'verify')
            if not rate_limit_check['allowed']:
                return {
                    'success': False,
                    'error': 'rate_limited',
                    'message': rate_limit_check['message'],
                    'retry_after': rate_limit_check.get('retry_after', self.RATE_LIMIT_WINDOW)
                }
            
            # Find user by email
            try:
                user = Account.objects.get(email=email)
            except Account.DoesNotExist:
                self._update_rate_limit_cache(email, 'verify')  # Count failed attempts
                self.logger.warning(f"Verification attempt for non-existent email: {email}")
                return {
                    'success': False,
                    'error': 'account_not_found',
                    'message': 'Account not found with this email address'
                }
            
            # Find valid OTP for verification
            otp = OTP.objects.filter(
                valid_for=user,
                code=code,
                channel='email',
                purpose='verification',
                used=False
            ).first()
            
            if not otp:
                self._update_rate_limit_cache(email, 'verify')  # Count failed attempts
                self.logger.warning(f"Invalid verification code attempted for {email}")
                return {
                    'success': False,
                    'error': 'invalid_code',
                    'message': 'Invalid or expired verification code'
                }
            
            # Check if OTP is still valid
            if not otp.is_valid_for_verification():
                self._update_rate_limit_cache(email, 'verify')  # Count failed attempts
                self.logger.warning(f"Expired verification code attempted for {email}")
                return {
                    'success': False,
                    'error': 'code_expired',
                    'message': 'Verification code has expired or exceeded maximum attempts'
                }
            
            # Verify the code using OTP's built-in method
            verification_success = otp.verify(code, user)
            
            if verification_success:
                # Additional verification if requested
                if mark_verified and not user.verified_email:
                    user.verified_email = True
                    user.save()
                
                self.logger.info(f"Email verification successful for {email}")
                return {
                    'success': True,
                    'message': 'Email verified successfully',
                    'user_id': user.id,
                    'email_verified': user.verified_email,
                    'user_type': user.user_type
                }
            else:
                self._update_rate_limit_cache(email, 'verify')  # Count failed attempts
                self.logger.warning(f"OTP verification failed for {email}")
                return {
                    'success': False,
                    'error': 'verification_failed',
                    'message': 'Verification failed. Please check your code and try again.'
                }
                
        except Exception as e:
            self.logger.error(f"Error verifying code for {email}: {str(e)}")
            return {
                'success': False,
                'error': 'system_error',
                'message': 'System error occurred during verification'
            }
    
    def resend_verification_code(self, email: str) -> Dict[str, Any]:
        """
        Resend verification code with rate limiting.
        
        This method handles resending verification codes with proper rate limiting
        to prevent spam and abuse.
        
        Args:
            email: Email address to resend verification code to
            
        Returns:
            Dict containing resend result and timing information
        """
        try:
            # Find user by email
            try:
                user = Account.objects.get(email=email)
            except Account.DoesNotExist:
                self.logger.warning(f"Resend attempt for non-existent email: {email}")
                return {
                    'success': False,
                    'error': 'account_not_found',
                    'message': 'Account not found with this email address'
                }
            
            # Check if email is already verified
            if user.verified_email:
                return {
                    'success': False,
                    'error': 'already_verified',
                    'message': 'Email address is already verified'
                }
            
            # Check resend cooldown
            cooldown_check = self._check_resend_cooldown(email)
            if not cooldown_check['allowed']:
                return {
                    'success': False,
                    'error': 'resend_cooldown',
                    'message': cooldown_check['message'],
                    'retry_after': cooldown_check.get('retry_after', self.RESEND_COOLDOWN)
                }
            
            # Check rate limiting for resend requests
            rate_limit_check = self._check_rate_limit(email, 'resend')
            if not rate_limit_check['allowed']:
                return {
                    'success': False,
                    'error': 'rate_limited',
                    'message': rate_limit_check['message'],
                    'retry_after': rate_limit_check.get('retry_after', self.RATE_LIMIT_WINDOW)
                }
            
            # Send new verification code
            result = self.send_verification_code(user, 'verification')
            
            if result['success']:
                # Update resend cooldown
                self._update_resend_cooldown(email)
                
                self.logger.info(f"Verification code resent successfully to {email}")
                return {
                    'success': True,
                    'message': 'Verification code sent successfully',
                    'expires_at': result.get('expires_at'),
                    'next_resend_allowed': timezone.now() + timedelta(seconds=self.RESEND_COOLDOWN)
                }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"Error resending verification code to {email}: {str(e)}")
            return {
                'success': False,
                'error': 'system_error',
                'message': 'System error occurred. Please try again later.'
            }
    
    def _invalidate_previous_otps(self, user: Account, purpose: str) -> None:
        """
        Invalidate previous unused OTPs for the same user and purpose.
        
        Args:
            user: Account instance
            purpose: OTP purpose to invalidate
        """
        try:
            updated_count = OTP.objects.filter(
                valid_for=user,
                channel='email',
                purpose=purpose,
                used=False
            ).update(used=True)
            
            if updated_count > 0:
                self.logger.info(f"Invalidated {updated_count} previous OTPs for {user.email}")
                
        except Exception as e:
            self.logger.error(f"Error invalidating previous OTPs for {user.email}: {str(e)}")
    
    def _check_rate_limit(self, email: str, action: str) -> Dict[str, Any]:
        """
        Check rate limiting for email verification actions.
        
        Args:
            email: Email address to check
            action: Action type ('send', 'verify', 'resend')
            
        Returns:
            Dict with 'allowed' boolean and optional 'message' and 'retry_after'
        """
        cache_key = f"email_verification_rate_limit:{action}:{email}"
        
        try:
            current_count = cache.get(cache_key, 0)
            
            if current_count >= self.MAX_REQUESTS_PER_WINDOW:
                return {
                    'allowed': False,
                    'message': f'Too many {action} attempts. Please wait before trying again.',
                    'retry_after': self.RATE_LIMIT_WINDOW
                }
            
            return {'allowed': True}
            
        except Exception as e:
            self.logger.error(f"Error checking rate limit for {email}: {str(e)}")
            # Allow the request if cache check fails
            return {'allowed': True}
    
    def _update_rate_limit_cache(self, email: str, action: str) -> None:
        """
        Update rate limiting cache for email verification actions.
        
        Args:
            email: Email address
            action: Action type ('send', 'verify', 'resend')
        """
        cache_key = f"email_verification_rate_limit:{action}:{email}"
        
        try:
            current_count = cache.get(cache_key, 0)
            cache.set(cache_key, current_count + 1, self.RATE_LIMIT_WINDOW)
            
        except Exception as e:
            self.logger.error(f"Error updating rate limit cache for {email}: {str(e)}")
    
    def _check_resend_cooldown(self, email: str) -> Dict[str, Any]:
        """
        Check resend cooldown for email address.
        
        Args:
            email: Email address to check
            
        Returns:
            Dict with 'allowed' boolean and optional 'message' and 'retry_after'
        """
        cache_key = f"email_verification_resend_cooldown:{email}"
        
        try:
            last_resend = cache.get(cache_key)
            
            if last_resend:
                return {
                    'allowed': False,
                    'message': f'Please wait {self.RESEND_COOLDOWN} seconds before requesting another code.',
                    'retry_after': self.RESEND_COOLDOWN
                }
            
            return {'allowed': True}
            
        except Exception as e:
            self.logger.error(f"Error checking resend cooldown for {email}: {str(e)}")
            # Allow the request if cache check fails
            return {'allowed': True}
    
    def _update_resend_cooldown(self, email: str) -> None:
        """
        Update resend cooldown cache for email address.
        
        Args:
            email: Email address
        """
        cache_key = f"email_verification_resend_cooldown:{email}"
        
        try:
            cache.set(cache_key, timezone.now().timestamp(), self.RESEND_COOLDOWN)
            
        except Exception as e:
            self.logger.error(f"Error updating resend cooldown for {email}: {str(e)}")
    
    def cleanup_expired_otps(self, days_old: int = 7) -> int:
        """
        Clean up expired OTPs older than specified days.
        
        Args:
            days_old: Number of days old to consider for cleanup
            
        Returns:
            Number of OTPs cleaned up
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=days_old)
            
            deleted_count, _ = OTP.objects.filter(
                expires_at__lt=cutoff_date
            ).delete()
            
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} expired OTPs older than {days_old} days")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired OTPs: {str(e)}")
            return 0
    
    def get_verification_status(self, email: str) -> Dict[str, Any]:
        """
        Get verification status for an email address.
        
        Args:
            email: Email address to check
            
        Returns:
            Dict containing verification status and related information
        """
        try:
            try:
                user = Account.objects.get(email=email)
            except Account.DoesNotExist:
                return {
                    'exists': False,
                    'verified': False,
                    'message': 'Account not found'
                }
            
            # Check for pending OTPs
            pending_otp = OTP.objects.filter(
                valid_for=user,
                channel='email',
                purpose='verification',
                used=False,
                expires_at__gt=timezone.now()
            ).first()
            
            return {
                'exists': True,
                'verified': user.verified_email,
                'has_pending_otp': pending_otp is not None,
                'otp_expires_at': pending_otp.expires_at if pending_otp else None,
                'user_type': user.user_type,
                'message': 'Email verified' if user.verified_email else 'Email not verified'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting verification status for {email}: {str(e)}")
            return {
                'exists': False,
                'verified': False,
                'error': 'system_error',
                'message': 'Unable to check verification status'
            }


# Create a singleton instance for easy import
email_verification_service = EmailVerificationService()