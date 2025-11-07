"""
API views for document management system
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.exceptions import PermissionDenied
import logging

from .models import InspectionDocument
from .serializers import InspectionDocumentSerializer
from .document_management import (
    DocumentAccessControl,
    DocumentVersionManager,
    DocumentAuditTrail,
    DocumentSearchManager,
    DocumentRetentionManager,
    DocumentSharingManager
)

logger = logging.getLogger(__name__)


class DocumentAccessCheckView(APIView):
    """
    Check user's access level for a document
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, document_id):
        """
        Get user's access permissions for document
        """
        try:
            document = get_object_or_404(InspectionDocument, id=document_id)
            user = request.user
            
            # Check different access levels
            access_info = {
                'document_id': document.id,
                'can_view': DocumentAccessControl.can_view(user, document),
                'can_download': DocumentAccessControl.can_download(user, document),
                'can_sign': DocumentAccessControl.can_sign(user, document),
                'can_manage': DocumentAccessControl.can_manage(user, document)
            }
            
            return Response({
                'success': True,
                'data': access_info
            })
            
        except Exception as e:
            logger.error(f"Error checking document access: {str(e)}")
            return Response({
                'error': 'Failed to check access'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentVersionHistoryView(APIView):
    """
    Get version history for a document
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, document_id):
        """
        Get document version history
        """
        try:
            document = get_object_or_404(InspectionDocument, id=document_id)
            
            # Check access
            if not DocumentAccessControl.can_view(request.user, document):
                return Response({
                    'error': 'Access denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get version history
            versions = DocumentVersionManager.get_version_history(document)
            
            return Response({
                'success': True,
                'data': {
                    'document_id': document.id,
                    'current_version': 1,
                    'versions': versions
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting version history: {str(e)}")
            return Response({
                'error': 'Failed to get version history'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentAuditTrailView(APIView):
    """
    Get audit trail for a document
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, document_id):
        """
        Get document audit trail
        """
        try:
            document = get_object_or_404(InspectionDocument, id=document_id)
            
            # Check access (only managers can view audit trail)
            if not DocumentAccessControl.can_manage(request.user, document):
                return Response({
                    'error': 'Access denied - management permission required'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get date filters
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            # Get audit trail
            audit_entries = DocumentAuditTrail.get_audit_trail(
                document,
                start_date=timezone.datetime.fromisoformat(start_date) if start_date else None,
                end_date=timezone.datetime.fromisoformat(end_date) if end_date else None
            )
            
            # Log this access
            DocumentAuditTrail.log_access(
                user=request.user,
                document=document,
                action='view_audit_trail',
                ip_address=self._get_client_ip(request)
            )
            
            return Response({
                'success': True,
                'data': {
                    'document_id': document.id,
                    'audit_entries': audit_entries,
                    'total_entries': len(audit_entries)
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting audit trail: {str(e)}")
            return Response({
                'error': 'Failed to get audit trail'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DocumentSearchView(APIView):
    """
    Search and filter documents
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Search documents with filters
        """
        try:
            # Get search filters
            filters = {
                'inspection_id': request.data.get('inspection_id'),
                'status': request.data.get('status'),
                'template_type': request.data.get('template_type'),
                'date_from': request.data.get('date_from'),
                'date_to': request.data.get('date_to'),
                'vehicle_id': request.data.get('vehicle_id'),
                'customer_id': request.data.get('customer_id'),
                'dealer_id': request.data.get('dealer_id'),
                'document_hash': request.data.get('document_hash')
            }
            
            # Remove None values
            filters = {k: v for k, v in filters.items() if v is not None}
            
            # Search documents
            documents = DocumentSearchManager.search_documents(request.user, filters)
            
            # Serialize results
            serializer = InspectionDocumentSerializer(documents, many=True)
            
            return Response({
                'success': True,
                'data': {
                    'count': len(documents),
                    'filters_applied': filters,
                    'documents': serializer.data
                }
            })
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return Response({
                'error': 'Failed to search documents'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentRetentionStatusView(APIView):
    """
    Check document retention status
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, document_id):
        """
        Get retention status for document
        """
        try:
            document = get_object_or_404(InspectionDocument, id=document_id)
            
            # Check access
            if not DocumentAccessControl.can_view(request.user, document):
                return Response({
                    'error': 'Access denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check retention policy
            retention_status = DocumentRetentionManager.check_retention_policy(document)
            
            return Response({
                'success': True,
                'data': retention_status
            })
            
        except Exception as e:
            logger.error(f"Error checking retention status: {str(e)}")
            return Response({
                'error': 'Failed to check retention status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentArchiveView(APIView):
    """
    Archive a document
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, document_id):
        """
        Archive document
        """
        try:
            document = get_object_or_404(InspectionDocument, id=document_id)
            
            # Check access (only managers can archive)
            if not DocumentAccessControl.can_manage(request.user, document):
                return Response({
                    'error': 'Access denied - management permission required'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get reason
            reason = request.data.get('reason', 'Manual archival')
            
            # Archive document
            success = DocumentRetentionManager.archive_document(document, reason)
            
            if success:
                # Log the action
                DocumentAuditTrail.log_modification(
                    user=request.user,
                    document=document,
                    modification_type='archived',
                    details={'reason': reason}
                )
                
                return Response({
                    'success': True,
                    'message': 'Document archived successfully',
                    'data': {
                        'document_id': document.id,
                        'status': document.get_status_display()
                    }
                })
            else:
                return Response({
                    'error': 'Failed to archive document'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            logger.error(f"Error archiving document: {str(e)}")
            return Response({
                'error': 'Failed to archive document'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentShareView(APIView):
    """
    Share document with another user
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, document_id):
        """
        Share document
        """
        try:
            document = get_object_or_404(InspectionDocument, id=document_id)
            
            # Get share parameters
            shared_with_email = request.data.get('email')
            permission_level = request.data.get('permission_level', 'view')
            expiry_hours = request.data.get('expiry_hours', 24)
            
            # Validate parameters
            if not shared_with_email:
                return Response({
                    'error': 'Email is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Share document
            share_info = DocumentSharingManager.share_document(
                document=document,
                shared_by=request.user,
                shared_with_email=shared_with_email,
                permission_level=permission_level,
                expiry_hours=expiry_hours
            )
            
            # Log the action
            DocumentAuditTrail.log_access(
                user=request.user,
                document=document,
                action='shared_document',
                details={
                    'shared_with': shared_with_email,
                    'permission_level': permission_level
                }
            )
            
            return Response({
                'success': True,
                'message': 'Document shared successfully',
                'data': share_info
            })
            
        except PermissionDenied as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"Error sharing document: {str(e)}")
            return Response({
                'error': 'Failed to share document'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentShareListView(APIView):
    """
    List all shares for a document
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, document_id):
        """
        Get document shares
        """
        try:
            document = get_object_or_404(InspectionDocument, id=document_id)
            
            # Check access (only managers can view shares)
            if not DocumentAccessControl.can_manage(request.user, document):
                return Response({
                    'error': 'Access denied - management permission required'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get shares
            shares = DocumentSharingManager.get_document_shares(document)
            
            return Response({
                'success': True,
                'data': {
                    'document_id': document.id,
                    'shares': shares,
                    'total_shares': len(shares)
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting document shares: {str(e)}")
            return Response({
                'error': 'Failed to get document shares'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentShareRevokeView(APIView):
    """
    Revoke document share
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, document_id):
        """
        Revoke share
        """
        try:
            document = get_object_or_404(InspectionDocument, id=document_id)
            share_token = request.data.get('share_token')
            
            if not share_token:
                return Response({
                    'error': 'Share token is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Revoke share
            success = DocumentSharingManager.revoke_share(
                document=document,
                share_token=share_token,
                revoked_by=request.user
            )
            
            if success:
                # Log the action
                DocumentAuditTrail.log_access(
                    user=request.user,
                    document=document,
                    action='revoked_share',
                    details={'share_token': share_token}
                )
                
                return Response({
                    'success': True,
                    'message': 'Share revoked successfully'
                })
            else:
                return Response({
                    'error': 'Failed to revoke share'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except PermissionDenied as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"Error revoking share: {str(e)}")
            return Response({
                'error': 'Failed to revoke share'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def run_retention_cleanup(request):
    """
    Run retention policy cleanup (admin only)
    """
    try:
        # Archive old documents
        archived_count = DocumentRetentionManager.archive_old_documents()
        
        # Delete expired documents
        deleted_count = DocumentRetentionManager.delete_expired_documents()
        
        return Response({
            'success': True,
            'message': 'Retention cleanup completed',
            'data': {
                'archived_count': archived_count,
                'deleted_count': deleted_count
            }
        })
        
    except Exception as e:
        logger.error(f"Error running retention cleanup: {str(e)}")
        return Response({
            'error': 'Failed to run retention cleanup'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
