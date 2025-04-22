import typing
from django.dispatch import Signal, receiver
from accounts.models import (Account, Customer, )
from feedback.models import Notification
from .sms import send_sms
from .mail import send_email
from django.dispatch import Signal, receiver
import threading

otp_requested = Signal()
on_booking_requested = Signal()
on_checkout_success = Signal(['listing', 'customer'])
on_inspection_created = Signal()
on_listing_created = Signal()
on_wallet_deposit = Signal()
user_just_registered = Signal(['otp'])


@receiver(on_wallet_deposit)
def create_notification(sender, **kwargs):
    # create a notification
    # send an email of the receipt from motaa
    user = sender
    notification = Notification(
        user=user,
        subject="Deposit Received!",
        message=f"You've added {kwargs['wallet'].currency} {kwargs['amount']} to your wallet.",
        level='success',
    )
    notification.save()


@receiver(on_listing_created)
def notify_motaa_staff_of_listing_creation(sender, **kwargs):
    # in the future, add this to a shelf db
    # and use celery to run this function after
    # 30 mins to catch bulk listings
    try:
        threading.Thread(
            target=send_email,
            kwargs={
                'message':'<b> Someone just added a new listing that needs approval. </b> ',
                'recipients':[user.email for user in Account.objects.filter(is_superuser=True)],
                'subject':"New Listing on Motaa!",
            }
        ).start()
    except Exception as error:
        print("Couldn't notify staff of listing.")



@receiver(on_inspection_created)
def handle_inspection_created(sender, **kwargs):
    customer = sender
    notification = Notification(
        user=customer.user,
        subject="Inspection Scheduled!",
        message=f"You've Scheduled an inpection for your car on {kwargs['date']} by {kwargs['time']}",
        level='success',
    )
    notification.save()


@receiver(otp_requested)
def handle_otp_requested(sender, user, otp, **kwargs):
    if sender == 'email':
        threading.Thread(
            target=send_email,
            kwargs={
                'template':'utils/templates/email-confirmation.html',
                'recipients':[user.email],
                'context':{'code': otp.code, 'user': user},
                'subject':"Motaa Verification",
            }
        ).start()
        # send_email(
        #     template='utils/templates/email-confirmation.html',
        #     recipients=[user.email],
        #     context={'code': otp.code, 'user': user},
        #     subject="Motaa Verification",
        # )
    elif sender == 'sms':
        profile = None
        if user.user_type == 'customer':
            profile = user.customer
        if user.user_type == 'dealer':
            profile = user.dealer
        if user.user_type == 'mechanic':
            profile = user.mechanic
        send_sms(
            message=f"Hi {user.name}, your Motaa authentication code is {otp.code}. \n \
             Do not share this code with anyone!",
            recipient=profile.phone_number
        )


@receiver(on_checkout_success)
def handle_checkout_success(sender, listing, customer, **kwargs):
    dealer = listing.vehicle.dealer

    def send_sales_email():pass

    def send_customer_notification():
        notification = Notification(
            user=customer.user,
            subject="Congrats on your new purchase!",
            message="You just bought a new car!",
            level='success',
        )
        notification.save()
    send_customer_notification()


def handle_new_signup(sender:Account, otp, **kwargs):
    send_email(
        subject="Motaa Verification: Confirm your Email address",
        recipients=[sender.email],
        context={'user': sender, 'code': otp.code},
        template='utils/templates/email-confirmation.html'
    )


def handle_phone_number_changed(sender:Account, otp):
    send_sms(
        message=f'Hi {sender.first_name}, welcome to Motaa, your verification code is {otp.code}',
        recipient=sender.phone_number,
    )



