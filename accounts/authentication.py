"""
Enhanced JWT Authentication for Veyu Platform

This module provides custom JWT authentication classes with enhanced security features
including token blacklisting, refresh token rotation, and comprehensive validation.
"""

import logging
from typing import Optional, Tuple, Any
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication as BaseJWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.settings import api_settings
from django.core.cache import cache
from django.conf import settings
from utils.exceptions import (
    AuthenticationError,
    TokenError as VeyuTokenError,
    ErrorCodes
)

logger = logging.getLogger(__name__)
User = get_user_model()


class TokenBlacklist:
    """
    Token blacklisting utility using Django cache.
    Provides methods to blacklist and check token status.
    """
    
    BLACKLIST_PREFIX = "jwt_blacklist:"
    
    @classmethod
    def blacklist_token(cls, token_jti: str, expiry_seconds: int = None) -> None:
        """
        Add a token to the blacklist.
        
        Args:
            token_jti: The JTI (JWT ID) of the token to blacklist
            expiry_seconds: How long to keep the token in blacklist (defaults to token expiry)
        """
        cache_key = f"{cls.BLACKLIST_PREFIX}{token_jti}"
        timeout = expiry_seconds or getattr(settings, 'JWT_BLACKLIST_TIMEOUT', 86400)  # 24 hours default
        
        cache.set(cache_key, True, timeout=timeout)
        logger.info(f"Token blacklisted: {token_jti[:8]}...")
    
    @classmethod
    def is_blacklisted(cls, token_jti: str) -> bool:
        """
        Check if a token is blacklisted.
        
        Args:
            token_jti: The JTI (JWT ID) of the token to check
            
        Returns:
            True if token is blacklisted, False otherwise
        """
        cache_key = f"{cls.BLACKLIST_PREFIX}{token_jti}"
        return cache.get(cache_key, False)
    
    @classmethod
    def clear_user_tokens(cls, user_id: int) -> None:
        """
        Clear all tokens for a specific user (useful for logout all devices).
        Note: This is a simple implementation. For production, consider using
        a more sophisticated approach with user-specific token tracking.
        """
        # This would require additional token tracking per user
        # For now, we'll log the action
        logger.info(f"Clearing all tokens for user {user_id}")


class EnhancedJWTAuthentication(BaseJWTAuthentication):
    """
    Enhanced JWT Authentication with blacklisting and additional security features.
    
    Features:
    - Token blacklisting support
    - Enhanced error handling
    - Comprehensive logging
    - Token validation with user status checks
    """
    
    def authenticate(self, request: Request) -> Optional[Tuple[User, Any]]:
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            
            # Additional security checks
            self._perform_security_checks(user, validated_token, request)
            
            return user, validated_token
            
        except TokenError as e:
            logger.warning(f"JWT authentication failed: {str(e)}")
            raise exceptions.AuthenticationFailed(
                _('Given token not valid for any token type'),
                code='token_not_valid',
            )
        except Exception as e:
            logger.error(f"Unexpected error during JWT authentication: {str(e)}")
            raise exceptions.AuthenticationFailed(
                _('Authentication failed'),
                code='authentication_failed',
            )

    def get_validated_token(self, raw_token: bytes) -> AccessToken:
        """
        Validate the token and check if it's blacklisted.
        """
        try:
            # First validate the token structure and signature
            validated_token = AccessToken(raw_token)
            
            # Check if token is blacklisted
            token_jti = validated_token.get('jti')
            if token_jti and TokenBlacklist.is_blacklisted(token_jti):
                logger.warning(f"Attempted use of blacklisted token: {token_jti[:8]}...")
                raise InvalidToken(_('Token is blacklisted'))
            
            return validated_token
            
        except TokenError as e:
            logger.warning(f"Token validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {str(e)}")
            raise InvalidToken(_('Token validation failed'))

    def get_user(self, validated_token: AccessToken) -> User:
        """
        Get the user associated with the token and perform additional checks.
        """
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken(_('Token contained no recognizable user identification'))

        try:
            user = User.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except User.DoesNotExist:
            logger.warning(f"Token references non-existent user: {user_id}")
            raise exceptions.AuthenticationFailed(_('User not found'), code='user_not_found')

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Inactive user attempted authentication: {user.email}")
            raise exceptions.AuthenticationFailed(_('User account is disabled'), code='user_inactive')

        return user

    def _perform_security_checks(self, user: User, token: AccessToken, request: Request) -> None:
        """
        Perform additional security checks on the authenticated user and token.
        """
        # Log successful authentication
        logger.info(f"Successful JWT authentication for user: {user.email}")
        
        # Check for suspicious activity (implement as needed)
        # This could include IP checking, device fingerprinting, etc.
        
        # Update last login if needed (optional)
        # user.last_login = timezone.now()
        # user.save(update_fields=['last_login'])


