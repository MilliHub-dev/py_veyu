"""
Secure document access views for business verification
"""
import os
import mimetypes
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.core.exceptions import PermissionDenied
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.models import BusinessVerificationSubmission, Dealership, Mechanic


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def serve_verification_document(request, submission_id, document_type):
    """
    Generate secure URL for business verification documents stored in Cloudinary
    
    Args:
        request: HTTP request
        submission_id: BusinessVerificationSubmission ID
        document_type: Type of document (cac_document, tin_document, etc.)
    
    Returns:
        Response with secure Cloudinary URL or error
    """
    from accounts.utils.document_storage import CloudinaryDocumentStorage
    from accounts.models import DocumentAccessLog
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Get the submission
    try:
        submission = BusinessVerificationSubmission.objects.get(id=submission_id)
    except BusinessVerificationSubmission.DoesNotExist:
        return Response({
            'error': True,
            'message': 'Document not found'
        }, status=404)
    
    # Check permissions
    user = request.user
    
    # Allow access if:
    # 1. User is the owner of the business profile
    # 2. User is staff/admin
    # 3. User is the reviewer
    has_permission = False
    
    if user.is_staff or user.is_superuser:
        has_permission = True
    elif submission.reviewed_by == user:
        has_permission = True
    elif submission.dealership and submission.dealership.user == user:
        has_permission = True
    elif submission.mechanic and submission.mechanic.user == user:
        has_permission = True
    
    if not has_permission:
        return Response({
            'error': True,
            'message': "You don't have permission to access this document"
        }, status=403)
    
    # Validate document type
    valid_document_types = ['cac_document', 'tin_document', 'proof_of_address', 'business_license']
    if document_type not in valid_document_types:
        return Response({
            'error': True,
            'message': f'Invalid document type. Must be one of: {", ".join(valid_document_types)}'
        }, status=400)
    
    # Get the document field
    document = getattr(submission, document_type, None)
    
    if not document or not hasattr(document, 'public_id'):
        return Response({
            'error': True,
            'message': f'Document {document_type} not found for this submission'
        }, status=404)
    
    # Generate secure URL from Cloudinary
    try:
        storage = CloudinaryDocumentStorage()
        expires_in = int(request.GET.get('expires_in', 3600))  # Default 1 hour
        secure_url = storage.get_secure_url(document.public_id, expires_in)
        
        # Log the access attempt
        try:
            DocumentAccessLog.objects.create(
                submission=submission,
                document_type=document_type,
                accessed_by=user,
                access_type='view',
                ip_address=_get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )
        except Exception as log_error:
            logger.warning(f"Failed to log document access: {str(log_error)}")
        
        return Response({
            'error': False,
            'secure_url': secure_url,
            'expires_in': expires_in,
            'document_type': document_type,
            'submission_id': submission_id,
            'message': 'Secure document URL generated successfully'
        }, status=200)
        
    except Exception as e:
        logger.error(f"Failed to generate secure URL for {document_type}: {str(e)}")
        return Response({
            'error': True,
            'message': 'Failed to generate secure document URL',
            'details': str(e)
        }, status=500)


def _get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_document_requirements(request):
    """
    Get document requirements for business verification
    
    Returns:
        Response with document requirements
    """
    from accounts.utils.document_validation import get_document_requirements
    
    requirements = get_document_requirements()
    
    return Response({
        'error': False,
        'message': 'Document requirements retrieved successfully',
        'data': {
            'requirements': requirements,
            'max_file_size': '5MB',
            'allowed_formats': ['PDF', 'JPG', 'JPEG', 'PNG'],
            'notes': [
                'All documents must be clear and legible',
                'Documents should be recent (within 6 months for utility bills)',
                'Business name on documents should match the business name in your profile',
                'All documents will be reviewed by our verification team'
            ]
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_verification_documents(request):
    """
    Get list of documents uploaded by the current user
    
    Returns:
        Response with user's verification documents
    """
    user = request.user
    
    # Find user's business profile
    try:
        if user.user_type == 'dealer':
            from accounts.models import Dealership
            business_profile = Dealership.objects.get(user=user)
        elif user.user_type == 'mechanic':
            from accounts.models import Mechanic
            business_profile = Mechanic.objects.get(user=user)
        else:
            return Response({
                'error': True,
                'message': 'Only dealers and mechanics can access verification documents'
            }, status=400)
    except (Dealership.DoesNotExist, Mechanic.DoesNotExist):
        return Response({
            'error': True,
            'message': 'Business profile not found'
        }, status=404)
    
    # Get verification submission
    try:
        submission = business_profile.verification_submission
    except BusinessVerificationSubmission.DoesNotExist:
        return Response({
            'error': False,
            'message': 'No verification submission found',
            'data': {
                'submission_exists': False,
                'documents': {}
            }
        })
    
    # Build document info
    documents = {}
    document_fields = ['cac_document', 'tin_document', 'proof_of_address', 'business_license']
    
    for field_name in document_fields:
        document_file = getattr(submission, field_name)
        if document_file and hasattr(document_file, 'public_id'):
            # Get original filename from metadata
            original_name_field = f'{field_name}_original_name'
            original_filename = getattr(submission, original_name_field, 'document')
            
            # Get upload date from metadata
            upload_date_field = f'{field_name}_uploaded_at'
            upload_date = getattr(submission, upload_date_field, submission.date_created)
            
            documents[field_name] = {
                'filename': original_filename or f'{field_name}.pdf',
                'public_id': document_file.public_id,
                'uploaded_date': upload_date.isoformat() if upload_date else submission.date_created.isoformat(),
                'url': f'/api/v1/accounts/verification/documents/{submission.id}/{field_name}/',
                'thumbnail_url': submission.get_document_thumbnail_url(field_name),
                'has_document': True
            }
        else:
            documents[field_name] = {
                'filename': None,
                'public_id': None,
                'uploaded_date': None,
                'url': None,
                'thumbnail_url': None,
                'has_document': False
            }
    
    return Response({
        'error': False,
        'message': 'Documents retrieved successfully',
        'data': {
            'submission_exists': True,
            'submission_id': submission.id,
            'status': submission.status,
            'status_display': submission.get_status_display(),
            'documents': documents,
            'business_name': submission.business_name,
            'submission_date': submission.date_created.isoformat()
        }
    })