"""
Signals for the vehicle inspection system
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
import logging

from .models import VehicleInspection, InspectionDocument, DigitalSignature

logger = logging.getLogger(__name__)


@receiver(post_save, sender=VehicleInspection)
def inspection_status_changed(sender, instance, created, **kwargs):
    """
    Handle inspection status changes
    """
    if created:
        logger.info(f"New inspection created: {instance.id} for vehicle {instance.vehicle.name}")
    
    # Auto-complete inspection if all required data is present
    if instance.status == 'in_progress' and instance._should_auto_complete():
        instance.status = 'completed'
        instance.completed_at = timezone.now()
        instance.save(update_fields=['status', 'completed_at'])
        logger.info(f"Inspection {instance.id} auto-completed")


@receiver(post_save, sender=DigitalSignature)
def signature_submitted(sender, instance, created, **kwargs):
    """
    Handle signature submission
    """
    if not created and instance.status == 'signed':
        logger.info(f"Signature submitted for document {instance.document.id} by {instance.signer.name}")
        
        # Check if all signatures are complete
        document = instance.document
        all_signatures = document.signatures.all()
        signed_count = all_signatures.filter(status='signed').count()
        
        if signed_count == all_signatures.count():
            # All signatures complete - update document and inspection status
            document.status = 'signed'
            document.save(update_fields=['status'])
            
            document.inspection.status = 'signed'
            document.inspection.save(update_fields=['status'])
            
            logger.info(f"Document {document.id} fully signed - inspection {document.inspection.id} completed")


@receiver(pre_save, sender=VehicleInspection)
def validate_inspection_before_save(sender, instance, **kwargs):
    """
    Validate inspection data before saving
    """
    # Ensure overall rating is set if inspection data exists
    if not instance.overall_rating and instance._has_inspection_data():
        from .services import InspectionValidationService
        
        inspection_data = {}
        for field in ['exterior_data', 'interior_data', 'engine_data', 'mechanical_data', 'safety_data']:
            data = getattr(instance, field, {})
            if data:
                section_name = field.replace('_data', '')
                inspection_data[section_name] = data
        
        if inspection_data:
            instance.overall_rating = InspectionValidationService.calculate_overall_rating(inspection_data)


# Add methods to VehicleInspection model for signal use
def _should_auto_complete(self):
    """Check if inspection should be auto-completed"""
    required_sections = ['exterior_data', 'interior_data', 'engine_data', 'mechanical_data', 'safety_data']
    
    for section in required_sections:
        data = getattr(self, section, {})
        if not data:
            return False
    
    return bool(self.overall_rating)


def _has_inspection_data(self):
    """Check if inspection has any data"""
    sections = ['exterior_data', 'interior_data', 'engine_data', 'mechanical_data', 'safety_data']
    
    for section in sections:
        data = getattr(self, section, {})
        if data:
            return True
    
    return False


# Monkey patch methods to VehicleInspection
VehicleInspection._should_auto_complete = _should_auto_complete
VehicleInspection._has_inspection_data = _has_inspection_data