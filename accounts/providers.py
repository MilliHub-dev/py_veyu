"""
Social Media Provider Authentication for Veyu Platform

This module provides authentication validation for external OAuth providers
including Google, Apple, and Facebook.
"""

import logging
import requests
from typing import Dict, Any, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
from abc import ABC, abstractmethod
from utils.exceptions import (
    AuthenticationError,
    ProviderMismatchError,
    ValidationError,
    ErrorCodes
)

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """
    Abstract base class for OAuth provider validation.
    """
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.timeout = getattr(settings, 'OAUTH_VALIDATION_TIMEOUT', 10)
    
    @abstractmethod
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate the OAuth token and return user information.
        
        Args:
            token: The OAuth access token
            
        Returns:
            Dictionary containing user information
            
        Raises:
            AuthenticationError: If token validation fails
        """
        pass
    
    def get_cache_key(self, token: str) -> str:
        """Generate cache key for token validation results."""
        return f"oauth_validation:{self.provider_name}:{token[:16]}"
    
    def cache_validation_result(self, token: str, result: Dict[str, Any], timeout: int = 300) -> None:
        """Cache validation result to reduce API calls."""
        cache_key = self.get_cache_key(token)
        cache.set(cache_key, result, timeout=timeout)
    
    def get_cached_validation(self, token: str) -> Optional[Dict[str, Any]]:
        """Get cached validation result."""
        cache_key = self.get_cache_key(token)
        return cache.get(cache_key)


class GoogleProvider(BaseProvider):
    """
    Google OAuth provider validation.
    """
    
    def __init__(self):
        super().__init__('google')
        self.validation_url = 'https://www.googleapis.com/oauth2/v1/tokeninfo'
        self.userinfo_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate Google OAuth token.
        
        Args:
            token: Google OAuth access token
            
        Returns:
            Dictionary containing user information
        """
        # Check cache first
        cached_result = self.get_cached_validation(token)
        if cached_result:
            logger.info("Using cached Google token validation")
            return cached_result
        
        try:
            # Validate token
            validation_response = requests.get(
                self.validation_url,
                params={'access_token': token},
                timeout=self.timeout
            )
            
            if validation_response.status_code != 200:
                logger.warning(f"Google token validation failed: {validation_response.status_code}")
                raise AuthenticationError(
                    "Invalid Google token",
                    ErrorCodes.TOKEN_INVALID,
                    user_message="Google authentication failed. Please try again."
                )
            
            validation_data = validation_response.json()
            
            # Check if token is for our application (if client_id is configured)
            google_client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', None)
            if google_client_id and validation_data.get('audience') != google_client_id:
                logger.warning("Google token audience mismatch")
                raise AuthenticationError(
                    "Google token audience mismatch",
                    ErrorCodes.TOKEN_INVALID,
                    user_message="Invalid Google token for this application."
                )
            
            # Get user information
            userinfo_response = requests.get(
                self.userinfo_url,
                headers={'Authorization': f'Bearer {token}'},
                timeout=self.timeout
            )
            
            if userinfo_response.status_code != 200:
                logger.warning(f"Google userinfo request failed: {userinfo_response.status_code}")
                raise AuthenticationError(
                    "Failed to get Google user information",
                    ErrorCodes.AUTHENTICATION_FAILED,
                    user_message="Failed to retrieve Google account information."
                )
            
            userinfo = userinfo_response.json()
            
            result = {
                'provider': 'google',
                'provider_id': userinfo.get('id'),
                'email': userinfo.get('email'),
                'first_name': userinfo.get('given_name', ''),
                'last_name': userinfo.get('family_name', ''),
                'verified_email': userinfo.get('verified_email', False),
                'picture': userinfo.get('picture'),
                'raw_data': userinfo
            }
            
            # Cache the result
            self.cache_validation_result(token, result)
            
            logger.info(f"Google token validated successfully for email: {result['email']}")
            return result
            
        except requests.RequestException as e:
            logger.error(f"Google API request failed: {str(e)}")
            raise AuthenticationError(
                f"Google API request failed: {str(e)}",
                ErrorCodes.API_SERVICE_UNAVAILABLE,
                user_message="Google authentication service is temporarily unavailable."
            )
        except Exception as e:
            logger.error(f"Unexpected error during Google token validation: {str(e)}")
            raise AuthenticationError(
                "Google token validation failed",
                ErrorCodes.AUTHENTICATION_FAILED,
                user_message="Google authentication failed. Please try again."
            )


