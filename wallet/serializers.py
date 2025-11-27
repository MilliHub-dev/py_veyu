from rest_framework import serializers 
from .models import Wallet, Transaction
from django.contrib.auth import get_user_model
from decimal import Decimal


User = get_user_model()

class TransferSerializer(serializers.Serializer):
    recipient = serializers.EmailField(required=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('100.00'))

    def validate_recipient(self, value):
        """
        Check that the recipient exists in the database.
        """
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Recipient not found")
        return value


class TransactionSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender', read_only=True)
    recipient_name = serializers.CharField(source='recipient', read_only=True)
    sender_email = serializers.SerializerMethodField()
    recipient_email = serializers.SerializerMethodField()
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    formatted_amount = serializers.CharField(read_only=True)
    transaction_direction = serializers.CharField(read_only=True)
    days_old = serializers.IntegerField(read_only=True)
    is_successful = serializers.BooleanField(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    
    # Related objects
    related_order_id = serializers.IntegerField(source='related_order.id', read_only=True, allow_null=True)
    related_booking_id = serializers.IntegerField(source='related_booking.id', read_only=True, allow_null=True)
    related_inspection_id = serializers.IntegerField(source='related_inspection.id', read_only=True, allow_null=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'sender_name',
            'sender_email',
            'recipient_name',
            'recipient_email',
            'amount',
            'formatted_amount',
            'type',
            'type_display',
            'status',
            'status_display',
            'source',
            'source_display',
            'tx_ref',
            'narration',
            'transaction_direction',
            'days_old',
            'is_successful',
            'is_pending',
            'date_created',
            'last_updated',
            'related_order_id',
            'related_booking_id',
            'related_inspection_id',
        ]
    
    def get_sender_email(self, obj):
        if obj.sender_wallet:
            return obj.sender_wallet.user.email
        return None
    
    def get_recipient_email(self, obj):
        if obj.recipient_wallet:
            return obj.recipient_wallet.user.email
        return None



class WalletSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    transactions = TransactionSerializer(many=True)

    class Meta:
        model = Wallet
        fields = ['user', 'ledger_balance', 'balance', 'currency', 'transactions', 'uuid']



class WalletBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['ledger_balance', 'balance', 'currency', 'id']



class InitiateDepositSerializer(serializers.Serializer):
    
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('100.00'))
    currency = serializers.CharField(max_length=3, default='NGN')
    gateway_name = serializers.CharField(max_length=11, default='flutterwave')

    

class ResolveAccountNumberSerializer(serializers.Serializer):
    account_number = serializers.CharField(max_length=10)
    bank_code = serializers.CharField(max_length=7)
    

class WithdrawalSerializer(serializers.Serializer):
    account_number = serializers.CharField(max_length=10)
    bank_code = serializers.CharField(max_length=7)
    account_name = serializers.CharField(max_length=50)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('100.00'))


class GetTranferFeeSerializer(serializers.Serializer):
    amount = serializers.CharField(max_length=6)



class WithdrawalRequestSerializer(serializers.Serializer):
    """Serializer for withdrawal request display"""
    id = serializers.IntegerField(read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Bank details (stored directly in withdrawal request)
    account_name = serializers.CharField(read_only=True)
    account_number = serializers.CharField(read_only=True)
    bank_name = serializers.CharField(read_only=True)
    bank_code = serializers.CharField(read_only=True)
    paystack_verified = serializers.BooleanField(read_only=True)
    
    # Review info
    reviewed_by_name = serializers.CharField(source='reviewed_by.name', read_only=True, allow_null=True)
    reviewed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    rejection_reason = serializers.CharField(read_only=True, allow_null=True)
    
    # Processing info
    processed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    payment_reference = serializers.CharField(read_only=True, allow_null=True)
    paystack_recipient_code = serializers.CharField(read_only=True, allow_null=True)
    transaction_id = serializers.IntegerField(source='transaction.id', read_only=True, allow_null=True)
    
    # Timestamps
    date_created = serializers.DateTimeField(read_only=True)
    last_updated = serializers.DateTimeField(read_only=True)


class WithdrawalRequestCreateSerializer(serializers.Serializer):
    """Serializer for creating withdrawal requests with Paystack verification"""
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('100.00'),
        error_messages={
            'min_value': 'Minimum withdrawal amount is ₦100.00'
        }
    )
    
    # Bank account details (verified with Paystack on frontend)
    account_name = serializers.CharField(
        max_length=200,
        help_text="Account holder name (verified with Paystack)"
    )
    account_number = serializers.CharField(
        max_length=20,
        help_text="Bank account number"
    )
    bank_name = serializers.CharField(
        max_length=200,
        help_text="Bank name"
    )
    bank_code = serializers.CharField(
        max_length=10,
        help_text="Bank code for Paystack"
    )
    
    # Paystack verification (set by frontend after verification)
    paystack_verified = serializers.BooleanField(
        default=False,
        help_text="Whether account was verified with Paystack"
    )
    
    def validate_amount(self, value):
        """Validate withdrawal amount against wallet balance"""
        wallet = self.context.get('wallet')
        if wallet and value > wallet.balance:
            raise serializers.ValidationError(
                f'Insufficient balance. Available: ₦{wallet.balance:,.2f}, Requested: ₦{value:,.2f}'
            )
        return value
    
    def validate_account_number(self, value):
        """Validate account number format"""
        # Remove any spaces or dashes
        clean_number = value.replace(' ', '').replace('-', '')
        
        # Check if it's numeric and has valid length (10 digits for Nigerian banks)
        if not clean_number.isdigit():
            raise serializers.ValidationError('Account number must contain only digits')
        
        if len(clean_number) != 10:
            raise serializers.ValidationError('Account number must be 10 digits')
        
        return clean_number
    
    def validate(self, data):
        """Cross-field validation"""
        # Recommend Paystack verification (but don't enforce to allow flexibility)
        if not data.get('paystack_verified'):
            # Add a warning but don't fail validation
            data['_warning'] = 'Account details not verified with Paystack. Verification recommended.'
        
        return data
    
    def create(self, validated_data):
        """Create withdrawal request"""
        from inspections.models_revenue import WithdrawalRequest
        
        # Remove warning if present
        validated_data.pop('_warning', None)
        
        return WithdrawalRequest.objects.create(
            user=validated_data['user'],
            wallet=validated_data['wallet'],
            amount=validated_data['amount'],
            account_name=validated_data['account_name'],
            account_number=validated_data['account_number'],
            bank_name=validated_data['bank_name'],
            bank_code=validated_data['bank_code'],
            paystack_verified=validated_data.get('paystack_verified', False),
            status='pending'
        )
