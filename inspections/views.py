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
            
        if hasattr(user, 'customer_profile'):
            queryset = queryset.filter(customer=user.customer_profile)
        elif hasattr(user, 'dealership_profile'):
            queryset = queryset.filter(dealer=user.dealership_profile)
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
        from .services import InspectionFeeService
        
        # Calculate inspection fee
        inspection_type = serializer.validated_data.get('inspection_type')
        vehicle = serializer.validated_data.get('vehicle')
        inspection_fee = InspectionFeeService.calculate_inspection_fee(inspection_type, vehicle)
        
        # Auto-assign inspector if user is a mechanic
        if getattr(self.request.user, 'user_type', None) == 'mechanic':
            serializer.save(
                inspector=self.request.user,
                inspection_fee=inspection_fee,
                status='pending_payment'
            )
        else:
            serializer.save(
                inspection_fee=inspection_fee,
                status='pending_payment'
            )


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
            
        if hasattr(user, 'customer_profile'):
            queryset = queryset.filter(customer=user.customer_profile)
        elif hasattr(user, 'dealership_profile'):
            queryset = queryset.filter(dealer=user.dealership_profile)
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
            (hasattr(user, 'customer_profile') and user.customer_profile == inspection.customer) or
            (hasattr(user, 'dealership_profile') and user.dealership_profile == inspection.dealer)
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
            (hasattr(user, 'dealership_profile') and user.dealership_profile == inspection.dealer)
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
            (hasattr(user, 'customer_profile') and user.customer_profile == inspection.customer) or
            (hasattr(user, 'dealership_profile') and user.dealership_profile == inspection.dealer)
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
            (hasattr(user, 'customer_profile') and user.customer_profile == inspection.customer) or
            (hasattr(user, 'dealership_profile') and user.dealership_profile == inspection.dealer)
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
            if hasattr(user, 'customer_profile'):
                queryset = VehicleInspection.objects.filter(customer=user.customer_profile)
            elif hasattr(user, 'dealership_profile'):
                queryset = VehicleInspection.objects.filter(dealer=user.dealership_profile)
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


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def get_inspection_quote(request):
    """
    Get fee quote for an inspection
    """
    from .serializers import InspectionQuoteSerializer, InspectionQuoteResponseSerializer
    from .services import InspectionFeeService
    
    try:
        serializer = InspectionQuoteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        inspection_type = serializer.validated_data['inspection_type']
        vehicle_id = serializer.validated_data.get('vehicle_id')
        
        # Get fee quote
        quote = InspectionFeeService.get_fee_quote(inspection_type, vehicle_id)
        
        response_serializer = InspectionQuoteResponseSerializer(quote)
        
        return Response({
            'success': True,
            'data': response_serializer.data,
            'message': 'Fee quote generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting inspection quote: {str(e)}")
        return Response(
            {'error': 'Failed to get inspection quote'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def pay_for_inspection(request, inspection_id):
    """
    Process payment for an inspection using ONLY Paystack
    Payment triggers revenue split: dealer gets 60%, platform gets 40%
    """
    from .serializers import InspectionPaymentSerializer
    from wallet.models import Wallet, Transaction
    from wallet.gateway.payment_adapter import PaystackAdapter
    from django.db import transaction as db_transaction
    import uuid
    
    try:
        inspection = get_object_or_404(VehicleInspection, id=inspection_id)
        
        # Check if user is the customer
        if not hasattr(request.user, 'customer_profile') or request.user.customer_profile != inspection.customer:
            return Response(
                {'error': 'Only the customer can pay for this inspection'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already paid
        if inspection.is_paid:
            return Response(
                {'error': 'Inspection has already been paid for'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate payment data
        serializer = InspectionPaymentSerializer(
            data=request.data,
            context={'inspection': inspection}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        amount = inspection.inspection_fee
        
        # ONLY Paystack payment is allowed for inspections
        # Generate unique reference
        uid = str(uuid.uuid4())
        parts = uid.split('-')
        reference = f'veyu-inspection-{inspection.id}-' + ''.join(parts[1:3])
        
        # Store pending transaction
        payment_transaction = Transaction.objects.create(
            sender=request.user.name,
            recipient='Veyu Inspection Service',
            type='payment',
            amount=amount,
            status='pending',
            source='bank',
            tx_ref=reference,
            narration=f'Payment for {inspection.get_inspection_type_display()} - Inspection #{inspection.id}',
            related_inspection=inspection
        )
        
        # Return payment initialization data for frontend to use with Paystack
        return Response({
            'success': True,
            'data': {
                'payment_method': 'paystack',
                'amount': float(amount),
                'inspection_id': inspection.id,
                'transaction_id': payment_transaction.id,
                'reference': reference,
                'email': request.user.email,
                'currency': 'NGN',
                'callback_url': f'{request.build_absolute_uri("/api/v1/inspections/")}{inspection.id}/verify-payment/',
                'paystack_public_key': 'pk_test_xxxx',  # Frontend should use their own key
            },
            'message': 'Initialize Paystack payment on frontend with the provided reference'
        })
        
    except Exception as e:
        logger.error(f"Error processing payment for inspection {inspection_id}: {str(e)}")
        return Response(
            {'error': 'Failed to process payment'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_inspection_payment(request, inspection_id):
    """
    Verify Paystack payment for inspection and trigger revenue split
    Dealer gets 60%, platform gets 40% (configurable in admin)
    """
    from wallet.models import Wallet, Transaction
    from wallet.gateway.payment_adapter import PaystackAdapter
    from django.db import transaction as db_transaction
    from .models_revenue import InspectionRevenueSplit
    
    try:
        inspection = get_object_or_404(VehicleInspection, id=inspection_id)
        
        # Check if user is the customer
        if not hasattr(request.user, 'customer_profile') or request.user.customer_profile != inspection.customer:
            return Response(
                {'error': 'Only the customer can verify payment for this inspection'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get reference from request
        reference = request.data.get('reference')
        if not reference:
            return Response(
                {'error': 'Payment reference is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify with Paystack
        gateway = PaystackAdapter()
        verification_response = gateway.verify_transaction(reference)
        
        if verification_response.get('status') == 'success':
            # Payment successful
            with db_transaction.atomic():
                # Get the pending transaction
                payment_transaction = Transaction.objects.filter(
                    tx_ref=reference,
                    related_inspection=inspection,
                    status='pending'
                ).first()
                
                if not payment_transaction:
                    return Response(
                        {'error': 'Transaction not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                # Update transaction status
                payment_transaction.status = 'completed'
                payment_transaction.save()
                
                # Mark inspection as paid
                inspection.mark_paid(payment_transaction, payment_method='paystack')
                
                # Create revenue split and credit dealer wallet
                revenue_split = InspectionRevenueSplit.create_split(
                    inspection=inspection,
                    payment_transaction=payment_transaction
                )
                
                # Generate inspection slip
                from .slip_service import InspectionSlipService
                slip_service = InspectionSlipService()
                try:
                    slip_file, slip_filename = slip_service.generate_inspection_slip(inspection)
                    inspection.inspection_slip = slip_file
                    inspection.save()
                    slip_url = inspection.inspection_slip.url if inspection.inspection_slip else None
                except Exception as e:
                    logger.error(f"Error generating inspection slip: {str(e)}")
                    slip_url = None
                
                return Response({
                    'success': True,
                    'data': {
                        'inspection_id': inspection.id,
                        'inspection_number': inspection.inspection_number,
                        'transaction_id': payment_transaction.id,
                        'amount_paid': float(payment_transaction.amount),
                        'payment_method': 'paystack',
                        'payment_status': inspection.payment_status,
                        'inspection_status': inspection.get_status_display(),
                        'paid_at': inspection.paid_at,
                        'reference': reference,
                        'inspection_slip_url': slip_url,
                        'revenue_split': {
                            'dealer_amount': float(revenue_split.dealer_amount),
                            'dealer_percentage': float(revenue_split.dealer_percentage),
                            'platform_amount': float(revenue_split.platform_amount),
                            'platform_percentage': float(revenue_split.platform_percentage),
                            'dealer_credited': revenue_split.dealer_credited
                        }
                    },
                    'message': 'Payment verified successfully. Dealer wallet credited. Inspection slip generated. Inspection can now begin.'
                })
        else:
            # Payment failed
            return Response({
                'success': False,
                'error': 'Payment verification failed',
                'message': verification_response.get('message', 'Unable to verify payment')
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error verifying payment for inspection {inspection_id}: {str(e)}")
        return Response(
            {'error': 'Failed to verify payment'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



class InspectionSlipRetrievalView(APIView):
    """
    Retrieve inspection slip by slip number or inspection ID
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, slip_number):
        """
        Get inspection slip details
        """
        try:
            # Try to find by slip number
            try:
                inspection = VehicleInspection.objects.get(inspection_number=slip_number)
            except VehicleInspection.DoesNotExist:
                logger.error(f"Error retrieving inspection slip {slip_number}: No VehicleInspection matches the given query.")
                return Response({
                    'success': False,
                    'error': 'Inspection slip not found',
                    'message': f'No inspection found with slip number "{slip_number}". Please verify the slip number and try again.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check permissions
            user = request.user
            has_permission = (
                (hasattr(user, 'customer_profile') and user.customer_profile == inspection.customer) or
                (hasattr(user, 'dealership_profile') and user.dealership_profile == inspection.dealer) or
                user == inspection.inspector or
                user.is_staff
            )
            
            if not has_permission:
                return Response({
                    'success': False,
                    'error': 'Permission denied',
                    'message': 'You do not have permission to view this inspection slip.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Return slip details
            return Response({
                'success': True,
                'data': {
                    'inspection_id': inspection.id,
                    'inspection_number': inspection.inspection_number,
                    'inspection_type': inspection.get_inspection_type_display(),
                    'payment_status': inspection.payment_status,
                    'inspection_status': inspection.get_status_display(),
                    'paid_at': inspection.paid_at,
                    'inspection_fee': float(inspection.inspection_fee),
                    'slip_url': inspection.inspection_slip.url if inspection.inspection_slip else None,
                    'vehicle': {
                        'id': inspection.vehicle.id,
                        'name': inspection.vehicle.name,
                        'brand': inspection.vehicle.brand,
                        'model': inspection.vehicle.model or 'N/A',
                        'condition': inspection.vehicle.get_condition_display(),
                        'color': inspection.vehicle.color,
                    },
                    'customer': {
                        'name': inspection.customer.user.name,
                        'phone': inspection.customer.phone_number or 'N/A',
                        'email': inspection.customer.user.email,
                    },
                    'dealer': {
                        'name': inspection.dealer.business_name,
                        'phone': inspection.dealer.phone_number or 'N/A',
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Error retrieving inspection slip {slip_number}: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to retrieve inspection slip',
                'message': 'An unexpected error occurred while retrieving the inspection slip.',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InspectionSlipVerificationView(APIView):
    """
    Verify inspection slip (for dealers to verify customer payment)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Verify inspection slip by slip number or QR code data
        """
        try:
            slip_number = request.data.get('slip_number')
            qr_data = request.data.get('qr_data')
            
            if not slip_number and not qr_data:
                return Response({
                    'error': 'Either slip_number or qr_data is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract slip number from QR data if provided
            if qr_data:
                # QR format: VEYU-INSPECTION:<slip_number>:<inspection_id>
                try:
                    parts = qr_data.split(':')
                    if len(parts) >= 2 and parts[0] == 'VEYU-INSPECTION':
                        slip_number = parts[1]
                except Exception:
                    return Response({
                        'error': 'Invalid QR code format'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Find inspection
            try:
                inspection = VehicleInspection.objects.get(inspection_number=slip_number)
            except VehicleInspection.DoesNotExist:
                return Response({
                    'success': False,
                    'valid': False,
                    'message': 'Invalid slip number'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if dealer is authorized
            user = request.user
            if hasattr(user, 'dealership_profile') and user.dealership_profile != inspection.dealer:
                return Response({
                    'error': 'This slip is not for your dealership'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Verify payment status
            is_valid = inspection.is_paid and inspection.status in ['draft', 'in_progress']
            
            return Response({
                'success': True,
                'valid': is_valid,
                'data': {
                    'inspection_id': inspection.id,
                    'inspection_number': inspection.inspection_number,
                    'inspection_type': inspection.get_inspection_type_display(),
                    'payment_status': inspection.payment_status,
                    'inspection_status': inspection.get_status_display(),
                    'paid_at': inspection.paid_at,
                    'amount_paid': float(inspection.inspection_fee),
                    'vehicle': {
                        'name': inspection.vehicle.name,
                        'brand': inspection.vehicle.brand,
                        'model': inspection.vehicle.model or 'N/A',
                        'condition': inspection.vehicle.get_condition_display(),
                    },
                    'customer': {
                        'name': inspection.customer.user.name,
                        'phone': inspection.customer.phone_number or 'N/A',
                    }
                },
                'message': 'Slip verified successfully. Customer has paid.' if is_valid else 'Slip is not valid for inspection.'
            })
            
        except Exception as e:
            logger.error(f"Error verifying inspection slip: {str(e)}")
            return Response({
                'error': 'Failed to verify inspection slip',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def regenerate_inspection_slip(request, inspection_id):
    """
    Regenerate inspection slip (in case of loss or damage)
    """
    try:
        inspection = get_object_or_404(VehicleInspection, id=inspection_id)
        
        # Check if user is the customer
        if not hasattr(request.user, 'customer_profile') or request.user.customer_profile != inspection.customer:
            return Response({
                'error': 'Only the customer can regenerate their inspection slip'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if inspection is paid
        if not inspection.is_paid:
            return Response({
                'error': 'Inspection must be paid before generating slip'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate slip
        from .slip_service import InspectionSlipService
        slip_service = InspectionSlipService()
        
        slip_file, slip_filename = slip_service.generate_inspection_slip(inspection)
        inspection.inspection_slip = slip_file
        inspection.save()
        
        return Response({
            'success': True,
            'data': {
                'inspection_id': inspection.id,
                'inspection_number': inspection.inspection_number,
                'slip_url': inspection.inspection_slip.url if inspection.inspection_slip else None
            },
            'message': 'Inspection slip regenerated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error regenerating inspection slip for {inspection_id}: {str(e)}")
        return Response({
            'error': 'Failed to regenerate inspection slip',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
