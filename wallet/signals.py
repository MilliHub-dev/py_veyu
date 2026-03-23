from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from feedback.models import create_and_send_user_notifications

from .models import Transaction


@receiver(pre_save, sender=Transaction)
def transaction_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_status = None
        return

    try:
        old_instance = Transaction.objects.get(pk=instance.pk)
        instance._old_status = old_instance.status
    except Transaction.DoesNotExist:
        instance._old_status = None


@receiver(post_save, sender=Transaction)
def transaction_post_save(sender, instance, created, **kwargs):
    became_completed = instance.status == 'completed' and (
        created or getattr(instance, '_old_status', None) != 'completed'
    )
    if not became_completed:
        return

    notified_users = set()

    sender_user = getattr(getattr(instance, 'sender_wallet', None), 'user', None)
    recipient_user = getattr(getattr(instance, 'recipient_wallet', None), 'user', None)
    related_user = (
        getattr(getattr(instance, 'related_order', None), 'customer', None)
        or getattr(getattr(instance, 'related_booking', None), 'customer', None)
        or getattr(getattr(instance, 'related_inspection', None), 'customer', None)
    )
    related_user = getattr(related_user, 'user', None)

    type_messages = {
        'deposit': ("Wallet Deposit Successful", f"Your wallet has been credited with ₦{instance.amount:,.2f}.", 'success', '/wallet'),
        'withdraw': ("Withdrawal Processed", f"Your withdrawal of ₦{instance.amount:,.2f} has been processed.", 'success', '/wallet/transactions'),
        'transfer_in': ("Money Received", f"You received ₦{instance.amount:,.2f} in your wallet.", 'success', '/wallet/transactions'),
        'transfer_out': ("Transfer Successful", f"You sent ₦{instance.amount:,.2f} from your wallet.", 'success', '/wallet/transactions'),
        'payment': ("Payment Successful", f"Your payment of ₦{instance.amount:,.2f} was completed successfully.", 'success', '/wallet/transactions'),
        'charge': ("Wallet Charge Recorded", f"A charge of ₦{instance.amount:,.2f} has been recorded on your wallet.", 'warning', '/wallet/transactions'),
    }

    subject, message, level, cta_link = type_messages.get(
        instance.type,
        ("Transaction Update", f"Your transaction of ₦{instance.amount:,.2f} has been completed.", 'info', '/wallet/transactions'),
    )

    if sender_user:
        create_and_send_user_notifications(
            user=sender_user,
            subject=subject,
            message=message,
            level=level,
            cta_text='View Transaction',
            cta_link=cta_link,
        )
        notified_users.add(sender_user.pk)

    if recipient_user and recipient_user.pk not in notified_users:
        recipient_subject = "Wallet Credit Received" if instance.type in ['deposit', 'transfer_in'] else "Transaction Update"
        recipient_message = (
            f"You received ₦{instance.amount:,.2f} in your wallet."
            if instance.type in ['deposit', 'transfer_in']
            else f"A transaction of ₦{instance.amount:,.2f} has been completed for your wallet."
        )
        create_and_send_user_notifications(
            user=recipient_user,
            subject=recipient_subject,
            message=recipient_message,
            level='success',
            cta_text='View Transaction',
            cta_link='/wallet/transactions',
        )
        notified_users.add(recipient_user.pk)

    if related_user and related_user.pk not in notified_users:
        create_and_send_user_notifications(
            user=related_user,
            subject=subject,
            message=message,
            level=level,
            cta_text='View Transaction',
            cta_link=cta_link,
        )
