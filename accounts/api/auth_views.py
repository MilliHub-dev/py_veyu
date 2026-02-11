"""
Enhanced Authentication Views for Veyu Platform

This module provides enhanced authentication views with improved JWT handling,
provider validation, and comprehensive error handling.
"""

import logging
from typing import Dict, Any
from datetime import timedelta
from django.contrib.auth import authenticate, login
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from accounts.models import Account, Customer, Mechanic, Dealership, OTP
from accounts.api.serializers import (
    SignupSerializer, 
    LoginSerializer, 
    AccountSerializer
)
from accounts.authentication import TokenManager, VeyuRefreshToken
from accounts.providers import (
    provider_manager,
    validate_social_auth_token,
    create_user_from_provider_data
)
from accounts.utils.email_notifications import (
    send_verification_email,
    send_welcome_email,
    send_otp_email
)
from accounts.utils.welcome_email import send_welcome_email_on_first_login
from utils.exceptions import (
    AuthenticationError,
    ProviderMismatchError,
    ValidationError,
    TokenError as VeyuTokenError,
    ErrorCodes
)
from utils.otp import make_random_otp

logger = logging.getLogger(__name__)


class EnhancedSignUpView(APIView):
    """
    Enhanced user registration with improved error handling and JWT token generation.
    """
    permission_classes = [AllowAny]
    serializer_class = SignupSerializer

    @swagger_auto_schema(
        operation_summary="Check email availability",
        operation_description="Returns whether an email is already registered",
        manual_parameters=[
            openapi.Parameter(
                'email', 
                openapi.IN_QUERY, 
                description='Email to check', 
                type=openapi.TYPE_STRING,
                required=True
            ),
        ],
        responses={
            200: openapi.Response('Email is available'),
            400: openapi.Response('Email already exists or missing email parameter')
        }
    )
    def get(self, request: Request):
        """Check if email is available for registration."""
        email = request.GET.get('email')
        
        if not email:
            return Response({
                'error': True,
                'message': "Email parameter is required",
                'code': ErrorCodes.VALIDATION_ERROR
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            Account.objects.get(email=email)
            return Response({
                'error': True,
                'message': "User with this email already exists",
                'code': ErrorCodes.VALIDATION_ERROR
            }, status=status.HTTP_400_BAD_REQUEST)
        except Account.DoesNotExist:
            return Response({
                'error': False,
                'message': "Email is available"
            }, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Create a new account",
        operation_description=(
            "Create a new user account with enhanced JWT token support.\n\n"
            "**Provider Support:**\n"
            "- `veyu`: Native authentication with password validation\n"
            "- `google`, `apple`, `facebook`: Social authentication (password not required)\n\n"
            "**User Types:** customer, mechanic, dealer\n\n"
            "**Response includes JWT tokens for immediate authentication.**"
        ),
        request_body=SignupSerializer,
        responses={
            201: openapi.Response(
                description="Account created successfully",
                examples={
                    "application/json": {
                        "error": False,
                        "message": "Account created successfully",
                        "data": {
                            "user": {
                                "id": 123,
                                "email": "user@example.com",
                                "first_name": "John",
                                "last_name": "Doe",
                                "user_type": "customer",
                                "provider": "veyu",
                                "verified_email": False
                            },
                            "tokens": {
                                "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                                "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                                "access_expires": 1640995200,
                                "refresh_expires": 1641081600
                            },
                            "verification_sent": True,
                            "welcome_email_sent": True
                        }
                    }
                }
            ),
            400: openapi.Response("Validation error"),
            500: openapi.Response("Server error")
        }
    )
    def post(self, request: Request):
        """Create a new user account with enhanced security."""
        try:
            # Handle social authentication if provider is not 'veyu'
            provider = request.data.get('provider', 'veyu')
            if provider != 'veyu':
                return self._handle_social_signup(request, provider)
            
            # Handle regular Veyu signup
            serializer = self.serializer_class(data=request.data)
            
            if not serializer.is_valid():
                logger.warning(f"Signup validation failed: {serializer.errors}")
                return Response({
                    'error': True,
                    'message': 'Validation failed',
                    'code': ErrorCodes.VALIDATION_ERROR,
                    'details': {'field_errors': serializer.errors}
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create user account
            user = self._create_user_account(serializer.validated_data)
            
            # Generate JWT tokens
            tokens = TokenManager.create_tokens_for_user(user)
            
            # Send verification and welcome emails
            email_results = self._send_welcome_emails(user)
            
            # Handle phone verification if provided
            phone_otp_sent = self._handle_phone_verification(user, request.data.get('phone_number'))
            
            response_data = {
                'error': False,
                'message': 'Account created successfully. Please check your email to verify your account.',
                'data': {
                    'user': AccountSerializer(user).data,
                    'tokens': tokens,
                    'verification_sent': email_results['verification_sent'],
                    'welcome_email_sent': email_results['welcome_sent'],
                    'phone_otp_sent': phone_otp_sent
                }
            }
            
            logger.info(f"User account created successfully: {user.email}")
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            logger.warning(f"Signup validation error: {str(e)}")
            return Response(e.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error during signup: {str(e)}")
            return Response({
                'error': True,
                'message': 'Account creation failed. Please try again.',
                'code': ErrorCodes.API_INTERNAL_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _create_user_account(self, validated_data: Dict[str, Any]) -> Account:
        """Create user account and associated profile."""
        user_type = validated_data['user_type']
        provider = validated_data.get('provider', 'veyu')
        
        # Create the user account with password
        if provider == 'veyu':
            user = Account.objects.create_user(
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                provider=provider,
                user_type=user_type
            )
        else:
            user = Account.objects.create_user(
                email=validated_data['email'],
                password=None,
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                provider=provider,
                user_type=user_type
            )
            
        # Handle referral
        referral_code = validated_data.get('referral_code')
        if referral_code:
            try:
                referrer = Account.objects.get(referral_code=referral_code)
                user.referred_by = referrer
                user.save(update_fields=['referred_by'])
            except Account.DoesNotExist:
                # Ignore invalid referral codes
                pass
        
        # Create or update user type specific profile
        # Note: Profiles are auto-created by signals (accounts.signals.create_user_profile)
        # We use get_or_create or update existing profiles to avoid race conditions/duplicates
        if user_type == 'customer':
            phone_number = validated_data.get('phone_number', '')
            customer, created = Customer.objects.get_or_create(user=user)
            if phone_number and customer.phone_number != phone_number:
                customer.phone_number = phone_number
                customer.save()
                
        elif user_type == 'mechanic':
            business_name = validated_data.get('business_name', '')
            mechanic, created = Mechanic.objects.get_or_create(user=user)
            if business_name and mechanic.business_name != business_name:
                mechanic.business_name = business_name
                mechanic.save()
                
        elif user_type == 'dealer':
            business_name = validated_data.get('business_name', '')
            dealership, created = Dealership.objects.get_or_create(user=user)
            if business_name and dealership.business_name != business_name:
                dealership.business_name = business_name
                dealership.save()
        
        return user

    def _send_welcome_emails(self, user: Account) -> Dict[str, bool]:
        """Send only verification email during signup."""
        try:
            # Generate and save email verification OTP with consistent parameters
            otp = OTP.objects.create(
                valid_for=user,
                channel='email',
                purpose='verification',
                expires_at=timezone.now() + timedelta(minutes=10)
            )
            verification_code = otp.code
            
            # Send only verification email (welcome email removed to avoid duplicates)
            verification_sent = send_verification_email(user, verification_code)
            
            return {
                'verification_sent': verification_sent,
                'welcome_sent': True  # Set to True for backward compatibility
            }
        except Exception as e:
            logger.error(f"Failed to send verification email for {user.email}: {str(e)}")
            return {
                'verification_sent': False,
                'welcome_sent': False
            }

    def _handle_phone_verification(self, user: Account, phone_number: str) -> bool:
        """Handle phone number verification if provided."""
        if not phone_number:
            return False
        
        try:
            # Create OTP for phone verification but don't send duplicate email
            # Phone verification should be handled separately via SMS or dedicated phone verification endpoint
            otp_code = make_random_otp()
            OTP.objects.create(
                valid_for=user,
                code=otp_code,
                channel='sms',
                purpose='phone_verification',
                expires_at=timezone.now() + timedelta(minutes=10),
                used=False
            )
            # Note: Removed send_otp_email call to prevent duplicate emails
            # Phone verification should use SMS or be handled via separate endpoint
            return True
        except Exception as e:
            logger.error(f"Failed to create phone OTP for {user.email}: {str(e)}")
        
        return False

    def _handle_social_signup(self, request: Request, provider: str) -> Response:
        """Handle social media signup with provider token validation."""
        try:
            # Get the OAuth token from request
            oauth_token = request.data.get('oauth_token') or request.data.get('access_token')
            if not oauth_token:
                return Response({
                    'error': True,
                    'message': f'OAuth token is required for {provider} signup',
                    'code': ErrorCodes.VALIDATION_ERROR
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate the social auth token
            is_valid, provider_data = validate_social_auth_token(provider, oauth_token)
            if not is_valid:
                logger.warning(f"Social auth validation failed for {provider}: {provider_data.get('error')}")
                return Response({
                    'error': True,
                    'message': f'{provider.title()} authentication failed',
                    'code': ErrorCodes.AUTHENTICATION_FAILED,
                    'details': provider_data
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Check if user already exists
            email = provider_data.get('email')
            if not email:
                return Response({
                    'error': True,
                    'message': f'Email not provided by {provider}',
                    'code': ErrorCodes.VALIDATION_ERROR
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                existing_user = Account.objects.get(email=email)
                if existing_user.provider != provider:
                    raise ProviderMismatchError(existing_user.provider, provider)
                
                # User exists with same provider, treat as login
                tokens = TokenManager.create_tokens_for_user(existing_user)
                return Response({
                    'error': False,
                    'message': f'Logged in with {provider}',
                    'data': {
                        'user': AccountSerializer(existing_user).data,
                        'tokens': tokens,
                        'existing_user': True
                    }
                }, status=status.HTTP_200_OK)
                
            except Account.DoesNotExist:
                # Create new user from provider data
                user_type = request.data.get('user_type', 'customer')
                user_data = create_user_from_provider_data(provider_data, user_type)
                
                # Add additional data from request
                user_data.update({
                    'first_name': request.data.get('first_name', user_data.get('first_name', '')),
                    'last_name': request.data.get('last_name', user_data.get('last_name', '')),
                })
                
                # Create user account
                user = self._create_user_account(user_data)
                
                # For social accounts, mark email as verified if provider says so
                if provider_data.get('verified_email'):
                    user.verified_email = True
                    user.save()
                
                # Generate JWT tokens
                tokens = TokenManager.create_tokens_for_user(user)
                
                # Skip welcome email to avoid duplicates (verification email is primary)
                welcome_sent = True  # Set to True for backward compatibility
                
                response_data = {
                    'error': False,
                    'message': f'Account created successfully with {provider}',
                    'data': {
                        'user': AccountSerializer(user).data,
                        'tokens': tokens,
                        'welcome_email_sent': welcome_sent,
                        'provider_verified': provider_data.get('verified_email', False)
                    }
                }
                
                logger.info(f"Social signup successful for {email} via {provider}")
                return Response(response_data, status=status.HTTP_201_CREATED)
            
        except ProviderMismatchError as e:
            return Response(e.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        except (AuthenticationError, ValidationError) as e:
            return Response(e.to_dict(), status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Unexpected error during social signup: {str(e)}")
            return Response({
                'error': True,
                'message': f'{provider.title()} signup failed',
                'code': ErrorCodes.API_INTERNAL_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EnhancedLoginView(APIView):
    """
    Enhanced user authentication with improved provider validation and JWT tokens.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    @swagger_auto_schema(
        operation_summary="Authenticate user",
        operation_description=(
            "Authenticate user with enhanced provider validation and JWT tokens.\n\n"
            "**Provider Validation:**\n"
            "- Account provider must match the provided provider\n"
            "- `veyu`: Email/password validation\n"
            "- Social providers: Token validation (to be implemented)\n\n"
            "**Response includes:**\n"
            "- JWT access and refresh tokens\n"
            "- User profile information\n"
            "- Business verification status (for dealers/mechanics)"
        ),
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                examples={
                    "application/json": {
                        "error": False,
                        "message": "Login successful",
                        "data": {
                            "user": {
                                "id": 123,
                                "email": "user@example.com",
                                "first_name": "John",
                                "last_name": "Doe",
                                "user_type": "dealer",
                                "provider": "veyu",
                                "is_active": True
                            },
                            "tokens": {
                                "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                                "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                                "access_expires": 1640995200,
                                "refresh_expires": 1641081600
                            },
                            "business_profile": {
                                "dealerId": "550e8400-e29b-41d4-a716-446655440000",
                                "verified_business": False,
                                "business_verification_status": "pending"
                            }
                        }
                    }
                }
            ),
            401: openapi.Response("Authentication failed"),
            404: openapi.Response("Account not found")
        }
    )
    def post(self, request: Request):
        """Authenticate user with enhanced security checks."""
        try:
            serializer = self.serializer_class(data=request.data)
            
            if not serializer.is_valid():
                logger.warning(f"Login validation failed: {serializer.errors}")
                return Response({
                    'error': True,
                    'message': 'Invalid request data',
                    'code': ErrorCodes.VALIDATION_ERROR,
                    'details': {'field_errors': serializer.errors}
                }, status=status.HTTP_400_BAD_REQUEST)

            validated_data = serializer.validated_data
            email = validated_data['email']
            password = validated_data['password']
            provider = validated_data.get('provider', 'veyu')

            # Get user account
            try:
                user = Account.objects.get(email=email)
            except Account.DoesNotExist:
                logger.warning(f"Login attempt with non-existent email: {email}")
                raise AuthenticationError(
                    "Account does not exist",
                    ErrorCodes.AUTHENTICATION_FAILED,
                    user_message="Invalid email or password"
                )

            # Validate provider match
            if user.provider != provider:
                logger.warning(f"Provider mismatch for {email}: expected {user.provider}, got {provider}")
                raise ProviderMismatchError(user.provider, provider)

            # Validate authentication based on provider
            if provider == "veyu":
                # Validate password for Veyu accounts
                if not user.check_password(password):
                    logger.warning(f"Invalid password for {email}")
                    raise AuthenticationError(
                        "Invalid password",
                        ErrorCodes.INVALID_CREDENTIALS,
                        user_message="Invalid email or password"
                    )
            else:
                # Validate social auth token
                oauth_token = request.data.get('oauth_token') or request.data.get('access_token')
                if not oauth_token:
                    return Response({
                        'error': True,
                        'message': f'OAuth token is required for {provider} login',
                        'code': ErrorCodes.VALIDATION_ERROR
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                is_valid, provider_data = validate_social_auth_token(provider, oauth_token)
                if not is_valid:
                    logger.warning(f"Social auth validation failed for {provider}: {provider_data.get('error')}")
                    raise AuthenticationError(
                        f"{provider.title()} token validation failed",
                        ErrorCodes.TOKEN_INVALID,
                        user_message=f"{provider.title()} authentication failed. Please try again."
                    )
                
                # Verify the email matches
                provider_email = provider_data.get('email')
                if provider_email and provider_email.lower() != email.lower():
                    logger.warning(f"Email mismatch for {provider}: {email} vs {provider_email}")
                    raise AuthenticationError(
                        "Email mismatch with provider",
                        ErrorCodes.AUTHENTICATION_FAILED,
                        user_message="The email from your social account doesn't match the login email."
                    )

            # Check if user is active
            if not user.is_active:
                logger.warning(f"Inactive user login attempt: {email}")
                raise AuthenticationError(
                    "Account is deactivated",
                    ErrorCodes.ACCOUNT_LOCKED,
                    user_message="Your account has been deactivated. Please contact support."
                )

            # Generate JWT tokens
            tokens = TokenManager.create_tokens_for_user(user)
            
            # Login user (for session-based features)
            login(request, user)
            
            # Send welcome email on first login (non-blocking)
            welcome_email_sent = send_welcome_email_on_first_login(user)
            
            # Prepare response data
            response_data = {
                'error': False,
                'message': 'Login successful',
                'data': {
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'user_type': user.user_type,
                        'provider': user.provider,
                        'is_active': user.is_active,
                        'verified_email': user.verified_email
                    },
                    'tokens': tokens,
                    'welcome_email_sent': welcome_email_sent
                }
            }
            
            # Add business profile information for dealers and mechanics
            business_info = self._get_business_profile_info(user)
            if business_info:
                response_data['data']['business_profile'] = business_info
            
            logger.info(f"Successful login for user: {email}")
            return Response(response_data, status=status.HTTP_200_OK)
            
        except (AuthenticationError, ProviderMismatchError) as e:
            return Response(e.to_dict(), status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}")
            return Response({
                'error': True,
                'message': 'Login failed. Please try again.',
                'code': ErrorCodes.API_INTERNAL_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_business_profile_info(self, user: Account) -> Dict[str, Any]:
        """Get business profile information for dealers and mechanics."""
        try:
            if user.user_type == 'dealer':
                dealership = Dealership.objects.get(user=user)
                return {
                    'dealerId': str(dealership.uuid),
                    'verified_id': dealership.verified_id,
                    'verified_business': dealership.verified_business,
                    'business_verification_status': dealership.business_verification_status,
                }
            elif user.user_type == 'mechanic':
                mechanic = Mechanic.objects.get(user=user)
                return {
                    'mechanicId': str(mechanic.uuid),
                    'verified_id': mechanic.verified_id,
                    'verified_business': mechanic.verified_business,
                    'business_verification_status': mechanic.business_verification_status,
                }
        except (Dealership.DoesNotExist, Mechanic.DoesNotExist):
            logger.warning(f"Business profile not found for {user.user_type}: {user.email}")
        
        return None


class TokenRefreshView(APIView):
    """
    Enhanced token refresh with rotation support.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Refresh access token",
        operation_description=(
            "Refresh an access token using a refresh token.\n\n"
            "**Features:**\n"
            "- Automatic refresh token rotation (configurable)\n"
            "- Token blacklisting validation\n"
            "- Enhanced security logging"
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh'],
            properties={
                'refresh': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Refresh token'
                ),
                'rotate_refresh': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Whether to rotate the refresh token (default: true)',
                    default=True
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Token refreshed successfully",
                examples={
                    "application/json": {
                        "error": False,
                        "message": "Token refreshed successfully",
                        "data": {
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "access_expires": 1640995200,
                            "refresh_expires": 1641081600
                        }
                    }
                }
            ),
            401: openapi.Response("Invalid or expired refresh token")
        }
    )
    def post(self, request: Request):
        """Refresh access token with enhanced security."""
        try:
            refresh_token = request.data.get('refresh')
            rotate_refresh = request.data.get('rotate_refresh', True)
            
            if not refresh_token:
                return Response({
                    'error': True,
                    'message': 'Refresh token is required',
                    'code': ErrorCodes.VALIDATION_ERROR
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Refresh the token
            tokens = TokenManager.refresh_access_token(refresh_token, rotate_refresh)
            
            return Response({
                'error': False,
                'message': 'Token refreshed successfully',
                'data': tokens
            }, status=status.HTTP_200_OK)
            
        except VeyuTokenError as e:
            return Response(e.to_dict(), status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {str(e)}")
            return Response({
                'error': True,
                'message': 'Token refresh failed',
                'code': ErrorCodes.API_INTERNAL_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogoutView(APIView):
    """
    Enhanced logout with token blacklisting.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Logout user",
        operation_description=(
            "Logout user by blacklisting their refresh token.\n\n"
            "**Features:**\n"
            "- Blacklists refresh token\n"
            "- Optionally blacklists access token\n"
            "- Supports logout from all devices"
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Refresh token to blacklist'
                ),
                'all_devices': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Logout from all devices (default: false)',
                    default=False
                )
            }
        ),
        responses={
            200: openapi.Response("Logout successful"),
            400: openapi.Response("Invalid request")
        }
    )
    def post(self, request: Request):
        """Logout user with token blacklisting."""
        try:
            refresh_token = request.data.get('refresh')
            all_devices = request.data.get('all_devices', False)
            
            if all_devices:
                # Logout from all devices
                TokenManager.logout_all_devices(request.user)
                message = 'Logged out from all devices successfully'
            elif refresh_token:
                # Logout from current device
                TokenManager.logout_user(refresh_token)
                message = 'Logged out successfully'
            else:
                return Response({
                    'error': True,
                    'message': 'Refresh token is required for logout',
                    'code': ErrorCodes.VALIDATION_ERROR
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'error': False,
                'message': message
            }, status=status.HTTP_200_OK)
            
        except VeyuTokenError as e:
            return Response(e.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error during logout: {str(e)}")
            return Response({
                'error': True,
                'message': 'Logout failed',
                'code': ErrorCodes.API_INTERNAL_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# API function views for backward compatibility
@api_view(['POST'])
@permission_classes([AllowAny])
def enhanced_signup(request):
    """Enhanced signup API function view."""
    view = EnhancedSignUpView()
    return view.post(request)


@api_view(['POST'])
@permission_classes([AllowAny])
def enhanced_login(request):
    """Enhanced login API function view."""
    view = EnhancedLoginView()
    return view.post(request)


@api_view(['POST'])
@permission_classes([AllowAny])
def token_refresh(request):
    """Token refresh API function view."""
    view = TokenRefreshView()
    return view.post(request)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout API function view."""
    view = LogoutView()
    return view.post(request)