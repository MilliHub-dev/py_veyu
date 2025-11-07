"""
Password Reset API Views for Veyu Platform

This module provides API endpoints for password reset functionality
with comprehensive validation and security measures.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from accounts.password_reset import (
    initiate_password_reset,
    reset_password_with_token,
    validate_password_reset_token
)
from utils.exceptions import (
    ValidationError,
    AuthenticationError,
    ErrorCodes
)

logger = logging.getLogger(__name__)


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request."""
    
    email = serializers.EmailField(
        required=True,
        help_text="Email address of the account to reset password for"
    )
    
    class Meta:
        swagger_schema_fields = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation."""
    
    token = serializers.CharField(
        required=True,
        help_text="Password reset token received via email"
    )
    new_password = serializers.CharField(
        required=True,
        min_length=8,
        max_length=128,
        write_only=True,
        help_text="New password (minimum 8 characters, must contain letters and numbers)",
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Confirm new password",
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs
    
    class Meta:
        swagger_schema_fields = {
            "example": {
                "token": "abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
                "new_password": "NewSecurePass123!",
                "confirm_password": "NewSecurePass123!"
            }
        }


class PasswordResetTokenValidationSerializer(serializers.Serializer):
    """Serializer for password reset token validation."""
    
    token = serializers.CharField(
        required=True,
        help_text="Password reset token to validate"
    )
    
    class Meta:
        swagger_schema_fields = {
            "example": {
                "token": "abc123def456ghi789jkl012mno345pqr678stu901vwx234yz"
            }
        }


class PasswordResetRequestView(APIView):
    """
    API view for requesting password reset.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    @swagger_auto_schema(
        operation_summary="Request password reset",
        operation_description=(
            "Request a password reset link to be sent to the specified email address.\n\n"
            "**Security Features:**\n"
            "- Rate limiting (max 3 requests per hour per email)\n"
            "- Doesn't reveal if email exists in system\n"
            "- Only works for Veyu native accounts (not social auth)\n"
            "- Secure token generation with 1-hour expiry\n\n"
            "**Process:**\n"
            "1. Submit email address\n"
            "2. If account exists and uses Veyu auth, reset email is sent\n"
            "3. User clicks link in email to reset password\n"
            "4. Use the token from email with the reset confirmation endpoint"
        ),
        request_body=PasswordResetRequestSerializer,
        responses={
            200: openapi.Response(
                description="Reset request processed (always returns success for security)",
                examples={
                    "application/json": {
                        "error": False,
                        "message": "If an account with this email exists, you will receive a password reset link.",
                        "data": {
                            "email_sent": True
                        }
                    }
                }
            ),
            400: openapi.Response("Invalid email format or rate limit exceeded"),
            429: openapi.Response("Too many requests")
        },
        tags=['Authentication', 'Password Reset']
    )
    def post(self, request: Request):
        """Request password reset for an email address."""
        try:
            serializer = self.serializer_class(data=request.data)
            
            if not serializer.is_valid():
                logger.warning(f"Password reset request validation failed: {serializer.errors}")
                return Response({
                    'error': True,
                    'message': 'Invalid email address',
                    'code': ErrorCodes.VALIDATION_ERROR,
                    'details': {'field_errors': serializer.errors}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            email = serializer.validated_data['email']
            
            # Initiate password reset
            result = initiate_password_reset(email)
            
            # Always return success for security (don't reveal if email exists)
            response_data = {
                'error': False,
                'message': result['message'],
                'data': {
                    'email_sent': result.get('email_sent', False)
                }
            }
            
            # Include additional info for social auth users
            if not result['success'] and 'provider' in result:
                response_data.update({
                    'error': True,
                    'message': result['message'],
                    'data': {
                        'provider': result['provider'],
                        'email_sent': False
                    }
                })
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"Password reset requested for: {email}")
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            if e.error_code == ErrorCodes.API_RATE_LIMIT_EXCEEDED:
                return Response(e.to_dict(), status=status.HTTP_429_TOO_MANY_REQUESTS)
            return Response(e.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error during password reset request: {str(e)}")
            return Response({
                'error': True,
                'message': 'Password reset request failed. Please try again.',
                'code': ErrorCodes.API_INTERNAL_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordResetConfirmView(APIView):
    """
    API view for confirming password reset with token.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    @swagger_auto_schema(
        operation_summary="Confirm password reset",
        operation_description=(
            "Reset password using the token received via email.\n\n"
            "**Security Features:**\n"
            "- Token validation with expiry check\n"
            "- One-time use tokens (cannot be reused)\n"
            "- Password strength validation\n"
            "- Prevents setting same password as current\n\n"
            "**Password Requirements:**\n"
            "- Minimum 8 characters\n"
            "- Maximum 128 characters\n"
            "- Must contain at least one letter and one number\n"
            "- Cannot be a common weak password\n"
            "- Must be different from current password"
        ),
        request_body=PasswordResetConfirmSerializer,
        responses={
            200: openapi.Response(
                description="Password reset successful",
                examples={
                    "application/json": {
                        "error": False,
                        "message": "Password has been reset successfully. Please log in with your new password.",
                        "data": {
                            "success": True
                        }
                    }
                }
            ),
            400: openapi.Response("Invalid token or password validation failed"),
            401: openapi.Response("Invalid or expired token")
        },
        tags=['Authentication', 'Password Reset']
    )
    def post(self, request: Request):
        """Confirm password reset with token and new password."""
        try:
            serializer = self.serializer_class(data=request.data)
            
            if not serializer.is_valid():
                logger.warning(f"Password reset confirmation validation failed: {serializer.errors}")
                return Response({
                    'error': True,
                    'message': 'Validation failed',
                    'code': ErrorCodes.VALIDATION_ERROR,
                    'details': {'field_errors': serializer.errors}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            
            # Reset password
            result = reset_password_with_token(token, new_password)
            
            response_data = {
                'error': False,
                'message': result['message'],
                'data': {
                    'success': result['success']
                }
            }
            
            logger.info(f"Password reset completed for user ID: {result.get('user_id')}")
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            if e.error_code == ErrorCodes.TOKEN_INVALID:
                return Response(e.to_dict(), status=status.HTTP_401_UNAUTHORIZED)
            return Response(e.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error during password reset confirmation: {str(e)}")
            return Response({
                'error': True,
                'message': 'Password reset failed. Please try again.',
                'code': ErrorCodes.API_INTERNAL_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordResetTokenValidationView(APIView):
    """
    API view for validating password reset tokens.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetTokenValidationSerializer

    @swagger_auto_schema(
        operation_summary="Validate password reset token",
        operation_description=(
            "Validate a password reset token without using it.\n\n"
            "This endpoint allows frontend applications to check if a reset token\n"
            "is valid before showing the password reset form to the user.\n\n"
            "**Use Cases:**\n"
            "- Validate token when user clicks reset link\n"
            "- Show appropriate UI based on token validity\n"
            "- Provide user feedback for expired/invalid tokens"
        ),
        request_body=PasswordResetTokenValidationSerializer,
        responses={
            200: openapi.Response(
                description="Token validation result",
                examples={
                    "application/json": {
                        "error": False,
                        "message": "Token is valid",
                        "data": {
                            "valid": True,
                            "user_email": "user@example.com",
                            "expires_soon": False
                        }
                    }
                }
            ),
            400: openapi.Response("Invalid request"),
            401: openapi.Response("Invalid or expired token")
        },
        tags=['Authentication', 'Password Reset']
    )
    def post(self, request: Request):
        """Validate a password reset token."""
        try:
            serializer = self.serializer_class(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'error': True,
                    'message': 'Invalid request',
                    'code': ErrorCodes.VALIDATION_ERROR,
                    'details': {'field_errors': serializer.errors}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = serializer.validated_data['token']
            
            # Validate token
            is_valid, user, error_message = validate_password_reset_token(token)
            
            if not is_valid:
                return Response({
                    'error': True,
                    'message': error_message or 'Invalid token',
                    'code': ErrorCodes.TOKEN_INVALID,
                    'data': {
                        'valid': False
                    }
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            response_data = {
                'error': False,
                'message': 'Token is valid',
                'data': {
                    'valid': True,
                    'user_email': user.email,
                    'expires_soon': False  # Could implement expiry warning logic here
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {str(e)}")
            return Response({
                'error': True,
                'message': 'Token validation failed',
                'code': ErrorCodes.API_INTERNAL_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Function-based views for backward compatibility
@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    """Function-based view for password reset request."""
    view = PasswordResetRequestView()
    return view.post(request)


@api_view(['POST'])
@permission_classes([AllowAny])
def confirm_password_reset(request):
    """Function-based view for password reset confirmation."""
    view = PasswordResetConfirmView()
    return view.post(request)


@api_view(['POST'])
@permission_classes([AllowAny])
def validate_reset_token(request):
    """Function-based view for token validation."""
    view = PasswordResetTokenValidationView()
    return view.post(request)