"""
Transaction Analytics Module
Provides analytics and reporting for wallet transactions
"""
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Transaction, Wallet


class TransactionAnalytics:
    """
    Analytics service for transaction data
    """
    
    @staticmethod
    def get_transaction_summary(start_date=None, end_date=None):
        """
        Get overall transaction summary for a date range
        
        Args:
            start_date: Start date for filtering (default: 30 days ago)
            end_date: End date for filtering (default: now)
            
        Returns:
            dict: Transaction summary statistics
        """
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()
        
        transactions = Transaction.objects.filter(
            date_created__gte=start_date,
            date_created__lte=end_date
        )
        
        # Total transactions by type
        deposits = transactions.filter(type='deposit', status='completed')
        withdrawals = transactions.filter(type='withdraw', status='completed')
        payments = transactions.filter(type='payment', status='completed')
        transfers = transactions.filter(type__in=['transfer_in', 'transfer_out'], status='completed')
        
        # Calculate totals
        total_deposit_amount = deposits.aggregate(Sum('amount'))['amount__sum'] or 0
        total_withdrawal_amount = withdrawals.aggregate(Sum('amount'))['amount__sum'] or 0
        total_payment_amount = payments.aggregate(Sum('amount'))['amount__sum'] or 0
        total_transfer_amount = transfers.aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Transaction counts
        deposit_count = deposits.count()
        withdrawal_count = withdrawals.count()
        payment_count = payments.count()
        transfer_count = transfers.count()
        
        # Status breakdown
        pending_count = transactions.filter(status='pending').count()
        completed_count = transactions.filter(status='completed').count()
        failed_count = transactions.filter(status='failed').count()
        
        # Source breakdown
        bank_transactions = transactions.filter(source='bank', status='completed')
        wallet_transactions = transactions.filter(source='wallet', status='completed')
        
        bank_amount = bank_transactions.aggregate(Sum('amount'))['amount__sum'] or 0
        wallet_amount = wallet_transactions.aggregate(Sum('amount'))['amount__sum'] or 0
        
        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': (end_date - start_date).days
            },
            'totals': {
                'deposits': {
                    'count': deposit_count,
                    'amount': float(total_deposit_amount)
                },
                'withdrawals': {
                    'count': withdrawal_count,
                    'amount': float(total_withdrawal_amount)
                },
                'payments': {
                    'count': payment_count,
                    'amount': float(total_payment_amount)
                },
                'transfers': {
                    'count': transfer_count,
                    'amount': float(total_transfer_amount)
                }
            },
            'status': {
                'pending': pending_count,
                'completed': completed_count,
                'failed': failed_count
            },
            'sources': {
                'bank': {
                    'count': bank_transactions.count(),
                    'amount': float(bank_amount)
                },
                'wallet': {
                    'count': wallet_transactions.count(),
                    'amount': float(wallet_amount)
                }
            },
            'total_transaction_count': transactions.count(),
            'total_transaction_volume': float(
                (total_deposit_amount + total_withdrawal_amount + 
                 total_payment_amount + total_transfer_amount)
            )
        }
    
    @staticmethod
    def get_daily_transaction_stats(days=7):
        """
        Get daily transaction statistics for the last N days
        
        Args:
            days: Number of days to analyze (default: 7)
            
        Returns:
            list: Daily transaction statistics
        """
        from django.db.models.functions import TruncDate
        
        start_date = timezone.now() - timedelta(days=days)
        
        daily_stats = Transaction.objects.filter(
            date_created__gte=start_date,
            status='completed'
        ).annotate(
            date=TruncDate('date_created')
        ).values('date').annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            deposits=Count('id', filter=Q(type='deposit')),
            withdrawals=Count('id', filter=Q(type='withdraw')),
            payments=Count('id', filter=Q(type='payment'))
        ).order_by('date')
        
        return list(daily_stats)
    
    @staticmethod
    def get_top_users_by_transaction_volume(limit=10):
        """
        Get top users by transaction volume
        
        Args:
            limit: Number of users to return (default: 10)
            
        Returns:
            list: Top users with transaction statistics
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        wallets = Wallet.objects.annotate(
            total_transactions=Count('sent_transactions') + Count('received_transactions'),
            total_volume=Sum('sent_transactions__amount') + Sum('received_transactions__amount')
        ).select_related('user').order_by('-total_volume')[:limit]
        
        return [
            {
                'user_id': wallet.user.id,
                'user_email': wallet.user.email,
                'user_name': wallet.user.name,
                'balance': float(wallet.balance),
                'total_transactions': wallet.total_transactions,
                'total_volume': float(wallet.total_volume or 0)
            }
            for wallet in wallets
        ]
    
    @staticmethod
    def get_failed_transactions(days=7):
        """
        Get failed transactions for investigation
        
        Args:
            days: Number of days to look back (default: 7)
            
        Returns:
            QuerySet: Failed transactions
        """
        start_date = timezone.now() - timedelta(days=days)
        
        return Transaction.objects.filter(
            status='failed',
            date_created__gte=start_date
        ).select_related(
            'sender_wallet__user',
            'recipient_wallet__user'
        ).order_by('-date_created')
    
    @staticmethod
    def get_pending_transactions():
        """
        Get all pending transactions that need attention
        
        Returns:
            QuerySet: Pending transactions
        """
        return Transaction.objects.filter(
            status='pending'
        ).select_related(
            'sender_wallet__user',
            'recipient_wallet__user'
        ).order_by('-date_created')
    
    @staticmethod
    def get_wallet_statistics():
        """
        Get overall wallet statistics
        
        Returns:
            dict: Wallet statistics
        """
        wallets = Wallet.objects.all()
        
        total_wallets = wallets.count()
        total_balance = wallets.aggregate(Sum('ledger_balance'))['ledger_balance__sum'] or 0
        avg_balance = wallets.aggregate(Avg('ledger_balance'))['ledger_balance__avg'] or 0
        
        # Wallets with balance
        active_wallets = wallets.filter(ledger_balance__gt=0).count()
        
        # Top wallet balance
        top_wallet = wallets.order_by('-ledger_balance').first()
        
        return {
            'total_wallets': total_wallets,
            'active_wallets': active_wallets,
            'total_balance': float(total_balance),
            'average_balance': float(avg_balance),
            'top_wallet_balance': float(top_wallet.ledger_balance) if top_wallet else 0,
            'top_wallet_user': top_wallet.user.email if top_wallet else None
        }
    
    @staticmethod
    def get_transaction_success_rate(days=30):
        """
        Calculate transaction success rate
        
        Args:
            days: Number of days to analyze (default: 30)
            
        Returns:
            dict: Success rate statistics
        """
        start_date = timezone.now() - timedelta(days=days)
        
        transactions = Transaction.objects.filter(date_created__gte=start_date)
        
        total = transactions.count()
        completed = transactions.filter(status='completed').count()
        failed = transactions.filter(status='failed').count()
        pending = transactions.filter(status='pending').count()
        
        success_rate = (completed / total * 100) if total > 0 else 0
        failure_rate = (failed / total * 100) if total > 0 else 0
        
        return {
            'period_days': days,
            'total_transactions': total,
            'completed': completed,
            'failed': failed,
            'pending': pending,
            'success_rate': round(success_rate, 2),
            'failure_rate': round(failure_rate, 2)
        }
