"""
Serializers for the vehicle inspection system API
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from accounts.models import Customer, Dealership
from listings.models import Vehicle
from .models import (
    VehicleInspection,
    InspectionPhoto,
    InspectionDocument,
    DigitalSignature,
    InspectionTemplate
)
from .services import InspectionValidationService

User = get_user_model()


class InspectionPhotoSerializer(serializers.ModelSerializer):
    """Serializer for inspection photos"""
    
    class Meta:
        model = InspectionPhoto
        fields = [
            'id', 'category', 'image', 'description', 'date_created'
        ]
        read_only_fields = ['id', 'date_created']


class DigitalSignatureSerializer(serializers.ModelSerializer):
    """Serializer for digital signatures"""
    signer_name = serializers.CharField(source='signer.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DigitalSignature
        fields = [
            'id', 'role', 'role_display', 'status', 'status_display',
            'signer_name', 'signature_method', 'signed_at', 'is_verified'
        ]
        read_only_fields = [
            'id', 'role_display', 'status_display', 'signer_name',
            'signed_at', 'is_verified'
        ]


class InspectionDocumentSerializer(serializers.ModelSerializer):
    """Serializer for inspection documents"""
    signatures = DigitalSignatureSerializer(many=True, read_only=True)
    template_type_display = serializers.CharField(source='get_template_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    formatted_file_size = serializers.CharField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = InspectionDocument
        fields = [
            'id', 'template_type', 'template_type_display', 'status', 'status_display',
            'document_file', 'document_hash', 'file_size', 'formatted_file_size',
            'page_count', 'include_photos', 'include_recommendations', 'language',
            'compliance_standards', 'generated_at', 'expires_at', 'is_expired',
            'signatures'
        ]
        read_only_fields = [
            'id', 'template_type_display', 'status_display', 'document_file',
            'document_hash', 'file_size', 'formatted_file_size', 'page_count',
            'generated_at', 'expires_at', 'is_expired', 'signatures'
        ]


class VehicleInspectionListSerializer(serializers.ModelSerializer):
    """Serializer for listing vehicle inspections"""
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    inspector_name = serializers.CharField(source='inspector.name', read_only=True)
    customer_name = serializers.CharField(source='customer.user.name', read_only=True)
    dealer_name = serializers.CharField(source='dealer.business_name', read_only=True)
    inspection_type_display = serializers.CharField(source='get_inspection_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    overall_rating_display = serializers.CharField(source='get_overall_rating_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    
    class Meta:
        model = VehicleInspection
        fields = [
            'id', 'inspection_number', 'vehicle_name', 'inspector_name', 'customer_name', 'dealer_name',
            'inspection_type', 'inspection_type_display', 'status', 'status_display',
            'overall_rating', 'overall_rating_display', 'inspection_date', 'completed_at',
            'inspection_fee', 'payment_status', 'payment_status_display', 'paid_at', 'inspection_slip'
        ]


class VehicleInspectionDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed vehicle inspection view"""
    vehicle = serializers.SerializerMethodField()
    inspector = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()
    dealer = serializers.SerializerMethodField()
    photos = InspectionPhotoSerializer(many=True, read_only=True)
    documents = InspectionDocumentSerializer(many=True, read_only=True)
    inspection_type_display = serializers.CharField(source='get_inspection_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    overall_rating_display = serializers.CharField(source='get_overall_rating_display', read_only=True)
    inspection_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = VehicleInspection
        fields = [
            'id', 'inspection_number', 'vehicle', 'inspector', 'customer', 'dealer',
            'inspection_type', 'inspection_type_display', 'status', 'status_display',
            'overall_rating', 'overall_rating_display', 'exterior_data', 'interior_data',
            'engine_data', 'mechanical_data', 'safety_data', 'documentation_data',
            'inspector_notes', 'recommended_actions', 'inspection_date', 'completed_at',
            'inspection_fee', 'payment_status', 'payment_method', 'paid_at',
            'inspection_slip', 'photos', 'documents', 'inspection_summary'
        ]
        read_only_fields = [
            'id', 'inspection_number', 'inspection_type_display', 'status_display', 'overall_rating_display',
            'inspection_fee', 'payment_status', 'payment_method', 'paid_at',
            'inspection_slip', 'photos', 'documents', 'inspection_summary'
        ]
    
    def get_vehicle(self, obj):
        """Get vehicle information"""
        return {
            'id': obj.vehicle.id,
            'name': obj.vehicle.name,
            'brand': obj.vehicle.brand,
            'model': obj.vehicle.model,
            'color': obj.vehicle.color,
            'condition': obj.vehicle.get_condition_display(),
            'mileage': obj.vehicle.mileage,
        }
    
    def get_inspector(self, obj):
        """Get inspector information"""
        return {
            'id': obj.inspector.id,
            'name': obj.inspector.name,
            'email': obj.inspector.email,
        }
    
    def get_customer(self, obj):
        """Get customer information"""
        return {
            'id': obj.customer.id,
            'name': obj.customer.user.name,
            'email': obj.customer.user.email,
        }
    
    def get_dealer(self, obj):
        """Get dealer information"""
        return {
            'id': obj.dealer.id,
            'name': obj.dealer.business_name or obj.dealer.user.name,
            'email': obj.dealer.user.email,
        }
    
    def get_inspection_summary(self, obj):
        """Get inspection summary"""
        return obj.get_inspection_summary()


class VehicleInspectionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating vehicle inspections"""
    photos = InspectionPhotoSerializer(many=True, required=False)
    
    class Meta:
        model = VehicleInspection
        fields = [
            'vehicle', 'inspector', 'customer', 'dealer', 'inspection_type',
            'exterior_data', 'interior_data', 'engine_data', 'mechanical_data',
            'safety_data', 'documentation_data', 'inspector_notes',
            'recommended_actions', 'overall_rating', 'photos'
        ]
    
    def validate(self, data):
        """Validate inspection data"""
        # Combine all inspection data for validation
        inspection_data = {}
        for field in ['exterior_data', 'interior_data', 'engine_data', 'mechanical_data', 'safety_data']:
            if field in data:
                section_name = field.replace('_data', '')
                inspection_data[section_name] = data[field]
        
        # Validate inspection data structure
        is_valid, errors = InspectionValidationService.validate_inspection_data(inspection_data)
        if not is_valid:
            raise serializers.ValidationError({'inspection_data': errors})
        
        # Auto-calculate overall rating if not provided
        if not data.get('overall_rating'):
            data['overall_rating'] = InspectionValidationService.calculate_overall_rating(inspection_data)
        
        return data
    
    def create(self, validated_data):
        """Create inspection with photos"""
        photos_data = validated_data.pop('photos', [])
        
        # Create inspection
        inspection = VehicleInspection.objects.create(**validated_data)
        
        # Create photos
        for photo_data in photos_data:
            InspectionPhoto.objects.create(inspection=inspection, **photo_data)
        
        return inspection


class DocumentGenerationSerializer(serializers.Serializer):
    """Serializer for document generation requests"""
    template_type = serializers.ChoiceField(
        choices=['standard', 'detailed', 'legal'],
        default='standard'
    )
    include_photos = serializers.BooleanField(default=True)
    include_recommendations = serializers.BooleanField(default=True)
    language = serializers.CharField(max_length=5, default='en')
    compliance_standards = serializers.ListField(
        child=serializers.CharField(max_length=20),
        required=False,
        default=list
    )


class SignatureSubmissionSerializer(serializers.Serializer):
    """Serializer for signature submission"""
    signature_data = serializers.JSONField()
    signature_field_id = serializers.CharField(max_length=50)
    signature_method = serializers.ChoiceField(
        choices=['drawn', 'typed', 'uploaded'],
        default='drawn'
    )
    
    def validate_signature_data(self, value):
        """Validate signature data structure"""
        required_fields = ['signature_image']
        
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Missing required field: {field}")
        
        # Validate signature image format (basic validation)
        signature_image = value.get('signature_image', '')
        if not signature_image.startswith('data:image/'):
            raise serializers.ValidationError("Invalid signature image format")
        
        return value


class InspectionTemplateSerializer(serializers.ModelSerializer):
    """Serializer for inspection templates"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    
    class Meta:
        model = InspectionTemplate
        fields = [
            'id', 'name', 'category', 'category_display', 'description',
            'template_file', 'is_active', 'supports_photos', 'supports_recommendations',
            'compliance_standards', 'created_by_name', 'version', 'date_created'
        ]
        read_only_fields = ['id', 'category_display', 'created_by_name', 'date_created']


class InspectionStatsSerializer(serializers.Serializer):
    """Serializer for inspection statistics"""
    total_inspections = serializers.IntegerField()
    completed_inspections = serializers.IntegerField()
    pending_inspections = serializers.IntegerField()
    signed_documents = serializers.IntegerField()
    average_rating = serializers.FloatField()
    inspections_by_type = serializers.DictField()
    inspections_by_status = serializers.DictField()
    recent_inspections = VehicleInspectionListSerializer(many=True)


class InspectionPaymentSerializer(serializers.Serializer):
    """Serializer for inspection payment requests"""
    payment_method = serializers.ChoiceField(
        choices=['wallet', 'bank'],
        default='wallet',
        help_text="Payment method: wallet or bank"
    )
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Payment amount"
    )
    
    def validate_amount(self, value):
        """Validate payment amount matches inspection fee"""
        inspection = self.context.get('inspection')
        if inspection and value != inspection.inspection_fee:
            raise serializers.ValidationError(
                f"Payment amount must match inspection fee of ₦{inspection.inspection_fee:,.2f}"
            )
        return value


class InspectionQuoteSerializer(serializers.Serializer):
    """Serializer for inspection fee quote"""
    inspection_type = serializers.ChoiceField(
        choices=['pre_purchase', 'pre_rental', 'maintenance', 'insurance']
    )
    vehicle_id = serializers.IntegerField(required=False, allow_null=True)
    
    
class InspectionQuoteResponseSerializer(serializers.Serializer):
    """Serializer for inspection fee quote response"""
    inspection_type = serializers.CharField()
    base_fee = serializers.DecimalField(max_digits=10, decimal_places=2)
    vehicle_info = serializers.DictField(required=False)
    total_fee = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(default='NGN')