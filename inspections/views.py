"""
API views for the vehicle inspection system
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Count, Avg, Q
from django.utils import timezone
from django.http import HttpResponse, Http404
import logging

from .models import (
    VehicleInspection,
    InspectionPhoto,
    InspectionDocument,
    DigitalSignature,
    InspectionTemplate
)
from .serializers import (
    VehicleInspectionListSerializer,
    VehicleInspectionDetailSerializer,
    VehicleInspectionCreateSerializer,
    InspectionPhotoSerializer,
    InspectionDocumentSerializer,
    DocumentGenerationSerializer,
    SignatureSubmissionSerializer,
    InspectionTemplateSerializer,
    InspectionStatsSerializer
)
from .services import DocumentManagementService, InspectionValidationService

logger = logging.getLogger(__name__)


class VehicleInspectionListCreateView(generics.ListCreateAPIView):
    """
    List all inspections or create a new inspection
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VehicleInspectionCreateSerializer
        return VehicleInspectionListSerializer
    
    def get_queryset(self):
        queryset = VehicleInspection.objects.select_related(
            'vehicle', 'inspector', 'customer__user', 'dealer__user'
        ).order_by('-inspection_date')
        
        # Handle swagger schema generation with fake view
        if getattr(self, 'swagger_fake_view', False):
            return queryset
        
        # Filter by user role
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
            
        if hasattr(user, 'customer'):
            queryset = queryset.filter(customer=user.customer)
        elif hasattr(user, 'dealership'):
            queryset = queryset.filter(dealer=user.dealership)
        elif getattr(user, 'user_type', None) == 'mechanic':
            queryset = queryset.filter(inspector=user)
        
        # Additional filters
        inspection_type = self.request.query_params.get('type')
        if inspection_type:
            queryset = queryset.filter(inspection_type=inspection_type)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        vehicle_id = self.request.query_params.get('vehicle_id')
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set default values when creating inspection"""
        # Auto-assign inspector if user is a mechanic
        if getattr(self.request.user, 'user_type', None) == 'mechanic':
            serializer.save(inspector=self.request.user)
        else:
            serializer.save()


class VehicleInspectionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a specific inspection
    """
    serializer_class = VehicleInspectionDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = VehicleInspection.objects.select_related(
            'vehicle', 'inspector', 'customer__user', 'dealer__user'
        ).prefetch_related('photos', 'documents__signatures')
        
        # Handle swagger schema generation with fake view
        if getattr(self, 'swagger_fake_view', False):
            return queryset
        
        # Filter by user permissions
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
            
        if hasattr(user, 'customer'):
            queryset = queryset.filter(customer=user.customer)
        elif hasattr(user, 'dealership'):
            queryset = queryset.filter(dealer=user.dealership)
        elif getattr(user, 'user_type', None) == 'mechanic':
            queryset = queryset.filter(inspector=user)
        
        return queryset


