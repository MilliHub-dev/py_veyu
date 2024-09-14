from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, Group, PermissionsMixin
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import make_password
from utils.models import DbModel
from django.utils import timezone
from utils import make_random_otp


class AccountManager(BaseUserManager):

    def _create_user(self, email, password=None, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        
        return self._create_user(email, password, **extra_fields)


class Account(AbstractBaseUser, PermissionsMixin, DbModel):
    USER_TYPES = {
        'customer': 'Customer Account',
        'dealer': 'Car Dealer',
        'mech': 'Mechanic',
    }

    api_token = models.ForeignKey(Token, on_delete=models.SET_NULL, blank=True, null=True)
    image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=False, unique=True)
    verified_email = models.BooleanField(default=False)
    
    role = models.ForeignKey(Group, on_delete=models.SET_NULL, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    user_type = models.CharField(max_length=20, default='staff', choices=USER_TYPES)
    
    objects = AccountManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = 'email'

    def save(self, *args, **kwargs):
        if self.id and not self.api_token:
            self.api_token = Token.objects.get_or_create(user=self)[0]
        super().save(*args, **kwargs)

    @property
    def name(self):
        return f'{self.first_name} {self.last_name if self.last_name else ""}'


class UserProfile(DbModel):
    account = models.OneToOneField('Account', on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    wallet = models.OneToOneField('Wallet', on_delete=models.CASCADE, blank=True, null=True)
    payout_info = models.ManyToManyField('PayoutInformation', blank=True,)
    location = models.ForeignKey("Location", on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        abstract = True


class Customer(UserProfile):
    orders = models.ManyToManyField('rentals.Order', blank=True, related_name='orders')
    service_history = models.ManyToManyField('Service', blank=True)

    # primary_billing_info = models.ForeignKey("BillingInformation", blank=True, null=True, on_delete=models.CASCADE)
    # billing_info = models.ManyToManyField("BillingInformation", blank=True)

    def __str__(self):
        return self.account.name



class Mechanic(UserProfile):
    account = models.OneToOneField('Account', on_delete=models.CASCADE)
    available = models.BooleanField(default=True)
    services = models.ManyToManyField('Service', blank=True)
    current_job = models.ForeignKey('ServiceBooking', null=True, blank=True, on_delete=models.CASCADE, related_name='current_job')
    job_history = models.ManyToManyField('ServiceBooking', blank=True, related_name='job_history')
    ratings = models.ManyToManyField('feedback.Rating', blank=True, related_name='reviews')

    @property
    def avg_rating(self):
        return self.account.name


class Dealer(UserProfile):
    account = models.OneToOneField('Account', on_delete=models.CASCADE)
    listings = models.ManyToManyField('rentals.Listing', blank=True, related_name='listings')
    vehicles = models.ManyToManyField('rentals.Vehicle', blank=True, related_name='vehicles')
    # billing_info = models.ManyToManyField('PayoutInformation', blank=True, )
    ratings = models.ManyToManyField('feedback.Rating', blank=True, related_name='ratings')

    
class Wallet(DbModel):
    owner = models.ForeignKey('Account', on_delete=models.CASCADE)
    transactions = models.ManyToManyField("Transaction", blank=True)
    balance = models.DecimalField(max_digits=10000, decimal_places=2, blank=True, null=True)

    def withdraw(self, amt) -> bool:
        # return true if available balance >= amt
        return True
    
    @property
    def available_balance(self):
        return
    
    @property
    def pending_funds(self):
        return
    

class Transaction(DbModel):
    related_order = models.ForeignKey('rentals.Order', blank=True, null=True, on_delete=models.CASCADE)
    status = models.CharField(max_length=200, default='pending')
    amount = models.DecimalField(decimal_places=2, max_digits=10000)

class PayoutInformation(DbModel):
    channel = models.CharField(max_length=200, default='bank')
    bank_name = models.CharField(max_length=200)
    account_holder_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=10)

    def __str__(self) -> str:
        return f'{self.account_holder_name} @ {self.bank_name}'


class BillingInformation(DbModel):
    pass


class Location(DbModel):
    country = models.CharField(max_length=2, default='NG')
    state = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    zip_code = models.CharField(max_length=6, blank=True, null=True)
    added_by = models.ForeignKey('Account', on_delete=models.CASCADE)
    

class Service(DbModel):
    RATES = {
        'flat': 'Flat Rate', 
        'hourly': 'Hourly Rate', 
    }
    title = models.CharField(max_length=400, unique=True)
    description = models.TextField(max_length=1200, blank=True, null=True)
    charge = models.DecimalField(blank=True, null=True, max_digits=1000, decimal_places=2)
    charge_rate = models.CharField(default='flat', max_length=20, choices=RATES)


class ServiceBooking(DbModel):
    SERVICE_DELIVERY = {
        'emergency': 'Emergency Assistance',
        'routine': 'Routine Check',
    }
    mechanic = models.ForeignKey('Mechanic', on_delete=models.CASCADE)
    client_feedback = models.ForeignKey('feedback.Rating', blank=True, null=True, on_delete=models.SET_NULL)
    completed = models.BooleanField(default=False)
    service_delivery = models.CharField(max_length=20, default='routine', choices=SERVICE_DELIVERY)
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)



class OTP(DbModel):
    valid_for = models.ForeignKey('Account', on_delete=models.CASCADE)
    channel = models.CharField(max_length=10, default='email', choices={'email': 'Email', 'sms': 'SMS'})
    code = models.CharField(max_length=7, default=make_random_otp)
    used = models.BooleanField(default=False)

    def verify(self, code, channel):
        if self.code == code and self.channel == channel:
            self.delete()
            return True
        return False

    def __str__(self) -> str:
        return self.code

