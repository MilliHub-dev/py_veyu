"""
URL configuration for frontend integration API endpoints
"""
from django.urls import path
from . import frontend_api_views

app_name = 'frontend'

urlpatterns = [
    # Inspection data collection
    path('collect-data/', 
         frontend_api_views.InspectionDataCollectionView.as_view(), 
         name='collect-inspection-data'),
    
    # Document preview and generation
    path('inspections/<int:inspection_id>/generate-preview/', 
         frontend_api_views.DocumentPreviewGenerationView.as_view(), 
         name='generate-document-preview'),
    
    # Signature submission
    path('documents/<int:document_id>/submit-signature/', 
         frontend_api_views.SignatureSubmissionView.as_view(), 
         name='submit-signature'),
    
    # Document retrieval
    path('documents/<int:document_id>/', 
         frontend_api_views.DocumentRetrievalView.as_view(), 
         name='retrieve-document'),
    
    # Real-time status updates
    path('inspections/<int:inspection_id>/status/', 
         frontend_api_views.InspectionStatusUpdateView.as_view(), 
         name='inspection-status'),
    
    # Photo upload
    path('inspections/<int:inspection_id>/upload-photo/', 
         frontend_api_views.InspectionPhotoUploadView.as_view(), 
         name='upload-photo'),
    
    # Form schema
    path('form-schema/', 
         frontend_api_views.get_inspection_form_schema, 
         name='form-schema'),
]
