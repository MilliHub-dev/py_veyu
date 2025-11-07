"""
Document Management System for inspection documents
Provides secure storage, access controls, versioning, audit trail, and retention policies
"""
from django.db import models
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from datetime import timedelta
from typing import List, Dict, Optional, Tuple
import logging

from .models import InspectionDocument, DigitalSignature, VehicleInspection
from accounts.models import Account

logger = logging.getLogger(__name__)


class DocumentAccessControl:
    """
    Manages access control for inspection documents
    """
    
    # Access levels
    ACCESS_NONE = 0
    ACCESS_VIEW = 1
    ACCESS_DOWNLOAD = 2
    ACCESS_SIGN = 3
    ACCESS_MANAGE = 4
    
    @staticmethod
    def check_access(user: Account, document: InspectionDocument, required_level: int) -> Tuple[bool, str]:
        """
        Check if user has required access level for document
        
        Args:
            user: User requesting access
            document: Document to access
            required_level: Required access level
            
        Returns:
            Tuple of (has_access, reason)
        """
        try:
            inspection = document.inspection
            user_level = DocumentAccessControl._get_user_access_level(user, inspection)
            
            if user_level >= required_level:
                return True, "Access granted"
            
            return False, f"Insufficient permissions (required: {required_level}, has: {user_level})"
            
        except Exception as e:
            logger.error(f"Error checking document access: {str(e)}")
            return False, "Access check failed"
    
    @staticmethod
    def _get_user_access_level(user: Account, inspection: VehicleInspection) -> int:
        """Get user's access level for inspection"""
        # Inspector has full management access
        if user == inspection.inspector:
            return DocumentAccessControl.ACCESS_MANAGE
        
        # Dealer has management access
        if hasattr(user, 'dealership') and user.dealership == inspection.dealer:
            return DocumentAccessControl.ACCESS_MANAGE
        
        # Customer has sign and download access
        if hasattr(user, 'customer') and user.customer == inspection.customer:
            return DocumentAccessControl.ACCESS_SIGN
        
        # Admin has full access
        if user.is_staff or user.is_superuser:
            return DocumentAccessControl.ACCESS_MANAGE
        
        # No access by default
        return DocumentAccessControl.ACCESS_NONE
    
    @staticmethod
    def can_view(user: Account, document: InspectionDocument) -> bool:
        """Check if user can view document"""
        has_access, _ = DocumentAccessControl.check_access(user, document, DocumentAccessControl.ACCESS_VIEW)
        return has_access
    
    @staticmethod
    def can_download(user: Account, document: InspectionDocument) -> bool:
        """Check if user can download document"""
        has_access, _ = DocumentAccessControl.check_access(user, document, DocumentAccessControl.ACCESS_DOWNLOAD)
        return has_access
    
    @staticmethod
    def can_sign(user: Account, document: InspectionDocument) -> bool:
        """Check if user can sign document"""
        has_access, _ = DocumentAccessControl.check_access(user, document, DocumentAccessControl.ACCESS_SIGN)
        return has_access
    
    @staticmethod
    def can_manage(user: Account, document: InspectionDocument) -> bool:
        """Check if user can manage document"""
        has_access, _ = DocumentAccessControl.check_access(user, document, DocumentAccessControl.ACCESS_MANAGE)
        return has_access


