from django.db import models
from django.core.validators import RegexValidator, MinLengthValidator, MaxLengthValidator
from django.core.exceptions import ValidationError
from utils.models import DbModel
from django.utils import timezone
from cloudinary.models import CloudinaryField
import json
import hashlib
import uuid


class VehicleInspection(DbModel):
    """
    Main model for vehicle inspection records with comprehensive inspection data
    """
    INSPECTION_TYPES = [
        ('pre_purchase', 'Pre-Purchase Inspection'),
        ('pre_rental', 'Pre-Rental Inspection'),
        ('maintenance', 'Maintenance Inspection'),
        ('insurance', 'Insurance Inspection'),
    ]
    
    STATUS_CHOICES = [
        ('pending_payment', 'Pending Payment'),
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('signed', 'Signed'),
        ('archived', 'Archived'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
    ]
    
    CONDITION_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]
    
    # Core relationships
    vehicle = models.ForeignKey('listings.Vehicle', on_delete=models.CASCADE, related_name='inspections')
    inspector = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='conducted_inspections')
    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE, related_name='vehicle_inspections')
    dealer = models.ForeignKey('accounts.Dealership', on_delete=models.CASCADE, related_name='dealer_inspections')
    
    # Inspection metadata
    inspection_number = models.CharField(max_length=20, unique=True, blank=True, null=True, help_text="Unique inspection slip number (e.g., INSP-7)")
    inspection_type = models.CharField(max_length=20, choices=INSPECTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    overall_rating = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True, null=True)
    
    # Inspection slip
    inspection_slip = CloudinaryField('inspection_slip', folder='inspections/slips/', blank=True, null=True, help_text="PDF slip for customer to show dealer")
    
    # Payment fields
    inspection_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Inspection fee amount")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    payment_method = models.CharField(max_length=20, blank=True, null=True, help_text="Payment method used (wallet, bank)")
    payment_transaction = models.ForeignKey('wallet.Transaction', null=True, blank=True, on_delete=models.SET_NULL, related_name='inspection_payments')
    paid_at = models.DateTimeField(blank=True, null=True, help_text="Timestamp when payment was completed")
    
    # Inspection data (stored as JSON for flexibility)
    exterior_data = models.JSONField(default=dict, blank=True)
    interior_data = models.JSONField(default=dict, blank=True)
    engine_data = models.JSONField(default=dict, blank=True)
    mechanical_data = models.JSONField(default=dict, blank=True)
    safety_data = models.JSONField(default=dict, blank=True)
    documentation_data = models.JSONField(default=dict, blank=True)
    
    # Inspector notes and recommendations
    inspector_notes = models.TextField(blank=True, null=True)
    recommended_actions = models.JSONField(default=list, blank=True)
    
    # Timestamps
    inspection_date = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"Inspection #{self.id} - {self.vehicle.name} ({self.get_status_display()})"
    
    def __repr__(self):
        return f"<VehicleInspection: {self.vehicle.name} - {self.get_inspection_type_display()}>"
    
    @property
    def is_completed(self):
        """Check if inspection is completed"""
        return self.status in ['completed', 'signed', 'archived']
    
    @property
    def requires_signature(self):
        """Check if inspection requires signatures"""
        return self.status == 'completed'
    
    @property
    def is_paid(self):
        """Check if inspection fee is paid"""
        return self.payment_status == 'paid'
    
    @property
    def can_start_inspection(self):
        """Check if inspection can be started (payment completed)"""
        return self.is_paid and self.status in ['pending_payment', 'draft']
    
    def mark_completed(self):
        """Mark inspection as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_paid(self, transaction, payment_method='wallet'):
        """Mark inspection as paid"""
        self.payment_status = 'paid'
        self.payment_transaction = transaction
        self.payment_method = payment_method
        self.paid_at = timezone.now()
        self.status = 'draft'  # Move to draft after payment
        
        # Generate inspection number if not exists
        if not self.inspection_number:
            self.inspection_number = self._generate_inspection_number()
        
        self.save()
    
    def _generate_inspection_number(self):
        """Generate unique inspection number"""
        prefix = 'INSP'
        # Get the last inspection number
        last_inspection = VehicleInspection.objects.filter(
            inspection_number__startswith=prefix
        ).order_by('-id').first()
        
        if last_inspection and last_inspection.inspection_number:
            try:
                last_number = int(last_inspection.inspection_number.split('-')[1])
                new_number = last_number + 1
            except (IndexError, ValueError):
                new_number = 1
        else:
            new_number = 1
        
        return f"{prefix}-{new_number}"
    
    def get_inspection_summary(self):
        """Get a summary of inspection results"""
        sections = ['exterior_data', 'interior_data', 'engine_data', 'mechanical_data', 'safety_data']
        total_issues = 0
        
        for section in sections:
            data = getattr(self, section, {})
            if isinstance(data, dict):
                for key, value in data.items():
                    if value in ['poor', 'fair']:
                        total_issues += 1
        
        return {
            'overall_rating': self.overall_rating,
            'total_issues': total_issues,
            'recommendations_count': len(self.recommended_actions) if self.recommended_actions else 0,
            'inspection_date': self.inspection_date,
            'status': self.get_status_display()
        }
    
    class Meta:
        indexes = [
            models.Index(fields=['vehicle']),
            models.Index(fields=['inspector']),
            models.Index(fields=['customer']),
            models.Index(fields=['dealer']),
            models.Index(fields=['inspection_type']),
            models.Index(fields=['status']),
            models.Index(fields=['inspection_date']),
        ]
        ordering = ['-inspection_date']
        verbose_name = 'Vehicle Inspection'
        verbose_name_plural = 'Vehicle Inspections'


class InspectionPhoto(DbModel):
    """
    Model for storing inspection photos with categories
    """
    PHOTO_CATEGORIES = [
        ('exterior_front', 'Exterior - Front View'),
        ('exterior_rear', 'Exterior - Rear View'),
        ('exterior_left', 'Exterior - Left Side'),
        ('exterior_right', 'Exterior - Right Side'),
        ('interior_dashboard', 'Interior - Dashboard'),
        ('interior_seats', 'Interior - Seats'),
        ('engine_bay', 'Engine Bay'),
        ('tires_wheels', 'Tires and Wheels'),
        ('damage_detail', 'Damage Detail'),
        ('documents', 'Vehicle Documents'),
        ('other', 'Other'),
    ]
    
    inspection = models.ForeignKey(VehicleInspection, on_delete=models.CASCADE, related_name='photos')
    category = models.CharField(max_length=20, choices=PHOTO_CATEGORIES)
    image = CloudinaryField('inspection_photo', folder='inspections/photos/')
    description = models.CharField(max_length=200, blank=True, null=True)
    
    def __str__(self):
        return f"Photo - {self.get_category_display()} for Inspection #{self.inspection.id}"
    
    def __repr__(self):
        return f"<InspectionPhoto: {self.category} - Inspection #{self.inspection.id}>"
    
    class Meta:
        indexes = [
            models.Index(fields=['inspection']),
            models.Index(fields=['category']),
        ]
        ordering = ['category', 'date_created']
        verbose_name = 'Inspection Photo'
        verbose_name_plural = 'Inspection Photos'


class InspectionDocument(DbModel):
    """
    Model for generated inspection documents (PDFs)
    """
    TEMPLATE_TYPES = [
        ('standard', 'Standard Report'),
        ('detailed', 'Detailed Report'),
        ('legal', 'Legal Compliance Report'),
    ]
    
    DOCUMENT_STATUS = [
        ('generating', 'Generating'),
        ('ready', 'Ready for Signature'),
        ('signed', 'Fully Signed'),
        ('archived', 'Archived'),
    ]
    
    inspection = models.ForeignKey(VehicleInspection, on_delete=models.CASCADE, related_name='documents')
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES, default='standard')
    status = models.CharField(max_length=20, choices=DOCUMENT_STATUS, default='generating')
    
    # Document file and metadata
    document_file = CloudinaryField('inspection_document', folder='inspections/documents/', blank=True, null=True)
    document_hash = models.CharField(max_length=64, blank=True, null=True)  # SHA-256 hash for integrity
    file_size = models.PositiveIntegerField(blank=True, null=True)  # Size in bytes
    page_count = models.PositiveIntegerField(default=1)
    
    # Generation settings
    include_photos = models.BooleanField(default=True)
    include_recommendations = models.BooleanField(default=True)
    language = models.CharField(max_length=5, default='en')
    compliance_standards = models.JSONField(default=list, blank=True)  # ['NURTW', 'FRSC', 'SON']
    
    # Timestamps
    generated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"Document - {self.get_template_type_display()} for Inspection #{self.inspection.id}"
    
    def __repr__(self):
        return f"<InspectionDocument: {self.template_type} - Inspection #{self.inspection.id}>"
    
    def generate_document_hash(self):
        """Generate SHA-256 hash of the document for integrity verification"""
        if self.document_file:
            # In a real implementation, you would read the file content
            # For now, we'll create a hash based on inspection data
            content = f"{self.inspection.id}{self.template_type}{self.generated_at}"
            return hashlib.sha256(content.encode()).hexdigest()
        return None
    
    def save(self, *args, **kwargs):
        if not self.document_hash and self.document_file:
            self.document_hash = self.generate_document_hash()
        
        # Set expiration time (24 hours from generation)
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if document has expired"""
        return timezone.now() > self.expires_at if self.expires_at else False
    
    @property
    def formatted_file_size(self):
        """Return human-readable file size"""
        if not self.file_size:
            return "Unknown size"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"
    
    class Meta:
        indexes = [
            models.Index(fields=['inspection']),
            models.Index(fields=['status']),
            models.Index(fields=['generated_at']),
            models.Index(fields=['expires_at']),
        ]
        ordering = ['-generated_at']
        verbose_name = 'Inspection Document'
        verbose_name_plural = 'Inspection Documents'


