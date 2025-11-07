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
    ]
    list_display_links = [
        'name',
        'email',
        'uuid',
    ]

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

    def send_welcome_email(self, request, queryset, *args, **kwargs):
        for account in queryset:
            try:
                from accounts.utils.email_notifications import send_welcome_email
                send_welcome_email(account)
                self.message_user(request, f"Successfully sent welcome email to {account.email}")
            except Exception as e:
                self.message_user(request, f"Failed to send welcome email to {account.email}: {str(e)}", level='error')

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
        docs = []
        if obj.cac_document:
            docs.append(f'<a href="{obj.cac_document.url}" target="_blank" style="margin-right: 10px; padding: 2px 8px; background: #007cba; color: white; text-decoration: none; border-radius: 3px;">CAC</a>')
        if obj.tin_document:
            docs.append(f'<a href="{obj.tin_document.url}" target="_blank" style="margin-right: 10px; padding: 2px 8px; background: #007cba; color: white; text-decoration: none; border-radius: 3px;">TIN</a>')
        if obj.proof_of_address:
            docs.append(f'<a href="{obj.proof_of_address.url}" target="_blank" style="margin-right: 10px; padding: 2px 8px; background: #007cba; color: white; text-decoration: none; border-radius: 3px;">Address</a>')
        if obj.business_license:
            docs.append(f'<a href="{obj.business_license.url}" target="_blank" style="margin-right: 10px; padding: 2px 8px; background: #007cba; color: white; text-decoration: none; border-radius: 3px;">License</a>')
        return format_html(''.join(docs)) if docs else format_html('<span style="color: #999;">No documents</span>')
    view_documents.short_description = 'Documents'
    
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