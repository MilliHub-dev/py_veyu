from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, Group, PermissionsMixin
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import make_password
from utils.models import DbModel
from django.utils import timezone
from django.utils.timesince import timeuntil, timesince
from utils import make_random_otp
from django.db.models.signals import post_save
from django.dispatch import receiver

class AccountManager(BaseUserManager):

    def _create_user(self, email, password=None, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if extra_fields.get('provider', 'motaa') == 'motaa':
            user.password = make_password(password)
        else:
            user.set_unusable_password()
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
        'staff': 'Staff / Agent',
        'customer': 'Customer',
        'dealer': 'Car Dealer',
        'mechanic': 'Mechanic',
    }

    # for OAuth
    ACCOUNT_PROVIDERS = {
        'motaa': 'Motaa',
        'google': 'Google',
        'facebook': 'Facebook',
        'apple': 'Apple',
    }

    email = models.EmailField(blank=False, unique=True)
    first_name = models.CharField(max_length=150, blank=False)
    last_name = models.CharField(max_length=150, blank=False)
    role = models.ForeignKey(Group, on_delete=models.SET_NULL, blank=True, null=True)
    verified_email = models.BooleanField(default=False)
    api_token = models.ForeignKey('authtoken.Token', blank=True, null=True, on_delete=models.SET_NULL)
    provider = models.CharField(max_length=20, choices=ACCOUNT_PROVIDERS, default='motaa')

    groups = None
    user_permissions = None

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    user_type = models.CharField(max_length=20, default='customer', choices=USER_TYPES)

    objects = AccountManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = 'email'

    def save(self, *args, **kwargs):
        if not self.api_token:
            super().save(using=None)
            self.api_token = Token.objects.get_or_create(user=self)[0]
        super().save(*args, **kwargs)

    @property
    def token(self):
        return self.api_token.key

    def verify_email(self):
        self.verified_email = True
        self.save()
        return True

    @property
    def name(self):
        return f'{self.first_name} {self.last_name if self.last_name else ""}'

    @property
    def last_seen(self):
        if self.last_login:
            return timesince(self.last_login)
        return None


class UserProfile(DbModel):
    ID_TYPES = [
        ('nin', 'National Identification'),
        ('drivers-license', 'National Identification'),
        ('voters-card', 'National Identification'),
        ('passport', 'National Identification'),
    ]
    user = models.OneToOneField(Account, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    id_type = models.CharField(max_length=200, default='nin', choices=ID_TYPES, blank=True, null=True)
    verified_phone_number = models.BooleanField(default=False)
    verified_id = models.BooleanField(default=False)
    payout_info = models.ManyToManyField('PayoutInformation', blank=True,)
    location = models.ForeignKey("Location", on_delete=models.SET_NULL, blank=True, null=True)
    documents = models.ManyToManyField('Document', blank=True)
    # primary_billing_info = models.ForeignKey("BillingInformation", blank=True, null=True, on_delete=models.CASCADE)
    billing_info = models.ManyToManyField("BillingInformation", blank=True)


    def __str__(self) -> str:
        return self.user.name

    @classmethod
    def me(cls, obj_id):
        obj = None
        try:
            obj = cls.objects.get(uuid=obj_id)
        except:
            obj = cls.objects.get(id=obj_id)
        finally:
            return obj


    def verify_phone_number(self):
        self.verified_phone_number = True
        self.save()
        return True

    @property
    def verifed_email(self) -> bool:
        return self.user.verified_email()

    def verify_email(self):
        self.user.verify_email()

    class Meta:
        abstract = True


class Customer(UserProfile):
    image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    cart = models.ManyToManyField("listings.Listing", blank=True, related_name="cart")
    favorites = models.ManyToManyField("listings.Listing", blank=True, related_name="favorites")
    service_history = models.ManyToManyField('bookings.ServiceBooking', blank=True, related_name='service_history')
    orders = models.ManyToManyField('listings.Order', blank=True, related_name='orders')

    def __str__(self):
        return self.user.email


def slugify(text:str) -> str:
    return text.lower().replace(' ', '-').replace("'", '').replace('.', '')



class Mechanic(UserProfile):
    MECHANIC_TYPE = {
        'business': 'Registered Business',
        'individual': 'Individual Mechanic',
    }
    about = models.TextField(blank=True, null=True)
    business_name = models.CharField(max_length=300, blank=True, null=True)
    headline = models.CharField(max_length=200, blank=True, null=True)
    available = models.BooleanField(default=True)
    services = models.ManyToManyField('bookings.ServiceOffering', blank=True)
    current_job = models.ForeignKey('bookings.ServiceBooking', null=True, blank=True, on_delete=models.CASCADE, related_name='current_job')
    reviews = models.ManyToManyField('feedback.Review', blank=True,)
    job_history = models.ManyToManyField('bookings.ServiceBooking', blank=True, related_name='job_history')
    mechanic_type = models.CharField(max_length=50, choices=MECHANIC_TYPE, default='business')
    logo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    slug = models.SlugField(blank=True, null=True)


    def __str__(self) -> str:
        return self.business_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.business_name)
        super().save(*args, **kwargs)

    def rating(self):
        return '0.0'


