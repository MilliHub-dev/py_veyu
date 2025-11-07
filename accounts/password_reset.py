"""
Password Reset System for Veyu Platform

This module provides secure password reset functionality with token generation,
validation, and comprehensive security measures.
"""

import logging
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from accounts.models import Account
from accounts.utils.email_notifications import send_password_reset_email
from utils.exceptions import (
    ValidationError,
    AuthenticationError,
    ErrorCodes
)

logger = logging.getLogger(__name__)


class PasswordResetManager:
    """
    Manager class for handling password reset operations with enhanced security.
    """
    
    # Configuration
    TOKEN_LENGTH = 32
    TOKEN_EXPIRY_HOURS = 1  # 1 hour expiry for security
    MAX_RESET_ATTEMPTS = 3  # Maximum reset attempts per hour
    RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds
    
    @classmethod
    def generate_reset_token(cls, user: Account) -> str:
        """
        Generate a secure password reset token for the user.
        
        Args:
            user: The user account requesting password reset
            
        Returns:
            Secure reset token string
        """
        # Generate cryptographically secure random token
        token = secrets.token_urlsafe(cls.TOKEN_LENGTH)
        
        # Create token data
        token_data = {
            'user_id': user.id,
            'email': user.email,
            'created_at': timezone.now().isoformat(),
            'expires_at': (timezone.now() + timedelta(hours=cls.TOKEN_EXPIRY_HOURS)).isoformat(),
            'used': False
        }
        
        # Store token in cache with expiry
        cache_key = cls._get_token_cache_key(token)
        cache.set(
            cache_key, 
            token_data, 
            timeout=cls.TOKEN_EXPIRY_HOURS * 3600
        )
        
        logger.info(f"Password reset token generated for user: {user.email}")
        return token
    
    @classmethod
    def validate_reset_token(cls, token: str) -> Tuple[bool, Optional[Account], Optional[str]]:
        """
        Validate a password reset token.
        
        Args:
            token: The reset token to validate
            
        Returns:
            Tuple of (is_valid, user_account, error_message)
        """
        try:
            cache_key = cls._get_token_cache_key(token)
            token_data = cache.get(cache_key)
            
            if not token_data:
                logger.warning(f"Password reset token not found or expired: {token[:8]}...")
                return False, None, "Invalid or expired reset token"
            
            # Check if token has been used
            if token_data.get('used', False):
                logger.warning(f"Attempted reuse of password reset token: {token[:8]}...")
                return False, None, "Reset token has already been used"
            
            # Check expiry
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            if timezone.now() > expires_at.replace(tzinfo=timezone.utc):
                logger.warning(f"Expired password reset token used: {token[:8]}...")
                # Clean up expired token
                cache.delete(cache_key)
                return False, None, "Reset token has expired"
            
            # Get user account
            try:
                user = Account.objects.get(id=token_data['user_id'])
                
                # Verify email matches (additional security check)
                if user.email != token_data['email']:
                    logger.error(f"Email mismatch for reset token: {token[:8]}...")
                    return False, None, "Invalid reset token"
                
                return True, user, None
                
            except Account.DoesNotExist:
                logger.error(f"User not found for reset token: {token_data['user_id']}")
                return False, None, "Invalid reset token"
            
        except Exception as e:
            logger.error(f"Error validating reset token: {str(e)}")
            return False, None, "Token validation failed"
    
    @classmethod
    def mark_token_used(cls, token: str) -> None:
        """
        Mark a reset token as used to prevent reuse.
        
        Args:
            token: The reset token to mark as used
        """
        try:
            cache_key = cls._get_token_cache_key(token)
            token_data = cache.get(cache_key)
            
            if token_data:
                token_data['used'] = True
                token_data['used_at'] = timezone.now().isoformat()
                
                # Keep the token in cache for a short time to prevent reuse
                cache.set(cache_key, token_data, timeout=3600)  # 1 hour
                
                logger.info(f"Password reset token marked as used: {token[:8]}...")
        except Exception as e:
            logger.error(f"Error marking token as used: {str(e)}")
    
    @classmethod
    def initiate_password_reset(cls, email: str) -> Dict[str, Any]:
        """
        Initiate password reset process for a user.
        
        Args:
            email: Email address of the user requesting reset
            
        Returns:
            Dictionary containing operation result
        """
        try:
            # Check rate limiting
            if not cls._check_rate_limit(email):
                logger.warning(f"Password reset rate limit exceeded for: {email}")
                raise ValidationError(
                    "Too many password reset attempts",
                    ErrorCodes.API_RATE_LIMIT_EXCEEDED,
                    user_message="Too many password reset attempts. Please try again later."
                )
            
            # Find user account
            try:
                user = Account.objects.get(email=email, is_active=True)
            except Account.DoesNotExist:
                # For security, don't reveal if email exists
                logger.info(f"Password reset requested for non-existent email: {email}")
                return {
                    'success': True,
                    'message': 'If an account with this email exists, you will receive a password reset link.',
                    'email_sent': False
                }
            
            # Check if user uses social authentication
            if user.provider != 'veyu':
                logger.info(f"Password reset requested for social auth user: {email}")
                return {
                    'success': False,
                    'message': f'This account uses {user.provider} authentication. Please reset your password through {user.provider}.',
                    'email_sent': False,
                    'provider': user.provider
                }
            
            # Generate reset token
            reset_token = cls.generate_reset_token(user)
            
            # Generate reset URL
            reset_url = cls._generate_reset_url(reset_token)
            
            # Send reset email
            email_sent = send_password_reset_email(user, reset_url, reset_token)
            
            # Update rate limiting
            cls._update_rate_limit(email)
            
            result = {
                'success': True,
                'message': 'If an account with this email exists, you will receive a password reset link.',
                'email_sent': email_sent,
                'token': reset_token if settings.DEBUG else None  # Only include token in debug mode
            }
            
            logger.info(f"Password reset initiated for: {email}")
            return result
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error initiating password reset for {email}: {str(e)}")
            raise ValidationError(
                "Password reset initiation failed",
                ErrorCodes.API_INTERNAL_ERROR,
                user_message="Password reset request failed. Please try again."
            )
    
    @classmethod
    def reset_password(cls, token: str, new_password: str) -> Dict[str, Any]:
        """
        Reset user password using a valid reset token.
        
        Args:
            token: Password reset token
            new_password: New password to set
            
        Returns:
            Dictionary containing operation result
        """
        try:
            # Validate token
            is_valid, user, error_message = cls.validate_reset_token(token)
            
            if not is_valid:
                raise ValidationError(
                    error_message or "Invalid reset token",
                    ErrorCodes.TOKEN_INVALID,
                    user_message=error_message or "Invalid or expired reset token"
                )
            
            # Validate password strength
            cls._validate_password_strength(new_password)
            
            # Check if new password is different from current
            if user.check_password(new_password):
                raise ValidationError(
                    "New password must be different from current password",
                    ErrorCodes.VALIDATION_ERROR,
                    user_message="Please choose a different password from your current one."
                )
            
            # Set new password
            user.set_password(new_password)
            user.save(update_fields=['password'])
            
            # Mark token as used
            cls.mark_token_used(token)
            
            # Clear any existing sessions/tokens for security
            # This would require additional implementation for JWT blacklisting
            
            logger.info(f"Password reset completed for user: {user.email}")
            
            return {
                'success': True,
                'message': 'Password has been reset successfully. Please log in with your new password.',
                'user_id': user.id
            }
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}")
            raise ValidationError(
                "Password reset failed",
                ErrorCodes.API_INTERNAL_ERROR,
                user_message="Password reset failed. Please try again."
            )
    
    @classmethod
    def _get_token_cache_key(cls, token: str) -> str:
        """Generate cache key for reset token."""
        # Hash the token for additional security
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return f"password_reset_token:{token_hash}"
    
    @classmethod
    def _get_rate_limit_key(cls, email: str) -> str:
        """Generate cache key for rate limiting."""
        email_hash = hashlib.sha256(email.lower().encode()).hexdigest()
        return f"password_reset_rate_limit:{email_hash}"
    
    @classmethod
    def _check_rate_limit(cls, email: str) -> bool:
        """Check if user has exceeded rate limit for password reset requests."""
        cache_key = cls._get_rate_limit_key(email)
        attempts = cache.get(cache_key, 0)
        return attempts < cls.MAX_RESET_ATTEMPTS
    
    @classmethod
    def _update_rate_limit(cls, email: str) -> None:
        """Update rate limit counter for password reset requests."""
        cache_key = cls._get_rate_limit_key(email)
        attempts = cache.get(cache_key, 0)
        cache.set(cache_key, attempts + 1, timeout=cls.RATE_LIMIT_WINDOW)
    
    @classmethod
    def _generate_reset_url(cls, token: str) -> str:
        """Generate password reset URL."""
        frontend_url = getattr(settings, 'FRONTEND_URL', 'https://dev.veyu.cc')
        return f"{frontend_url}/reset-password?token={token}"
    
    @classmethod
    def _validate_password_strength(cls, password: str) -> None:
        """
        Validate password strength requirements.
        
        Args:
            password: Password to validate
            
        Raises:
            ValidationError: If password doesn't meet requirements
        """
        if len(password) < 8:
            raise ValidationError(
                "Password too short",
                ErrorCodes.VALIDATION_ERROR,
                user_message="Password must be at least 8 characters long."
            )
        
        if len(password) > 128:
            raise ValidationError(
                "Password too long",
                ErrorCodes.VALIDATION_ERROR,
                user_message="Password must be less than 128 characters long."
            )
        
        # Check for at least one letter and one number
        has_letter = any(c.isalpha() for c in password)
        has_number = any(c.isdigit() for c in password)
        
        if not (has_letter and has_number):
            raise ValidationError(
                "Password must contain letters and numbers",
                ErrorCodes.VALIDATION_ERROR,
                user_message="Password must contain at least one letter and one number."
            )
        
        # Check for common weak passwords
        weak_passwords = [
            'password', '12345678', 'qwerty123', 'abc12345',
            'password123', '123456789', 'letmein123'
        ]
        
        if password.lower() in weak_passwords:
            raise ValidationError(
                "Password is too common",
                ErrorCodes.VALIDATION_ERROR,
                user_message="Please choose a stronger, less common password."
            )


# Convenience functions for external use
def initiate_password_reset(email: str) -> Dict[str, Any]:
    """
    Convenience function to initiate password reset.
    
    Args:
        email: Email address of the user
        
    Returns:
        Dictionary containing operation result
    """
    return PasswordResetManager.initiate_password_reset(email)


def reset_password_with_token(token: str, new_password: str) -> Dict[str, Any]:
    """
    Convenience function to reset password with token.
    
    Args:
        token: Password reset token
        new_password: New password to set
        
    Returns:
        Dictionary containing operation result
    """
    return PasswordResetManager.reset_password(token, new_password)


def validate_password_reset_token(token: str) -> Tuple[bool, Optional[Account], Optional[str]]:
    """
    Convenience function to validate reset token.
    
    Args:
        token: Reset token to validate
        
    Returns:
        Tuple of (is_valid, user_account, error_message)
    """
    return PasswordResetManager.validate_reset_token(token)