"""
Revenue sharing models for inspection payments
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from utils.models import DbModel
from decimal import Decimal


class InspectionRevenueSettings(DbModel):
    """
    Configurable revenue sharing settings for inspection payments
    Admin can adjust dealer/platform split percentages
    """
    dealer_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=60.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of inspection fee that goes to the dealer (0-100)"
    )
    platform_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=40.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of inspection fee that goes to the platform (0-100)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only one settings record can be active at a time"
    )
    effective_date = models.DateTimeField(
        auto_now_add=True,
        help_text="When these settings became effective"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Admin notes about this revenue split configuration"
    )
    
    class Meta:
        verbose_name = 'Inspection Revenue Settings'
        verbose_name_plural = 'Inspection Revenue Settings'
        ordering = ['-effective_date']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['effective_date']),
        ]
    
    def clean(self):
        """Validate that percentages add up to 100"""
        super().clean()
        total = self.dealer_percentage + self.platform_percentage
        if total != 100:
            raise ValidationError(
                f'Dealer and platform percentages must add up to 100%. Current total: {total}%'
            )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        
        # If this is being set as active, deactivate all others
        if self.is_active:
            InspectionRevenueSettings.objects.filter(is_active=True).update(is_active=False)
        
        super().save(*args, **kwargs)
    
    @classmethod
    def get_active_settings(cls):
        """Get the currently active revenue settings"""
        settings = cls.objects.filter(is_active=True).first()
        if not settings:
            # Create default settings if none exist
            settings = cls.objects.create(
                dealer_percentage=60.00,
                platform_percentage=40.00,
                is_active=True,
                notes="Default revenue split settings"
            )
        return settings
    
    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"Revenue Split: {self.dealer_percentage}% Dealer / {self.platform_percentage}% Platform ({status})"
    
    def __repr__(self):
        return f"<InspectionRevenueSettings: {self.dealer_percentage}/{self.platform_percentage} - {self.is_active}>"


class InspectionRevenueSplit(DbModel):
    """
    Tracks revenue distribution for each inspection payment
    """
    inspection = models.OneToOneField(
        'inspections.VehicleInspection',
        on_delete=models.CASCADE,
        related_name='revenue_split'
    )
    payment_transaction = models.ForeignKey(
        'wallet.Transaction',
        on_delete=models.CASCADE,
        related_name='inspection_revenue_splits'
    )
    
    # Total amounts
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total inspection fee paid"
    )
    
    # Dealer share
    dealer_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount allocated to dealer wallet"
    )
    dealer_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Percentage used for dealer calculation"
    )
    dealer_credited = models.BooleanField(
        default=False,
        help_text="Whether dealer wallet has been credited"
    )
    dealer_credited_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When dealer wallet was credited"
    )
    
    # Platform share
    platform_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount retained by platform"
    )
    platform_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Percentage used for platform calculation"
    )
    
    # Settings snapshot
    revenue_settings = models.ForeignKey(
        InspectionRevenueSettings,
        on_delete=models.PROTECT,
        related_name='revenue_splits',
        help_text="Revenue settings used for this split"
    )
    
    class Meta:
        verbose_name = 'Inspection Revenue Split'
        verbose_name_plural = 'Inspection Revenue Splits'
        ordering = ['-date_created']
        indexes = [
            models.Index(fields=['inspection']),
            models.Index(fields=['payment_transaction']),
            models.Index(fields=['dealer_credited']),
            models.Index(fields=['date_created']),
        ]
    
    @classmethod
    def create_split(cls, inspection, payment_transaction):
        """
        Create revenue split for an inspection payment
        """
        from django.utils import timezone
        
        # Get active revenue settings
        settings = InspectionRevenueSettings.get_active_settings()
        
        # Calculate splits
        total_amount = payment_transaction.amount
        dealer_amount = (total_amount * settings.dealer_percentage) / Decimal('100')
        platform_amount = (total_amount * settings.platform_percentage) / Decimal('100')
        
        # Create split record
        split = cls.objects.create(
            inspection=inspection,
            payment_transaction=payment_transaction,
            total_amount=total_amount,
            dealer_amount=dealer_amount,
            dealer_percentage=settings.dealer_percentage,
            platform_amount=platform_amount,
            platform_percentage=settings.platform_percentage,
            revenue_settings=settings
        )
        
        # Credit dealer wallet immediately
        split.credit_dealer_wallet()
        
        return split
    
    def credit_dealer_wallet(self):
        """
        Credit the dealer's wallet with their share
        """
        from wallet.models import Wallet, Transaction
        from django.utils import timezone
        from django.db import transaction as db_transaction
        
        if self.dealer_credited:
            return False
        
        with db_transaction.atomic():
            # Get dealer's wallet
            dealer = self.inspection.dealer
            dealer_wallet, created = Wallet.objects.get_or_create(
                user=dealer.user,
                defaults={'currency': 'NGN'}
            )
            
            # Create credit transaction
            credit_transaction = Transaction.objects.create(
                sender='Veyu Platform',
                recipient=dealer.user.name,
                recipient_wallet=dealer_wallet,
                type='transfer_in',
                amount=self.dealer_amount,
                status='completed',
                source='wallet',
                narration=f'Inspection revenue share ({self.dealer_percentage}%) - Inspection #{self.inspection.id}',
                related_inspection=self.inspection
            )
            
            # Credit wallet
            dealer_wallet.ledger_balance += self.dealer_amount
            dealer_wallet.transactions.add(credit_transaction)
            dealer_wallet.save()
            
            # Mark as credited
            self.dealer_credited = True
            self.dealer_credited_at = timezone.now()
            self.save()
            
            return True
    
    def __str__(self):
        return f"Revenue Split: Inspection #{self.inspection.id} - ₦{self.total_amount:,.2f}"
    
    def __repr__(self):
        return f"<InspectionRevenueSplit: Inspection #{self.inspection.id} - Dealer: ₦{self.dealer_amount} / Platform: ₦{self.platform_amount}>"


class WithdrawalRequest(DbModel):
    """
    Tracks withdrawal requests from business accounts
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        related_name='withdrawal_requests'
    )
    wallet = models.ForeignKey(
        'wallet.Wallet',
        on_delete=models.CASCADE,
        related_name='withdrawal_requests'
    )
    
    # Withdrawal details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('100.00'))],
        help_text="Minimum withdrawal amount: ₦100"
    )
    
    # Bank account details (stored directly, verified with Paystack)
    account_name = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text="Account holder name (verified with Paystack)"
    )
    account_number = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text="Bank account number"
    )
    bank_name = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text="Bank name"
    )
    bank_code = models.CharField(
        max_length=10,
        blank=True,
        default='',
        help_text="Bank code for Paystack"
    )
    
    # Paystack verification
    paystack_verified = models.BooleanField(
        default=False,
        help_text="Whether account details were verified with Paystack"
    )
    paystack_recipient_code = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Paystack transfer recipient code"
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    transaction = models.ForeignKey(
        'wallet.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='withdrawal_request'
    )
    
    # Review information
    reviewed_by = models.ForeignKey(
        'accounts.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_withdrawals'
    )
    reviewed_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    
    # Processing information
    processed_at = models.DateTimeField(blank=True, null=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Withdrawal Request'
        verbose_name_plural = 'Withdrawal Requests'
        ordering = ['-date_created']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['wallet']),
            models.Index(fields=['status']),
            models.Index(fields=['date_created']),
        ]
    
    def clean(self):
        """Validate withdrawal request"""
        super().clean()
        
        # Check if user has sufficient balance
        if self.wallet and self.amount:
            if self.wallet.balance < self.amount:
                raise ValidationError(
                    f'Insufficient balance. Available: ₦{self.wallet.balance:,.2f}, Requested: ₦{self.amount:,.2f}'
                )
    
    def approve(self, admin_user):
        """Approve withdrawal request"""
        from django.utils import timezone
        
        if self.status != 'pending':
            raise ValidationError('Only pending requests can be approved')
        
        self.status = 'approved'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()
    
    def reject(self, admin_user, reason):
        """Reject withdrawal request"""
        from django.utils import timezone
        
        if self.status != 'pending':
            raise ValidationError('Only pending requests can be rejected')
        
        self.status = 'rejected'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save()
    
    def process_withdrawal(self):
        """Process approved withdrawal"""
        from wallet.models import Transaction
        from django.utils import timezone
        from django.db import transaction as db_transaction
        
        if self.status != 'approved':
            raise ValidationError('Only approved requests can be processed')
        
        with db_transaction.atomic():
            # Create withdrawal transaction
            withdrawal_transaction = Transaction.objects.create(
                sender=self.user.name,
                sender_wallet=self.wallet,
                recipient=f"{self.payout_info.account_name} - {self.payout_info.account_number}",
                type='withdraw',
                amount=self.amount,
                status='completed',
                source='bank',
                narration=f'Withdrawal to {self.payout_info.bank_name}',
                payout_info=self.payout_info
            )
            
            # Deduct from wallet
            self.wallet.ledger_balance -= self.amount
            self.wallet.transactions.add(withdrawal_transaction)
            self.wallet.save()
            
            # Update request
            self.transaction = withdrawal_transaction
            self.status = 'completed'
            self.processed_at = timezone.now()
            self.save()
            
            return withdrawal_transaction
    
    def __str__(self):
        return f"Withdrawal Request: {self.user.name} - ₦{self.amount:,.2f} to {self.bank_name} ({self.get_status_display()})"
    
    def __repr__(self):
        return f"<WithdrawalRequest: {self.user.email} - ₦{self.amount} - {self.bank_name} - {self.status}>"
