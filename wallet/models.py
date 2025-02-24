from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from utils.models import DbModel
from django.core.exceptions import ValidationError


User = get_user_model()

class Wallet(DbModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    ledger_balance = models.DecimalField(max_digits=100, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=4, default="NGN")
    transactions = models.ManyToManyField("wallet.Transaction", blank=True, related_name="transactions")
    
    @property
    def balance(self):
        # if there are locked transactions (ie awaiting escrow action)
        # do not allow the user withdraw funds from those transactions
        # return ledger balance for now
        amt = self.ledger_balance
        locked_trans = self.transactions.filter(status='locked')
        # for trans in locked_trans:
        #     if trans.wallet
        return amt

    def deposit(self, amount, type='deposit', reference=None):
        self.balance = F('balance') + amount
        self.save()
        Transaction.objects.create(wallet=self, type=type, amount=amount, reference=reference)
        return f'{amount} deposited to {self.user} wallet'


    def transfer(self, amount, recipient_wallet, narration=None):
        # for use between wallets
        # e.g paying for a car rental from your wallet
        if self.balance >= amount:
            sender_transaction =  Transaction.objects.create(
                sender=self.user.name,
                sender_wallet=self,
                recipient=recipient_wallet.user.name,
                recipient_wallet=recipient_wallet,
                type='transfer_out',
                status='pending',
                source='wallet',
                amount=amount,
            )

            recipient_transaction =  Transaction.objects.create(
                sender=self.user.name,
                sender_wallet=self,
                recipient=recipient_wallet.user.name,
                recipient_wallet=recipient_wallet,
                type='transfer_in',
                status='pending',
                source='wallet',
                amount=amount,
            )
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


    def withdraw(self, amount, payout_info, narration=None):
        if not narration:
            narration = f"Withdrwal to {payout_info.account_number}"
            Transaction.objects.create(
                sender='Me',
                wallet=self,
                type='transfer_out',
                amount=amount,
                status=transaction_status,
                recipient=account_details,
                narration=narration
            )

    
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
        'deposit': 'Deposit', # deposit into wallet from bank
        'withdraw': 'Withdraw', # withdrawing to bank
        'transfer_in': 'Transfer In', # a tranfer into the wallet
        'transfer_out': 'Transfer Out', # transfer to another wallet
        'charge': 'Wallet Charge', # for system charges/services e.g premium sub
        'payment': 'Payment', # payment for services/sale
    }
    TRANSACTION_STATUS = {
        'pending': 'Pending',
        'reversed': 'Reversed',
        'locked': 'Locked',
        'completed': 'Completed',
        'failed': 'Failed',
    }
    PAYMENT_SOURCES = {
        'wallet': 'Wallet', # user's wallet
        'bank': 'Bank' # card, bank transfer, ussd, etc
    }

    # defaluts to motaa, but can be 'me@gmail.com', 'Julien Namaste'
    sender = models.CharField(max_length=50, blank=True, null=True, default='Motaa')
    recipient = models.CharField(max_length=50, blank=True, null=True) # e.g Manga Auto's
    
    # optional when depositing, as transaction does not originate from the wallet.
    sender_wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, null=True, blank=True)
    
    # for internal transfers, optional when withdrawing
    recipient_wallet = models.ForeignKey('Wallet', null=True, blank=True, on_delete=models.CASCADE, related_name='recipient_wallet')
    amount = models.DecimalField(max_digits=100, decimal_places=2, default=0.00)
    
    source = models.CharField(max_length=20, default='bank', choices=PAYMENT_SOURCES)
    type = models.CharField(max_length=30, choices=TRANSACTION_TYPES, default='deposit')
    tx_ref = models.CharField(max_length=40, null=True, blank=True)
    status = models.CharField(max_length=20, default='pending', choices=TRANSACTION_STATUS)
    narration = models.CharField(max_length=200, default='Motaa Subscription')

    # selected payout info when withdrawing to local bank
    payout_info = models.ForeignKey('accounts.PayoutInformation', null=True, blank=True, on_delete=models.SET_NULL)

    # optional if not paying for a car, rental or service on motaa
    related_order = models.ForeignKey('listings.Order', blank=True, null=True, on_delete=models.CASCADE)
    related_booking = models.ForeignKey('bookings.ServiceBooking', blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.type} of {self.amount} on {self.date_created.strftime('%H:%M:%S, %D-%M-%Y')}"
    