class DocumentVersionManager:
    """
    Manages document versioning and history
    """
    
    @staticmethod
    def create_version(document: InspectionDocument, reason: str = None) -> Dict:
        """
        Create a new version of the document
        
        Args:
            document: Document to version
            reason: Reason for creating new version
            
        Returns:
            Version information dictionary
        """
        try:
            # In a real implementation, you would:
            # 1. Copy the current document file
            # 2. Store it with a version number
            # 3. Update metadata
            
            version_info = {
                'document_id': document.id,
                'version_number': DocumentVersionManager._get_next_version_number(document),
                'created_at': timezone.now(),
                'reason': reason or 'Version created',
                'file_hash': document.document_hash,
                'status': document.status
            }
            
            logger.info(f"Created version for document {document.id}: {version_info}")
            return version_info
            
        except Exception as e:
            logger.error(f"Error creating document version: {str(e)}")
            raise
    
    @staticmethod
    def _get_next_version_number(document: InspectionDocument) -> int:
        """Get next version number for document"""
        # In a real implementation, you would query version history
        # For now, return a simple version number
        return 1
    
    @staticmethod
    def get_version_history(document: InspectionDocument) -> List[Dict]:
        """
        Get version history for document
        
        Returns:
            List of version information dictionaries
        """
        try:
            # In a real implementation, you would query version records
            # For now, return current version info
            return [
                {
                    'version_number': 1,
                    'created_at': document.generated_at,
                    'status': document.status,
                    'file_hash': document.document_hash,
                    'is_current': True
                }
            ]
            
        except Exception as e:
            logger.error(f"Error getting version history: {str(e)}")
            return []


class DocumentAuditTrail:
    """
    Manages audit trail for document access and modifications
    """
    
    @staticmethod
    def log_access(user: Account, document: InspectionDocument, action: str, 
                   ip_address: str = None, details: Dict = None):
        """
        Log document access event
        
        Args:
            user: User accessing document
            document: Document being accessed
            action: Action performed (view, download, sign, etc.)
            ip_address: IP address of user
            details: Additional details
        """
        try:
            audit_entry = {
                'timestamp': timezone.now(),
                'user_id': user.id,
                'user_email': user.email,
                'document_id': document.id,
                'inspection_id': document.inspection.id,
                'action': action,
                'ip_address': ip_address,
                'details': details or {}
            }
            
            logger.info(f"Document audit: {audit_entry}")
            
            # In a real implementation, you would store this in a database table
            # For now, we're just logging it
            
        except Exception as e:
            logger.error(f"Error logging document access: {str(e)}")
    
    @staticmethod
    def log_modification(user: Account, document: InspectionDocument, 
                        modification_type: str, details: Dict = None):
        """
        Log document modification event
        
        Args:
            user: User modifying document
            document: Document being modified
            modification_type: Type of modification
            details: Additional details
        """
        try:
            audit_entry = {
                'timestamp': timezone.now(),
                'user_id': user.id,
                'user_email': user.email,
                'document_id': document.id,
                'modification_type': modification_type,
                'previous_status': details.get('previous_status') if details else None,
                'new_status': document.status,
                'details': details or {}
            }
            
            logger.info(f"Document modification: {audit_entry}")
            
        except Exception as e:
            logger.error(f"Error logging document modification: {str(e)}")
    
    @staticmethod
    def get_audit_trail(document: InspectionDocument, 
                       start_date: timezone.datetime = None,
                       end_date: timezone.datetime = None) -> List[Dict]:
        """
        Get audit trail for document
        
        Args:
            document: Document to get audit trail for
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            List of audit entries
        """
        try:
            # In a real implementation, you would query audit records from database
            # For now, return basic information
            
            audit_entries = []
            
            # Document creation
            audit_entries.append({
                'timestamp': document.generated_at,
                'action': 'document_created',
                'user': 'System',
                'details': {
                    'template_type': document.template_type,
                    'status': 'generating'
                }
            })
            
            # Signature events
            for signature in document.signatures.all():
                if signature.signed_at:
                    audit_entries.append({
                        'timestamp': signature.signed_at,
                        'action': 'document_signed',
                        'user': signature.signer.email,
                        'details': {
                            'role': signature.role,
                            'signature_method': signature.signature_method,
                            'ip_address': signature.signer_ip
                        }
                    })
            
            # Sort by timestamp
            audit_entries.sort(key=lambda x: x['timestamp'])
            
            return audit_entries
            
        except Exception as e:
            logger.error(f"Error getting audit trail: {str(e)}")
            return []


