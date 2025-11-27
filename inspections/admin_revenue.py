"""
Admin configuration for inspection revenue management
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.utils import timezone
from decimal import Decimal
from .models_revenue import (
    InspectionRevenueSettings,
    InspectionRevenueSplit,
    WithdrawalRequest
)
from utils.admin import veyu_admin


@admin.register(InspectionRevenueSettings, site=veyu_admin)
class InspectionRevenueSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'revenue_split_display',
        'status_badge',
        'effective_date',
        'usage_count'
    ]
    list_filter = ['is_active', 'effective_date']
    readonly_fields = ['effective_date', 'date_created', 'last_updated', 'usage_statistics']
    
    fieldsets = (
        ('Revenue Split Configuration', {
            'fields': ('dealer_percentage', 'platform_percentage'),
            'description': 'Configure how inspection fees are split between dealers and platform. Must total 100%.'
        }),
        ('Status', {
            'fields': ('is_active',),
            'description': 'Only one settings record can be active at a time.'
        }),
        ('Notes', {
            'fields': ('notes',),
        }),
        ('Information', {
            'fields': ('effective_date', 'date_created', 'last_updated', 'usage_statistics'),
            'classes': ('collapse',)
        }),
    )
    
    def revenue_split_display(self, obj):
        """Display revenue split with visual representation"""
        return format_html(
            '<div style="display: flex; align-items: center; gap: 10px;">'
            '<div style="background: linear-gradient(to right, #28a745 0%, #28a745 {}%, #007bff {}%, #007bff 100%); '
            'width: 200px; height: 20px; border-radius: 4px; border: 1px solid #ddd;"></div>'
            '<span style="font-weight: 500;">Dealer: {}% | Platform: {}%</span>'
            '</div>',
            obj.dealer_percentage,
            obj.dealer_percentage,
            obj.dealer_percentage,
            obj.platform_percentage
        )
    revenue_split_display.short_description = 'Revenue Split'
    
    def status_badge(self, obj):
        """Display active status badge"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px; font-weight: 500;">Active</span>'
            )
        return format_html(
            '<span style="background-color: gray; color: white; padding: 3px 10px; border-radius: 3px;">Inactive</span>'
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'is_active'
    
    def usage_count(self, obj):
        """Display number of splits using this setting"""
        count = obj.revenue_splits.count()
        return format_html(
            '<span style="font-weight: 500;">{} splits</span>',
            count
        )
    usage_count.short_description = 'Usage'
    
    def usage_statistics(self, obj):
        """Display detailed usage statistics"""
        splits = obj.revenue_splits.all()
        total_splits = splits.count()
        
        if total_splits == 0:
            return format_html('<p style="color: #999;">No revenue splits using this configuration yet.</p>')
        
        total_revenue = splits.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        total_dealer = splits.aggregate(Sum('dealer_amount'))['dealer_amount__sum'] or 0
        total_platform = splits.aggregate(Sum('platform_amount'))['platform_amount__sum'] or 0
        
        return format_html(
            '<div style="line-height: 1.8;">'
            '<strong>Total Splits:</strong> {}<br>'
            '<strong>Total Revenue:</strong> ₦{:,.2f}<br>'
            '<strong>Total to Dealers:</strong> ₦{:,.2f}<br>'
            '<strong>Total to Platform:</strong> ₦{:,.2f}<br>'
            '</div>',
            total_splits,
            total_revenue,
            total_dealer,
            total_platform
        )
    usage_statistics.short_description = 'Usage Statistics'


@admin.register(InspectionRevenueSplit, site=veyu_admin)
class InspectionRevenueSplitAdmin(admin.ModelAdmin):
    list_display = [
        'inspection_id',
        'inspection_type',
        'dealer_name',
        'total_amount_display',
        'dealer_amount_display',
        'platform_amount_display',
        'dealer_credited_badge',
        'date_created'
    ]
    list_filter = [
        'dealer_credited',
        'date_created',
        'revenue_settings',
        'inspection__inspection_type'
    ]
    search_fields = [
        'inspection__id',
        'inspection__dealer__business_name',
        'inspection__dealer__user__email',
        'payment_transaction__tx_ref'
    ]
    readonly_fields = [
        'inspection',
        'payment_transaction',
        'total_amount',
        'dealer_amount',
        'dealer_percentage',
        'platform_amount',
        'platform_percentage',
        'revenue_settings',
        'dealer_credited',
        'dealer_credited_at',
        'date_created',
        'split_details'
    ]
    
    fieldsets = (
        ('Inspection Information', {
            'fields': ('inspection', 'payment_transaction')
        }),
        ('Revenue Split', {
            'fields': ('total_amount', 'dealer_amount', 'dealer_percentage', 'platform_amount', 'platform_percentage')
        }),
        ('Dealer Credit Status', {
            'fields': ('dealer_credited', 'dealer_credited_at')
        }),
        ('Configuration', {
            'fields': ('revenue_settings',)
        }),
        ('Details', {
            'fields': ('split_details', 'date_created'),
            'classes': ('collapse',)
        }),
    )
    
    def inspection_id(self, obj):
        """Display inspection ID with link"""
        return format_html(
            '<a href="/admin/inspections/vehicleinspection/{}/change/">Inspection #{}</a>',
            obj.inspection.id,
            obj.inspection.id
        )
    inspection_id.short_description = 'Inspection'
    
    def inspection_type(self, obj):
        """Display inspection type"""
        return obj.inspection.get_inspection_type_display()
    inspection_type.short_description = 'Type'
    
    def dealer_name(self, obj):
        """Display dealer name"""
        return obj.inspection.dealer.business_name or obj.inspection.dealer.user.name
    dealer_name.short_description = 'Dealer'
    
    def total_amount_display(self, obj):
        """Display total amount"""
        return format_html(
            '<strong style="color: #333;">₦{:,.2f}</strong>',
            obj.total_amount
        )
    total_amount_display.short_description = 'Total'
    total_amount_display.admin_order_field = 'total_amount'
    
    def dealer_amount_display(self, obj):
        """Display dealer amount"""
        return format_html(
            '<span style="color: #28a745; font-weight: 500;">₦{:,.2f} ({}%)</span>',
            obj.dealer_amount,
            obj.dealer_percentage
        )
    dealer_amount_display.short_description = 'Dealer Share'
    
    def platform_amount_display(self, obj):
        """Display platform amount"""
        return format_html(
            '<span style="color: #007bff; font-weight: 500;">₦{:,.2f} ({}%)</span>',
            obj.platform_amount,
            obj.platform_percentage
        )
    platform_amount_display.short_description = 'Platform Share'
    
    def dealer_credited_badge(self, obj):
        """Display dealer credit status"""
        if obj.dealer_credited:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Credited</span>'
            )
        return format_html(
            '<span style="background-color: orange; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Pending</span>'
        )
    dealer_credited_badge.short_description = 'Status'
    dealer_credited_badge.admin_order_field = 'dealer_credited'
    
    def split_details(self, obj):
        """Display detailed split information"""
        return format_html(
            '<div style="line-height: 1.8;">'
            '<strong>Inspection:</strong> #{} - {}<br>'
            '<strong>Customer:</strong> {}<br>'
            '<strong>Dealer:</strong> {}<br>'
            '<strong>Payment Transaction:</strong> #{}<br>'
            '<strong>Revenue Settings:</strong> {}<br>'
            '<strong>Split Date:</strong> {}<br>'
            '<strong>Dealer Credited:</strong> {} {}<br>'
            '</div>',
            obj.inspection.id,
            obj.inspection.get_inspection_type_display(),
            obj.inspection.customer.user.name,
            obj.inspection.dealer.business_name or obj.inspection.dealer.user.name,
            obj.payment_transaction.id,
            obj.revenue_settings,
            obj.date_created.strftime('%Y-%m-%d %H:%M'),
            'Yes' if obj.dealer_credited else 'No',
            f'on {obj.dealer_credited_at.strftime("%Y-%m-%d %H:%M")}' if obj.dealer_credited_at else ''
        )
    split_details.short_description = 'Split Details'
    
    def has_add_permission(self, request):
        """Prevent manual creation of splits"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of splits"""
        return False


