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
