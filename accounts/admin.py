from django.contrib import admin
from django import forms
from .models import (
    Account,
    Customer,
    Mechanic,
    Location,
    OTP,
    Dealer,
    BusinessVerificationSubmission,
)
from .newsletter import Newsletter, NewsletterAdmin
from utils.sms import send_sms
from utils.mail import send_email
from utils.admin import veyu_admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone




class AccountsAdmin(admin.ModelAdmin):
    actions = [
        'send_test_sms',
        'send_test_email',
        'send_welcome_email',
    ]
    list_display = [
        'name',
        'email',
        'uuid',
        'user_type',
        'provider',
        'welcome_email_status',
        'welcome_email_sent_date',
    ]
    list_display_links = [
        'name',
        'email',
        'uuid',
    ]
    list_filter = [
        'user_type',
        'provider',
        'verified_email',
        'welcome_email_sent_at',
    ]
    readonly_fields = [
        'welcome_email_sent_at',
        'has_received_welcome_email',
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('email', 'first_name', 'last_name', 'user_type', 'provider')
        }),
        ('Account Status', {
            'fields': ('verified_email', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('Welcome Email Status', {
            'fields': ('welcome_email_sent_at', 'has_received_welcome_email'),
            'description': 'Welcome email tracking information'
        }),
        ('Timestamps', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
    )

    def send_test_sms(self, request, queryset, *args, **kwargs):
        for account in queryset:
            if account.user_type == 'customer':
                send_sms(f"Hi {account.first_name}, welcome to veyu. \
                          \nYour verification code is 121-678 ", recipient=account.customer.phone_number)
            elif account.user_type == 'mechanic':
                print('User Phone Number:', account.mechanic.phone_number)
                send_sms(f"Hi {account.first_name}, welcome to veyu. \
                          \nYour verification code is 121-678 ", recipient=account.mechanic.phone_number)
        self.message_user(request, "Successfully sent sms")

    def welcome_email_status(self, obj):
        """Display welcome email status with colored badge."""
        if obj.has_received_welcome_email:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Sent</span>'
            )
        else:
            return format_html(
                '<span style="background-color: orange; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Not Sent</span>'
            )
    welcome_email_status.short_description = 'Welcome Email'
    welcome_email_status.admin_order_field = 'welcome_email_sent_at'

    def welcome_email_sent_date(self, obj):
        """Display formatted welcome email sent date."""
        if obj.welcome_email_sent_at:
            return obj.welcome_email_sent_at.strftime('%Y-%m-%d %H:%M')
        return '-'
    welcome_email_sent_date.short_description = 'Welcome Email Date'
    welcome_email_sent_date.admin_order_field = 'welcome_email_sent_at'

    def send_welcome_email(self, request, queryset, *args, **kwargs):
        """Send welcome email to selected users and update tracking."""
        success_count = 0
        error_count = 0
        
        for account in queryset:
            try:
                from accounts.utils.email_notifications import send_welcome_email
                from django.utils import timezone
                
                # Send the welcome email
                send_welcome_email(account)
                
                # Update the welcome email tracking
                account.welcome_email_sent_at = timezone.now()
                account.save(update_fields=['welcome_email_sent_at'])
                
                success_count += 1
            except Exception as e:
                error_count += 1
                self.message_user(request, f"Failed to send welcome email to {account.email}: {str(e)}", level='error')
        
        if success_count > 0:
            self.message_user(request, f"Successfully sent welcome email to {success_count} user(s)")
        if error_count > 0:
            self.message_user(request, f"Failed to send welcome email to {error_count} user(s)", level='warning')
    
    send_welcome_email.short_description = "Send welcome email to selected users"

    def send_test_email(self, request, queryset, *args, **kwargs):
        for account in queryset:
            try:
                from accounts.utils.email_notifications import send_verification_email
                # Generate a test verification code
                verification_code = "123456"
                send_verification_email(account, verification_code)
                self.message_user(request, f"Test verification email sent to {account.email}")
            except Exception as e:
                self.message_user(request, f"Failed to send test email to {account.email}: {str(e)}", level='error')


class OTPAdmin(admin.ModelAdmin):
    list_display_links = [
        'code'
    ]
    list_display = [
        'code',
        
    ]


class BusinessVerificationSubmissionForm(forms.ModelForm):
    class Meta:
        model = BusinessVerificationSubmission
        fields = '__all__'
        widgets = {
            'rejection_reason': forms.Textarea(attrs={
                'rows': 4, 
                'cols': 80,
                'placeholder': 'Provide specific feedback for rejection. This will be sent to the user via email.'
            }),
            'admin_notes': forms.Textarea(attrs={
                'rows': 3, 
                'cols': 80,
                'placeholder': 'Internal notes for admin use only (not visible to user)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Add helpful text for status changes
            if self.instance.status == 'pending':
                self.fields['status'].help_text = 'Changing to "verified" will approve and notify the user. Changing to "rejected" will reject and send the rejection reason.'
            elif self.instance.status == 'verified':
                self.fields['status'].help_text = 'This verification has been approved. Changing status will send a new notification.'
            elif self.instance.status == 'rejected':
                self.fields['status'].help_text = 'This verification was rejected. You can change to "pending" to allow re-review.'


class BusinessVerificationSubmissionAdmin(admin.ModelAdmin):
    form = BusinessVerificationSubmissionForm
    change_form_template = 'admin/accounts/businessverificationsubmission/change_form.html'
    list_display = [
        'business_name',
        'business_type',
        'status_badge',
        'submission_date',
        'reviewed_by',
        'view_documents',
        'business_profile_link'
    ]
    list_filter = ['status', 'business_type', 'date_created', 'reviewed_by']
    search_fields = ['business_name', 'business_email', 'cac_number', 'tin_number']
    readonly_fields = ['date_created', 'last_updated', 'uuid', 'business_profile_info']
    actions = ['approve_verification', 'reject_verification', 'mark_as_pending']
    list_per_page = 25
    date_hierarchy = 'date_created'
    
    fieldsets = (
        ('Business Information', {
            'fields': ('business_type', 'business_name', 'business_address', 
                      'business_email', 'business_phone', 'business_profile_info')
        }),
        ('Registration Details', {
            'fields': ('cac_number', 'tin_number')
        }),
        ('Documents', {
            'fields': ('cac_document', 'tin_document', 'proof_of_address', 'business_license'),
            'description': 'Click on document links to view/download files'
        }),
        ('Verification Status', {
            'fields': ('status', 'rejection_reason', 'admin_notes')
        }),
        ('Review Information', {
            'fields': ('reviewed_by', 'reviewed_at', 'date_created', 'last_updated', 'uuid'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'not_submitted': 'gray',
            'pending': 'orange',
            'verified': 'green',
            'rejected': 'red'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def submission_date(self, obj):
        return obj.date_created.strftime('%Y-%m-%d %H:%M')
    submission_date.short_description = 'Submitted'
    submission_date.admin_order_field = 'date_created'
    
    def business_profile_link(self, obj):
        business = obj.business_profile
        if business:
            if obj.business_type == 'dealership':
                url = reverse('admin:accounts_dealership_change', args=[business.pk])
                return format_html('<a href="{}" target="_blank">View Profile</a>', url)
            elif obj.business_type == 'mechanic':
                url = reverse('admin:accounts_mechanic_change', args=[business.pk])
                return format_html('<a href="{}" target="_blank">View Profile</a>', url)
        return '-'
    business_profile_link.short_description = 'Business Profile'
    
    def business_profile_info(self, obj):
        business = obj.business_profile
        if business:
            info = f"User: {business.user.email}<br>"
            info += f"Phone: {business.phone_number or 'Not provided'}<br>"
            info += f"Verified Business: {'Yes' if business.verified_business else 'No'}<br>"
            if hasattr(business, 'location') and business.location:
                info += f"Location: {business.location.city}, {business.location.state}"
            return format_html(info)
        return 'No profile found'
    business_profile_info.short_description = 'Profile Information'
    
    def view_documents(self, obj):
        """Enhanced document viewing with thumbnails and secure links"""
        docs = []
        
        document_fields = [
            ('cac_document', 'CAC', '#007cba'),
            ('tin_document', 'TIN', '#00a0d2'),
            ('proof_of_address', 'Address', '#826eb4'),
            ('business_license', 'License', '#46b450')
        ]
        
        for field_name, label, color in document_fields:
            document = getattr(obj, field_name, None)
            if document and hasattr(document, 'public_id') and document.public_id:
                # Generate thumbnail and secure link
                thumbnail_html = self.document_thumbnail(obj, field_name)
                if thumbnail_html:
                    docs.append(thumbnail_html)
                else:
                    # Fallback to button if thumbnail fails
                    secure_link = self.secure_document_link(obj, field_name, label, color)
                    if secure_link:
                        docs.append(secure_link)
        
        if docs:
            return format_html('<div style="display: flex; gap: 10px; flex-wrap: wrap;">{}</div>', format_html(''.join(docs)))
        else:
            return format_html('<span style="color: #999; font-style: italic;">No documents uploaded</span>')
    
    view_documents.short_description = 'Documents'
    view_documents.allow_tags = True
    
    def document_thumbnail(self, obj, field_name):
        """
        Generate thumbnail HTML for document preview with modal viewing capability
        
        Args:
            obj: BusinessVerificationSubmission instance
            field_name: Name of the document field
            
        Returns:
            HTML string with thumbnail and modal trigger
        """
        try:
            document = getattr(obj, field_name, None)
            if not document or not hasattr(document, 'public_id') or not document.public_id:
                return None
            
            # Get thumbnail URL
            thumbnail_url = obj.get_document_thumbnail_url(field_name, width=100, height=100)
            if not thumbnail_url:
                return None
            
            # Get secure full-size URL for modal
            secure_url = obj.get_document_secure_url(field_name, expires_in=3600)
            if not secure_url:
                return None
            
            # Document labels
            labels = {
                'cac_document': 'CAC',
                'tin_document': 'TIN',
                'proof_of_address': 'Address',
                'business_license': 'License'
            }
            label = labels.get(field_name, field_name.replace('_', ' ').title())
            
            # Generate HTML with thumbnail and modal trigger
            html = f'''
            <div class="document-thumbnail-wrapper" style="display: inline-block; text-align: center; margin: 5px;">
                <a href="{secure_url}" 
                   target="_blank" 
                   class="document-thumbnail-link"
                   data-document-type="{field_name}"
                   data-document-label="{label}"
                   onclick="return openDocumentModal(event, this);"
                   style="display: block; text-decoration: none; border: 2px solid #ddd; border-radius: 4px; padding: 5px; background: #f9f9f9; transition: all 0.2s;">
                    <img src="{thumbnail_url}" 
                         alt="{label}" 
                         style="width: 100px; height: 100px; object-fit: cover; display: block; border-radius: 2px;"
                         onerror="this.parentElement.innerHTML='<div style=\\'width:100px;height:100px;display:flex;align-items:center;justify-content:center;background:#f0f0f0;color:#666;\\'><span>📄</span></div>';">
                    <div style="margin-top: 5px; font-size: 11px; color: #333; font-weight: 500;">{label}</div>
                </a>
            </div>
            '''
            
            # Log thumbnail access
            self._log_document_access(obj, field_name, 'thumbnail')
            
            return html
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to generate thumbnail for {field_name}: {str(e)}")
            return None
    
    def secure_document_link(self, obj, field_name, label=None, color='#007cba'):
        """
        Generate secure download link with access logging
        
        Args:
            obj: BusinessVerificationSubmission instance
            field_name: Name of the document field
            label: Display label for the link
            color: Background color for the button
            
        Returns:
            HTML string with secure link button
        """
        try:
            document = getattr(obj, field_name, None)
            if not document or not hasattr(document, 'public_id') or not document.public_id:
                return None
            
            # Get secure URL
            secure_url = obj.get_document_secure_url(field_name, expires_in=3600)
            if not secure_url:
                return None
            
            # Use provided label or generate from field name
            if not label:
                labels = {
                    'cac_document': 'CAC',
                    'tin_document': 'TIN',
                    'proof_of_address': 'Address',
                    'business_license': 'License'
                }
                label = labels.get(field_name, field_name.replace('_', ' ').title())
            
            # Generate button HTML
            html = f'''
            <a href="{secure_url}" 
               target="_blank" 
               onclick="logDocumentAccess('{obj.uuid}', '{field_name}', 'download');"
               style="display: inline-block; margin-right: 5px; padding: 5px 12px; background: {color}; color: white; text-decoration: none; border-radius: 3px; font-size: 12px; font-weight: 500; transition: opacity 0.2s;"
               onmouseover="this.style.opacity='0.8';"
               onmouseout="this.style.opacity='1';">
                📄 {label}
            </a>
            '''
            
            # Log download access
            self._log_document_access(obj, field_name, 'download')
            
            return html
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to generate secure link for {field_name}: {str(e)}")
            return None
    
    def _log_document_access(self, obj, field_name, access_type, request=None):
        """
        Log document access for security auditing
        
        Args:
            obj: BusinessVerificationSubmission instance
            field_name: Name of the document field
            access_type: Type of access ('view', 'download', 'thumbnail')
            request: Django request object (optional)
        """
        try:
            from accounts.models import DocumentAccessLog
            
            # Try to get request from thread local storage
            if not request:
                try:
                    from threading import current_thread
                    thread = current_thread()
                    request = getattr(thread, 'request', None)
                except:
                    pass
            
            # If we have a request, log the access
            if request and hasattr(request, 'user') and request.user.is_authenticated:
                # Get IP address from request
                ip_address = self._get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                
                DocumentAccessLog.log_access(
                    submission=obj,
                    document_type=field_name,
                    user=request.user,
                    access_type=access_type,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=True
                )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Could not log document access: {str(e)}")
    
    def _get_client_ip(self, request):
        """
        Extract client IP address from request
        
        Args:
            request: Django request object
            
        Returns:
            IP address string
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip
    
    def approve_verification(self, request, queryset):
        count = 0
        for submission in queryset.filter(status='pending'):
            submission.approve(request.user)
            count += 1
        
        if count > 0:
            self.message_user(request, f'{count} verification(s) approved successfully. Notification emails have been sent.')
        else:
            self.message_user(request, 'No pending verifications were found to approve.', level='warning')
    approve_verification.short_description = 'Approve selected verifications'
    
    def reject_verification(self, request, queryset):
        # For bulk rejection, use a default message but encourage individual review
        count = 0
        for submission in queryset.filter(status='pending'):
            default_reason = 'Your submission requires additional review. Please ensure all documents are clear and complete, then resubmit.'
            submission.reject(request.user, default_reason)
            count += 1
        
        if count > 0:
            self.message_user(
                request, 
                f'{count} verification(s) rejected with default reason. For specific feedback, edit individual submissions and add detailed rejection reasons.',
                level='warning'
            )
        else:
            self.message_user(request, 'No pending verifications were found to reject.', level='warning')
    reject_verification.short_description = 'Reject selected verifications (with default reason)'
    
    def mark_as_pending(self, request, queryset):
        count = 0
        for submission in queryset.exclude(status='pending'):
            submission.status = 'pending'
            submission.reviewed_by = None
            submission.reviewed_at = None
            submission.rejection_reason = None
            submission.save()
            count += 1
        
        if count > 0:
            self.message_user(request, f'{count} verification(s) marked as pending for re-review.')
        else:
            self.message_user(request, 'No verifications were updated (already pending or no selection).', level='warning')
    mark_as_pending.short_description = 'Mark as pending for re-review'
    
    def save_model(self, request, obj, form, change):
        """Handle status changes when saving individual objects"""
        if change:  # Only for existing objects
            # Get the original object to compare status
            try:
                original = BusinessVerificationSubmission.objects.get(pk=obj.pk)
                old_status = original.status
                new_status = obj.status
                
                # If status is changing to verified or rejected, set review info
                if old_status != new_status and new_status in ['verified', 'rejected']:
                    obj.reviewed_by = request.user
                    obj.reviewed_at = timezone.now()
                    
                    # For rejection, ensure there's a reason
                    if new_status == 'rejected' and not obj.rejection_reason:
                        obj.rejection_reason = 'Please review your submission and ensure all documents are complete and accurate.'
                
            except BusinessVerificationSubmission.DoesNotExist:
                pass
        
        super().save_model(request, obj, form, change)


# Register your models here.
veyu_admin.register(Account, AccountsAdmin)
veyu_admin.register(Customer)
veyu_admin.register(Newsletter, NewsletterAdmin)
veyu_admin.register(Mechanic)
veyu_admin.register(Location)
veyu_admin.register(Dealer)
veyu_admin.register(OTP, OTPAdmin)
veyu_admin.register(BusinessVerificationSubmission, BusinessVerificationSubmissionAdmin)