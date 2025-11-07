from django.contrib import admin
from .models import (
    VehicleInspection,
    InspectionPhoto,
    InspectionDocument,
    DigitalSignature,
    InspectionTemplate
)


@admin.register(VehicleInspection)
class VehicleInspectionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'vehicle', 'inspector', 'customer', 'inspection_type', 
        'status', 'overall_rating', 'inspection_date'
    ]
    list_filter = ['inspection_type', 'status', 'overall_rating', 'inspection_date']
    search_fields = ['vehicle__name', 'inspector__first_name', 'inspector__last_name', 'customer__user__email']
    readonly_fields = ['date_created', 'last_updated', 'completed_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('vehicle', 'inspector', 'customer', 'dealer', 'inspection_type', 'status')
        }),
        ('Inspection Results', {
            'fields': ('overall_rating', 'inspector_notes', 'recommended_actions')
        }),
        ('Inspection Data', {
            'fields': ('exterior_data', 'interior_data', 'engine_data', 'mechanical_data', 'safety_data', 'documentation_data'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('inspection_date', 'completed_at', 'date_created', 'last_updated'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'vehicle', 'inspector', 'customer', 'dealer'
        )


@admin.register(InspectionPhoto)
class InspectionPhotoAdmin(admin.ModelAdmin):
    list_display = ['id', 'inspection', 'category', 'description', 'date_created']
    list_filter = ['category', 'date_created']
    search_fields = ['inspection__id', 'description']
    readonly_fields = ['date_created', 'last_updated']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('inspection')


@admin.register(InspectionDocument)
class InspectionDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'inspection', 'template_type', 'status', 'page_count', 
        'generated_at', 'expires_at'
    ]
    list_filter = ['template_type', 'status', 'generated_at', 'expires_at']
    search_fields = ['inspection__id', 'document_hash']
    readonly_fields = ['document_hash', 'generated_at', 'date_created', 'last_updated']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('inspection', 'template_type', 'status')
        }),
        ('Document Details', {
            'fields': ('document_file', 'document_hash', 'file_size', 'page_count')
        }),
        ('Generation Settings', {
            'fields': ('include_photos', 'include_recommendations', 'language', 'compliance_standards')
        }),
        ('Timestamps', {
            'fields': ('generated_at', 'expires_at', 'date_created', 'last_updated'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('inspection')


@admin.register(DigitalSignature)
class DigitalSignatureAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'document', 'signer', 'role', 'status', 'signature_method', 
        'signed_at', 'is_verified'
    ]
    list_filter = ['role', 'status', 'signature_method', 'is_verified', 'signed_at']
    search_fields = ['document__id', 'signer__first_name', 'signer__last_name', 'signer__email']
    readonly_fields = ['signature_hash', 'signed_at', 'date_created', 'last_updated']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('document', 'signer', 'role', 'status')
        }),
        ('Signature Details', {
            'fields': ('signature_image', 'signature_method', 'signature_coordinates')
        }),
        ('Audit Trail', {
            'fields': ('signed_at', 'signer_ip', 'signer_user_agent', 'signature_hash', 'is_verified'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('date_created', 'last_updated'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('document', 'signer')


@admin.register(InspectionTemplate)
class InspectionTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'category', 'version', 'is_active', 'created_by', 'date_created'
    ]
    list_filter = ['category', 'is_active', 'supports_photos', 'supports_recommendations']
    search_fields = ['name', 'description', 'created_by__first_name', 'created_by__last_name']
    readonly_fields = ['date_created', 'last_updated']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description', 'version', 'is_active')
        }),
        ('Template Configuration', {
            'fields': ('template_file', 'supports_photos', 'supports_recommendations', 'compliance_standards')
        }),
        ('Metadata', {
            'fields': ('created_by', 'date_created', 'last_updated'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')