class FacebookProvider(BaseProvider):
    """
    Facebook OAuth provider validation.
    """
    
    def __init__(self):
        super().__init__('facebook')
        self.validation_url = 'https://graph.facebook.com/me'
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate Facebook OAuth token.
        
        Args:
            token: Facebook OAuth access token
            
        Returns:
            Dictionary containing user information
        """
        # Check cache first
        cached_result = self.get_cached_validation(token)
        if cached_result:
            logger.info("Using cached Facebook token validation")
            return cached_result
        
        try:
            # Get user information with token validation
            response = requests.get(
                self.validation_url,
                params={
                    'access_token': token,
                    'fields': 'id,email,first_name,last_name,verified,picture'
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.warning(f"Facebook token validation failed: {response.status_code}")
                raise AuthenticationError(
                    "Invalid Facebook token",
                    ErrorCodes.TOKEN_INVALID,
                    user_message="Facebook authentication failed. Please try again."
                )
            
            userinfo = response.json()
            
            # Check for error in response
            if 'error' in userinfo:
                error_msg = userinfo['error'].get('message', 'Unknown error')
                logger.warning(f"Facebook API error: {error_msg}")
                raise AuthenticationError(
                    f"Facebook API error: {error_msg}",
                    ErrorCodes.TOKEN_INVALID,
                    user_message="Facebook authentication failed. Please try again."
                )
            
            result = {
                'provider': 'facebook',
                'provider_id': userinfo.get('id'),
                'email': userinfo.get('email'),
                'first_name': userinfo.get('first_name', ''),
                'last_name': userinfo.get('last_name', ''),
                'verified_email': userinfo.get('verified', False),
                'picture': userinfo.get('picture', {}).get('data', {}).get('url'),
                'raw_data': userinfo
            }
            
            # Cache the result
            self.cache_validation_result(token, result)
            
            logger.info(f"Facebook token validated successfully for email: {result['email']}")
            return result
            
        except requests.RequestException as e:
            logger.error(f"Facebook API request failed: {str(e)}")
            raise AuthenticationError(
                f"Facebook API request failed: {str(e)}",
                ErrorCodes.API_SERVICE_UNAVAILABLE,
                user_message="Facebook authentication service is temporarily unavailable."
            )
        except Exception as e:
            logger.error(f"Unexpected error during Facebook token validation: {str(e)}")
            raise AuthenticationError(
                "Facebook token validation failed",
                ErrorCodes.AUTHENTICATION_FAILED,
                user_message="Facebook authentication failed. Please try again."
            )


class AppleProvider(BaseProvider):
    """
    Apple OAuth provider validation.
    
    Note: Apple Sign-In uses JWT tokens that need to be validated differently.
    This is a simplified implementation that would need to be enhanced for production.
    """
    
    def __init__(self):
        super().__init__('apple')
        self.validation_url = 'https://appleid.apple.com/auth/keys'
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate Apple OAuth token (JWT).
        
        Args:
            token: Apple OAuth JWT token
            
        Returns:
            Dictionary containing user information
            
        Note:
            This is a simplified implementation. Production should include:
            - JWT signature validation using Apple's public keys
            - Proper audience and issuer validation
            - Nonce validation if used
        """
        # Check cache first
        cached_result = self.get_cached_validation(token)
        if cached_result:
            logger.info("Using cached Apple token validation")
            return cached_result
        
        try:
            import jwt
            from jwt.exceptions import InvalidTokenError
            
            # For now, we'll decode without verification (NOT RECOMMENDED FOR PRODUCTION)
            # In production, you should validate the signature using Apple's public keys
            decoded_token = jwt.decode(token, options={"verify_signature": False})
            
            # Basic validation
            if decoded_token.get('iss') != 'https://appleid.apple.com':
                raise AuthenticationError(
                    "Invalid Apple token issuer",
                    ErrorCodes.TOKEN_INVALID,
                    user_message="Invalid Apple token."
                )
            
            # Extract user information
            result = {
                'provider': 'apple',
                'provider_id': decoded_token.get('sub'),
                'email': decoded_token.get('email'),
                'first_name': '',  # Apple doesn't always provide names in JWT
                'last_name': '',
                'verified_email': decoded_token.get('email_verified', False),
                'picture': None,  # Apple doesn't provide profile pictures
                'raw_data': decoded_token
            }
            
            # Cache the result
            self.cache_validation_result(token, result)
            
            logger.info(f"Apple token validated successfully for email: {result['email']}")
            return result
            
        except ImportError:
            logger.error("PyJWT library not installed for Apple token validation")
            raise AuthenticationError(
                "Apple authentication not properly configured",
                ErrorCodes.API_INTERNAL_ERROR,
                user_message="Apple authentication is temporarily unavailable."
            )
        except InvalidTokenError as e:
            logger.warning(f"Apple JWT validation failed: {str(e)}")
            raise AuthenticationError(
                f"Invalid Apple token: {str(e)}",
                ErrorCodes.TOKEN_INVALID,
                user_message="Apple authentication failed. Please try again."
            )
        except Exception as e:
            logger.error(f"Unexpected error during Apple token validation: {str(e)}")
            raise AuthenticationError(
                "Apple token validation failed",
                ErrorCodes.AUTHENTICATION_FAILED,
                user_message="Apple authentication failed. Please try again."
            )