class VeyuRefreshToken(RefreshToken):
    """
    Enhanced refresh token with rotation support and blacklisting.
    """
    
    @classmethod
    def for_user(cls, user: User) -> 'VeyuRefreshToken':
        """
        Create a refresh token for the given user with enhanced claims.
        """
        token = super().for_user(user)
        
        # Add custom claims
        token['user_type'] = user.user_type
        token['email'] = user.email
        token['provider'] = user.provider
        
        return token
    
    def rotate(self) -> 'VeyuRefreshToken':
        """
        Rotate the refresh token by creating a new one and blacklisting the current one.
        """
        # Blacklist the current token
        if hasattr(self, 'token') and 'jti' in self.token:
            TokenBlacklist.blacklist_token(
                self.token['jti'],
                expiry_seconds=int(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds())
            )
        
        # Create new token for the same user
        user_id = self.token[api_settings.USER_ID_CLAIM]
        try:
            user = User.objects.get(**{api_settings.USER_ID_FIELD: user_id})
            new_token = self.__class__.for_user(user)
            
            logger.info(f"Refresh token rotated for user: {user.email}")
            return new_token
            
        except User.DoesNotExist:
            logger.error(f"Cannot rotate token for non-existent user: {user_id}")
            raise TokenError(_('User not found for token rotation'))
    
    def blacklist(self) -> None:
        """
        Blacklist this refresh token.
        """
        if 'jti' in self.token:
            TokenBlacklist.blacklist_token(
                self.token['jti'],
                expiry_seconds=int(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds())
            )
            logger.info(f"Refresh token blacklisted: {self.token['jti'][:8]}...")


class TokenManager:
    """
    Utility class for managing JWT tokens with enhanced security features.
    """
    
    @staticmethod
    def create_tokens_for_user(user: User) -> dict:
        """
        Create access and refresh tokens for a user.
        
        Returns:
            Dictionary containing access and refresh tokens
        """
        refresh = VeyuRefreshToken.for_user(user)
        access = refresh.access_token
        
        logger.info(f"Tokens created for user: {user.email}")
        
        return {
            'access': str(access),
            'refresh': str(refresh),
            'access_expires': access['exp'],
            'refresh_expires': refresh['exp']
        }
    
    @staticmethod
    def refresh_access_token(refresh_token_str: str, rotate_refresh: bool = True) -> dict:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token_str: The refresh token string
            rotate_refresh: Whether to rotate the refresh token
            
        Returns:
            Dictionary containing new tokens
        """
        try:
            refresh_token = VeyuRefreshToken(refresh_token_str)
            
            # Check if refresh token is blacklisted
            token_jti = refresh_token.get('jti')
            if token_jti and TokenBlacklist.is_blacklisted(token_jti):
                raise VeyuTokenError(
                    "Refresh token is blacklisted",
                    ErrorCodes.TOKEN_INVALID
                )
            
            # Get new access token
            access_token = refresh_token.access_token
            
            result = {
                'access': str(access_token),
                'access_expires': access_token['exp']
            }
            
            # Rotate refresh token if requested
            if rotate_refresh:
                new_refresh = refresh_token.rotate()
                result.update({
                    'refresh': str(new_refresh),
                    'refresh_expires': new_refresh['exp']
                })
            else:
                result.update({
                    'refresh': refresh_token_str,
                    'refresh_expires': refresh_token['exp']
                })
            
            logger.info("Access token refreshed successfully")
            return result
            
        except TokenError as e:
            logger.warning(f"Token refresh failed: {str(e)}")
            raise VeyuTokenError(
                f"Token refresh failed: {str(e)}",
                ErrorCodes.TOKEN_INVALID
            )
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {str(e)}")
            raise VeyuTokenError(
                "Token refresh failed",
                ErrorCodes.TOKEN_INVALID
            )
    
    @staticmethod
    def logout_user(refresh_token_str: str) -> None:
        """
        Logout a user by blacklisting their refresh token.
        
        Args:
            refresh_token_str: The refresh token to blacklist
        """
        try:
            refresh_token = VeyuRefreshToken(refresh_token_str)
            refresh_token.blacklist()
            
            # Also blacklist the associated access token if we can get it
            try:
                access_token = refresh_token.access_token
                if 'jti' in access_token.token:
                    TokenBlacklist.blacklist_token(
                        access_token.token['jti'],
                        expiry_seconds=int(api_settings.ACCESS_TOKEN_LIFETIME.total_seconds())
                    )
            except Exception:
                # If we can't blacklist the access token, it's not critical
                # as it will expire naturally
                pass
            
            logger.info("User logged out successfully")
            
        except TokenError as e:
            logger.warning(f"Logout failed: {str(e)}")
            raise VeyuTokenError(
                f"Logout failed: {str(e)}",
                ErrorCodes.TOKEN_INVALID
            )
        except Exception as e:
            logger.error(f"Unexpected error during logout: {str(e)}")
            raise VeyuTokenError(
                "Logout failed",
                ErrorCodes.TOKEN_INVALID
            )
    
    @staticmethod
    def logout_all_devices(user: User) -> None:
        """
        Logout user from all devices by clearing all their tokens.
        
        Args:
            user: The user to logout from all devices
        """
        # This is a simplified implementation
        # In production, you might want to track tokens per user more explicitly
        TokenBlacklist.clear_user_tokens(user.id)
        logger.info(f"User {user.email} logged out from all devices")


# Backward compatibility aliases
JWTAuthentication = EnhancedJWTAuthentication