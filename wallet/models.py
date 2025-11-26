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
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_wallet')
    ledger_balance = models.DecimalField(max_digits=100, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=4, default="NGN")
    transactions = models.ManyToManyField("wallet.Transaction", blank=True, related_name="wallet_transactions")
    
    @property
    def balance(self):
        # if there are locked transactions (ie awaiting escrow action)
        # do not allow the user withdraw funds from those transactions
        # return ledger balance for now
        amt = self.ledger_balance
        locked_trans = self.transactions.filter(status__in=['locked', 'pending', ])
        for trans in locked_trans:
            amt -= trans.amount
        return amt

    def apply_transaction(self, trans):
        if trans.type in ['payment', 'charge', 'transfer_out', 'withdraw']:
            self.ledger_balance -= trans.amount7
        elif trans.type in ['transfer_in', 'deposit']:
            self.ledger_balance += trans.amount
        self.transactions.add(trans,)
        self.save()
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
        return f"{self.user.name}'s Wallet - {self.currency} {self.ledger_balance:,.2f} (Available: {self.balance:,.2f})"
    
    def __repr__(self):
        return f"<Wallet: {self.user.email} - {self.currency} {self.ledger_balance}>"
    
    @property
    def formatted_balance(self):
        """Returns formatted available balance"""
        return f"{self.currency} {self.balance:,.2f}"
    
    @property
    def formatted_ledger_balance(self):
        """Returns formatted ledger balance"""
        return f"{self.currency} {self.ledger_balance:,.2f}"
    
    @property
    def total_transactions(self):
        """Returns total number of transactions"""
        return self.transactions.count()
    
    @property
    def locked_amount(self):
        """Returns amount locked in pending transactions"""
        return self.ledger_balance - self.balance
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['currency']),
        ]
        ordering = ['-date_created']
        verbose_name = 'Wallet'
        verbose_name_plural = 'Wallets'
    
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

    # defaluts to veyu, but can be 'me@gmail.com', 'Julien Namaste'
    sender = models.CharField(max_length=50, blank=True, null=True, default='Veyu')
    recipient = models.CharField(max_length=50, blank=True, null=True) # e.g Manga Auto's
    
    # optional when depositing, as transaction does not originate from the wallet.
    sender_wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_transactions')
    
    # for internal transfers, optional when withdrawing
    recipient_wallet = models.ForeignKey('Wallet', null=True, blank=True, on_delete=models.CASCADE, related_name='received_transactions')
    amount = models.DecimalField(max_digits=100, decimal_places=2, default=0.00)
    
    source = models.CharField(max_length=20, default='bank', choices=PAYMENT_SOURCES)
    type = models.CharField(max_length=30, choices=TRANSACTION_TYPES, default='deposit')
    tx_ref = models.CharField(max_length=40, null=True, blank=True)
    status = models.CharField(max_length=20, default='pending', choices=TRANSACTION_STATUS)
    narration = models.CharField(max_length=200, default='Veyu Subscription')

    # selected payout info when withdrawing to local bank
    payout_info = models.ForeignKey('accounts.PayoutInformation', null=True, blank=True, on_delete=models.SET_NULL, related_name='payout_transactions')

    # optional if not paying for a car, rental or service on veyu
    related_order = models.ForeignKey('listings.Order', blank=True, null=True, on_delete=models.CASCADE, related_name='order_transactions')
    related_booking = models.ForeignKey('bookings.ServiceBooking', blank=True, null=True, on_delete=models.CASCADE, related_name='booking_transactions')
    related_inspection = models.ForeignKey('inspections.VehicleInspection', blank=True, null=True, on_delete=models.CASCADE, related_name='inspection_transactions')

    def __str__(self):
        return f"{self.get_type_display()}: ₦{self.amount:,.2f} - {self.get_status_display()} ({self.date_created.strftime('%d/%m/%Y %H:%M')})"
    
    def __repr__(self):
        return f"<Transaction: {self.type} - ₦{self.amount} - {self.status}>"
    
    @property
    def formatted_amount(self):
        """Returns formatted transaction amount"""
        return f"₦{self.amount:,.2f}"
    
    @property
    def is_successful(self):
        """Check if transaction was successful"""
        return self.status == 'completed'
    
    @property
    def is_pending(self):
        """Check if transaction is pending"""
        return self.status == 'pending'
    
    @property
    def days_old(self):
        """Returns days since transaction"""
        return (now().date() - self.date_created.date()).days
    
    @property
    def transaction_direction(self):
        """Returns transaction direction (incoming/outgoing)"""
        if self.type in ['deposit', 'transfer_in']:
            return "Incoming"
        elif self.type in ['withdraw', 'transfer_out', 'payment', 'charge']:
            return "Outgoing"
        else:
            return "Unknown"
    
    class Meta:
        indexes = [
            models.Index(fields=['sender_wallet']),
            models.Index(fields=['recipient_wallet']),
            models.Index(fields=['type']),
            models.Index(fields=['status']),
            models.Index(fields=['source']),
            models.Index(fields=['date_created']),
            models.Index(fields=['tx_ref']),
        ]
        ordering = ['-date_created']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
    







