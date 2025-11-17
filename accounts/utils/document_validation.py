"""
Document validation utilities for business verification with Cloudinary integration
"""
import os
import mimetypes
import logging
from typing import Dict, List, Tuple, Optional
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
from django.core.exceptions import ValidationError


logger = logging.getLogger(__name__)


# Custom exception classes for document operations
class DocumentUploadError(Exception):
    """Base exception for document upload failures"""
    pass


class CloudinaryConnectionError(DocumentUploadError):
    """Cloudinary service unavailable or connection failed"""
    pass


class DocumentValidationError(DocumentUploadError):
    """Document validation failed"""
    pass


class FileSizeExceededError(DocumentValidationError):
    """File size exceeds the allowed limit"""
    pass


class InvalidFileFormatError(DocumentValidationError):
    """File format is not allowed or invalid"""
    pass


class MaliciousFileError(DocumentValidationError):
    """File contains potentially malicious content"""
    pass


class DocumentValidator:
    """Enhanced document validator for business verification with Cloudinary integration"""
    
    # Allowed file types and their MIME types
    ALLOWED_EXTENSIONS = {
        '.pdf': ['application/pdf'],
        '.jpg': ['image/jpeg'],
        '.jpeg': ['image/jpeg'],
        '.png': ['image/png'],
    }
    
    # Maximum file sizes (in bytes)
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    MIN_FILE_SIZE = 1024  # 1KB
    
    # File type specific validation
    PDF_MAGIC_NUMBERS = [b'%PDF']
    JPEG_MAGIC_NUMBERS = [b'\xff\xd8\xff']
    PNG_MAGIC_NUMBERS = [b'\x89PNG\r\n\x1a\n']
    
    # Security validation patterns
    SUSPICIOUS_PATTERNS = [
        b'<script',
        b'javascript:',
        b'vbscript:',
        b'onload=',
        b'onerror=',
        b'<?php',
        b'<%',
        b'#!/bin/',
        b'#!/usr/bin/',
    ]
    
    # Document type requirements
    DOCUMENT_REQUIREMENTS = {
        'cac_document': {
            'name': 'CAC Registration Certificate',
            'description': 'Corporate Affairs Commission registration certificate',
            'required': True,
            'formats': ['.pdf', '.jpg', '.jpeg', '.png']
        },
        'tin_document': {
            'name': 'TIN Certificate',
            'description': 'Tax Identification Number certificate',
            'required': True,
            'formats': ['.pdf', '.jpg', '.jpeg', '.png']
        },
        'proof_of_address': {
            'name': 'Proof of Address',
            'description': 'Business address verification (utility bill or lease agreement)',
            'required': True,
            'formats': ['.pdf', '.jpg', '.jpeg', '.png']
        },
        'business_license': {
            'name': 'Business License',
            'description': 'Business operating license or permit',
            'required': False,
            'formats': ['.pdf', '.jpg', '.jpeg', '.png']
        }
    }
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_file(self, uploaded_file: UploadedFile, field_name: str) -> Dict[str, List[str]]:
        """
        Enhanced validation for a single uploaded file
        
        Args:
            uploaded_file: The uploaded file to validate
            field_name: Name of the form field (for error reporting)
            
        Returns:
            Dict with validation errors (empty if valid)
        """
        errors = {}
        
        if not uploaded_file:
            return errors
        
        # Reset errors for this file
        file_errors = []
        
        try:
            # Validate file extension
            extension_error = self._validate_extension(uploaded_file)
            if extension_error:
                file_errors.append(extension_error)
            
            # Validate file size
            size_error = self._validate_size(uploaded_file)
            if size_error:
                file_errors.append(size_error)
            
            # Validate file content (magic numbers)
            content_error = self._validate_content(uploaded_file)
            if content_error:
                file_errors.append(content_error)
            
            # Validate MIME type
            mime_error = self._validate_mime_type(uploaded_file)
            if mime_error:
                file_errors.append(mime_error)
            
            # Enhanced security validation
            security_error = self._validate_security(uploaded_file)
            if security_error:
                file_errors.append(security_error)
            
            # Validate document type requirements
            if field_name in self.DOCUMENT_REQUIREMENTS:
                requirement_error = self._validate_document_requirements(uploaded_file, field_name)
                if requirement_error:
                    file_errors.append(requirement_error)
            
        except Exception as e:
            logger.error(f"Validation error for {field_name}: {str(e)}")
            file_errors.append(f"File validation failed: {str(e)}")
        
        if file_errors:
            errors[field_name] = file_errors
        
        return errors
    
    def validate_multiple_files(self, files_dict: Dict[str, UploadedFile]) -> Dict[str, List[str]]:
        """
        Validate multiple uploaded files
        
        Args:
            files_dict: Dictionary of field_name -> uploaded_file
            
        Returns:
            Dict with all validation errors
        """
        all_errors = {}
        
        for field_name, uploaded_file in files_dict.items():
            file_errors = self.validate_file(uploaded_file, field_name)
            if file_errors:
                all_errors.update(file_errors)
        
        return all_errors
    
    def _validate_extension(self, uploaded_file: UploadedFile) -> Optional[str]:
        """Validate file extension"""
        if not uploaded_file.name:
            return "File name is required"
        
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_extension not in self.ALLOWED_EXTENSIONS:
            allowed = ', '.join(self.ALLOWED_EXTENSIONS.keys())
            return f"Invalid file type. Allowed types: {allowed}"
        
        return None
    
    def _validate_size(self, uploaded_file: UploadedFile) -> Optional[str]:
        """Validate file size"""
        if uploaded_file.size > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE // (1024 * 1024)
            return f"File too large. Maximum size: {max_mb}MB"
        
        if uploaded_file.size < self.MIN_FILE_SIZE:
            return "File too small. Minimum size: 1KB"
        
        return None
    
    def _validate_content(self, uploaded_file: UploadedFile) -> Optional[str]:
        """Validate file content using magic numbers"""
        try:
            # Read first 10 bytes for magic number validation
            uploaded_file.seek(0)
            header = uploaded_file.read(10)
            uploaded_file.seek(0)  # Reset file pointer
            
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            
            if file_extension == '.pdf':
                if not any(header.startswith(magic) for magic in self.PDF_MAGIC_NUMBERS):
                    return "Invalid PDF file format"
            
            elif file_extension in ['.jpg', '.jpeg']:
                if not any(header.startswith(magic) for magic in self.JPEG_MAGIC_NUMBERS):
                    return "Invalid JPEG file format"
            
            elif file_extension == '.png':
                if not any(header.startswith(magic) for magic in self.PNG_MAGIC_NUMBERS):
                    return "Invalid PNG file format"
            
            return None
            
        except Exception as e:
            return f"Unable to validate file content: {str(e)}"
    
    def _validate_mime_type(self, uploaded_file: UploadedFile) -> Optional[str]:
        """Validate MIME type"""
        if not uploaded_file.name:
            return None
        
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        # Get expected MIME types for this extension
        expected_mimes = self.ALLOWED_EXTENSIONS.get(file_extension, [])
        
        if not expected_mimes:
            return None
        
        # Get actual MIME type
        actual_mime, _ = mimetypes.guess_type(uploaded_file.name)
        
        # Also check content type from upload
        content_type = getattr(uploaded_file, 'content_type', None)
        
        # Validate against expected MIME types
        if actual_mime not in expected_mimes and content_type not in expected_mimes:
            return f"MIME type mismatch. Expected: {', '.join(expected_mimes)}"
        
        return None
    
    def _validate_security(self, uploaded_file: UploadedFile) -> Optional[str]:
        """Enhanced security validation to detect malicious content"""
        try:
            # Read first 1KB for security scanning
            uploaded_file.seek(0)
            header = uploaded_file.read(1024)
            uploaded_file.seek(0)  # Reset file pointer
            
            # Convert to lowercase for case-insensitive matching
            header_lower = header.lower()
            
            # Check for suspicious patterns
            for pattern in self.SUSPICIOUS_PATTERNS:
                if pattern in header_lower:
                    logger.warning(f"Suspicious pattern detected in file: {uploaded_file.name}")
                    return "File contains potentially malicious content"
            
            # Additional checks for specific file types
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            
            if file_extension == '.pdf':
                # Check for embedded JavaScript in PDF
                if b'/js' in header_lower or b'javascript' in header_lower:
                    return "PDF contains embedded JavaScript which is not allowed"
            
            return None
            
        except Exception as e:
            logger.error(f"Security validation error: {str(e)}")
            return "Unable to perform security validation"
    
    def _validate_document_requirements(self, uploaded_file: UploadedFile, document_type: str) -> Optional[str]:
        """Validate document against specific requirements"""
        requirements = self.DOCUMENT_REQUIREMENTS.get(document_type)
        if not requirements:
            return None
        
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        # Check if file format is allowed for this document type
        if file_extension not in requirements['formats']:
            allowed_formats = ', '.join(requirements['formats'])
            return f"{requirements['name']} must be in one of these formats: {allowed_formats}"
        
        return None
    
    @staticmethod
    def get_secure_filename(filename: str) -> str:
        """
        Generate a secure filename for storage
        
        Args:
            filename: Original filename
            
        Returns:
            Secure filename
        """
        import uuid
        import re
        
        # Get file extension
        name, ext = os.path.splitext(filename)
        
        # Clean the name (remove special characters)
        clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        
        # Limit length
        clean_name = clean_name[:50]
        
        # Add UUID for uniqueness
        unique_id = str(uuid.uuid4())[:8]
        
        return f"{clean_name}_{unique_id}{ext}"
    
    @staticmethod
    def get_upload_path(instance, filename: str) -> str:
        """
        Generate upload path for business verification documents
        
        Args:
            instance: Model instance
            filename: Original filename
            
        Returns:
            Upload path
        """
        # Get secure filename
        secure_filename = DocumentValidator.get_secure_filename(filename)
        
        # Create path based on business type and user
        business_type = getattr(instance, 'business_type', 'unknown')
        user_id = None
        
        if hasattr(instance, 'dealership') and instance.dealership:
            user_id = instance.dealership.user.id
        elif hasattr(instance, 'mechanic') and instance.mechanic:
            user_id = instance.mechanic.user.id
        
        if user_id:
            return f'verification/{business_type}/{user_id}/{secure_filename}'
        else:
            return f'verification/{business_type}/{secure_filename}'
    
    def validate_for_cloudinary(self, uploaded_file: UploadedFile, document_type: str) -> Dict[str, any]:
        """
        Comprehensive validation specifically for Cloudinary upload
        
        Args:
            uploaded_file: The uploaded file to validate
            document_type: Type of document being uploaded
            
        Returns:
            Dict with validation result and metadata
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'metadata': {
                'original_filename': uploaded_file.name,
                'file_size': uploaded_file.size,
                'content_type': getattr(uploaded_file, 'content_type', None),
                'document_type': document_type
            }
        }
        
        # Perform all validations
        validation_errors = self.validate_file(uploaded_file, document_type)
        
        if validation_errors:
            result['is_valid'] = False
            result['errors'] = validation_errors.get(document_type, [])
        
        # Add file metadata
        if uploaded_file.name:
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            result['metadata']['file_extension'] = file_extension
            result['metadata']['secure_filename'] = self.get_secure_filename(uploaded_file.name)
        
        return result
    
    def get_validation_summary(self, files_dict: Dict[str, UploadedFile]) -> Dict[str, any]:
        """
        Get comprehensive validation summary for multiple files
        
        Args:
            files_dict: Dictionary of document_type -> uploaded_file
            
        Returns:
            Validation summary with overall status and details
        """
        summary = {
            'overall_valid': True,
            'total_files': len(files_dict),
            'valid_files': 0,
            'invalid_files': 0,
            'required_missing': [],
            'file_results': {},
            'total_size': 0
        }
        
        # Validate each file
        for document_type, uploaded_file in files_dict.items():
            if uploaded_file:
                file_result = self.validate_for_cloudinary(uploaded_file, document_type)
                summary['file_results'][document_type] = file_result
                summary['total_size'] += uploaded_file.size
                
                if file_result['is_valid']:
                    summary['valid_files'] += 1
                else:
                    summary['invalid_files'] += 1
                    summary['overall_valid'] = False
        
        # Check for missing required documents
        for document_type, requirements in self.DOCUMENT_REQUIREMENTS.items():
            if requirements['required'] and document_type not in files_dict:
                summary['required_missing'].append({
                    'type': document_type,
                    'name': requirements['name'],
                    'description': requirements['description']
                })
        
        if summary['required_missing']:
            summary['overall_valid'] = False
        
        return summary


def validate_business_documents(files_dict: Dict[str, UploadedFile]) -> Dict[str, List[str]]:
    """
    Convenience function to validate business verification documents
    
    Args:
        files_dict: Dictionary of field_name -> uploaded_file
        
    Returns:
        Dict with validation errors
    """
    validator = DocumentValidator()
    return validator.validate_multiple_files(files_dict)


def validate_for_cloudinary_upload(files_dict: Dict[str, UploadedFile]) -> Dict[str, any]:
    """
    Convenience function for comprehensive Cloudinary validation
    
    Args:
        files_dict: Dictionary of document_type -> uploaded_file
        
    Returns:
        Comprehensive validation summary
    """
    validator = DocumentValidator()
    return validator.get_validation_summary(files_dict)


def get_document_requirements() -> Dict[str, Dict[str, any]]:
    """
    Get detailed document requirements for business verification
    
    Returns:
        Dict with detailed document requirements
    """
    return DocumentValidator.DOCUMENT_REQUIREMENTS.copy()


def get_document_requirements_summary() -> Dict[str, str]:
    """
    Get simple document requirements summary for display
    
    Returns:
        Dict with simple requirement descriptions
    """
    requirements = DocumentValidator.DOCUMENT_REQUIREMENTS
    summary = {}
    
    for doc_type, req in requirements.items():
        formats = ', '.join(req['formats']).upper()
        required_text = "Required" if req['required'] else "Optional"
        max_size = DocumentValidator.MAX_FILE_SIZE // (1024 * 1024)  # Convert to MB
        
        summary[doc_type] = f"{req['description']} - {formats} format, max {max_size}MB ({required_text})"
    
    return summary


class DocumentValidationError(ValidationError):
    """Custom exception for document validation errors"""
    
    def __init__(self, message, errors=None, document_type=None):
        super().__init__(message)
        self.errors = errors or {}
        self.document_type = document_type


class DocumentSecurityError(DocumentValidationError):
    """Exception for security-related validation failures"""
    pass


class DocumentSizeError(DocumentValidationError):
    """Exception for file size validation failures"""
    pass


class DocumentFormatError(DocumentValidationError):
    """Exception for file format validation failures"""
    pass