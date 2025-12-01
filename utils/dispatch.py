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
user_just_registered = Signal()


@receiver(on_booking_requested)
def handle_booking_request(sender, **kwargs):
    # create a notification for mechanics and customers
    customer = kwargs['customer']
    mechanic = kwargs['mechanic']
    services = kwargs['services']
    
    # Format services list
    services_text = ', '.join(service for service in services) if services else 'service'
    
    # Customer notification
    user_notification = Notification(
        user=customer.user,
        subject="Service Booking Confirmed",
        message=f"Your booking with {mechanic.user.name or 'mechanic'} for {services_text} has been confirmed. They will contact you shortly.",
        level='success',
        cta_text='View Booking',
        cta_link='/bookings'
    )
    user_notification.save()

    # Mechanic notification
    mech_notification = Notification(
        user=mechanic.user,
        subject="New Service Booking",
        message=f"{customer.user.name or 'A customer'} has booked you for {services_text}. Please review the booking details and contact the customer.",
        level='info',
        cta_text='View Booking',
        cta_link='/bookings'
    )
    mech_notification.save()

    threading.Thread(
        target=send_email,
        kwargs={
            'subject':"Booking Request Sent!",
            'template':'utils/templates/new_booking.html',
            'context': {
                'booking': sender,
                'customer': kwargs['customer'],
                'mechanic': kwargs['mechanic'],
                'services': kwargs['services']
            },
            'recipients':[
                kwargs['customer'].user.email,
                kwargs['mechanic'].user.email,
                '7thogofe@gmail.com',
            ],
        }
    ).start()



@receiver(on_wallet_deposit)
def handle_wallet_deposit(sender, **kwargs):
    # create a notification
    # send an email of the receipt from veyu
    user = sender
    wallet = kwargs['wallet']
    amount = kwargs['amount']
    
    # Format amount with currency symbol
    currency_symbol = '₦' if wallet.currency == 'NGN' else wallet.currency
    formatted_amount = f"{currency_symbol}{amount:,.2f}"
    
    notification = Notification(
        user=user,
        subject="Wallet Funded Successfully",
        message=f"Your wallet has been credited with {formatted_amount}. Your new balance is {currency_symbol}{wallet.balance:,.2f}.",
        level='success',
        cta_text='View Wallet',
        cta_link='/wallet'
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
                'subject':"New Listing on veyu!",
            }
        ).start()
    except Exception as error:
        print("Couldn't notify staff of listing.")



@receiver(on_inspection_created)
def handle_inspection_created(sender, **kwargs):
    customer = sender
    # Format the date and time for better readability
    from datetime import datetime
    try:
        date_obj = datetime.strptime(kwargs['date'], '%Y-%m-%d')
        formatted_date = date_obj.strftime('%B %d, %Y')
    except:
        formatted_date = kwargs['date']
    
    notification = Notification(
        user=customer.user,
        subject="Vehicle Inspection Scheduled",
        message=f"Your vehicle inspection has been scheduled for {formatted_date} at {kwargs['time']}. The inspector will contact you before the appointment.",
        level='info',
        cta_text='View Details',
        cta_link='/inspections'
    )
    notification.save()


@receiver(otp_requested)
def handle_otp_requested(sender, **kwargs):
    user = kwargs['user']
    otp = kwargs['otp']

    if sender == 'email':
        threading.Thread(
            target=send_email,
            kwargs={
                'template':'utils/templates/email-confirmation.html',
                'recipients':[user.email],
                'context':{'code': otp.code, 'user': user},
                'subject':"Veyu Verification",
            }
        ).start()
        # send_email(
        #     template='utils/templates/email-confirmation.html',
        #     recipients=[user.email],
        #     context={'code': otp.code, 'user': user},
        #     subject="Veyu Verification",
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
            message=f"Hi {user.name}, your veyu authentication code is {otp.code}. \n \
             Do not share this code with anyone!",
            recipient=profile.phone_number
        )


@receiver(on_checkout_success)
def handle_checkout_success(sender, listing, customer, **kwargs):
    dealer = listing.vehicle.dealer

    def send_sales_email():pass

    def send_customer_notification():
        # Get vehicle details for better notification
        vehicle_name = listing.vehicle.name if hasattr(listing, 'vehicle') else 'vehicle'
        listing_type = listing.get_listing_type_display() if hasattr(listing, 'get_listing_type_display') else listing.listing_type
        
        if listing.listing_type == 'sale':
            subject = "Order Placed Successfully!"
            message = f"Your order for {vehicle_name} has been placed. You'll receive an inspection appointment confirmation shortly."
            cta_text = "View Order"
        else:  # rental
            subject = "Rental Booking Confirmed!"
            message = f"Your rental booking for {vehicle_name} has been confirmed. Check your email for details."
            cta_text = "View Booking"
        
        notification = Notification(
            user=customer.user,
            subject=subject,
            message=message,
            level='success',
            cta_text=cta_text,
            cta_link='/orders'
        )
        notification.save()
    send_customer_notification()

@receiver(user_just_registered)
def handle_welcome_new_signup(sender:Account, **kwargs):
    send_email(
        subject="Welcome To veyu",
        recipients=[sender.email],
        context={'user': sender},
        template='utils/templates/welcome.html'
    )


def handle_phone_number_changed(sender:Account, otp):
    send_sms(
        message=f'Hi {sender.first_name}, welcome to veyu, your verification code is {otp.code}',
        recipient=sender.phone_number,
    )



