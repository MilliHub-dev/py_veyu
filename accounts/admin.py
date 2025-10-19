from django.contrib import admin
from .models import (
    Account,
    Customer,
    Mechanic,
    Location,
    OTP,
    Dealer,
)
from utils.sms import send_sms
from utils.mail import send_email
from utils.admin import veyu_admin
from django.contrib.admin import AdminSite




class AccountsAdmin(admin.ModelAdmin):
    actions = [
        'send_test_sms',
        'send_test_email',
        'send_welcome_email',
    ]
    list_display = [
        'name',
        'email',
        'uuid',
        'user_type',
        'provider',
    ]
    list_display_links = [
        'name',
        'email',
        'uuid',
    ]

    def send_test_sms(self, request, queryset, *args, **kwargs):
        for account in queryset:
            if account.user_type == 'customer':
                send_sms(f"Hi {account.first_name}, welcome to veyu. \
                          \nYour verification code is 121-678 ", recipient=account.customer.phone_number)
            elif account.user_type == 'mechanic':
                print('User Phone Number:', account.mechanic.phone_number)
                send_sms(f"Hi {account.first_name}, welcome to veyu. \
                          \nYour verification code is 121-678 ", recipient=account.mechanic.phone_number)
        self.message_user(request, "Successfully sent sms")

    def send_welcome_email(self, request, queryset, *args, **kwargs):
        for account in queryset:
            send_email(
                subject="Welcome to veyu",
                context={'user': account},
                recipients=[account.email],
                template="utils/templates/welcome.html",
            )
        self.message_user(request, "Successfully sent welcome email")

    def send_test_email(self, request, queryset, *args, **kwargs):
        for account in queryset:
            send_email(
                subject="Welcome to veyu",
                context={'user': account},
                recipients=[account.email],
                template="utils/templates/email-confirmation.html",
            )
        self.message_user(request, "Successfully sent sms")


class OTPAdmin(admin.ModelAdmin):
    list_display_links = [
        'code'
    ]
    list_display = [
        'code',
        
    ]


# Register your models here.
veyu_admin.register(Account, AccountsAdmin)
veyu_admin.register(Customer)
veyu_admin.register(Mechanic)
veyu_admin.register(Location)
veyu_admin.register(Dealer)
veyu_admin.register(OTP, OTPAdmin)