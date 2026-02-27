"""
API views specifically designed for frontend integration
Provides simplified endpoints for inspection data collection, document preview, and status updates
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
import logging

from .models import (
    VehicleInspection,
    InspectionDocument,
    DigitalSignature,
    InspectionPhoto
)
from .serializers import (
    VehicleInspectionDetailSerializer,
    InspectionDocumentSerializer,
    InspectionPhotoSerializer
)
from .services import DocumentManagementService, InspectionValidationService

logger = logging.getLogger(__name__)


class InspectionDataCollectionView(APIView):
    """
    Simplified endpoint for collecting inspection data from frontend forms
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Submit inspection data from frontend
        """
        try:
            # Extract data from request
            vehicle_id = request.data.get('vehicle_id')
            inspection_type = request.data.get('inspection_type', 'pre_purchase')
            customer_id = request.data.get('customer_id')
            dealer_id = request.data.get('dealer_id')
            
            # Validate required fields
            if not all([vehicle_id, customer_id, dealer_id]):
                return Response({
                    'error': 'Missing required fields: vehicle_id, customer_id, dealer_id'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get inspection data sections
            inspection_data = {
                'exterior_data': request.data.get('exterior', {}),
                'interior_data': request.data.get('interior', {}),
                'engine_data': request.data.get('engine', {}),
                'mechanical_data': request.data.get('mechanical', {}),
                'safety_data': request.data.get('safety', {}),
                'documentation_data': request.data.get('documentation', {})
            }
            
            # Validate inspection data
            validation_data = {
                'exterior': inspection_data['exterior_data'],
                'interior': inspection_data['interior_data'],
                'engine': inspection_data['engine_data'],
                'mechanical': inspection_data['mechanical_data'],
                'safety': inspection_data['safety_data']
            }
            
            is_valid, errors = InspectionValidationService.validate_inspection_data(validation_data)
            if not is_valid:
                return Response({
                    'error': 'Invalid inspection data',
                    'validation_errors': errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate overall rating
            overall_rating = InspectionValidationService.calculate_overall_rating(validation_data)
            
            # Create or update inspection
            inspection_id = request.data.get('inspection_id')
            
            if inspection_id:
                # Update existing inspection
                inspection = get_object_or_404(VehicleInspection, id=inspection_id)
                
                # Check permissions
                if not self._has_permission(request.user, inspection):
                    return Response({
                        'error': 'Permission denied'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Update fields
                for key, value in inspection_data.items():
                    setattr(inspection, key, value)
                
                inspection.overall_rating = overall_rating
                inspection.inspector_notes = request.data.get('notes', '')
                inspection.recommended_actions = request.data.get('recommendations', [])
                inspection.save()
                
                message = 'Inspection updated successfully'
            else:
                # Create new inspection
                from listings.models import Vehicle
                from accounts.models import Customer, Dealership
                
                # Get related objects
                vehicle = get_object_or_404(Vehicle, id=vehicle_id)
                
                # Determine dealer (optional)
                dealer = None
                if dealer_id:
                    dealer = get_object_or_404(Dealership, id=dealer_id)
                
                # Determine inspector based on user type
                inspector = request.user if getattr(request.user, 'user_type', None) == 'mechanic' else None
                
                # Determine customer
                if hasattr(request.user, 'customer_profile'):
                    customer = request.user.customer_profile
                elif customer_id:
                    customer = get_object_or_404(Customer, id=customer_id)
                else:
                    return Response({
                        'error': 'Customer identification required'
                    }, status=status.HTTP_400_BAD_REQUEST)

                inspection = VehicleInspection.objects.create(
                    vehicle=vehicle,
                    inspector=inspector,
                    customer=customer,
                    dealer=dealer,
                    inspection_type=inspection_type,
                    overall_rating=overall_rating,
                    inspector_notes=request.data.get('notes', ''),
                    recommended_actions=request.data.get('recommendations', []),
                    scheduled_date=request.data.get('scheduled_date'),
                    **inspection_data
                )
                
                message = 'Inspection created successfully'
            
            # Serialize response
            serializer = VehicleInspectionDetailSerializer(inspection)
            
            return Response({
                'success': True,
                'message': message,
                'data': serializer.data
            }, status=status.HTTP_201_CREATED if not inspection_id else status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error collecting inspection data: {str(e)}")
            return Response({
                'error': 'Failed to save inspection data',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _has_permission(self, user, inspection):
        """Check if user has permission to update inspection"""
        return user == inspection.inspector


class DocumentPreviewGenerationView(APIView):
    """
    Generate document preview for frontend display
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, inspection_id):
        """
        Generate document preview
        """
        try:
            inspection = get_object_or_404(VehicleInspection, id=inspection_id)
            
            # Check permissions
            if not self._has_permission(request.user, inspection):
                return Response({
                    'error': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get preview settings
            template_type = request.data.get('template_type', 'standard')
            include_photos = request.data.get('include_photos', True)
            include_recommendations = request.data.get('include_recommendations', True)
            
            # Check if document already exists
            existing_document = inspection.documents.filter(
                template_type=template_type,
                status__in=['ready', 'generating']
            ).first()
            
            if existing_document:
                # Return existing document
                serializer = InspectionDocumentSerializer(existing_document)
                return Response({
                    'success': True,
                    'message': 'Document already exists',
                    'data': serializer.data
                })
            
            # Generate new document
            doc_service = DocumentManagementService()
            document = doc_service.create_inspection_document(
                inspection=inspection,
                template_type=template_type,
                include_photos=include_photos,
                include_recommendations=include_recommendations
            )
            
            # Serialize response
            serializer = InspectionDocumentSerializer(document)
            
            return Response({
                'success': True,
                'message': 'Document preview generated successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error generating document preview for inspection {inspection_id}: {str(e)}")
            return Response({
                'error': 'Failed to generate document preview',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _has_permission(self, user, inspection):
        """Check if user has permission to generate document"""
        return (
            user == inspection.inspector or
            (hasattr(user, 'dealership_profile') and user.dealership_profile == inspection.dealer) or
            (hasattr(user, 'customer_profile') and user.customer_profile == inspection.customer)
        )


class SignatureSubmissionView(APIView):
    """
    Simplified signature submission endpoint for frontend
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, document_id):
        """
        Submit signature from frontend
        """
        try:
            document = get_object_or_404(InspectionDocument, id=document_id)
            
            # Get signature data
            signature_image = request.data.get('signature_image')
            signature_method = request.data.get('signature_method', 'drawn')
            coordinates = request.data.get('coordinates', {})
            
            # Validate signature data
            if not signature_image:
                return Response({
                    'error': 'Signature image is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Prepare signature data
            signature_data = {
                'signature_image': signature_image,
                'signature_method': signature_method,
                'coordinates': coordinates
            }
            
            # Get client info
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Submit signature
            doc_service = DocumentManagementService()
            signature = doc_service.submit_signature(
                document=document,
                signer_id=request.user.id,
                signature_data=signature_data,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Check if document is fully signed
            all_signatures = document.signatures.all()
            signed_count = all_signatures.filter(status='signed').count()
            total_count = all_signatures.count()
            is_fully_signed = signed_count == total_count
            
            return Response({
                'success': True,
                'message': 'Signature submitted successfully',
                'data': {
                    'signature_id': signature.id,
                    'status': signature.get_status_display(),
                    'signed_at': signature.signed_at,
                    'document_status': document.get_status_display(),
                    'is_fully_signed': is_fully_signed,
                    'signature_progress': {
                        'signed': signed_count,
                        'total': total_count,
                        'percentage': round((signed_count / total_count * 100) if total_count > 0 else 0, 2)
                    }
                }
            })
            
        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error submitting signature for document {document_id}: {str(e)}")
            return Response({
                'error': 'Failed to submit signature',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DocumentRetrievalView(APIView):
    """
    Retrieve document with all related information for frontend display
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, document_id):
        """
        Get document details with signatures and status
        """
        try:
            document = get_object_or_404(InspectionDocument, id=document_id)
            
            # Check permissions
            if not self._has_permission(request.user, document.inspection):
                return Response({
                    'error': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get document status
            doc_service = DocumentManagementService()
            document_status = doc_service.get_document_status(document)
            
            # Serialize document
            serializer = InspectionDocumentSerializer(document)
            
            # Prepare response
            response_data = {
                'document': serializer.data,
                'status_info': document_status,
                'download_url': request.build_absolute_uri(
                    f'/api/v1/inspections/documents/{document.id}/download/'
                ) if document.document_file else None,
                'can_sign': self._can_user_sign(request.user, document),
                'user_signature_status': self._get_user_signature_status(request.user, document)
            }
            
            return Response({
                'success': True,
                'data': response_data
            })
            
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {str(e)}")
            return Response({
                'error': 'Failed to retrieve document',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _has_permission(self, user, inspection):
        """Check if user has permission to view document"""
        return (
            user == inspection.inspector or
            (hasattr(user, 'customer') and user.customer == inspection.customer) or
            (hasattr(user, 'dealership') and user.dealership == inspection.dealer)
        )
    
    def _can_user_sign(self, user, document):
        """Check if user can sign the document"""
        try:
            signature = document.signatures.get(signer=user, status='pending')
            return document.status == 'ready' and not document.is_expired
        except DigitalSignature.DoesNotExist:
            return False
    
    def _get_user_signature_status(self, user, document):
        """Get user's signature status for this document"""
        try:
            signature = document.signatures.get(signer=user)
            return {
                'has_signature': True,
                'status': signature.get_status_display(),
                'signed_at': signature.signed_at,
                'role': signature.get_role_display()
            }
        except DigitalSignature.DoesNotExist:
            return {
                'has_signature': False,
                'status': None,
                'signed_at': None,
                'role': None
            }


class InspectionStatusUpdateView(APIView):
    """
    Real-time inspection status updates for frontend
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, inspection_id):
        """
        Get current status of inspection with all related information
        """
        try:
            inspection = get_object_or_404(VehicleInspection, id=inspection_id)
            
            # Check permissions
            if not self._has_permission(request.user, inspection):
                return Response({
                    'error': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get documents
            documents = inspection.documents.all()
            
            # Calculate overall progress
            total_documents = documents.count()
            signed_documents = documents.filter(status='signed').count()
            
            # Get signature progress for each document
            document_progress = []
            for doc in documents:
                signatures = doc.signatures.all()
                signed_count = signatures.filter(status='signed').count()
                total_count = signatures.count()
                
                document_progress.append({
                    'document_id': doc.id,
                    'template_type': doc.get_template_type_display(),
                    'status': doc.get_status_display(),
                    'signature_progress': {
                        'signed': signed_count,
                        'total': total_count,
                        'percentage': round((signed_count / total_count * 100) if total_count > 0 else 0, 2)
                    }
                })
            
            # Prepare response
            response_data = {
                'inspection_id': inspection.id,
                'status': inspection.get_status_display(),
                'overall_rating': inspection.get_overall_rating_display() if inspection.overall_rating else None,
                'inspection_date': inspection.inspection_date,
                'completed_at': inspection.completed_at,
                'is_completed': inspection.is_completed,
                'requires_signature': inspection.requires_signature,
                'document_count': total_documents,
                'signed_document_count': signed_documents,
                'document_progress': document_progress,
                'overall_completion': round((signed_documents / total_documents * 100) if total_documents > 0 else 0, 2),
                'last_updated': inspection.last_updated
            }
            
            return Response({
                'success': True,
                'data': response_data
            })
            
        except Exception as e:
            logger.error(f"Error getting inspection status for {inspection_id}: {str(e)}")
            return Response({
                'error': 'Failed to get inspection status',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _has_permission(self, user, inspection):
        """Check if user has permission to view inspection status"""
        return (
            user == inspection.inspector or
            (hasattr(user, 'customer') and user.customer == inspection.customer) or
            (hasattr(user, 'dealership') and user.dealership == inspection.dealer)
        )


class InspectionPhotoUploadView(APIView):
    """
    Upload photos for inspection from frontend
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, inspection_id):
        """
        Upload inspection photo
        """
        try:
            inspection = get_object_or_404(VehicleInspection, id=inspection_id)
            
            # Check permissions
            if not self._has_permission(request.user, inspection):
                return Response({
                    'error': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Validate photo data
            category = request.data.get('category')
            image = request.data.get('image')
            description = request.data.get('description', '')
            
            if not category or not image:
                return Response({
                    'error': 'Category and image are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create photo
            photo = InspectionPhoto.objects.create(
                inspection=inspection,
                category=category,
                image=image,
                description=description
            )
            
            # Serialize response
            serializer = InspectionPhotoSerializer(photo)
            
            return Response({
                'success': True,
                'message': 'Photo uploaded successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error uploading photo for inspection {inspection_id}: {str(e)}")
            return Response({
                'error': 'Failed to upload photo',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _has_permission(self, user, inspection):
        """Check if user has permission to upload photos"""
        return (
            user == inspection.inspector or
            (hasattr(user, 'customer') and user.customer == inspection.customer) or
            (hasattr(user, 'dealership') and user.dealership == inspection.dealer)
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_inspection_form_schema(request):
    """
    Get inspection form schema for frontend form generation
    """
    try:
        schema = {
            'sections': [
                {
                    'name': 'exterior',
                    'label': 'Exterior Inspection',
                    'fields': [
                        {'name': 'body_condition', 'label': 'Body Condition', 'type': 'select', 'options': ['excellent', 'good', 'fair', 'poor'], 'required': True},
                        {'name': 'paint_condition', 'label': 'Paint Condition', 'type': 'select', 'options': ['excellent', 'good', 'fair', 'poor'], 'required': True},
                        {'name': 'windshield_condition', 'label': 'Windshield Condition', 'type': 'select', 'options': ['excellent', 'good', 'fair', 'poor'], 'required': True},
                        {'name': 'lights_condition', 'label': 'Lights Condition', 'type': 'select', 'options': ['excellent', 'good', 'fair', 'poor'], 'required': True},
                        {'name': 'tires_condition', 'label': 'Tires Condition', 'type': 'select', 'options': ['excellent', 'good', 'fair', 'poor'], 'required': True},
                        {'name': 'notes', 'label': 'Additional Notes', 'type': 'textarea', 'required': False}
                    ]
                },
                {
                    'name': 'interior',
                    'label': 'Interior Inspection',
                    'fields': [
                        {'name': 'seats_condition', 'label': 'Seats Condition', 'type': 'select', 'options': ['excellent', 'good', 'fair', 'poor'], 'required': True},
                        {'name': 'dashboard_condition', 'label': 'Dashboard Condition', 'type': 'select', 'options': ['excellent', 'good', 'fair', 'poor'], 'required': True},
                        {'name': 'ac_condition', 'label': 'AC Condition', 'type': 'select', 'options': ['excellent', 'good', 'fair', 'poor'], 'required': True},
                        {'name': 'audio_system_condition', 'label': 'Audio System', 'type': 'select', 'options': ['excellent', 'good', 'fair', 'poor'], 'required': True},
                        {'name': 'notes', 'label': 'Additional Notes', 'type': 'textarea', 'required': False}
                    ]
                },
                {
                    'name': 'engine',
                    'label': 'Engine Inspection',
                    'fields': [
                        {'name': 'engine_condition', 'label': 'Engine Condition', 'type': 'select', 'options': ['excellent', 'good', 'fair', 'poor'], 'required': True},
                        {'name': 'oil_level', 'label': 'Oil Level', 'type': 'select', 'options': ['excellent', 'good', 'fair', 'poor'], 'required': True},
                        {'name': 'coolant_level', 'label': 'Coolant Level', 'type': 'select', 'options': ['excellent', 'good', 'fair', 'poor'], 'required': True},
                        {'name': 'battery_condition', 'label': 'Battery Condition', 'type': 'select', 'options': ['excellent', 'good', 'fair', 'poor'], 'required': True},
                        {'name': 'notes', 'label': 'Additional Notes', 'type': 'textarea', 'required': False}
                    ]
                },
                {
                    'name': 'mechanical',
                    'label': 'Mechanical Inspection',
                    'fields': [
                        {'name': 'transmission_condition', 'label': 'Transmission', 'type': 'select', 'options': ['excellent', 'good', 'fair', 'poor'], 'required': True},
                        {'name': 'brakes_condition', 'label': 'Brakes', 'type': 'select', 'options': ['excellent', 'good', 'fair', 'poor'], 'required': True},
                        {'name': 'suspension_condition', 'label': 'Suspension', 'type': 'select', 'options': ['excellent', 'good', 'fair', 'poor'], 'required': True},
                        {'name': 'steering_condition', 'label': 'Steering', 'type': 'select', 'options': ['excellent', 'good', 'fair', 'poor'], 'required': True},
                        {'name': 'notes', 'label': 'Additional Notes', 'type': 'textarea', 'required': False}
                    ]
                },
                {
                    'name': 'safety',
                    'label': 'Safety Inspection',
                    'fields': [
                        {'name': 'airbags_condition', 'label': 'Airbags', 'type': 'select', 'options': ['excellent', 'good', 'fair', 'poor'], 'required': True},
                        {'name': 'seatbelts_condition', 'label': 'Seatbelts', 'type': 'select', 'options': ['excellent', 'good', 'fair', 'poor'], 'required': True},
                        {'name': 'warning_lights', 'label': 'Warning Lights', 'type': 'select', 'options': ['excellent', 'good', 'fair', 'poor'], 'required': True},
                        {'name': 'notes', 'label': 'Additional Notes', 'type': 'textarea', 'required': False}
                    ]
                }
            ],
            'photo_categories': [
                {'value': 'exterior_front', 'label': 'Exterior - Front View'},
                {'value': 'exterior_rear', 'label': 'Exterior - Rear View'},
                {'value': 'exterior_left', 'label': 'Exterior - Left Side'},
                {'value': 'exterior_right', 'label': 'Exterior - Right Side'},
                {'value': 'interior_dashboard', 'label': 'Interior - Dashboard'},
                {'value': 'interior_seats', 'label': 'Interior - Seats'},
                {'value': 'engine_bay', 'label': 'Engine Bay'},
                {'value': 'tires_wheels', 'label': 'Tires and Wheels'},
                {'value': 'damage_detail', 'label': 'Damage Detail'},
                {'value': 'documents', 'label': 'Vehicle Documents'},
                {'value': 'other', 'label': 'Other'}
            ]
        }
        
        return Response({
            'success': True,
            'data': schema
        })
        
    except Exception as e:
        logger.error(f"Error getting inspection form schema: {str(e)}")
        return Response({
            'error': 'Failed to get form schema'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