@admin.register(WithdrawalRequest, site=veyu_admin)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user_name',
        'amount_display',
        'status_badge',
        'bank_info',
        'date_created',
        'reviewed_by_display'
    ]
    list_filter = [
        'status',
        'date_created',
        'reviewed_at'
    ]
    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name',
        'account_number',
        'account_name',
        'bank_name',
        'payment_reference'
    ]
    readonly_fields = [
        'user',
        'wallet',
        'amount',
        'account_name',
        'account_number',
        'bank_name',
        'bank_code',
        'paystack_verified',
        'paystack_recipient_code',
        'transaction',
        'date_created',
        'last_updated',
        'reviewed_at',
        'processed_at',
        'request_details'
    ]
    
    fieldsets = (
        ('Request Information', {
            'fields': ('user', 'wallet', 'amount')
        }),
        ('Bank Account Details', {
            'fields': ('account_name', 'account_number', 'bank_name', 'bank_code', 'paystack_verified', 'paystack_recipient_code')
        }),
        ('Status', {
            'fields': ('status', 'transaction', 'payment_reference')
        }),
        ('Review', {
            'fields': ('reviewed_by', 'reviewed_at', 'rejection_reason', 'admin_notes')
        }),
        ('Processing', {
            'fields': ('processed_at',)
        }),
        ('Details', {
            'fields': ('request_details', 'date_created', 'last_updated'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_requests', 'reject_requests']
    
    def user_name(self, obj):
        """Display user name with email"""
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.user.name,
            obj.user.email
        )
    user_name.short_description = 'User'
    
    def amount_display(self, obj):
        """Display amount"""
        return format_html(
            '<strong style="color: #dc3545;">₦{:,.2f}</strong>',
            obj.amount
        )
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def status_badge(self, obj):
        """Display status badge"""
        colors = {
            'pending': '#ffc107',
            'approved': '#28a745',
            'processing': '#17a2b8',
            'completed': '#28a745',
            'rejected': '#dc3545',
            'cancelled': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: 500;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def bank_info(self, obj):
        """Display bank information"""
        verified_badge = ''
        if obj.paystack_verified:
            verified_badge = '<span style="background-color: green; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; margin-left: 5px;">✓ Verified</span>'
        
        return format_html(
            '<strong>{}</strong>{}<br>'
            '<small>{} - {}</small>',
            obj.bank_name,
            verified_badge,
            obj.account_name,
            obj.account_number
        )
    bank_info.short_description = 'Bank Account'
    
    def reviewed_by_display(self, obj):
        """Display reviewer information"""
        if obj.reviewed_by:
            return format_html(
                '{}<br><small>{}</small>',
                obj.reviewed_by.name,
                obj.reviewed_at.strftime('%Y-%m-%d %H:%M') if obj.reviewed_at else ''
            )
        return '-'
    reviewed_by_display.short_description = 'Reviewed By'
    
    def request_details(self, obj):
        """Display detailed request information"""
        details = '<div style="line-height: 1.8;">'
        details += f'<strong>Request ID:</strong> {obj.id}<br>'
        details += f'<strong>User:</strong> {obj.user.name} ({obj.user.email})<br>'
        details += f'<strong>Amount:</strong> ₦{obj.amount:,.2f}<br>'
        details += f'<strong>Wallet Balance:</strong> ₦{obj.wallet.balance:,.2f}<br>'
        details += f'<strong>Bank:</strong> {obj.bank_name}<br>'
        details += f'<strong>Account:</strong> {obj.account_name} - {obj.account_number}<br>'
        details += f'<strong>Bank Code:</strong> {obj.bank_code}<br>'
        
        if obj.paystack_verified:
            details += f'<strong>Paystack Verified:</strong> <span style="color: green;">✓ Yes</span><br>'
        else:
            details += f'<strong>Paystack Verified:</strong> <span style="color: orange;">⚠ No</span><br>'
        
        if obj.paystack_recipient_code:
            details += f'<strong>Paystack Recipient Code:</strong> {obj.paystack_recipient_code}<br>'
        
        details += f'<strong>Status:</strong> {obj.get_status_display()}<br>'
        details += f'<strong>Created:</strong> {obj.date_created.strftime("%Y-%m-%d %H:%M")}<br>'
        
        if obj.reviewed_by:
            details += f'<strong>Reviewed By:</strong> {obj.reviewed_by.name}<br>'
            details += f'<strong>Reviewed At:</strong> {obj.reviewed_at.strftime("%Y-%m-%d %H:%M")}<br>'
        
        if obj.rejection_reason:
            details += f'<strong>Rejection Reason:</strong> {obj.rejection_reason}<br>'
        
        if obj.processed_at:
            details += f'<strong>Processed At:</strong> {obj.processed_at.strftime("%Y-%m-%d %H:%M")}<br>'
        
        if obj.payment_reference:
            details += f'<strong>Payment Reference:</strong> {obj.payment_reference}<br>'
        
        details += '</div>'
        return format_html(details)
    request_details.short_description = 'Request Details'
    
    def approve_requests(self, request, queryset):
        """Approve selected withdrawal requests"""
        count = 0
        for withdrawal in queryset.filter(status='pending'):
            try:
                withdrawal.approve(request.user)
                count += 1
            except Exception as e:
                self.message_user(request, f'Failed to approve request #{withdrawal.id}: {str(e)}', level='error')
        
        if count > 0:
            self.message_user(request, f'{count} withdrawal request(s) approved successfully.')
    approve_requests.short_description = 'Approve selected requests'
    
    def reject_requests(self, request, queryset):
        """Reject selected withdrawal requests"""
        count = 0
        default_reason = 'Your withdrawal request has been rejected. Please contact support for more information.'
        
        for withdrawal in queryset.filter(status='pending'):
            try:
                withdrawal.reject(request.user, default_reason)
                count += 1
            except Exception as e:
                self.message_user(request, f'Failed to reject request #{withdrawal.id}: {str(e)}', level='error')
        
        if count > 0:
            self.message_user(
                request,
                f'{count} withdrawal request(s) rejected with default reason. Edit individual requests for specific feedback.',
                level='warning'
            )
    reject_requests.short_description = 'Reject selected requests (with default reason)'
    
    def save_model(self, request, obj, form, change):
        """Handle status changes when saving"""
        if change:
            try:
                original = WithdrawalRequest.objects.get(pk=obj.pk)
                old_status = original.status
                new_status = obj.status
                
                # If status is changing to approved or rejected, set review info
                if old_status != new_status:
                    if new_status == 'approved':
                        obj.approve(request.user)
                        return
                    elif new_status == 'rejected':
                        if not obj.rejection_reason:
                            obj.rejection_reason = 'Your withdrawal request has been rejected. Please contact support.'
                        obj.reject(request.user, obj.rejection_reason)
                        return
            except WithdrawalRequest.DoesNotExist:
                pass
        
        super().save_model(request, obj, form, change)