class Dealership(UserProfile):
    about = models.TextField(blank=True, null=True)
    slug = models.SlugField(blank=True, null=True)
    logo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    business_name = models.CharField(max_length=300, blank=True, null=True)
    headline = models.CharField(max_length=200, blank=True, null=True)

    # verifications
    cac_number = models.CharField(max_length=200)
    tin_number = models.CharField(max_length=200)

    verified_business = models.BooleanField(default=False) # cac / business verification
    verified_tin = models.BooleanField(default=False) # verified tax number
    verified_location = models.BooleanField(default=False) # verified proof of address
    
    listings = models.ManyToManyField('listings.Listing', blank=True, related_name='listings')
    vehicles = models.ManyToManyField('listings.Vehicle', blank=True, related_name='vehicles')
    reviews = models.ManyToManyField('feedback.Review', blank=True,)
    
    # service scope
    offers_rental = models.BooleanField(default=False) # rents?
    offers_purchase = models.BooleanField(default=True) # sells cars, by default yes
    offers_drivers = models.BooleanField(default=False) # provide driver services
    offers_trade_in = models.BooleanField(default=False) # can customers trade in

    class Meta:
        verbose_name = 'Dealership'

    def __str__(self):
        return self.business_name or self.user.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.business_name)
        super().save(*args, **kwargs)

    def rating(self):
        return '0.0'


class PayoutInformation(DbModel):
    user = models.ForeignKey('Account', on_delete=models.CASCADE)
    channel = models.CharField(max_length=200, default='bank')
    bank_name = models.CharField(max_length=200)
    account_holder_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=10)

    def __str__(self) -> str:
        return f'{self.account_holder_name} @ {self.bank_name}'


class BillingInformation(DbModel):
    user = models.ForeignKey('Account', on_delete=models.CASCADE)
    billing_address = models.ForeignKey('Location', on_delete=models.CASCADE)
    card_holder_name = models.CharField(max_length=200)
    card_number = models.CharField(max_length=20)
    card_exp_month = models.CharField(max_length=2)
    card_exp_year = models.CharField(max_length=4)
    card_cvv = models.CharField(max_length=3)
    is_primary = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.user.name}'s card <{self.id}>"


class Location(DbModel):
    user = models.ForeignKey('Account', on_delete=models.CASCADE)
    country = models.CharField(max_length=2, default='NG')
    state = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    zip_code = models.CharField(max_length=6, blank=True, null=True)

    def __str__(self):
        return f'{self.country}' +', '+ f'{self.state}'



class OTP(DbModel):
    valid_for = models.ForeignKey('Account', on_delete=models.CASCADE)
    code = models.CharField(max_length=7, default=make_random_otp)
    used = models.BooleanField(default=False)
    channel = models.CharField(max_length=20, default='email', choices=(('email', 'Email'), ('sms', 'SMS'))) # email | sms

    class Meta:
        verbose_name = 'One Time Pin (OTP)'
        verbose_name_plural = 'One Time Pins (OTPs)'

    def verify(self, code, user=None):
        if self.code == code:
            if user and user == self.valid_for: # for verifying user_profiles
                user_profile = self.get_user_profile()
                if user_profile is not None: # if None ie user/valid_for is an agent/staff account
                    if self.channel == 'email':
                        user_profile.verify_email()
                    elif self.channel == 'sms':
                        user_profile.verify_phone_number()
                    self.delete()
                    return True
                else:
                    self.valid_for.verify_email()
                    self.delete()
                    return True
            return False
        return False

    def get_user_profile(self):
        if self.valid_for.user_type == 'customer':
            return Customer.objects.get(user=self.valid_for)
        if self.valid_for.user_type == 'dealer':
            return Dealer.objects.get(user=self.valid_for)
        if self.valid_for.user_type == 'mechanic':
            return Mechanic.objects.get(user=self.valid_for)
        return None

    def __str__(self) -> str:
        return self.code


class File(DbModel):
    name = models.CharField(max_length=200, blank=True, null=True)
    file = models.FileField(upload_to='docs/')

    def save(self, *args, **kwargs):
        if not self.name and self.file:
            self.name = self.file.name
        super().save(*args, **kwargs)

    def file_type(self):
        ext = self.file.name.split('.')[-1]
        types = {
            'pdf': 'PDF Document',
            'docx': 'MS-Word Document',
            'jpeg': 'Image Document',
            'png': 'Image Document',
        }
        return types[ext] or f"Unknown Document type => {ext}"


class Document(DbModel):
    DOCTYPES = [
        ('drivers-license', "Driver's License"),
        ('nin', "National Identification"),
        ('proof-of-address', "Proof of Address"),
    ]

    owner = models.ForeignKey('Account', on_delete=models.CASCADE)
    doctype = models.CharField(max_length=200, choices=DOCTYPES)
    files = models.ManyToManyField('File', blank=True)



# use as ref to old imports for now
# TODO: rename old imports before staging
Dealer = Dealership