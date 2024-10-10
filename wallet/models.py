from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models import F
from django.core.exceptions import ValidationError
from djmoney.models.fields import MoneyField


User = get_user_model()

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = MoneyField(max_digits=30, decimal_places=2, default=0.00, default_currency='NGN')
    
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

class MotaaWalletEmail(models.Model):
    wallet_email = models.EmailField(unique=True)

    def clean(self):
        if not self.pk and MotaaWalletEmail.objects.exists():
            raise ValidationError('There can be only one MotaaWalletEmail instance')
        
                # Check if the email exists in the User table
        try:
            user = User.objects.get(email=self.wallet_email)
        except User.DoesNotExist:
            raise ValidationError('The email does not exist in the User table')

        # Check if the user is an admin
        if not user.is_staff:
            raise ValidationError('The email does not belong to an admin user')

    def save(self, *args, **kwargs):
        self.clean()
        return super(MotaaWalletEmail, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.wallet_email 

class Transaction(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='Transactions')
    type = models.CharField(max_length=30)
    recipient = models.CharField(max_length=100, null=True)
    amount = MoneyField(max_digits=30, decimal_places=2, default=0.00, default_currency='NGN')
    reference = models.CharField(max_length=40, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, default='pending')

    def __str__(self):
        return f"{self.type} of {self.amount} on {self.timestamp.strftime('%H:%M:%S, %D-%M-%Y')}"
    







