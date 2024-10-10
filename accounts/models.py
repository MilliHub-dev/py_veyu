from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, Group, PermissionsMixin
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import make_password
from utils.models import DbModel
from django.utils import timezone
from django.utils.timesince import timeuntil, timesince
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
        'admin': 'Admin',
        'staff': 'Agent',
        'customer': 'Customer',
        'dealer': 'Car Dealer',
        'mechanic': 'Mechanic',
    }

    email = models.EmailField(blank=False, unique=True)
    first_name = models.CharField(max_length=150, blank=False)
    last_name = models.CharField(max_length=150, blank=False)
    phone_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    verified_email = models.BooleanField(default=False)
    
    groups = None
    user_permissions = None

    role = models.ForeignKey(Group, on_delete=models.SET_NULL, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    user_type = models.CharField(max_length=20, null=False)
    
    objects = AccountManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = 'email'

    @property
    def name(self):
        return f'{self.first_name} {self.last_name if self.last_name else ""}'

    @property
    def last_seen(self):
        if self.last_login:
            return timesince(self.last_login)
        return None



class UserProfile(DbModel):
    phone_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    verified_phone_number = models.BooleanField(default=False)
    verified_email = models.BooleanField(default=False)
    payout_info = models.ManyToManyField('PayoutInformation', blank=True,)
    location = models.ForeignKey("Location", on_delete=models.SET_NULL, blank=True, null=True)
    reviews = models.ManyToManyField('feedback.Rating', blank=True)

<<<<<<< HEAD
    def __str__(self) -> str:
        return self.account.name

    @classmethod
    def me(cls, obj_id):
        obj = None
        try:
            obj = cls.objects.get(uuid=obj_id)
        except:
            obj = cls.objects.get(id=obj_id)
        finally:
            return obj
        


    @property
    def rating(self):
        return self.account.name

=======
    def verify_phone_number(self):
        self.verified_phone_number = True
        self.save() 
        return True
    
    def verify_email(self):
        self.verified_email = True
        self.save() 
        return True

    
>>>>>>> 37fbae9c0eca9fbcb78f038b374d72b0561c286a
    class Meta:
        abstract = True



class Customer(UserProfile):
<<<<<<< HEAD
    orders = models.ManyToManyField('rentals.Order', blank=True, related_name='orders')
    service_history = models.ManyToManyField('bookings.ServiceBooking', blank=True, related_name='service_history')

    # primary_billing_info = models.ForeignKey("BillingInformation", blank=True, null=True, on_delete=models.CASCADE)
    # billing_info = models.ManyToManyField("BillingInformation", blank=True)
=======
    user = models.OneToOneField(Account, on_delete=models.CASCADE, related_name='customer')
    
>>>>>>> 37fbae9c0eca9fbcb78f038b374d72b0561c286a

    def __str__(self):
        return self.user.email



class Mechanic(UserProfile):
    user = models.OneToOneField(Account, on_delete=models.CASCADE, related_name='mechanic')
    available = models.BooleanField(default=True)
    services = models.ManyToManyField('bookings.ServiceOffering', blank=True)
    current_job = models.ForeignKey('bookings.ServiceBooking', null=True, blank=True, on_delete=models.CASCADE, related_name='current_job')
    job_history = models.ManyToManyField('bookings.ServiceBooking', blank=True, related_name='job_history')

<<<<<<< HEAD
    def __str__(self) -> str:
        return self.account.name
=======
    def __str__(self):
        return f'{self.user.email} {self.user.first_name} {self.user.last_name}'

    @property
    def avg_rating(self):
        return self.user.email
>>>>>>> 37fbae9c0eca9fbcb78f038b374d72b0561c286a

class Dealer(UserProfile):
    user = models.OneToOneField(Account, on_delete=models.CASCADE, related_name='dealer')
    listings = models.ManyToManyField('rentals.Listing', blank=True, related_name='listings')
    vehicles = models.ManyToManyField('rentals.Vehicle', blank=True, related_name='vehicles')
    ratings = models.ManyToManyField('feedback.Rating', blank=True, related_name='ratings')

    def __str__(self):
        return self.user.email

<<<<<<< HEAD
=======
    
class Agent(UserProfile):
    user = models.OneToOneField(Account, on_delete=models.CASCADE, related_name='agent')

    def __str__(self):
        return self.user.email
    
>>>>>>> 37fbae9c0eca9fbcb78f038b374d72b0561c286a

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
    user = models.ForeignKey('Account', on_delete=models.CASCADE)
    country = models.CharField(max_length=2, default='NG')
    state = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    zip_code = models.CharField(max_length=6, blank=True, null=True)
    # added_by = models.ForeignKey('Account', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.country}' +', '+ f'{self.state}' 



class OTP(DbModel):
    valid_for = models.ForeignKey('Account', on_delete=models.CASCADE)
    code = models.CharField(max_length=7, default=make_random_otp)
    used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'One Time Pin (OTP)'
        verbose_name_plural = 'One Time Pins (OTPs)'

    def verify(self, code, channel):
        if self.code == code:
            self.used = True

            user_profile = (
                Customer.objects.get(user=self.valid_for) or
                Mechanic.objects.get(user=self.valid_for) or
                Dealer.objects.get(user=self.valid_for) or
                Agent.objects.get(user=self.valid_for)
            )
            if channel == 'sms':
                user_profile.verify_phone_number()

            if channel == 'email':
                user_profile.verify_email()
            self.delete()
            return True
        return False

    def __str__(self) -> str:
        return self.code

