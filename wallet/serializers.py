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


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['user', 'balance']



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
