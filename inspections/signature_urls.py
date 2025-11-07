"""
URL configuration for digital signature API endpoints
"""
from django.urls import path
from . import signature_views

app_name = 'signatures'

urlpatterns = [
    # Signature validation and submission
    path('validate/', signature_views.SignatureValidationView.as_view(), name='signature-validate'),
    
    # Signature permissions and status
    path('documents/<int:document_id>/permission-check/', 
         signature_views.SignaturePermissionCheckView.as_view(), 
         name='signature-permission-check'),
    path('documents/<int:document_id>/status/', 
         signature_views.SignatureStatusView.as_view(), 
         name='signature-status'),
    path('documents/<int:document_id>/audit-trail/', 
         signature_views.SignatureAuditTrailView.as_view(), 
         name='signature-audit-trail'),
    
    # Signature verification
    path('<int:signature_id>/verify/', 
         signature_views.SignatureVerificationView.as_view(), 
         name='signature-verify'),
    
    # Signature actions
    path('<int:signature_id>/resend-notification/', 
         signature_views.resend_signature_notification, 
         name='signature-resend-notification'),
    path('<int:signature_id>/reject/', 
         signature_views.reject_signature, 
         name='signature-reject'),
    
    # Bulk operations
    path('bulk-status/', 
         signature_views.BulkSignatureStatusView.as_view(), 
         name='signature-bulk-status'),
]
