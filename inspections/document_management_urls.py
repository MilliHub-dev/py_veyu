"""
URL configuration for document management system
"""
from django.urls import path
from . import document_management_views

app_name = 'document_management'

urlpatterns = [
    # Access control
    path('documents/<int:document_id>/access-check/', 
         document_management_views.DocumentAccessCheckView.as_view(), 
         name='document-access-check'),
    
    # Version management
    path('documents/<int:document_id>/versions/', 
         document_management_views.DocumentVersionHistoryView.as_view(), 
         name='document-versions'),
    
    # Audit trail
    path('documents/<int:document_id>/audit-trail/', 
         document_management_views.DocumentAuditTrailView.as_view(), 
         name='document-audit-trail'),
    
    # Search and filtering
    path('documents/search/', 
         document_management_views.DocumentSearchView.as_view(), 
         name='document-search'),
    
    # Retention management
    path('documents/<int:document_id>/retention-status/', 
         document_management_views.DocumentRetentionStatusView.as_view(), 
         name='document-retention-status'),
    path('documents/<int:document_id>/archive/', 
         document_management_views.DocumentArchiveView.as_view(), 
         name='document-archive'),
    path('documents/retention-cleanup/', 
         document_management_views.run_retention_cleanup, 
         name='retention-cleanup'),
    
    # Sharing and permissions
    path('documents/<int:document_id>/share/', 
         document_management_views.DocumentShareView.as_view(), 
         name='document-share'),
    path('documents/<int:document_id>/shares/', 
         document_management_views.DocumentShareListView.as_view(), 
         name='document-shares'),
    path('documents/<int:document_id>/revoke-share/', 
         document_management_views.DocumentShareRevokeView.as_view(), 
         name='document-revoke-share'),
]
