"""
Utilities for digital signature validation and security
"""
import hashlib
import hmac
import base64
import json
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class SignatureValidator:
    """
    Utility class for validating digital signatures and ensuring tamper-proof mechanisms
    """
    
    @staticmethod
    def validate_signature_image(signature_data: str) -> Tuple[bool, str]:
        """
        Validate signature image format and basic security checks
        
        Args:
            signature_data: Base64 encoded signature image data
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if it's a valid data URL
            if not signature_data.startswith('data:image/'):
                return False, "Invalid signature image format"
            
            # Extract the base64 part
            if ';base64,' not in signature_data:
                return False, "Invalid base64 encoding"
            
            header, encoded = signature_data.split(';base64,', 1)
            
            # Validate image type
            allowed_types = ['data:image/png', 'data:image/jpeg', 'data:image/jpg']
            if header not in allowed_types:
                return False, f"Unsupported image type. Allowed: {', '.join(allowed_types)}"
            
            # Decode and validate base64
            try:
                decoded = base64.b64decode(encoded)
            except Exception:
                return False, "Invalid base64 encoding"
            
            # Check file size (max 1MB)
            max_size = 1024 * 1024  # 1MB
            if len(decoded) > max_size:
                return False, f"Signature image too large. Max size: {max_size} bytes"
            
            # Basic image validation (check for PNG/JPEG headers)
            if header == 'data:image/png' and not decoded.startswith(b'\x89PNG'):
                return False, "Invalid PNG image data"
            elif header in ['data:image/jpeg', 'data:image/jpg'] and not decoded.startswith(b'\xff\xd8'):
                return False, "Invalid JPEG image data"
            
            return True, "Valid signature image"
            
        except Exception as e:
            logger.error(f"Error validating signature image: {str(e)}")
            return False, "Signature validation failed"
    
    @staticmethod
    def generate_signature_hash(document_id: int, signer_id: int, timestamp: datetime, signature_data: str) -> str:
        """
        Generate a secure hash for signature verification
        
        Args:
            document_id: ID of the document being signed
            signer_id: ID of the signer
            timestamp: Timestamp of signature
            signature_data: The signature image data
            
        Returns:
            SHA-256 hash string
        """
        # Create a string with all signature components
        signature_string = f"{document_id}:{signer_id}:{timestamp.isoformat()}:{signature_data}"
        
        # Add a secret key if available
        secret_key = getattr(settings, 'SIGNATURE_SECRET_KEY', 'default-secret-key')
        signature_string += f":{secret_key}"
        
        # Generate SHA-256 hash
        return hashlib.sha256(signature_string.encode('utf-8')).hexdigest()
    
    @staticmethod
    def verify_signature_integrity(signature_hash: str, document_id: int, signer_id: int, 
                                 timestamp: datetime, signature_data: str) -> bool:
        """
        Verify the integrity of a signature by comparing hashes
        
        Args:
            signature_hash: The stored signature hash
            document_id: ID of the document
            signer_id: ID of the signer
            timestamp: Timestamp of signature
            signature_data: The signature image data
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Generate expected hash
            expected_hash = SignatureValidator.generate_signature_hash(
                document_id, signer_id, timestamp, signature_data
            )
            
            # Compare hashes using secure comparison
            return hmac.compare_digest(signature_hash, expected_hash)
            
        except Exception as e:
            logger.error(f"Error verifying signature integrity: {str(e)}")
            return False


class SignatureAuditLogger:
    """
    Utility class for logging signature-related events for audit trail
    """
    
    @staticmethod
    def log_signature_attempt(document_id: int, signer_id: int, ip_address: str, 
                            user_agent: str, success: bool, error_message: str = None):
        """
        Log signature attempt for audit purposes
        
        Args:
            document_id: ID of the document
            signer_id: ID of the signer
            ip_address: IP address of the signer
            user_agent: User agent string
            success: Whether the signature was successful
            error_message: Error message if failed
        """
        log_data = {
            'event': 'signature_attempt',
            'document_id': document_id,
            'signer_id': signer_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'success': success,
            'timestamp': timezone.now().isoformat(),
        }
        
        if error_message:
            log_data['error'] = error_message
        
        if success:
            logger.info(f"Signature successful: {json.dumps(log_data)}")
        else:
            logger.warning(f"Signature failed: {json.dumps(log_data)}")
    
    @staticmethod
    def log_signature_verification(signature_id: int, verified: bool, verifier_id: int = None):
        """
        Log signature verification events
        
        Args:
            signature_id: ID of the signature
            verified: Whether verification was successful
            verifier_id: ID of the verifier (if applicable)
        """
        log_data = {
            'event': 'signature_verification',
            'signature_id': signature_id,
            'verified': verified,
            'verifier_id': verifier_id,
            'timestamp': timezone.now().isoformat(),
        }
        
        logger.info(f"Signature verification: {json.dumps(log_data)}")
    
    @staticmethod
    def log_document_access(document_id: int, user_id: int, action: str, ip_address: str):
        """
        Log document access events
        
        Args:
            document_id: ID of the document
            user_id: ID of the user accessing the document
            action: Action performed (view, download, sign, etc.)
            ip_address: IP address of the user
        """
        log_data = {
            'event': 'document_access',
            'document_id': document_id,
            'user_id': user_id,
            'action': action,
            'ip_address': ip_address,
            'timestamp': timezone.now().isoformat(),
        }
        
        logger.info(f"Document access: {json.dumps(log_data)}")