class DigitalSignature(DbModel):
    """
    Model for storing digital signatures on inspection documents
    """
    SIGNATURE_ROLES = [
        ('inspector', 'Inspector'),
        ('customer', 'Customer'),
        ('dealer', 'Dealer Representative'),
    ]
    
    SIGNATURE_METHODS = [
        ('drawn', 'Hand Drawn'),
        ('typed', 'Typed Name'),
        ('uploaded', 'Uploaded Image'),
    ]
    
    SIGNATURE_STATUS = [
        ('pending', 'Pending'),
        ('signed', 'Signed'),
        ('rejected', 'Rejected'),
    ]
    
    document = models.ForeignKey(InspectionDocument, on_delete=models.CASCADE, related_name='signatures')
    signer = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='inspection_signatures')
    role = models.CharField(max_length=20, choices=SIGNATURE_ROLES)
    status = models.CharField(max_length=20, choices=SIGNATURE_STATUS, default='pending')
    
    # Signature data
    signature_image = CloudinaryField('signature', folder='inspections/signatures/', blank=True, null=True)
    signature_method = models.CharField(max_length=20, choices=SIGNATURE_METHODS, blank=True, null=True)
    
    # Signature metadata for audit trail
    signed_at = models.DateTimeField(blank=True, null=True)
    signer_ip = models.GenericIPAddressField(blank=True, null=True)
    signer_user_agent = models.TextField(blank=True, null=True)
    signature_coordinates = models.JSONField(default=dict, blank=True)  # x, y, width, height
    
    # Verification
    signature_hash = models.CharField(max_length=64, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Signature - {self.get_role_display()} for Document #{self.document.id}"
    
    def __repr__(self):
        return f"<DigitalSignature: {self.role} - {self.signer.name} - {self.get_status_display()}>"
    
    def sign(self, signature_data, ip_address=None, user_agent=None):
        """Process the signature submission"""
        self.signature_image = signature_data.get('signature_image')
        self.signature_method = signature_data.get('signature_method', 'drawn')
        self.signature_coordinates = signature_data.get('coordinates', {})
        self.signer_ip = ip_address
        self.signer_user_agent = user_agent
        self.signed_at = timezone.now()
        self.status = 'signed'
        
        # Generate signature hash for verification
        content = f"{self.document.id}{self.signer.id}{self.signed_at}"
        self.signature_hash = hashlib.sha256(content.encode()).hexdigest()
        self.is_verified = True
        
        self.save()
        
        # Check if all signatures are complete
        self._check_document_completion()
    
    def _check_document_completion(self):
        """Check if all required signatures are complete and update document status"""
        all_signatures = self.document.signatures.all()
        if all_signatures.filter(status='signed').count() == all_signatures.count():
            self.document.status = 'signed'
            self.document.save()
            
            # Update inspection status
            self.document.inspection.status = 'signed'
            self.document.inspection.save()
    
    class Meta:
        indexes = [
            models.Index(fields=['document']),
            models.Index(fields=['signer']),
            models.Index(fields=['role']),
            models.Index(fields=['status']),
            models.Index(fields=['signed_at']),
        ]
        ordering = ['role', '-signed_at']
        verbose_name = 'Digital Signature'
        verbose_name_plural = 'Digital Signatures'
        unique_together = ['document', 'signer', 'role']  # One signature per role per document


class InspectionTemplate(DbModel):
    """
    Model for storing inspection report templates
    """
    TEMPLATE_CATEGORIES = [
        ('standard', 'Standard Template'),
        ('detailed', 'Detailed Template'),
        ('legal', 'Legal Compliance Template'),
        ('custom', 'Custom Template'),
    ]
    
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=TEMPLATE_CATEGORIES)
    description = models.TextField(blank=True, null=True)
    
    # Template file
    template_file = models.FileField(upload_to='inspections/templates/', blank=True, null=True)
    
    # Template configuration
    is_active = models.BooleanField(default=True)
    supports_photos = models.BooleanField(default=True)
    supports_recommendations = models.BooleanField(default=True)
    compliance_standards = models.JSONField(default=list, blank=True)
    
    # Template metadata
    created_by = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='created_templates')
    version = models.CharField(max_length=10, default='1.0')
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    def __repr__(self):
        return f"<InspectionTemplate: {self.name} - {self.category}>"
    
    class Meta:
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_by']),
        ]
        ordering = ['category', 'name']
        verbose_name = 'Inspection Template'
        verbose_name_plural = 'Inspection Templates'