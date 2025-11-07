"""
Document validation utilities for business verification
"""
import os
import mimetypes
from typing import Dict, List, Tuple, Optional
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings


class DocumentValidator:
    """Validates uploaded documents for business verification"""
    
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
    
    def __init__(self):
        self.errors = []
    
    def validate_file(self, uploaded_file: UploadedFile, field_name: str) -> Dict[str, List[str]]:
        """
        Validate a single uploaded file
        
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


def get_document_requirements() -> Dict[str, str]:
    """
    Get document requirements for business verification
    
    Returns:
        Dict with document requirements
    """
    return {
        'cac_document': 'Corporate Affairs Commission (CAC) registration certificate - PDF, JPG, or PNG format, max 5MB',
        'tin_document': 'Tax Identification Number (TIN) certificate - PDF, JPG, or PNG format, max 5MB',
        'proof_of_address': 'Proof of business address (utility bill or lease agreement) - PDF, JPG, or PNG format, max 5MB',
        'business_license': 'Business operating license or permit - PDF, JPG, or PNG format, max 5MB'
    }