class DocumentSearchManager:
    """
    Manages document search and filtering capabilities
    """
    
    @staticmethod
    def search_documents(user: Account, filters: Dict = None) -> List[InspectionDocument]:
        """
        Search documents with filters
        
        Args:
            user: User performing search
            filters: Search filters
            
        Returns:
            List of matching documents
        """
        try:
            # Start with base queryset
            queryset = InspectionDocument.objects.all()
            
            # Filter by user access
            queryset = DocumentSearchManager._filter_by_user_access(queryset, user)
            
            if not filters:
                return list(queryset)
            
            # Apply filters
            if 'inspection_id' in filters:
                queryset = queryset.filter(inspection_id=filters['inspection_id'])
            
            if 'status' in filters:
                queryset = queryset.filter(status=filters['status'])
            
            if 'template_type' in filters:
                queryset = queryset.filter(template_type=filters['template_type'])
            
            if 'date_from' in filters:
                queryset = queryset.filter(generated_at__gte=filters['date_from'])
            
            if 'date_to' in filters:
                queryset = queryset.filter(generated_at__lte=filters['date_to'])
            
            if 'vehicle_id' in filters:
                queryset = queryset.filter(inspection__vehicle_id=filters['vehicle_id'])
            
            if 'customer_id' in filters:
                queryset = queryset.filter(inspection__customer_id=filters['customer_id'])
            
            if 'dealer_id' in filters:
                queryset = queryset.filter(inspection__dealer_id=filters['dealer_id'])
            
            # Search by document hash
            if 'document_hash' in filters:
                queryset = queryset.filter(document_hash=filters['document_hash'])
            
            return list(queryset)
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    @staticmethod
    def _filter_by_user_access(queryset, user: Account):
        """Filter queryset by user access permissions"""
        from django.db.models import Q
        
        # Admin can see all
        if user.is_staff or user.is_superuser:
            return queryset
        
        # Build access filter
        access_filter = Q()
        
        # Inspector access
        access_filter |= Q(inspection__inspector=user)
        
        # Customer access
        if hasattr(user, 'customer'):
            access_filter |= Q(inspection__customer=user.customer)
        
        # Dealer access
        if hasattr(user, 'dealership'):
            access_filter |= Q(inspection__dealer=user.dealership)
        
        return queryset.filter(access_filter)


class DocumentRetentionManager:
    """
    Manages document retention and archival policies
    """
    
    # Retention periods (in days)
    RETENTION_ACTIVE = 365  # 1 year
    RETENTION_ARCHIVED = 2555  # 7 years
    
    @staticmethod
    def check_retention_policy(document: InspectionDocument) -> Dict:
        """
        Check document against retention policy
        
        Returns:
            Dictionary with retention status
        """
        try:
            now = timezone.now()
            age_days = (now - document.generated_at).days
            
            # Determine retention status
            if document.status == 'archived':
                days_until_deletion = DocumentRetentionManager.RETENTION_ARCHIVED - age_days
                should_delete = days_until_deletion <= 0
                status = 'archived'
            else:
                days_until_archive = DocumentRetentionManager.RETENTION_ACTIVE - age_days
                should_archive = days_until_archive <= 0
                status = 'active'
            
            return {
                'document_id': document.id,
                'status': status,
                'age_days': age_days,
                'should_archive': should_archive if status == 'active' else False,
                'should_delete': should_delete if status == 'archived' else False,
                'days_until_archive': days_until_archive if status == 'active' else None,
                'days_until_deletion': days_until_deletion if status == 'archived' else None
            }
            
        except Exception as e:
            logger.error(f"Error checking retention policy: {str(e)}")
            return {}
    
    @staticmethod
    def archive_document(document: InspectionDocument, reason: str = None) -> bool:
        """
        Archive a document
        
        Args:
            document: Document to archive
            reason: Reason for archiving
            
        Returns:
            True if successful
        """
        try:
            # Update document status
            previous_status = document.status
            document.status = 'archived'
            document.save()
            
            # Log the archival
            logger.info(f"Document {document.id} archived. Reason: {reason or 'Retention policy'}")
            
            # Create version before archiving
            DocumentVersionManager.create_version(document, reason=f"Archived: {reason or 'Retention policy'}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error archiving document {document.id}: {str(e)}")
            return False
    
    @staticmethod
    def delete_expired_documents() -> int:
        """
        Delete documents that have exceeded retention period
        
        Returns:
            Number of documents deleted
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=DocumentRetentionManager.RETENTION_ARCHIVED)
            
            # Find expired archived documents
            expired_documents = InspectionDocument.objects.filter(
                status='archived',
                generated_at__lt=cutoff_date
            )
            
            count = expired_documents.count()
            
            # Log before deletion
            for doc in expired_documents:
                logger.info(f"Deleting expired document {doc.id} (age: {(timezone.now() - doc.generated_at).days} days)")
            
            # Delete documents
            expired_documents.delete()
            
            logger.info(f"Deleted {count} expired documents")
            return count
            
        except Exception as e:
            logger.error(f"Error deleting expired documents: {str(e)}")
            return 0
    
    @staticmethod
    def archive_old_documents() -> int:
        """
        Archive documents that have exceeded active retention period
        
        Returns:
            Number of documents archived
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=DocumentRetentionManager.RETENTION_ACTIVE)
            
            # Find old active documents
            old_documents = InspectionDocument.objects.filter(
                status__in=['ready', 'signed'],
                generated_at__lt=cutoff_date
            )
            
            count = 0
            for doc in old_documents:
                if DocumentRetentionManager.archive_document(doc, reason="Automatic archival - retention policy"):
                    count += 1
            
            logger.info(f"Archived {count} old documents")
            return count
            
        except Exception as e:
            logger.error(f"Error archiving old documents: {str(e)}")
            return 0