class SignatureSecurityManager:
    """
    Manager for signature security policies and enforcement
    """
    
    @staticmethod
    def check_signature_permissions(user, document) -> Tuple[bool, str]:
        """
        Check if user has permission to sign the document
        
        Args:
            user: User attempting to sign
            document: Document to be signed
            
        Returns:
            Tuple of (has_permission, error_message)
        """
        try:
            # Check if user is one of the required signers
            required_signature = document.signatures.filter(signer=user, status='pending').first()
            if not required_signature:
                return False, "User is not authorized to sign this document"
            
            # Check if document is in correct status
            if document.status != 'ready':
                return False, f"Document is not ready for signing (status: {document.get_status_display()})"
            
            # Check if document has expired
            if document.is_expired:
                return False, "Document has expired and cannot be signed"
            
            # Check if user has already signed
            if required_signature.status == 'signed':
                return False, "User has already signed this document"
            
            return True, "Permission granted"
            
        except Exception as e:
            logger.error(f"Error checking signature permissions: {str(e)}")
            return False, "Permission check failed"
    
    @staticmethod
    def validate_signature_timing(document, current_time: datetime = None) -> Tuple[bool, str]:
        """
        Validate signature timing constraints
        
        Args:
            document: Document being signed
            current_time: Current timestamp (defaults to now)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if current_time is None:
            current_time = timezone.now()
        
        # Check if document has expired
        if document.expires_at and current_time > document.expires_at:
            return False, "Document has expired"
        
        # Check if document was generated too long ago (security policy)
        max_age_hours = getattr(settings, 'SIGNATURE_MAX_DOCUMENT_AGE_HOURS', 72)  # 3 days default
        max_age = timedelta(hours=max_age_hours)
        
        if current_time - document.generated_at > max_age:
            return False, f"Document is too old to sign (max age: {max_age_hours} hours)"
        
        return True, "Timing validation passed"
    
    @staticmethod
    def check_signature_rate_limit(user, time_window_minutes: int = 5, max_attempts: int = 3) -> Tuple[bool, str]:
        """
        Check signature rate limiting to prevent abuse
        
        Args:
            user: User attempting to sign
            time_window_minutes: Time window for rate limiting
            max_attempts: Maximum attempts in time window
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        try:
            from .models import DigitalSignature
            
            # Calculate time window
            time_threshold = timezone.now() - timedelta(minutes=time_window_minutes)
            
            # Count recent signature attempts
            recent_attempts = DigitalSignature.objects.filter(
                signer=user,
                date_created__gte=time_threshold
            ).count()
            
            if recent_attempts >= max_attempts:
                return False, f"Too many signature attempts. Please wait {time_window_minutes} minutes."
            
            return True, "Rate limit check passed"
            
        except Exception as e:
            logger.error(f"Error checking signature rate limit: {str(e)}")
            return True, "Rate limit check skipped due to error"


class SignatureNotificationManager:
    """
    Manager for signature-related notifications
    """
    
    @staticmethod
    def notify_signature_required(document, signature):
        """
        Send notification when signature is required
        
        Args:
            document: Document requiring signature
            signature: Signature record
        """
        try:
            # In a real implementation, this would send email/SMS notifications
            logger.info(f"Signature required notification sent to {signature.signer.email} for document {document.id}")
            
            # You could integrate with your existing notification system here
            # For example:
            # from utils.notifications import send_email_notification
            # send_email_notification(
            #     to_email=signature.signer.email,
            #     subject="Document Signature Required",
            #     template="signature_required",
            #     context={'document': document, 'signature': signature}
            # )
            
        except Exception as e:
            logger.error(f"Error sending signature notification: {str(e)}")
    
    @staticmethod
    def notify_signature_completed(document, signature):
        """
        Send notification when signature is completed
        
        Args:
            document: Document that was signed
            signature: Completed signature record
        """
        try:
            logger.info(f"Signature completed notification for document {document.id} by {signature.signer.email}")
            
            # Notify other parties about the signature completion
            other_signatures = document.signatures.exclude(id=signature.id)
            for other_sig in other_signatures:
                logger.info(f"Notifying {other_sig.signer.email} about signature completion")
            
        except Exception as e:
            logger.error(f"Error sending signature completion notification: {str(e)}")
    
    @staticmethod
    def notify_document_fully_signed(document):
        """
        Send notification when all signatures are completed
        
        Args:
            document: Fully signed document
        """
        try:
            logger.info(f"Document {document.id} fully signed - notifying all parties")
            
            # Notify all signers that the document is complete
            for signature in document.signatures.all():
                logger.info(f"Notifying {signature.signer.email} about document completion")
            
            # Notify the inspection parties
            inspection = document.inspection
            logger.info(f"Inspection {inspection.id} completed - document fully signed")
            
        except Exception as e:
            logger.error(f"Error sending document completion notification: {str(e)}")


def validate_signature_coordinates(coordinates: Dict) -> Tuple[bool, str]:
    """
    Validate signature coordinates for PDF placement
    
    Args:
        coordinates: Dictionary with x, y, width, height
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['x', 'y', 'width', 'height']
    
    for field in required_fields:
        if field not in coordinates:
            return False, f"Missing required coordinate field: {field}"
        
        try:
            value = float(coordinates[field])
            if value < 0:
                return False, f"Coordinate {field} cannot be negative"
        except (ValueError, TypeError):
            return False, f"Invalid coordinate value for {field}"
    
    # Validate reasonable bounds (assuming standard page size)
    max_x, max_y = 600, 800  # Approximate A4 size in points
    
    if coordinates['x'] > max_x or coordinates['y'] > max_y:
        return False, "Signature coordinates exceed page bounds"
    
    if coordinates['width'] > 300 or coordinates['height'] > 100:
        return False, "Signature dimensions too large"
    
    return True, "Coordinates valid"