class InspectionPhotoUploadView(APIView):
    """
    Upload photos for an inspection
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, inspection_id):
        """Upload a photo for the inspection"""
        try:
            inspection = get_object_or_404(VehicleInspection, id=inspection_id)
            
            # Check permissions
            if not self._has_permission(request.user, inspection):
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = InspectionPhotoSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(inspection=inspection)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error uploading photo for inspection {inspection_id}: {str(e)}")
            return Response(
                {'error': 'Failed to upload photo'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _has_permission(self, user, inspection):
        """Check if user has permission to upload photos"""
        return (
            user == inspection.inspector or
            (hasattr(user, 'customer') and user.customer == inspection.customer) or
            (hasattr(user, 'dealership') and user.dealership == inspection.dealer)
        )


class DocumentGenerationView(APIView):
    """
    Generate inspection document PDF
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, inspection_id):
        """Generate document for inspection"""
        try:
            inspection = get_object_or_404(VehicleInspection, id=inspection_id)
            
            # Check permissions
            if not self._has_permission(request.user, inspection):
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Validate request data
            serializer = DocumentGenerationSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate document
            doc_service = DocumentManagementService()
            document = doc_service.create_inspection_document(
                inspection=inspection,
                **serializer.validated_data
            )
            
            # Return document details
            doc_serializer = InspectionDocumentSerializer(document)
            return Response({
                'success': True,
                'data': doc_serializer.data,
                'message': 'Document generated successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error generating document for inspection {inspection_id}: {str(e)}")
            return Response(
                {'error': 'Failed to generate document'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _has_permission(self, user, inspection):
        """Check if user has permission to generate documents"""
        return (
            user == inspection.inspector or
            (hasattr(user, 'dealership') and user.dealership == inspection.dealer)
        )


class DocumentPreviewView(APIView):
    """
    Get document preview information
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, document_id):
        """Get document preview data"""
        try:
            document = get_object_or_404(InspectionDocument, id=document_id)
            
            # Check permissions
            if not self._has_permission(request.user, document.inspection):
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get document status
            doc_service = DocumentManagementService()
            document_status = doc_service.get_document_status(document)
            
            # Prepare response data
            response_data = {
                'document_id': document.id,
                'preview_url': request.build_absolute_uri(document.document_file.url) if document.document_file else None,
                'thumbnail_url': None,  # Would be generated in real implementation
                'page_count': document.page_count,
                'document_size': document.formatted_file_size,
                'metadata': {
                    'title': f'Vehicle Inspection Report - {document.inspection.vehicle.name}',
                    'created_at': document.generated_at,
                    'inspector': document.inspection.inspector.name,
                    'vehicle_vin': getattr(document.inspection.vehicle, 'vin', 'N/A'),
                },
                'signature_fields': self._get_signature_fields(document),
                'status': document_status
            }
            
            return Response({
                'success': True,
                'data': response_data
            })
            
        except Exception as e:
            logger.error(f"Error getting document preview {document_id}: {str(e)}")
            return Response(
                {'error': 'Failed to get document preview'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _has_permission(self, user, inspection):
        """Check if user has permission to view document"""
        return (
            user == inspection.inspector or
            (hasattr(user, 'customer') and user.customer == inspection.customer) or
            (hasattr(user, 'dealership') and user.dealership == inspection.dealer)
        )
    
    def _get_signature_fields(self, document):
        """Get signature field information"""
        signatures = document.signatures.all()
        fields = []
        
        y_position = 200
        for signature in signatures:
            fields.append({
                'field_id': f'{signature.role}_signature',
                'role': signature.role,
                'page': document.page_count,  # Signatures on last page
                'coordinates': {
                    'x': 100 if signature.role == 'inspector' else (350 if signature.role == 'customer' else 600),
                    'y': y_position,
                    'width': 200,
                    'height': 50
                },
                'required': True,
                'status': signature.status
            })
        
        return fields


class DocumentSignatureView(APIView):
    """
    Submit digital signature for document
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, document_id):
        """Submit signature for document"""
        try:
            document = get_object_or_404(InspectionDocument, id=document_id)
            
            # Validate request data
            serializer = SignatureSubmissionSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Submit signature
            doc_service = DocumentManagementService()
            signature = doc_service.submit_signature(
                document=document,
                signer_id=request.user.id,
                signature_data=serializer.validated_data['signature_data'],
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                'success': True,
                'data': {
                    'signature_id': signature.id,
                    'status': signature.get_status_display(),
                    'signed_at': signature.signed_at,
                    'document_status': document.get_status_display()
                },
                'message': 'Signature submitted successfully'
            })
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error submitting signature for document {document_id}: {str(e)}")
            return Response(
                {'error': 'Failed to submit signature'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DocumentDownloadView(APIView):
    """
    Download inspection document
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, document_id):
        """Download document file"""
        try:
            document = get_object_or_404(InspectionDocument, id=document_id)
            
            # Check permissions
            if not self._has_permission(request.user, document.inspection):
                raise Http404("Document not found")
            
            # Check if document file exists
            if not document.document_file:
                return Response(
                    {'error': 'Document file not available'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Return file response
            response = HttpResponse(
                document.document_file.read(),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="inspection_{document.inspection.id}.pdf"'
            return response
            
        except Exception as e:
            logger.error(f"Error downloading document {document_id}: {str(e)}")
            raise Http404("Document not found")
    
    def _has_permission(self, user, inspection):
        """Check if user has permission to download document"""
        return (
            user == inspection.inspector or
            (hasattr(user, 'customer') and user.customer == inspection.customer) or
            (hasattr(user, 'dealership') and user.dealership == inspection.dealer)
        )


class InspectionStatsView(APIView):
    """
    Get inspection statistics
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get inspection statistics for the user"""
        try:
            user = request.user
            
            # Get base queryset based on user role
            if hasattr(user, 'customer'):
                queryset = VehicleInspection.objects.filter(customer=user.customer)
            elif hasattr(user, 'dealership'):
                queryset = VehicleInspection.objects.filter(dealer=user.dealership)
            elif getattr(user, 'user_type', None) == 'mechanic':
                queryset = VehicleInspection.objects.filter(inspector=user)
            else:
                queryset = VehicleInspection.objects.all()
            
            # Calculate statistics
            total_inspections = queryset.count()
            completed_inspections = queryset.filter(status__in=['completed', 'signed']).count()
            pending_inspections = queryset.filter(status__in=['draft', 'in_progress']).count()
            
            # Signed documents count
            signed_documents = InspectionDocument.objects.filter(
                inspection__in=queryset,
                status='signed'
            ).count()
            
            # Average rating
            avg_rating = queryset.exclude(overall_rating__isnull=True).aggregate(
                avg=Avg('overall_rating')
            )['avg'] or 0
            
            # Convert rating to numeric for calculation
            rating_map = {'poor': 1, 'fair': 2, 'good': 3, 'excellent': 4}
            numeric_ratings = []
            for inspection in queryset.exclude(overall_rating__isnull=True):
                if inspection.overall_rating in rating_map:
                    numeric_ratings.append(rating_map[inspection.overall_rating])
            
            average_rating = sum(numeric_ratings) / len(numeric_ratings) if numeric_ratings else 0
            
            # Inspections by type
            inspections_by_type = dict(
                queryset.values('inspection_type').annotate(count=Count('id')).values_list('inspection_type', 'count')
            )
            
            # Inspections by status
            inspections_by_status = dict(
                queryset.values('status').annotate(count=Count('id')).values_list('status', 'count')
            )
            
            # Recent inspections
            recent_inspections = queryset.order_by('-inspection_date')[:5]
            
            stats_data = {
                'total_inspections': total_inspections,
                'completed_inspections': completed_inspections,
                'pending_inspections': pending_inspections,
                'signed_documents': signed_documents,
                'average_rating': round(average_rating, 2),
                'inspections_by_type': inspections_by_type,
                'inspections_by_status': inspections_by_status,
                'recent_inspections': recent_inspections
            }
            
            serializer = InspectionStatsSerializer(stats_data)
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error getting inspection stats: {str(e)}")
            return Response(
                {'error': 'Failed to get statistics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InspectionTemplateListView(generics.ListAPIView):
    """
    List available inspection templates
    """
    serializer_class = InspectionTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return InspectionTemplate.objects.filter(is_active=True).order_by('category', 'name')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def complete_inspection(request, inspection_id):
    """
    Mark an inspection as completed
    """
    try:
        inspection = get_object_or_404(VehicleInspection, id=inspection_id)
        
        # Check permissions
        if request.user != inspection.inspector:
            return Response(
                {'error': 'Only the inspector can complete the inspection'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Mark as completed
        inspection.mark_completed()
        
        return Response({
            'success': True,
            'message': 'Inspection marked as completed',
            'data': {
                'inspection_id': inspection.id,
                'status': inspection.get_status_display(),
                'completed_at': inspection.completed_at
            }
        })
        
    except Exception as e:
        logger.error(f"Error completing inspection {inspection_id}: {str(e)}")
        return Response(
            {'error': 'Failed to complete inspection'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def inspection_validation(request):
    """
    Validate inspection data structure
    """
    try:
        inspection_data = request.query_params.get('data', '{}')
        
        # Parse JSON data
        import json
        try:
            data = json.loads(inspection_data)
        except json.JSONDecodeError:
            return Response(
                {'error': 'Invalid JSON data'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate data
        is_valid, errors = InspectionValidationService.validate_inspection_data(data)
        
        response_data = {
            'is_valid': is_valid,
            'errors': errors
        }
        
        if is_valid:
            response_data['suggested_rating'] = InspectionValidationService.calculate_overall_rating(data)
        
        return Response({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"Error validating inspection data: {str(e)}")
        return Response(
            {'error': 'Failed to validate inspection data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )