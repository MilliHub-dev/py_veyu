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
from accounts.models import BusinessVerificationSubmission


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def serve_verification_document(request, submission_id, document_type):
    """
    Securely serve business verification documents
    
    Args:
        request: HTTP request
        submission_id: BusinessVerificationSubmission ID
        document_type: Type of document (cac_document, tin_document, etc.)
    
    Returns:
        HttpResponse with document content or error
    """
    # Get the submission
    try:
        submission = BusinessVerificationSubmission.objects.get(id=submission_id)
    except BusinessVerificationSubmission.DoesNotExist:
        raise Http404("Document not found")
    
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
    elif submission.business_profile and submission.business_profile.user == user:
        has_permission = True
    
    if not has_permission:
        return HttpResponseForbidden("You don't have permission to access this document")
    
    # Get the document field
    document_fields = {
        'cac_document': submission.cac_document,
        'tin_document': submission.tin_document,
        'proof_of_address': submission.proof_of_address,
        'business_license': submission.business_license,
    }
    
    if document_type not in document_fields:
        raise Http404("Invalid document type")
    
    document_file = document_fields[document_type]
    
    if not document_file:
        raise Http404("Document not found")
    
    # Serve the file
    try:
        # Get file path
        file_path = document_file.path
        
        if not os.path.exists(file_path):
            raise Http404("Document file not found on disk")
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'
        
        # Read and serve file
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
            
        # Set headers
        filename = os.path.basename(file_path)
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        
        return response
        
    except Exception as e:
        raise Http404(f"Error serving document: {str(e)}")


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
        if document_file:
            documents[field_name] = {
                'filename': os.path.basename(document_file.name),
                'size': document_file.size,
                'uploaded_date': submission.date_created.isoformat(),
                'url': f'/api/accounts/verification/documents/{submission.id}/{field_name}/'
            }
        else:
            documents[field_name] = None
    
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