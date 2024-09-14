from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models import F
from django.core.exceptions import ValidationError


User = get_user_model()

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def deposit(self, amount, reference=None):
        self.balance = F('balance') + amount
        self.save()
        Transaction.objects.create(wallet=self, type='deposit', amount=amount, reference=reference)
        return f'{amount} deposited to {self.user} wallet'

    def transfer(self, amount, recipient_wallet):
        if self.balance >= amount:
            with transaction.atomic():
                self.balance = F('balance') - amount
                recipient_wallet.deposit(amount)
                self.save()
                recipient_wallet.save()
                Transaction.objects.create(wallet=self, type='transfer', amount=amount, receiver=recipient_wallet.user)
                return True
        return False

    def withdraw(self, amount, transaction_status, account_details, reference):
        if self.balance >= amount:
            self.balance = F('balance') - amount
            self.save()
            Transaction.objects.create(wallet=self, type=f'withdrwal', amount=amount, status=transaction_status, recipient=account_details, reference=reference)

    
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
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=40, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, default='pending')

    def __str__(self):
        return f"{self.type} of {self.amount} on {self.timestamp.strftime('%H:%M:%S, %D-%M-%Y')}"
    







