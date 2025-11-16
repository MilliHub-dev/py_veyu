"""
Cloudinary document storage service for business verification
"""
import os
import logging
from typing import Optional, Dict, Any, Tuple
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone
import cloudinary
import cloudinary.uploader
import cloudinary.utils
from cloudinary.exceptions import Error as CloudinaryError


logger = logging.getLogger(__name__)


class CloudinaryDocumentStorage:
    """
    Handles Cloudinary document operations for business verification
    """
    
    # Document folder structure
    BASE_FOLDER = 'verification'
    
    # Document types and their folder names
    DOCUMENT_FOLDERS = {
        'cac_document': 'cac',
        'tin_document': 'tin',
        'proof_of_address': 'address',
        'business_license': 'license'
    }
    
    # Cloudinary transformation settings
    DEFAULT_TRANSFORMATIONS = {
        'quality': 'auto',
        'fetch_format': 'auto',
        'flags': 'attachment'  # Force download for security
    }
    
    # Thumbnail transformation for admin previews
    THUMBNAIL_TRANSFORMATIONS = {
        'width': 200,
        'height': 200,
        'crop': 'fit',
        'quality': 'auto',
        'fetch_format': 'auto'
    }
    
    def __init__(self):
        """Initialize Cloudinary configuration"""
        self._ensure_cloudinary_config()
    
    def _ensure_cloudinary_config(self):
        """Ensure Cloudinary is properly configured"""
        if not hasattr(settings, 'CLOUDINARY_URL') and not os.getenv('CLOUDINARY_URL'):
            raise CloudinaryError("Cloudinary configuration not found. Please set CLOUDINARY_URL.")
    
    def upload_document(
        self, 
        file: UploadedFile, 
        user_id: int, 
        submission_id: int, 
        document_type: str
    ) -> Dict[str, Any]:
        """
        Upload document to Cloudinary with proper folder structure and metadata
        
        Args:
            file: The uploaded file
            user_id: ID of the user uploading
            submission_id: ID of the verification submission
            document_type: Type of document (cac_document, tin_document, etc.)
            
        Returns:
            Dict containing upload result with public_id, secure_url, etc.
            
        Raises:
            CloudinaryError: If upload fails
            ValueError: If invalid parameters provided
        """
        if not file:
            raise ValueError("File is required for upload")
        
        if document_type not in self.DOCUMENT_FOLDERS:
            raise ValueError(f"Invalid document type: {document_type}")
        
        try:
            # Generate folder path
            folder_path = self._generate_folder_path(user_id, submission_id, document_type)
            
            # Generate public ID
            public_id = self._generate_public_id(file.name, user_id, submission_id, document_type)
            
            # Prepare upload options
            upload_options = {
                'folder': folder_path,
                'public_id': public_id,
                'resource_type': 'auto',  # Auto-detect file type
                'use_filename': False,  # Use our generated public_id
                'unique_filename': False,  # Don't add random suffix
                'overwrite': True,  # Allow overwriting existing files
                'transformation': self.DEFAULT_TRANSFORMATIONS,
                'tags': [
                    'business_verification',
                    document_type,
                    f'user_{user_id}',
                    f'submission_{submission_id}'
                ],
                'context': {
                    'user_id': str(user_id),
                    'submission_id': str(submission_id),
                    'document_type': document_type,
                    'original_filename': file.name,
                    'upload_timestamp': timezone.now().isoformat()
                }
            }
            
            # Upload to Cloudinary
            logger.info(f"Uploading document {document_type} for user {user_id}, submission {submission_id}")
            
            result = cloudinary.uploader.upload(file, **upload_options)
            
            logger.info(f"Successfully uploaded document: {result.get('public_id')}")
            
            return {
                'public_id': result['public_id'],
                'secure_url': result['secure_url'],
                'url': result['url'],
                'format': result['format'],
                'resource_type': result['resource_type'],
                'bytes': result['bytes'],
                'width': result.get('width'),
                'height': result.get('height'),
                'created_at': result['created_at'],
                'version': result['version']
            }
            
        except CloudinaryError as e:
            logger.error(f"Cloudinary upload failed for {document_type}: {str(e)}")
            raise CloudinaryError(f"Failed to upload document: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during upload: {str(e)}")
            raise CloudinaryError(f"Upload failed due to unexpected error: {str(e)}")
    
    def get_secure_url(
        self, 
        public_id: str, 
        expires_in: int = 3600,
        transformation: Optional[Dict] = None
    ) -> str:
        """
        Generate time-limited secure URL for document access
        
        Args:
            public_id: Cloudinary public ID of the document
            expires_in: URL expiration time in seconds (default: 1 hour)
            transformation: Optional transformation parameters
            
        Returns:
            Secure URL with expiration
            
        Raises:
            CloudinaryError: If URL generation fails
        """
        if not public_id:
            raise ValueError("Public ID is required")
        
        try:
            # Calculate expiration timestamp
            expires_at = int(timezone.now().timestamp()) + expires_in
            
            # Prepare transformation options
            transform_options = transformation or self.DEFAULT_TRANSFORMATIONS.copy()
            
            # Add security flags
            transform_options.update({
                'flags': 'attachment',  # Force download
                'sign_url': True,  # Sign the URL
                'expires_at': expires_at
            })
            
            # Generate secure URL
            secure_url = cloudinary.utils.cloudinary_url(
                public_id,
                **transform_options
            )[0]
            
            logger.debug(f"Generated secure URL for {public_id}, expires in {expires_in}s")
            
            return secure_url
            
        except Exception as e:
            logger.error(f"Failed to generate secure URL for {public_id}: {str(e)}")
            raise CloudinaryError(f"Failed to generate secure URL: {str(e)}")
    
    def get_thumbnail_url(self, public_id: str) -> str:
        """
        Generate thumbnail URL for admin preview
        
        Args:
            public_id: Cloudinary public ID of the document
            
        Returns:
            Thumbnail URL
        """
        if not public_id:
            return ""
        
        try:
            thumbnail_url = cloudinary.utils.cloudinary_url(
                public_id,
                **self.THUMBNAIL_TRANSFORMATIONS
            )[0]
            
            return thumbnail_url
            
        except Exception as e:
            logger.error(f"Failed to generate thumbnail URL for {public_id}: {str(e)}")
            return ""
    
    def delete_document(self, public_id: str) -> bool:
        """
        Delete document from Cloudinary
        
        Args:
            public_id: Cloudinary public ID of the document to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        if not public_id:
            return False
        
        try:
            result = cloudinary.uploader.destroy(public_id)
            
            if result.get('result') == 'ok':
                logger.info(f"Successfully deleted document: {public_id}")
                return True
            else:
                logger.warning(f"Document deletion returned: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete document {public_id}: {str(e)}")
            return False
    
    def migrate_local_file(
        self, 
        local_path: str, 
        user_id: int, 
        submission_id: int, 
        document_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Migrate existing local file to Cloudinary
        
        Args:
            local_path: Path to the local file
            user_id: ID of the user
            submission_id: ID of the verification submission
            document_type: Type of document
            
        Returns:
            Upload result dict or None if migration fails
        """
        if not os.path.exists(local_path):
            logger.error(f"Local file not found: {local_path}")
            return None
        
        try:
            # Generate folder path and public ID
            folder_path = self._generate_folder_path(user_id, submission_id, document_type)
            filename = os.path.basename(local_path)
            public_id = self._generate_public_id(filename, user_id, submission_id, document_type)
            
            # Prepare upload options for migration
            upload_options = {
                'folder': folder_path,
                'public_id': public_id,
                'resource_type': 'auto',
                'use_filename': False,
                'unique_filename': False,
                'overwrite': True,
                'transformation': self.DEFAULT_TRANSFORMATIONS,
                'tags': [
                    'business_verification',
                    'migrated',
                    document_type,
                    f'user_{user_id}',
                    f'submission_{submission_id}'
                ],
                'context': {
                    'user_id': str(user_id),
                    'submission_id': str(submission_id),
                    'document_type': document_type,
                    'original_filename': filename,
                    'migration_timestamp': timezone.now().isoformat(),
                    'migrated_from': local_path
                }
            }
            
            # Upload the local file
            logger.info(f"Migrating local file {local_path} to Cloudinary")
            
            result = cloudinary.uploader.upload(local_path, **upload_options)
            
            logger.info(f"Successfully migrated file: {result.get('public_id')}")
            
            return {
                'public_id': result['public_id'],
                'secure_url': result['secure_url'],
                'url': result['url'],
                'format': result['format'],
                'resource_type': result['resource_type'],
                'bytes': result['bytes'],
                'created_at': result['created_at'],
                'version': result['version']
            }
            
        except Exception as e:
            logger.error(f"Failed to migrate file {local_path}: {str(e)}")
            return None
    
    def _generate_folder_path(self, user_id: int, submission_id: int, document_type: str) -> str:
        """Generate Cloudinary folder path"""
        document_folder = self.DOCUMENT_FOLDERS.get(document_type, 'other')
        return f"{self.BASE_FOLDER}/{user_id}/{submission_id}/{document_folder}"
    
    def _generate_public_id(
        self, 
        filename: str, 
        user_id: int, 
        submission_id: int, 
        document_type: str
    ) -> str:
        """Generate unique public ID for the document"""
        # Clean filename
        name, ext = os.path.splitext(filename)
        clean_name = "".join(c for c in name if c.isalnum() or c in ('-', '_'))[:20]
        
        # Generate timestamp
        timestamp = int(timezone.now().timestamp())
        
        return f"{document_type}_{user_id}_{submission_id}_{clean_name}_{timestamp}"
    
    def get_document_info(self, public_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document information from Cloudinary
        
        Args:
            public_id: Cloudinary public ID
            
        Returns:
            Document information dict or None if not found
        """
        try:
            result = cloudinary.api.resource(public_id)
            
            return {
                'public_id': result['public_id'],
                'format': result['format'],
                'resource_type': result['resource_type'],
                'bytes': result['bytes'],
                'width': result.get('width'),
                'height': result.get('height'),
                'created_at': result['created_at'],
                'secure_url': result['secure_url'],
                'context': result.get('context', {}),
                'tags': result.get('tags', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to get document info for {public_id}: {str(e)}")
            return None


# Convenience functions for easy access
def upload_business_document(
    file: UploadedFile, 
    user_id: int, 
    submission_id: int, 
    document_type: str
) -> Dict[str, Any]:
    """
    Convenience function to upload a business verification document
    """
    storage = CloudinaryDocumentStorage()
    return storage.upload_document(file, user_id, submission_id, document_type)


def get_document_secure_url(public_id: str, expires_in: int = 3600) -> str:
    """
    Convenience function to get a secure document URL
    """
    storage = CloudinaryDocumentStorage()
    return storage.get_secure_url(public_id, expires_in)


def get_document_thumbnail_url(public_id: str) -> str:
    """
    Convenience function to get a document thumbnail URL
    """
    storage = CloudinaryDocumentStorage()
    return storage.get_thumbnail_url(public_id)


def delete_business_document(public_id: str) -> bool:
    """
    Convenience function to delete a business document
    """
    storage = CloudinaryDocumentStorage()
    return storage.delete_document(public_id)