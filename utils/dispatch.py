import typing
from django.dispatch import Signal
from accounts.models import Account, Customer
from .sms import send_sms
from .mail import send_email

def handle_new_signup(sender:Account, is_customer=False, customer=Customer):
    # send_email()
    if is_customer:
        send_sms(
            message=f'Hi {sender.first_name}, welcome to Motaa, your verification code is {code}',
            recipient=customer.phone_number,
        )



    


user_just_registered = Signal(['is_customer'])
user_just_registered.connect(handle_new_signup, Account)



