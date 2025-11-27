from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Wallet, Transaction
from utils.admin import veyu_admin


@admin.register(Wallet, site=veyu_admin)
class WalletAdmin(admin.ModelAdmin):
    list_display = [
        'user_email',
        'user_name',
        'formatted_ledger_balance',
        'formatted_available_balance',
        'formatted_locked_amount',
        'total_transactions',
        'currency',
        'date_created'
    ]
    
    list_filter = (
        'currency',
        'date_created',
    )
    
    search_fields = (
        'user__email',
        'user__first_name',
        'user__last_name',
    )
    
    readonly_fields = (
        'user',
        'ledger_balance',
        'currency',
        'date_created',
        'last_updated',
        'transaction_summary'
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def user_name(self, obj):
        return obj.user.name
    user_name.short_description = 'User Name'
    
    def formatted_ledger_balance(self, obj):
        amount = Decimal(str(obj.ledger_balance))
        formatted = f'₦{amount:,.2f}'
        return format_html('<strong>{}</strong>', formatted)
    formatted_ledger_balance.short_description = 'Ledger Balance'
    formatted_ledger_balance.admin_order_field = 'ledger_balance'
    
    def formatted_available_balance(self, obj):
        color = 'green' if obj.balance > 0 else 'red'
        amount = Decimal(str(obj.balance))
        formatted = f'₦{amount:,.2f}'
        return format_html('<span style="color: {};">{}</span>', color, formatted)
    formatted_available_balance.short_description = 'Available Balance'
    
    def formatted_locked_amount(self, obj):
        locked = obj.locked_amount
        if locked > 0:
            amount = Decimal(str(locked))
            formatted = f'₦{amount:,.2f}'
            return format_html('<span style="color: orange;">{}</span>', formatted)
        return '₦0.00'
    formatted_locked_amount.short_description = 'Locked Amount'
    
    def transaction_summary(self, obj):
        """Display transaction summary statistics"""
        transactions = obj.transactions.all()
        
        total_deposits = transactions.filter(type='deposit', status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
        total_withdrawals = transactions.filter(type='withdraw', status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
        total_payments = transactions.filter(type='payment', status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
        pending_count = transactions.filter(status='pending').count()
        
        deposits_fmt = f'₦{Decimal(str(total_deposits)):,.2f}'
        withdrawals_fmt = f'₦{Decimal(str(total_withdrawals)):,.2f}'
        payments_fmt = f'₦{Decimal(str(total_payments)):,.2f}'
        
        return format_html(
            '<div style="line-height: 1.8;">'
            '<strong>Total Deposits:</strong> {}<br>'
            '<strong>Total Withdrawals:</strong> {}<br>'
            '<strong>Total Payments:</strong> {}<br>'
            '<strong>Pending Transactions:</strong> {}'
            '</div>',
            deposits_fmt,
            withdrawals_fmt,
            payments_fmt,
            pending_count
        )
    transaction_summary.short_description = 'Transaction Summary'


@admin.register(Transaction, site=veyu_admin)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'transaction_type_badge',
        'sender_info',
        'recipient_info',
        'formatted_amount',
        'status_badge',
        'source',
        'tx_ref',
        'date_created',
    ]

    list_filter = (
        'type',
        'status',
        'source',
        'date_created',
    )
    
    search_fields = (
        'sender',
        'recipient',
        'tx_ref',
        'sender_wallet__user__email',
        'recipient_wallet__user__email',
        'narration',
    )
    
    readonly_fields = (
        'sender',
        'recipient',
        'sender_wallet',
        'recipient_wallet',
        'amount',
        'source',
        'type',
        'tx_ref',
        'narration',
        'date_created',
        'last_updated',
        'related_order',
        'related_booking',
        'related_inspection',
        'transaction_details'
    )
    
    date_hierarchy = 'date_created'
    
    def transaction_type_badge(self, obj):
        """Display transaction type with color coding"""
        colors = {
            'deposit': '#28a745',
            'withdraw': '#dc3545',
            'transfer_in': '#17a2b8',
            'transfer_out': '#ffc107',
            'charge': '#6c757d',
            'payment': '#007bff',
        }
        color = colors.get(obj.type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_type_display()
        )
    transaction_type_badge.short_description = 'Type'
    transaction_type_badge.admin_order_field = 'type'
    
    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'pending': '#ffc107',
            'completed': '#28a745',
            'failed': '#dc3545',
            'reversed': '#6c757d',
            'locked': '#fd7e14',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def sender_info(self, obj):
        """Display sender information"""
        if obj.sender_wallet:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.sender,
                obj.sender_wallet.user.email
            )
        return obj.sender or 'N/A'
    sender_info.short_description = 'Sender'
    
    def recipient_info(self, obj):
        """Display recipient information"""
        if obj.recipient_wallet:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.recipient,
                obj.recipient_wallet.user.email
            )
        return obj.recipient or 'N/A'
    recipient_info.short_description = 'Recipient'
    
    def formatted_amount(self, obj):
        """Display formatted amount with direction indicator"""
        amount = Decimal(str(obj.amount))
        formatted = f'₦{amount:,.2f}'
        if obj.type in ['deposit', 'transfer_in']:
            return format_html('<span style="color: green;">+{}</span>', formatted)
        elif obj.type in ['withdraw', 'transfer_out', 'payment', 'charge']:
            return format_html('<span style="color: red;">-{}</span>', formatted)
        return format_html('{}', formatted)
    formatted_amount.short_description = 'Amount'
    formatted_amount.admin_order_field = 'amount'
    
    def transaction_details(self, obj):
        """Display detailed transaction information"""
        details = f'<div style="line-height: 1.8;">'
        details += f'<strong>Transaction ID:</strong> {obj.id}<br>'
        details += f'<strong>Reference:</strong> {obj.tx_ref or "N/A"}<br>'
        details += f'<strong>Narration:</strong> {obj.narration}<br>'
        details += f'<strong>Direction:</strong> {obj.transaction_direction}<br>'
        details += f'<strong>Age:</strong> {obj.days_old} days<br>'
        
        if obj.related_order:
            details += f'<strong>Related Order:</strong> #{obj.related_order.id}<br>'
        if obj.related_booking:
            details += f'<strong>Related Booking:</strong> #{obj.related_booking.id}<br>'
        if obj.related_inspection:
            details += f'<strong>Related Inspection:</strong> #{obj.related_inspection.id}<br>'
        
        details += '</div>'
        return format_html(details)
    transaction_details.short_description = 'Transaction Details'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'sender_wallet__user',
            'recipient_wallet__user',
            'related_order',
            'related_booking',
            'related_inspection'
        )
    
    # Add custom actions
    actions = ['mark_as_completed', 'mark_as_failed']
    
    def mark_as_completed(self, request, queryset):
        """Mark selected transactions as completed"""
        updated = queryset.filter(status='pending').update(status='completed')
        self.message_user(request, f'{updated} transaction(s) marked as completed.')
    mark_as_completed.short_description = 'Mark selected as completed'
    
    def mark_as_failed(self, request, queryset):
        """Mark selected transactions as failed"""
        updated = queryset.filter(status='pending').update(status='failed')
        self.message_user(request, f'{updated} transaction(s) marked as failed.')
    mark_as_failed.short_description = 'Mark selected as failed'
