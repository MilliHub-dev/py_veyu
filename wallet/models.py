from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models import F
from utils.models import DbModel
from django.core.exceptions import ValidationError
from djmoney.models.fields import MoneyField


User = get_user_model()

class Wallet(DbModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    # switching to normal decimal field, money field raises serialization errors
    # it's a debugging stress that is completely unnecessary
    # balance = MoneyField(max_digits=30, decimal_places=2, default=0.00, default_currency='NGN')
    balance = models.DecimalField(max_digits=100, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=4, default="NGN")
    transactions = models.ManyToManyField("wallet.Transaction", blank=True, related_name="transactions")
    
    def deposit(self, amount, type='deposit', reference=None):
        self.balance = F('balance') + amount
        self.save()
        Transaction.objects.create(wallet=self, type=type, amount=amount, reference=reference)
        return f'{amount} deposited to {self.user} wallet'

    def transfer(self, amount, recipient_wallet):
        if self.balance >= amount:
            new_transaction =  Transaction.objects.create(wallet=self, type='Transfer to', amount=amount, recipient=recipient_wallet.user.email, status='Pending')
            with transaction.atomic():
                try:
                    self.balance = F('balance') - amount
                    recipient_wallet.deposit(amount, type='Transfer from')
                    self.save()
                    recipient_wallet.save()
                    new_transaction.status = 'Completed'
                    new_transaction.save()
                    return True
                
                except Exception as e:
                    new_transaction.status = 'Failed'
                    new_transaction.save()
                    raise ValidationError(f"Failed to complete transaction: {str(e)}")
        else:
            raise ValidationError("Insufficient funds to complete this transaction.")
        return False
    
    def complete_order(self, amount, recipient_wallet):
        if self.balance >= amount:
            new_transaction = Transaction.objects.create(wallet=self, type='Order', amount=amount, recipient=recipient_wallet.user.email, status='Pending')
            with transaction.atomic():
                try:
                    self.balance = F('balance') - amount
                    recipient_wallet.deposit(amount, type='Payment for order')
                    self.save()
                    recipient_wallet.save()
                    new_transaction.status = 'Completed'
                    new_transaction.save()
                    return True
                except Exception as e:
                    new_transaction.status = 'Failed'
                    new_transaction.save()
                    raise ValidationError(f"Failed to complete transaction: {str(e)}")
        else:
            raise ValidationError("Insufficient funds to complete this transaction.")
        
        return False

    def withdraw(self, amount, transaction_status, account_details, reference):
        if self.balance >= amount:
            self.balance = F('balance') - amount
            self.save()
            Transaction.objects.create(wallet=self, type=f'Bank withdrwal', amount=amount, status=transaction_status, recipient=account_details, reference=reference)

    
    def __str__(self):
        return f"{self.user.email}"
    
    @receiver(post_save, sender=User)
    def create_user_wallet(sender, instance, created, **kwargs):
        if created:
            Wallet.objects.create(user=instance)


# Why do we need this again?
# Seems redundant and has no actual implementation
# Will remove before production
# Ask Spider first
class MotaaWalletEmail(models.Model):pass


class Transaction(DbModel):
    TRANSACTION_TYPES = {
        'deposit': 'Deposit',
        'transfer_in': 'Transfer In',
        'transfer_out': 'Transfer Out',
        'car_payment': 'Car Payment',
        'rental_payment': 'Rental Payment',
        'mechanic_payment': 'Mechanic Payment',
        'payment': 'Payment', # for system charges/services e.g premium sub
    }
    TRANSACTION_STATUS = {
        'pending': 'Pending',
        'reversed': 'Reversed',
        'completed': 'Completed',
        'failed': 'Failed',
    }
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='Transactions')
    type = models.CharField(max_length=30, choices=TRANSACTION_TYPES, default='deposit')
    recipient = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(max_digits=100, decimal_places=2, default=0.00) # currency is set in stone at wallet
    reference = models.CharField(max_length=40, null=True, blank=True)
    status = models.CharField(max_length=20, default='pending', choices=TRANSACTION_STATUS)

    def __str__(self):
        return f"{self.type} of {self.amount} on {self.date_created.strftime('%H:%M:%S, %D-%M-%Y')}"
    







