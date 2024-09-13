import typing
from django.dispatch import Signal
from accounts.models import Account, Customer
from .sms import send_sms
from .mail import send_email

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



    


user_just_registered = Signal(['otp'])



