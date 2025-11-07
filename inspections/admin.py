from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from utils.admin import veyu_admin
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
        'status', 'overall_rating', 'document_count', 'inspection_date'
    ]
    list_filter = ['inspection_type', 'status', 'overall_rating', 'inspection_date']
    search_fields = ['vehicle__name', 'inspector__first_name', 'inspector__last_name', 'customer__user__email']
    readonly_fields = ['date_created', 'last_updated', 'completed_at', 'inspection_summary_display', 'related_documents']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('vehicle', 'inspector', 'customer', 'dealer', 'inspection_type', 'status')
        }),
        ('Inspection Results', {
            'fields': ('overall_rating', 'inspector_notes', 'recommended_actions', 'inspection_summary_display')
        }),
        ('Related Documents', {
            'fields': ('related_documents',)
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
        ).prefetch_related('documents', 'photos')
    
    def document_count(self, obj):
        """Display count of documents with status"""
        count = obj.documents.count()
        signed_count = obj.documents.filter(status='signed').count()
        
        if count == 0:
            return format_html('<span style="color: gray;">No documents</span>')
        
        if signed_count == count:
            return format_html('<span style="color: green; font-weight: bold;">✓ {} signed</span>', count)
        elif signed_count > 0:
            return format_html('<span style="color: orange; font-weight: bold;">◐ {}/{} signed</span>', signed_count, count)
        else:
            return format_html('<span style="color: red;">○ {} pending</span>', count)
    document_count.short_description = 'Documents'
    
    def inspection_summary_display(self, obj):
        """Display inspection summary"""
        summary = obj.get_inspection_summary()
        
        return format_html(
            '''
            <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; background: #f9f9f9;">
                <p><strong>Overall Rating:</strong> <span style="color: {};">{}</span></p>
                <p><strong>Total Issues Found:</strong> {}</p>
                <p><strong>Recommendations:</strong> {}</p>
                <p><strong>Status:</strong> {}</p>
            </div>
            ''',
            'green' if summary['overall_rating'] == 'Excellent' else ('orange' if summary['overall_rating'] in ['Good', 'Fair'] else 'red'),
            summary['overall_rating'] or 'Not Rated',
            summary['total_issues'],
            summary['recommendations_count'],
            summary['status']
        )
    inspection_summary_display.short_description = 'Inspection Summary'
    
    def related_documents(self, obj):
        """Display all related documents with links"""
        documents = obj.documents.all()
        
        if not documents.exists():
            return format_html('<span style="color: gray;">No documents generated yet</span>')
        
        html = '<div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; background: #f9f9f9;">'
        html += '<h4 style="margin-top: 0;">Generated Documents</h4>'
        
        for doc in documents:
            signatures = doc.signatures.all()
            total_sigs = signatures.count()
            signed_sigs = signatures.filter(status='signed').count()
            
            status_color = 'green' if doc.status == 'signed' else ('orange' if doc.status == 'ready' else 'gray')
            sig_status = f'{signed_sigs}/{total_sigs} signatures' if total_sigs > 0 else 'No signatures'
            
            html += f'''
            <div style="border: 1px solid #e0e0e0; padding: 10px; margin-bottom: 10px; border-radius: 3px; background: white;">
                <p style="margin: 5px 0;"><strong>Document #{doc.id}</strong> - {doc.get_template_type_display()}</p>
                <p style="margin: 5px 0;">Status: <span style="color: {status_color}; font-weight: bold;">{doc.get_status_display()}</span></p>
                <p style="margin: 5px 0;">Signatures: {sig_status}</p>
                <p style="margin: 5px 0;">Generated: {doc.generated_at.strftime("%Y-%m-%d %H:%M")}</p>
            '''
            
            if doc.document_file:
                html += f'''
                <div style="margin-top: 10px;">
                    <a href="{doc.document_file.url}" target="_blank" style="background: #417690; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px; font-size: 12px;">
                        📄 View
                    </a>
                    <a href="{doc.document_file.url}" download style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; font-size: 12px;">
                        ⬇️ Download
                    </a>
                    <a href="/admin/inspections/inspectiondocument/{doc.id}/change/" style="background: #6c757d; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; font-size: 12px;">
                        ⚙️ Details
                    </a>
                </div>
                '''
            
            html += '</div>'
        
        html += '</div>'
        return mark_safe(html)
    related_documents.short_description = 'Documents'


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
        'id', 'inspection', 'template_type', 'status', 'signature_status_badge',
        'page_count', 'view_document_link', 'download_document_link', 'generated_at'
    ]
    list_filter = ['template_type', 'status', 'generated_at', 'expires_at']
    search_fields = ['inspection__id', 'document_hash', 'inspection__vehicle__name']
    readonly_fields = [
        'document_hash', 'generated_at', 'date_created', 'last_updated',
        'document_preview', 'signature_summary', 'view_document_link', 'download_document_link'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('inspection', 'template_type', 'status')
        }),
        ('Document Details', {
            'fields': ('document_file', 'document_preview', 'document_hash', 'file_size', 'page_count')
        }),
        ('Signature Information', {
            'fields': ('signature_summary',)
        }),
        ('Actions', {
            'fields': ('view_document_link', 'download_document_link')
        }),
        ('Generation Settings', {
            'fields': ('include_photos', 'include_recommendations', 'language', 'compliance_standards'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('generated_at', 'expires_at', 'date_created', 'last_updated'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('inspection').prefetch_related('signatures')
    
    def signature_status_badge(self, obj):
        """Display signature completion status as a badge"""
        signatures = obj.signatures.all()
        total = signatures.count()
        signed = signatures.filter(status='signed').count()
        
        if total == 0:
            return format_html('<span style="color: gray;">No signatures required</span>')
        
        percentage = (signed / total * 100) if total > 0 else 0
        
        if percentage == 100:
            color = 'green'
            icon = '✓'
            text = 'Fully Signed'
        elif percentage > 0:
            color = 'orange'
            icon = '◐'
            text = f'Partially Signed ({signed}/{total})'
        else:
            color = 'red'
            icon = '○'
            text = 'Pending Signatures'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, text
        )
    signature_status_badge.short_description = 'Signature Status'
    
    def document_preview(self, obj):
        """Display document preview with thumbnail"""
        if not obj.document_file:
            return format_html('<span style="color: gray;">No document file</span>')
        
        return format_html(
            '''
            <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; background: #f9f9f9;">
                <p><strong>Document File:</strong> {}</p>
                <p><strong>File Size:</strong> {}</p>
                <p><strong>Pages:</strong> {}</p>
                <p><strong>Hash:</strong> <code style="font-size: 10px;">{}</code></p>
                <div style="margin-top: 10px;">
                    <a href="{}" target="_blank" style="background: #417690; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">
                        📄 View Document
                    </a>
                    <a href="{}" download style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">
                        ⬇️ Download
                    </a>
                </div>
            </div>
            ''',
            obj.document_file.url.split('/')[-1],
            obj.formatted_file_size,
            obj.page_count,
            obj.document_hash[:32] + '...' if obj.document_hash else 'N/A',
            obj.document_file.url,
            obj.document_file.url
        )
    document_preview.short_description = 'Document Preview'
    
    def signature_summary(self, obj):
        """Display detailed signature information"""
        signatures = obj.signatures.all().order_by('role')
        
        if not signatures.exists():
            return format_html('<span style="color: gray;">No signatures</span>')
        
        html = '<div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; background: #f9f9f9;">'
        html += '<h4 style="margin-top: 0;">Signature Details</h4>'
        html += '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr style="background: #e9ecef;"><th style="padding: 8px; text-align: left;">Role</th><th style="padding: 8px; text-align: left;">Signer</th><th style="padding: 8px; text-align: left;">Status</th><th style="padding: 8px; text-align: left;">Signed At</th><th style="padding: 8px; text-align: left;">Method</th></tr>'
        
        for sig in signatures:
            status_color = 'green' if sig.status == 'signed' else ('red' if sig.status == 'rejected' else 'orange')
            status_icon = '✓' if sig.status == 'signed' else ('✗' if sig.status == 'rejected' else '○')
            
            html += f'''
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 8px;"><strong>{sig.get_role_display()}</strong></td>
                <td style="padding: 8px;">{sig.signer.email}</td>
                <td style="padding: 8px;"><span style="color: {status_color}; font-weight: bold;">{status_icon} {sig.get_status_display()}</span></td>
                <td style="padding: 8px;">{sig.signed_at.strftime("%Y-%m-%d %H:%M") if sig.signed_at else "Not signed"}</td>
                <td style="padding: 8px;">{sig.get_signature_method_display() if sig.signature_method else "N/A"}</td>
            </tr>
            '''
        
        html += '</table></div>'
        return mark_safe(html)
    signature_summary.short_description = 'Signatures'
    
    def view_document_link(self, obj):
        """Link to view the document"""
        if not obj.document_file:
            return format_html('<span style="color: gray;">No document</span>')
        
        return format_html(
            '<a href="{}" target="_blank" style="background: #417690; color: white; padding: 8px 15px; text-decoration: none; border-radius: 3px; display: inline-block;">📄 View Document</a>',
            obj.document_file.url
        )
    view_document_link.short_description = 'View'
    
    def download_document_link(self, obj):
        """Link to download the document"""
        if not obj.document_file:
            return format_html('<span style="color: gray;">No document</span>')
        
        return format_html(
            '<a href="{}" download style="background: #28a745; color: white; padding: 8px 15px; text-decoration: none; border-radius: 3px; display: inline-block;">⬇️ Download</a>',
            obj.document_file.url
        )
    download_document_link.short_description = 'Download'


@admin.register(DigitalSignature)
class DigitalSignatureAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'document', 'signer', 'role', 'status_badge', 'signature_method', 
        'signed_at', 'verification_badge'
    ]
    list_filter = ['role', 'status', 'signature_method', 'is_verified', 'signed_at']
    search_fields = ['document__id', 'signer__first_name', 'signer__last_name', 'signer__email']
    readonly_fields = [
        'signature_hash', 'signed_at', 'date_created', 'last_updated',
        'signature_preview', 'audit_information'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('document', 'signer', 'role', 'status')
        }),
        ('Signature Details', {
            'fields': ('signature_image', 'signature_preview', 'signature_method', 'signature_coordinates')
        }),
        ('Audit Trail', {
            'fields': ('audit_information', 'signed_at', 'signer_ip', 'signer_user_agent', 'signature_hash', 'is_verified')
        }),
        ('Timestamps', {
            'fields': ('date_created', 'last_updated'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('document', 'signer')
    
    def status_badge(self, obj):
        """Display status as a colored badge"""
        if obj.status == 'signed':
            return format_html('<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">✓ Signed</span>')
        elif obj.status == 'rejected':
            return format_html('<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">✗ Rejected</span>')
        else:
            return format_html('<span style="background: #ffc107; color: black; padding: 3px 8px; border-radius: 3px; font-weight: bold;">○ Pending</span>')
    status_badge.short_description = 'Status'
    
    def verification_badge(self, obj):
        """Display verification status"""
        if obj.is_verified:
            return format_html('<span style="color: green; font-weight: bold;">✓ Verified</span>')
        else:
            return format_html('<span style="color: red;">✗ Not Verified</span>')
    verification_badge.short_description = 'Verified'
    
    def signature_preview(self, obj):
        """Display signature image preview"""
        if not obj.signature_image:
            return format_html('<span style="color: gray;">No signature image</span>')
        
        return format_html(
            '''
            <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; background: #f9f9f9;">
                <p><strong>Signature Preview:</strong></p>
                <div style="border: 1px solid #ccc; padding: 10px; background: white; display: inline-block;">
                    <img src="{}" alt="Signature" style="max-width: 300px; max-height: 100px; display: block;" />
                </div>
                <p style="margin-top: 10px;"><strong>Method:</strong> {}</p>
            </div>
            ''',
            obj.signature_image.url,
            obj.get_signature_method_display() if obj.signature_method else 'Unknown'
        )
    signature_preview.short_description = 'Signature Preview'
    
    def audit_information(self, obj):
        """Display audit trail information"""
        return format_html(
            '''
            <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; background: #f9f9f9;">
                <h4 style="margin-top: 0;">Audit Information</h4>
                <table style="width: 100%;">
                    <tr><td style="padding: 5px;"><strong>Signer:</strong></td><td style="padding: 5px;">{}</td></tr>
                    <tr><td style="padding: 5px;"><strong>Email:</strong></td><td style="padding: 5px;">{}</td></tr>
                    <tr><td style="padding: 5px;"><strong>Role:</strong></td><td style="padding: 5px;">{}</td></tr>
                    <tr><td style="padding: 5px;"><strong>Signed At:</strong></td><td style="padding: 5px;">{}</td></tr>
                    <tr><td style="padding: 5px;"><strong>IP Address:</strong></td><td style="padding: 5px;">{}</td></tr>
                    <tr><td style="padding: 5px;"><strong>User Agent:</strong></td><td style="padding: 5px; font-size: 10px;">{}</td></tr>
                    <tr><td style="padding: 5px;"><strong>Signature Hash:</strong></td><td style="padding: 5px;"><code style="font-size: 10px;">{}</code></td></tr>
                    <tr><td style="padding: 5px;"><strong>Verified:</strong></td><td style="padding: 5px;">{}</td></tr>
                </table>
            </div>
            ''',
            obj.signer.get_full_name() or obj.signer.email,
            obj.signer.email,
            obj.get_role_display(),
            obj.signed_at.strftime("%Y-%m-%d %H:%M:%S") if obj.signed_at else "Not signed yet",
            obj.signer_ip or "N/A",
            obj.signer_user_agent[:100] + "..." if obj.signer_user_agent and len(obj.signer_user_agent) > 100 else (obj.signer_user_agent or "N/A"),
            obj.signature_hash[:32] + "..." if obj.signature_hash else "N/A",
            "✓ Yes" if obj.is_verified else "✗ No"
        )
    audit_information.short_description = 'Audit Trail'


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


# Register models with custom Veyu admin site
veyu_admin.register(VehicleInspection, VehicleInspectionAdmin)
veyu_admin.register(InspectionPhoto, InspectionPhotoAdmin)
veyu_admin.register(InspectionDocument, InspectionDocumentAdmin)
veyu_admin.register(DigitalSignature, DigitalSignatureAdmin)
veyu_admin.register(InspectionTemplate, InspectionTemplateAdmin)