class ProviderManager:
    """
    Manager class for handling multiple OAuth providers.
    """
    
    def __init__(self):
        self.providers = {
            'google': GoogleProvider(),
            'facebook': FacebookProvider(),
            'apple': AppleProvider(),
        }
    
    def get_provider(self, provider_name: str) -> BaseProvider:
        """
        Get provider instance by name.
        
        Args:
            provider_name: Name of the provider (google, facebook, apple)
            
        Returns:
            Provider instance
            
        Raises:
            ValidationError: If provider is not supported
        """
        if provider_name not in self.providers:
            raise ValidationError(
                f"Unsupported provider: {provider_name}",
                details={'supported_providers': list(self.providers.keys())},
                user_message=f"Authentication provider '{provider_name}' is not supported."
            )
        
        return self.providers[provider_name]
    
    def validate_provider_token(self, provider_name: str, token: str) -> Dict[str, Any]:
        """
        Validate token for a specific provider.
        
        Args:
            provider_name: Name of the provider
            token: OAuth token to validate
            
        Returns:
            Dictionary containing validated user information
        """
        provider = self.get_provider(provider_name)
        return provider.validate_token(token)
    
    def is_provider_supported(self, provider_name: str) -> bool:
        """Check if a provider is supported."""
        return provider_name in self.providers
    
    def get_supported_providers(self) -> list:
        """Get list of supported providers."""
        return list(self.providers.keys())


# Global provider manager instance
provider_manager = ProviderManager()


def validate_social_auth_token(provider: str, token: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Convenience function to validate social authentication tokens.
    
    Args:
        provider: Provider name (google, facebook, apple)
        token: OAuth token to validate
        
    Returns:
        Tuple of (is_valid, user_data)
    """
    try:
        user_data = provider_manager.validate_provider_token(provider, token)
        return True, user_data
    except (AuthenticationError, ValidationError) as e:
        logger.warning(f"Social auth validation failed for {provider}: {str(e)}")
        return False, {'error': str(e)}
    except Exception as e:
        logger.error(f"Unexpected error during social auth validation: {str(e)}")
        return False, {'error': 'Authentication validation failed'}


def create_user_from_provider_data(provider_data: Dict[str, Any], user_type: str = 'customer') -> Dict[str, Any]:
    """
    Create user data dictionary from provider validation result.
    
    Args:
        provider_data: Data returned from provider validation
        user_type: Type of user account to create
        
    Returns:
        Dictionary suitable for user creation
    """
    return {
        'email': provider_data.get('email'),
        'first_name': provider_data.get('first_name', ''),
        'last_name': provider_data.get('last_name', ''),
        'provider': provider_data.get('provider'),
        'user_type': user_type,
        'verified_email': provider_data.get('verified_email', False),
        'provider_id': provider_data.get('provider_id'),
        'profile_picture_url': provider_data.get('picture')
    }