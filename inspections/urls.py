"""
URL configuration for the vehicle inspection system API
"""
from django.urls import path, include
from . import views

app_name = 'inspections'

urlpatterns = [
    # Inspection CRUD operations
    path('', views.VehicleInspectionListCreateView.as_view(), name='inspection-list-create'),
    path('<int:pk>/', views.VehicleInspectionDetailView.as_view(), name='inspection-detail'),
    path('<int:inspection_id>/complete/', views.complete_inspection, name='inspection-complete'),
    
    # Photo management
    path('<int:inspection_id>/photos/', views.InspectionPhotoUploadView.as_view(), name='inspection-photo-upload'),
    
    # Document generation and management
    path('<int:inspection_id>/generate-document/', views.DocumentGenerationView.as_view(), name='document-generate'),
    path('documents/<int:document_id>/preview/', views.DocumentPreviewView.as_view(), name='document-preview'),
    path('documents/<int:document_id>/download/', views.DocumentDownloadView.as_view(), name='document-download'),
    path('documents/<int:document_id>/sign/', views.DocumentSignatureView.as_view(), name='document-sign'),
    
    # Statistics and templates
    path('stats/', views.InspectionStatsView.as_view(), name='inspection-stats'),
    path('templates/', views.InspectionTemplateListView.as_view(), name='inspection-templates'),
    
    # Validation utilities
    path('validate/', views.inspection_validation, name='inspection-validation'),
    
    # Payment endpoints
    path('quote/', views.get_inspection_quote, name='inspection-quote'),
    path('<int:inspection_id>/pay/', views.pay_for_inspection, name='inspection-pay'),
    path('<int:inspection_id>/verify-payment/', views.verify_inspection_payment, name='inspection-verify-payment'),
    
    # Digital signature endpoints
    path('signatures/', include('inspections.signature_urls')),
    
    # Frontend integration endpoints
    path('frontend/', include('inspections.frontend_urls')),
    
    # Document management endpoints
    path('management/', include('inspections.document_management_urls')),
]