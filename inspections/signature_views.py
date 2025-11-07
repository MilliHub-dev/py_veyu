"""
Enhanced API views for digital signature management
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
import logging

from .models import InspectionDocument, DigitalSignature
from .signature_utils import (
    SignatureValidator,
    SignatureAuditLogger,
    SignatureSecurityManager,
    SignatureNotificationManager,
    validate_signature_coordinates
)
from .serializers import DigitalSignatureSerializer

logger = logging.getLogger(__name__)


class SignatureValidationView(APIView):
    """
    Validate signature data before submission
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Validate signature image and metadata
        """
        try:
            signature_data = request.data.get('signature_data', {})
            signature_image = signature_data.get('signature_image', '')
            coordinates = signature_data.get('coordinates', {})
            
            # Validate signature image
            is_valid_image, image_error = SignatureValidator.validate_signature_image(signature_image)
            if not is_valid_image:
                return Response({
                    'valid': False,
                    'errors': {'signature_image': image_error}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate coordinates if provided
            if coordinates:
                is_valid_coords, coords_error = validate_signature_coordinates(coordinates)
                if not is_valid_coords:
                    return Response({
                        'valid': False,
                        'errors': {'coordinates': coords_error}
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'valid': True,
                'message': 'Signature data is valid'
            })
            
        except Exception as e:
            logger.error(f"Error validating signature: {str(e)}")
            return Response({
                'valid': False,
                'errors': {'general': 'Signature validation failed'}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SignaturePermissionCheckView(APIView):
    """
    Check if user has permission to sign a document
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, document_id):
        """
        Check signature permissions for a document
        """
        try:
            document = get_object_or_404(InspectionDocument, id=document_id)
            user = request.user
            
            # Check permissions
            has_permission, error_message = SignatureSecurityManager.check_signature_permissions(user, document)
            
            if not has_permission:
                return Response({
                    'has_permission': False,
                    'message': error_message
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check timing constraints
            is_valid_timing, timing_error = SignatureSecurityManager.validate_signature_timing(document)
            if not is_valid_timing:
                return Response({
                    'has_permission': False,
                    'message': timing_error
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check rate limiting
            is_allowed, rate_limit_error = SignatureSecurityManager.check_signature_rate_limit(user)
            if not is_allowed:
                return Response({
                    'has_permission': False,
                    'message': rate_limit_error
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Get signature details
            signature = document.signatures.get(signer=user, status='pending')
            
            return Response({
                'has_permission': True,
                'signature_details': {
                    'signature_id': signature.id,
                    'role': signature.get_role_display(),
                    'document_id': document.id,
                    'document_status': document.get_status_display(),
                    'expires_at': document.expires_at
                }
            })
            
        except DigitalSignature.DoesNotExist:
            return Response({
                'has_permission': False,
                'message': 'No pending signature found for this user'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error checking signature permissions for document {document_id}: {str(e)}")
            return Response({
                'has_permission': False,
                'message': 'Permission check failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SignatureStatusView(APIView):
    """
    Get signature status for a document
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, document_id):
        """
        Get all signatures and their status for a document
        """
        try:
            document = get_object_or_404(InspectionDocument, id=document_id)
            
            # Check if user has access to this document
            if not self._has_access(request.user, document):
                return Response({
                    'error': 'Access denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get all signatures
            signatures = document.signatures.all()
            serializer = DigitalSignatureSerializer(signatures, many=True)
            
            # Calculate completion percentage
            total_signatures = signatures.count()
            completed_signatures = signatures.filter(status='signed').count()
            completion_percentage = (completed_signatures / total_signatures * 100) if total_signatures > 0 else 0
            
            return Response({
                'success': True,
                'data': {
                    'document_id': document.id,
                    'document_status': document.get_status_display(),
                    'total_signatures': total_signatures,
                    'completed_signatures': completed_signatures,
                    'pending_signatures': signatures.filter(status='pending').count(),
                    'completion_percentage': round(completion_percentage, 2),
                    'signatures': serializer.data
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting signature status for document {document_id}: {str(e)}")
            return Response({
                'error': 'Failed to get signature status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _has_access(self, user, document):
        """Check if user has access to view document signatures"""
        inspection = document.inspection
        return (
            user == inspection.inspector or
            (hasattr(user, 'customer') and user.customer == inspection.customer) or
            (hasattr(user, 'dealership') and user.dealership == inspection.dealer)
        )


class SignatureAuditTrailView(APIView):
    """
    Get audit trail for signatures on a document
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, document_id):
        """
        Get audit trail for all signatures on a document
        """
        try:
            document = get_object_or_404(InspectionDocument, id=document_id)
            
            # Check if user has access
            if not self._has_access(request.user, document):
                return Response({
                    'error': 'Access denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get all signatures with audit information
            signatures = document.signatures.all().order_by('signed_at')
            
            audit_trail = []
            for signature in signatures:
                audit_entry = {
                    'signature_id': signature.id,
                    'role': signature.get_role_display(),
                    'signer_name': signature.signer.name,
                    'signer_email': signature.signer.email,
                    'status': signature.get_status_display(),
                    'signature_method': signature.get_signature_method_display() if signature.signature_method else None,
                    'signed_at': signature.signed_at,
                    'signer_ip': signature.signer_ip,
                    'is_verified': signature.is_verified,
                    'signature_hash': signature.signature_hash,
                    'created_at': signature.date_created
                }
                audit_trail.append(audit_entry)
            
            return Response({
                'success': True,
                'data': {
                    'document_id': document.id,
                    'inspection_id': document.inspection.id,
                    'document_generated_at': document.generated_at,
                    'document_status': document.get_status_display(),
                    'audit_trail': audit_trail
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting audit trail for document {document_id}: {str(e)}")
            return Response({
                'error': 'Failed to get audit trail'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _has_access(self, user, document):
        """Check if user has access to view audit trail"""
        inspection = document.inspection
        return (
            user == inspection.inspector or
            (hasattr(user, 'customer') and user.customer == inspection.customer) or
            (hasattr(user, 'dealership') and user.dealership == inspection.dealer) or
            user.is_staff  # Admin access
        )


class SignatureVerificationView(APIView):
    """
    Verify the integrity of a signature
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, signature_id):
        """
        Verify a signature's integrity
        """
        try:
            signature = get_object_or_404(DigitalSignature, id=signature_id)
            
            # Check if user has access
            if not self._has_access(request.user, signature.document):
                return Response({
                    'error': 'Access denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Verify signature integrity
            if not signature.signature_hash:
                return Response({
                    'verified': False,
                    'message': 'Signature has no hash for verification'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # In a real implementation, you would verify against the original signature data
            # For now, we'll check if the signature is marked as verified
            is_verified = signature.is_verified
            
            # Log verification attempt
            SignatureAuditLogger.log_signature_verification(
                signature_id=signature.id,
                verified=is_verified,
                verifier_id=request.user.id
            )
            
            return Response({
                'success': True,
                'data': {
                    'signature_id': signature.id,
                    'verified': is_verified,
                    'signature_hash': signature.signature_hash,
                    'signed_at': signature.signed_at,
                    'signer': signature.signer.name,
                    'role': signature.get_role_display()
                }
            })
            
        except Exception as e:
            logger.error(f"Error verifying signature {signature_id}: {str(e)}")
            return Response({
                'error': 'Signature verification failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _has_access(self, user, document):
        """Check if user has access to verify signatures"""
        inspection = document.inspection
        return (
            user == inspection.inspector or
            (hasattr(user, 'customer') and user.customer == inspection.customer) or
            (hasattr(user, 'dealership') and user.dealership == inspection.dealer) or
            user.is_staff
        )


class BulkSignatureStatusView(APIView):
    """
    Get signature status for multiple documents
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Get signature status for multiple documents
        """
        try:
            document_ids = request.data.get('document_ids', [])
            
            if not document_ids:
                return Response({
                    'error': 'No document IDs provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get documents
            documents = InspectionDocument.objects.filter(id__in=document_ids)
            
            # Filter by user access
            accessible_documents = []
            for document in documents:
                if self._has_access(request.user, document):
                    accessible_documents.append(document)
            
            # Get signature status for each document
            results = []
            for document in accessible_documents:
                signatures = document.signatures.all()
                total = signatures.count()
                completed = signatures.filter(status='signed').count()
                
                results.append({
                    'document_id': document.id,
                    'inspection_id': document.inspection.id,
                    'document_status': document.get_status_display(),
                    'total_signatures': total,
                    'completed_signatures': completed,
                    'pending_signatures': total - completed,
                    'completion_percentage': round((completed / total * 100) if total > 0 else 0, 2)
                })
            
            return Response({
                'success': True,
                'data': {
                    'requested_count': len(document_ids),
                    'accessible_count': len(accessible_documents),
                    'results': results
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting bulk signature status: {str(e)}")
            return Response({
                'error': 'Failed to get signature status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _has_access(self, user, document):
        """Check if user has access to view document"""
        inspection = document.inspection
        return (
            user == inspection.inspector or
            (hasattr(user, 'customer') and user.customer == inspection.customer) or
            (hasattr(user, 'dealership') and user.dealership == inspection.dealer)
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def resend_signature_notification(request, signature_id):
    """
    Resend notification for a pending signature
    """
    try:
        signature = get_object_or_404(DigitalSignature, id=signature_id)
        
        # Check if user has permission to resend notification
        document = signature.document
        inspection = document.inspection
        
        if not (request.user == inspection.inspector or 
                (hasattr(request.user, 'dealership') and request.user.dealership == inspection.dealer)):
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if signature is still pending
        if signature.status != 'pending':
            return Response({
                'error': f'Signature is not pending (status: {signature.get_status_display()})'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Resend notification
        SignatureNotificationManager.notify_signature_required(document, signature)
        
        return Response({
            'success': True,
            'message': f'Notification sent to {signature.signer.email}'
        })
        
    except Exception as e:
        logger.error(f"Error resending signature notification for signature {signature_id}: {str(e)}")
        return Response({
            'error': 'Failed to resend notification'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reject_signature(request, signature_id):
    """
    Reject a signature request
    """
    try:
        signature = get_object_or_404(DigitalSignature, id=signature_id)
        
        # Check if user is the signer
        if request.user != signature.signer:
            return Response({
                'error': 'Only the signer can reject the signature'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if signature is pending
        if signature.status != 'pending':
            return Response({
                'error': f'Signature cannot be rejected (status: {signature.get_status_display()})'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get rejection reason
        rejection_reason = request.data.get('reason', 'No reason provided')
        
        # Update signature status
        signature.status = 'rejected'
        signature.save()
        
        # Log rejection
        logger.info(f"Signature {signature.id} rejected by user {request.user.id}. Reason: {rejection_reason}")
        
        return Response({
            'success': True,
            'message': 'Signature rejected successfully',
            'data': {
                'signature_id': signature.id,
                'status': signature.get_status_display(),
                'rejection_reason': rejection_reason
            }
        })
        
    except Exception as e:
        logger.error(f"Error rejecting signature {signature_id}: {str(e)}")
        return Response({
            'error': 'Failed to reject signature'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
