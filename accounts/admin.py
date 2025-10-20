from django.contrib import admin
from .models import (
    Account,
    Customer,
    Mechanic,
    Location,
    OTP,
    Dealer,
    BusinessVerificationSubmission,
)
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
            send_email(
                subject="Welcome to veyu",
                context={'user': account},
                recipients=[account.email],
                template="utils/templates/welcome.html",
            )
        self.message_user(request, "Successfully sent welcome email")

    def send_test_email(self, request, queryset, *args, **kwargs):
        for account in queryset:
            send_email(
                subject="Welcome to veyu",
                context={'user': account},
                recipients=[account.email],
                template="utils/templates/email-confirmation.html",
            )
        self.message_user(request, "Successfully sent sms")


class OTPAdmin(admin.ModelAdmin):
    list_display_links = [
        'code'
    ]
    list_display = [
        'code',
        
    ]


class BusinessVerificationSubmissionAdmin(admin.ModelAdmin):
    list_display = [
        'business_name',
        'business_type',
        'status_badge',
        'date_created',
        'reviewed_by',
        'view_documents'
    ]
    list_filter = ['status', 'business_type', 'date_created']
    search_fields = ['business_name', 'business_email', 'cac_number', 'tin_number']
    readonly_fields = ['date_created', 'last_updated', 'reviewed_by', 'reviewed_at']
    actions = ['approve_verification', 'reject_verification']
    
    fieldsets = (
        ('Business Information', {
            'fields': ('business_type', 'business_name', 'business_address', 
                      'business_email', 'business_phone')
        }),
        ('Registration Details', {
            'fields': ('cac_number', 'tin_number')
        }),
        ('Documents', {
            'fields': ('cac_document', 'tin_document', 'proof_of_address', 'business_license')
        }),
        ('Verification Status', {
            'fields': ('status', 'rejection_reason', 'admin_notes')
        }),
        ('Review Information', {
            'fields': ('reviewed_by', 'reviewed_at', 'date_created', 'last_updated'),
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
    
    def view_documents(self, obj):
        docs = []
        if obj.cac_document:
            docs.append(f'<a href="{obj.cac_document.url}" target="_blank">CAC</a>')
        if obj.tin_document:
            docs.append(f'<a href="{obj.tin_document.url}" target="_blank">TIN</a>')
        if obj.proof_of_address:
            docs.append(f'<a href="{obj.proof_of_address.url}" target="_blank">Address</a>')
        if obj.business_license:
            docs.append(f'<a href="{obj.business_license.url}" target="_blank">License</a>')
        return format_html(' | '.join(docs)) if docs else '-'
    view_documents.short_description = 'Documents'
    
    def approve_verification(self, request, queryset):
        count = 0
        for submission in queryset.filter(status='pending'):
            submission.approve(request.user)
            count += 1
        self.message_user(request, f'{count} verification(s) approved successfully.')
    approve_verification.short_description = 'Approve selected verifications'
    
    def reject_verification(self, request, queryset):
        # This would ideally open a form to enter rejection reason
        # For now, we'll use a default message
        count = 0
        for submission in queryset.filter(status='pending'):
            submission.reject(request.user, 'Please review and resubmit with correct information.')
            count += 1
        self.message_user(request, f'{count} verification(s) rejected. Note: Add rejection reason in the admin form.')
    reject_verification.short_description = 'Reject selected verifications'


# Register your models here.
veyu_admin.register(Account, AccountsAdmin)
veyu_admin.register(Customer)
veyu_admin.register(Mechanic)
veyu_admin.register(Location)
veyu_admin.register(Dealer)
veyu_admin.register(OTP, OTPAdmin)
veyu_admin.register(BusinessVerificationSubmission, BusinessVerificationSubmissionAdmin)