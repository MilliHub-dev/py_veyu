"""
Veyu Platform Exception Classes

This module defines the exception hierarchy for the Veyu platform,
providing structured error handling with consistent error codes.
"""

import uuid
from typing import Dict, Any, Optional


class ErrorCodes:
    """Constants for error codes used throughout the platform"""
    
    # General errors
    GENERAL_ERROR = "GENERAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    NOT_FOUND = "NOT_FOUND"
    
    # Email errors
    EMAIL_DELIVERY_FAILED = "EMAIL_DELIVERY_FAILED"
    EMAIL_TEMPLATE_NOT_FOUND = "EMAIL_TEMPLATE_NOT_FOUND"
    EMAIL_CONFIGURATION_ERROR = "EMAIL_CONFIGURATION_ERROR"
    EMAIL_SMTP_ERROR = "EMAIL_SMTP_ERROR"
    
    # Authentication errors
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    TOKEN_INVALID = "TOKEN_INVALID"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    PROVIDER_MISMATCH = "PROVIDER_MISMATCH"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    
    # Business verification errors
    VERIFICATION_DOCUMENT_INVALID = "VERIFICATION_DOCUMENT_INVALID"
    VERIFICATION_ALREADY_SUBMITTED = "VERIFICATION_ALREADY_SUBMITTED"
    VERIFICATION_NOT_FOUND = "VERIFICATION_NOT_FOUND"
    VERIFICATION_STATUS_INVALID = "VERIFICATION_STATUS_INVALID"
    
    # API errors
    API_RATE_LIMIT_EXCEEDED = "API_RATE_LIMIT_EXCEEDED"
    API_INVALID_REQUEST = "API_INVALID_REQUEST"
    API_INTERNAL_ERROR = "API_INTERNAL_ERROR"
    API_SERVICE_UNAVAILABLE = "API_SERVICE_UNAVAILABLE"
    
    # Database errors
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    DATABASE_CONSTRAINT_VIOLATION = "DATABASE_CONSTRAINT_VIOLATION"
    DATABASE_TRANSACTION_ERROR = "DATABASE_TRANSACTION_ERROR"
    
    # OTP errors
    OTP_INVALID = "OTP_INVALID"
    OTP_EXPIRED = "OTP_EXPIRED"
    OTP_ALREADY_USED = "OTP_ALREADY_USED"
    OTP_GENERATION_FAILED = "OTP_GENERATION_FAILED"