class DocumentSharingManager:
    """
    Manages document sharing and permission management
    """
    
    @staticmethod
    def share_document(document: InspectionDocument, shared_by: Account, 
                      shared_with_email: str, permission_level: str = 'view',
                      expiry_hours: int = 24) -> Dict:
        """
        Share document with another user
        
        Args:
            document: Document to share
            shared_by: User sharing the document
            shared_with_email: Email of user to share with
            permission_level: Permission level (view, download)
            expiry_hours: Hours until share link expires
            
        Returns:
            Share information dictionary
        """
        try:
            # Check if sharing user has permission
            if not DocumentAccessControl.can_manage(shared_by, document):
                raise PermissionDenied("User does not have permission to share this document")
            
            # Generate share token (in real implementation, use secure token generation)
            import uuid
            share_token = str(uuid.uuid4())
            
            # Calculate expiry
            expiry_time = timezone.now() + timedelta(hours=expiry_hours)
            
            share_info = {
                'document_id': document.id,
                'share_token': share_token,
                'shared_by': shared_by.email,
                'shared_with': shared_with_email,
                'permission_level': permission_level,
                'created_at': timezone.now(),
                'expires_at': expiry_time,
                'is_active': True
            }
            
            logger.info(f"Document {document.id} shared by {shared_by.email} with {shared_with_email}")
            
            # In a real implementation, you would:
            # 1. Store share info in database
            # 2. Send email notification to shared_with_email
            # 3. Generate secure access link
            
            return share_info
            
        except Exception as e:
            logger.error(f"Error sharing document: {str(e)}")
            raise
    
    @staticmethod
    def revoke_share(document: InspectionDocument, share_token: str, revoked_by: Account) -> bool:
        """
        Revoke document share
        
        Args:
            document: Document to revoke share for
            share_token: Share token to revoke
            revoked_by: User revoking the share
            
        Returns:
            True if successful
        """
        try:
            # Check if revoking user has permission
            if not DocumentAccessControl.can_manage(revoked_by, document):
                raise PermissionDenied("User does not have permission to revoke shares")
            
            logger.info(f"Share {share_token} for document {document.id} revoked by {revoked_by.email}")
            
            # In a real implementation, you would update the share record in database
            
            return True
            
        except Exception as e:
            logger.error(f"Error revoking share: {str(e)}")
            return False
    
    @staticmethod
    def get_document_shares(document: InspectionDocument) -> List[Dict]:
        """
        Get all active shares for a document
        
        Returns:
            List of share information dictionaries
        """
        try:
            # In a real implementation, you would query share records from database
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error getting document shares: {str(e)}")
            return []