class VeyuException(Exception):
    """
    Base exception class for all Veyu platform errors.
    
    Provides structured error handling with error codes, user-friendly messages,
    and additional context for debugging.
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = ErrorCodes.GENERAL_ERROR,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.user_message = user_message or message
        self.trace_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            'error': True,
            'message': self.user_message,
            'code': self.error_code,
            'details': self.details,
            'trace_id': self.trace_id
        }
    
    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


class EmailDeliveryError(VeyuException):
    """Exception raised when email delivery fails"""
    
    def __init__(
        self,
        message: str,
        error_code: str = ErrorCodes.EMAIL_DELIVERY_FAILED,
        details: Optional[Dict[str, Any]] = None,
        user_message: str = "Failed to send email. Please try again later."
    ):
        super().__init__(message, error_code, details, user_message)


class EmailTemplateError(EmailDeliveryError):
    """Exception raised when email template is not found or invalid"""
    
    def __init__(
        self,
        template_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Email template '{template_name}' not found or invalid"
        user_message = "Email template error. Please contact support."
        details = details or {}
        details['template_name'] = template_name
        
        super().__init__(
            message,
            ErrorCodes.EMAIL_TEMPLATE_NOT_FOUND,
            details,
            user_message
        )


class EmailConfigurationError(EmailDeliveryError):
    """Exception raised when email configuration is invalid"""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        user_message = "Email service configuration error. Please contact support."
        super().__init__(
            message,
            ErrorCodes.EMAIL_CONFIGURATION_ERROR,
            details,
            user_message
        )


class EmailSMTPError(EmailDeliveryError):
    """Exception raised when SMTP connection or sending fails"""
    
    def __init__(
        self,
        message: str,
        smtp_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if smtp_code:
            details['smtp_code'] = smtp_code
        
        user_message = "Email service temporarily unavailable. Please try again later."
        super().__init__(
            message,
            ErrorCodes.EMAIL_SMTP_ERROR,
            details,
            user_message
        )


class AuthenticationError(VeyuException):
    """Exception raised for authentication-related errors"""
    
    def __init__(
        self,
        message: str,
        error_code: str = ErrorCodes.AUTHENTICATION_FAILED,
        details: Optional[Dict[str, Any]] = None,
        user_message: str = "Authentication failed. Please check your credentials."
    ):
        super().__init__(message, error_code, details, user_message)


class TokenError(AuthenticationError):
    """Exception raised for JWT token-related errors"""
    
    def __init__(
        self,
        message: str,
        error_code: str = ErrorCodes.TOKEN_INVALID,
        details: Optional[Dict[str, Any]] = None
    ):
        user_message = "Invalid or expired token. Please log in again."
        super().__init__(message, error_code, details, user_message)


class ProviderMismatchError(AuthenticationError):
    """Exception raised when authentication provider doesn't match"""
    
    def __init__(
        self,
        expected_provider: str,
        actual_provider: str,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Provider mismatch: expected {expected_provider}, got {actual_provider}"
        user_message = "Please use the correct login method for your account."
        details = details or {}
        details.update({
            'expected_provider': expected_provider,
            'actual_provider': actual_provider
        })
        
        super().__init__(
            message,
            ErrorCodes.PROVIDER_MISMATCH,
            details,
            user_message
        )


class ValidationError(VeyuException):
    """Exception raised for data validation errors"""
    
    def __init__(
        self,
        message: str,
        field_errors: Optional[Dict[str, str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if field_errors:
            details['field_errors'] = field_errors
        
        user_message = "Please check the provided information and try again."
        super().__init__(
            message,
            ErrorCodes.VALIDATION_ERROR,
            details,
            user_message
        )


class BusinessVerificationError(VeyuException):
    """Exception raised for business verification-related errors"""
    
    def __init__(
        self,
        message: str,
        error_code: str = ErrorCodes.VERIFICATION_DOCUMENT_INVALID,
        details: Optional[Dict[str, Any]] = None,
        user_message: str = "Business verification error. Please check your documents."
    ):
        super().__init__(message, error_code, details, user_message)


class DocumentValidationError(BusinessVerificationError):
    """Exception raised when business verification documents are invalid"""
    
    def __init__(
        self,
        document_type: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Invalid {document_type}: {reason}"
        user_message = f"The {document_type} document is invalid. {reason}"
        details = details or {}
        details.update({
            'document_type': document_type,
            'validation_reason': reason
        })
        
        super().__init__(
            message,
            ErrorCodes.VERIFICATION_DOCUMENT_INVALID,
            details,
            user_message
        )


class APIError(VeyuException):
    """Exception raised for API-related errors"""
    
    def __init__(
        self,
        message: str,
        error_code: str = ErrorCodes.API_INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None,
        user_message: str = "An error occurred while processing your request."
    ):
        super().__init__(message, error_code, details, user_message)


class RateLimitError(APIError):
    """Exception raised when API rate limit is exceeded"""
    
    def __init__(
        self,
        limit: int,
        window: int,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Rate limit exceeded: {limit} requests per {window} seconds"
        user_message = "Too many requests. Please wait before trying again."
        details = details or {}
        details.update({
            'rate_limit': limit,
            'window_seconds': window
        })
        
        super().__init__(
            message,
            ErrorCodes.API_RATE_LIMIT_EXCEEDED,
            details,
            user_message
        )


class DatabaseError(VeyuException):
    """Exception raised for database-related errors"""
    
    def __init__(
        self,
        message: str,
        error_code: str = ErrorCodes.DATABASE_CONNECTION_ERROR,
        details: Optional[Dict[str, Any]] = None,
        user_message: str = "Database error occurred. Please try again later."
    ):
        super().__init__(message, error_code, details, user_message)


class DatabaseConstraintError(DatabaseError):
    """Exception raised when database constraint is violated"""
    
    def __init__(
        self,
        constraint_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Database constraint violation: {constraint_name}"
        user_message = "The operation violates data integrity rules."
        details = details or {}
        details['constraint_name'] = constraint_name
        
        super().__init__(
            message,
            ErrorCodes.DATABASE_CONSTRAINT_VIOLATION,
            details,
            user_message
        )


class OTPError(VeyuException):
    """Exception raised for OTP-related errors"""
    
    def __init__(
        self,
        message: str,
        error_code: str = ErrorCodes.OTP_INVALID,
        details: Optional[Dict[str, Any]] = None,
        user_message: str = "Invalid OTP code. Please try again."
    ):
        super().__init__(message, error_code, details, user_message)


class OTPExpiredError(OTPError):
    """Exception raised when OTP has expired"""
    
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        message = "OTP code has expired"
        user_message = "The OTP code has expired. Please request a new one."
        super().__init__(
            message,
            ErrorCodes.OTP_EXPIRED,
            details,
            user_message
        )


class OTPAlreadyUsedError(OTPError):
    """Exception raised when OTP has already been used"""
    
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        message = "OTP code has already been used"
        user_message = "This OTP code has already been used. Please request a new one."
        super().__init__(
            message,
            ErrorCodes.OTP_ALREADY_USED,
            details,
            user_message
        )