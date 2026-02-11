from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, Group, PermissionsMixin
from django.contrib.auth.hashers import make_password
from django.core.validators import RegexValidator, EmailValidator, MinLengthValidator, MaxLengthValidator
from django.core.exceptions import ValidationError
from utils.models import DbModel
from django.utils import timezone
from django.utils.timesince import timeuntil, timesince
from utils import make_random_otp
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from cloudinary.models import CloudinaryField
import re


class AccountManager(BaseUserManager):

    def _create_user(self, email, password=None, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if extra_fields.get('provider', 'veyu') == 'veyu':
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
        'veyu': 'Veyu',
        'google': 'Google',
        'facebook': 'Facebook',
        'apple': 'Apple',
    }

    email = models.EmailField(
        blank=False, 
        unique=True,
        validators=[EmailValidator(message="Enter a valid email address")]
    )
    first_name = models.CharField(
        max_length=150, 
        blank=True,  # Allow blank for system updates and existing users
        validators=[
            MinLengthValidator(2, message="First name must be at least 2 characters long"),
            RegexValidator(
                regex=r'^[a-zA-Z\s\-\'\.]+$',
                message="First name can only contain letters, spaces, hyphens, apostrophes, and periods"
            )
        ]
    )
    last_name = models.CharField(
        max_length=150, 
        blank=True,  # Allow blank for system updates and existing users
        validators=[
            MinLengthValidator(2, message="Last name must be at least 2 characters long"),
            RegexValidator(
                regex=r'^[a-zA-Z\s\-\'\.]+$',
                message="Last name can only contain letters, spaces, hyphens, apostrophes, and periods"
            )
        ]
    )
    role = models.ForeignKey(Group, on_delete=models.SET_NULL, blank=True, null=True)
    verified_email = models.BooleanField(default=True)
    api_token = models.CharField(max_length=64, blank=True, null=True, unique=True)
    
    referral_code = models.CharField(max_length=12, blank=True, null=True, unique=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='referrals')

    provider = models.CharField(max_length=20, choices=ACCOUNT_PROVIDERS, default='veyu')

    groups = None
    user_permissions = None

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    user_type = models.CharField(max_length=20, default='customer', choices=USER_TYPES)
    welcome_email_sent_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Timestamp when welcome email was sent on first login"
    )

    objects = AccountManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = 'email'
    
    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
            models.Index(fields=['provider']),
            models.Index(fields=['verified_email']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_staff']),
            models.Index(fields=['date_joined']),
            models.Index(fields=['api_token']),
            models.Index(fields=['welcome_email_sent_at']),
        ]
        ordering = ['-date_joined']

    def clean(self):
        """Custom validation for Account model"""
        super().clean()
        
        # Validate email format
        if self.email:
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, self.email):
                raise ValidationError({'email': 'Enter a valid email address'})
        
        # Validate names don't contain only spaces
        if self.first_name and self.first_name.strip() == '':
            raise ValidationError({'first_name': 'First name cannot be empty or contain only spaces'})
        
        if self.last_name and self.last_name.strip() == '':
            raise ValidationError({'last_name': 'Last name cannot be empty or contain only spaces'})
        
        # Validate user_type and provider combinations
        if self.provider != 'veyu' and self.user_type in ['admin', 'staff']:
            raise ValidationError({'provider': 'Admin and staff accounts must use Veyu provider'})

    def save(self, *args, **kwargs):
        # Skip validation if only updating specific fields (like last_login)
        update_fields = kwargs.get('update_fields')
        if update_fields and set(update_fields).issubset({'last_login', 'api_token'}):
            # Skip full_clean for system updates
            pass
        else:
            # Clean before saving for user-initiated changes
            self.full_clean()
        
        # Normalize names
        if self.first_name:
            self.first_name = self.first_name.strip().title()
        if self.last_name:
            self.last_name = self.last_name.strip().title()
        
        if not self.referral_code:
            # Generate a unique referral code
            import random
            import string
            
            while True:
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                if not Account.objects.filter(referral_code=code).exists():
                    self.referral_code = code
                    break

        if not self.api_token:
            super().save(using=None)
            # Generate/ensure DRF Token then store the key string to avoid FK dependency
            try:
                from rest_framework.authtoken.models import Token
                token_obj, _ = Token.objects.get_or_create(user=self)
                self.api_token = token_obj.key
            except Exception:
                # If authtoken not installed or unavailable, leave blank
                pass
        super().save(*args, **kwargs)

    @property
    def token(self):
        return self.api_token

    def verify_email(self):
        self.verified_email = True
        self.save()
        return True
    
    def create_verification_otp(self, invalidate_previous=True, check_rate_limit=True):
        """
        Create a new verification OTP for this user with rate limiting and proper cleanup.
        
        Args:
            invalidate_previous: Whether to invalidate previous unused OTPs
            check_rate_limit: Whether to check rate limiting before creating OTP
            
        Returns:
            OTP instance or raises ValidationError if rate limited
            
        Raises:
            ValidationError: If rate limit is exceeded
        """
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        from datetime import timedelta
        
        if check_rate_limit:
            # Check rate limiting - max 3 OTPs per hour, 10 per day
            now = timezone.now()
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)
            
            # Count recent OTPs
            recent_hour_count = OTP.objects.filter(
                valid_for=self,
                channel='email',
                purpose='verification',
                date_created__gte=hour_ago
            ).count()
            
            recent_day_count = OTP.objects.filter(
                valid_for=self,
                channel='email',
                purpose='verification',
                date_created__gte=day_ago
            ).count()
            
            if recent_hour_count >= 3:
                raise ValidationError(
                    "Too many verification requests. Please wait before requesting another code."
                )
            
            if recent_day_count >= 10:
                raise ValidationError(
                    "Daily verification limit exceeded. Please try again tomorrow."
                )
            
            # Check for recent OTP (cooldown period of 2 minutes)
            recent_otp = OTP.objects.filter(
                valid_for=self,
                channel='email',
                purpose='verification',
                date_created__gte=now - timedelta(minutes=2)
            ).first()
            
            if recent_otp:
                remaining_seconds = int((recent_otp.date_created + timedelta(minutes=2) - now).total_seconds())
                if remaining_seconds > 0:
                    raise ValidationError(
                        f"Please wait {remaining_seconds} seconds before requesting another verification code."
                    )
        
        if invalidate_previous:
            # Mark previous unused verification OTPs as used
            OTP.objects.filter(
                valid_for=self,
                channel='email',
                purpose='verification',
                used=False
            ).update(used=True)
        
        return OTP.objects.create(
            valid_for=self,
            channel='email',
            purpose='verification',
            expires_at=timezone.now() + timezone.timedelta(minutes=10)
        )

    def cleanup_expired_otps(self):
        """
        Clean up expired and used OTPs for this user.
        
        Returns:
            Dict with cleanup statistics
        """
        from django.utils import timezone
        
        now = timezone.now()
        
        # Count expired OTPs
        expired_otps = OTP.objects.filter(
            valid_for=self,
            expires_at__lt=now
        )
        expired_count = expired_otps.count()
        
        # Count used OTPs older than 24 hours
        old_used_otps = OTP.objects.filter(
            valid_for=self,
            used=True,
            date_created__lt=now - timezone.timedelta(days=1)
        )
        old_used_count = old_used_otps.count()
        
        # Delete expired and old used OTPs
        expired_otps.delete()
        old_used_otps.delete()
        
        return {
            'expired_deleted': expired_count,
            'old_used_deleted': old_used_count,
            'total_deleted': expired_count + old_used_count
        }

    @classmethod
    def cleanup_all_expired_otps(cls):
        """
        Clean up expired and old used OTPs for all users.
        This method should be called periodically (e.g., via cron job).
        
        Returns:
            Dict with cleanup statistics
        """
        from django.utils import timezone
        
        now = timezone.now()
        
        # Count and delete expired OTPs
        expired_otps = OTP.objects.filter(expires_at__lt=now)
        expired_count = expired_otps.count()
        expired_otps.delete()
        
        # Count and delete used OTPs older than 7 days
        old_used_otps = OTP.objects.filter(
            used=True,
            date_created__lt=now - timezone.timedelta(days=7)
        )
        old_used_count = old_used_otps.count()
        old_used_otps.delete()
        
        return {
            'expired_deleted': expired_count,
            'old_used_deleted': old_used_count,
            'total_deleted': expired_count + old_used_count
        }

    @property
    def name(self):
        return f'{self.first_name} {self.last_name if self.last_name else ""}'.strip()

    @property
    def last_seen(self):
        if self.last_login:
            return timesince(self.last_login)
        return None
    
    @property
    def full_name(self):
        """Returns the full name of the user"""
        return self.name
    
    @property
    def display_name(self):
        """Returns display name for UI purposes"""
        return self.name or self.email.split('@')[0]
    
    @property
    def has_received_welcome_email(self) -> bool:
        """Check if user has received welcome email."""
        return self.welcome_email_sent_at is not None
    
    def __str__(self):
        return f"{self.name} ({self.email})"
    
    def __repr__(self):
        return f"<Account: {self.email} - {self.get_user_type_display()}>"


class UserProfile(DbModel):
    ID_TYPES = [
        ('nin', 'National Identification'),
        ('drivers-license', 'Driver\'s License'),
        ('voters-card', 'Voter\'s Card'),
        ('passport', 'International Passport'),
    ]
    APPROVAL_STATUS = {
        'pending': 'Pending Approval',
        'approved': 'Account Approved',
        'disabled': 'Account Disabled',
    }
    VERIFICATION_STATUS = {
        'unverified': 'Requires Verification',
        'pending': 'Pending Verification',
        'completed': 'Account Approved',
    }
    
    user = models.OneToOneField(Account, on_delete=models.CASCADE, related_name='%(class)s_profile')
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[1-9]\d{1,14}$',
                message="Enter a valid phone number in international format (e.g., +234XXXXXXXXXX)"
            )
        ]
    )
    id_type = models.CharField(max_length=200, default='nin', choices=ID_TYPES, blank=True, null=True)
    verified_phone_number = models.BooleanField(default=False)
    verified_id = models.BooleanField(default=False)
    payout_info = models.ManyToManyField('PayoutInformation', blank=True, related_name='%(class)s_profiles')
    verification_ref = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z0-9\-_]+$',
                message="Verification reference can only contain uppercase letters, numbers, hyphens, and underscores"
            )
        ]
    )
    verification_status = models.CharField(max_length=20, default='unverified', choices=VERIFICATION_STATUS)
    account_status = models.CharField(max_length=20, default='pending', choices=APPROVAL_STATUS)

    location = models.ForeignKey("Location", on_delete=models.SET_NULL, blank=True, null=True, related_name='%(class)s_locations')
    documents = models.ManyToManyField('Document', blank=True, related_name='%(class)s_documents')
    # primary_billing_info = models.ForeignKey("BillingInformation", blank=True, null=True, on_delete=models.CASCADE)
    billing_info = models.ManyToManyField("BillingInformation", blank=True, related_name='%(class)s_billing')


    def clean(self):
        """Custom validation for UserProfile"""
        super().clean()
        
        # Validate phone number format if provided
        if self.phone_number:
            # Remove spaces and common separators for validation
            clean_phone = re.sub(r'[\s\-\(\)]', '', self.phone_number)
            if not re.match(r'^\+?[1-9]\d{1,14}$', clean_phone):
                raise ValidationError({'phone_number': 'Enter a valid phone number'})
        
        # Validate verification status logic
        if self.verified_phone_number and not self.phone_number:
            raise ValidationError({'verified_phone_number': 'Cannot verify phone number without providing one'})
        
        if self.verification_status == 'completed' and not (self.verified_phone_number or self.user.verified_email):
            raise ValidationError({'verification_status': 'Cannot mark as completed without email or phone verification'})

    def save(self, *args, **kwargs):
        # Clean before saving
        self.full_clean()
        
        # Normalize phone number
        if self.phone_number:
            self.phone_number = re.sub(r'[\s\-\(\)]', '', self.phone_number)
        
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.user.name} - {self.get_verification_status_display()}"
    
    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.user.email}>"

    @classmethod
    def me(cls, obj_id):
        obj = None
        try:
            obj = cls.objects.get(uuid=obj_id)
        except Exception:
            try:
                obj = cls.objects.get(id=obj_id)
            except Exception:
                obj = None
        return obj

    def verify_phone_number(self):
        self.verified_phone_number = True
        self.save()
        return True

    @property
    def verifed_email(self) -> bool:
        return self.user.verified_email

    def verify_email(self):
        self.user.verify_email()

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['verification_status']),
            models.Index(fields=['account_status']),
        ]


class Customer(UserProfile):
    image = CloudinaryField('profile_image', folder='users/profiles/', blank=True, null=True)
    cart = models.ManyToManyField("listings.Listing", blank=True, related_name="customer_cart")
    favorites = models.ManyToManyField("listings.Listing", blank=True, related_name="customer_favorites")
    service_history = models.ManyToManyField('bookings.ServiceBooking', blank=True, related_name='customer_service_history')
    orders = models.ManyToManyField('listings.Order', blank=True, related_name='customer_orders')

    def __str__(self):
        return f"{self.user.name} (Customer)"
    
    def __repr__(self):
        return f"<Customer: {self.user.email} - {self.get_verification_status_display()}>"
    
    @property
    def cart_count(self):
        """Returns the number of items in the customer's cart"""
        return self.cart.count()
    
    @property
    def favorites_count(self):
        """Returns the number of favorite listings"""
        return self.favorites.count()
    
    @property
    def total_orders(self):
        """Returns the total number of orders placed"""
        return self.orders.count()
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['verified_phone_number']),
        ]
        ordering = ['-date_created']
        verbose_name = 'Customer Profile'
        verbose_name_plural = 'Customer Profiles'


def slugify(text:str) -> str:
    return text.lower().replace(' ', '-').replace("'", '').replace('.', '')



class Mechanic(UserProfile):
    """
    Mechanic profile for service providers.
    
    Relationships:
        - Has a OneToOneField reverse relationship from BusinessVerificationSubmission
          (related_name='verification_submission')
          Access via: mechanic.verification_submission
          When this Mechanic is deleted, the associated BusinessVerificationSubmission
          is automatically deleted due to CASCADE behavior.
    """
    MECHANIC_TYPE = {
        'business': 'Registered Business',
        'individual': 'Individual Mechanic',
    }
    LEVELS = {
        'new': 'New Seller',
        'level-1': 'Trusted Mechanic',
        'top': 'Top Rated',
    }
    
    about = models.TextField(
        blank=True, 
        null=True,
        validators=[MaxLengthValidator(2000, message="About section cannot exceed 2000 characters")]
    )
    business_name = models.CharField(
        max_length=300, 
        blank=True, 
        null=True,
        validators=[
            MinLengthValidator(2, message="Business name must be at least 2 characters long"),
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s\-\'\.&]+$',
                message="Business name can only contain letters, numbers, spaces, hyphens, apostrophes, periods, and ampersands"
            )
        ]
    )
    slug = models.SlugField(blank=True, null=True, unique=True)
    logo = CloudinaryField('mechanic_logo', folder='mechanics/logos/', blank=True, null=True)
    level = models.CharField(max_length=20, default='new', choices=LEVELS)
    headline = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        validators=[MaxLengthValidator(200, message="Headline cannot exceed 200 characters")]
    )
    available = models.BooleanField(default=True)
    services = models.ManyToManyField('bookings.ServiceOffering', blank=True, related_name='mechanic_services')
    current_job = models.ForeignKey('bookings.ServiceBooking', null=True, blank=True, on_delete=models.SET_NULL, related_name='current_mechanic')
    reviews = models.ManyToManyField('feedback.Review', blank=True, related_name='mechanic_reviews')
    job_history = models.ManyToManyField('bookings.ServiceBooking', blank=True, related_name='mechanic_job_history')
    business_type = models.CharField(max_length=50, choices=MECHANIC_TYPE, default='business')
    verified_business = models.BooleanField(default=False) # cac / business verification
    contact_email = models.EmailField(
        blank=True, 
        null=True,
        validators=[EmailValidator(message="Enter a valid email address")]
    )
    contact_phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[1-9]\d{1,14}$',
                message="Enter a valid phone number"
            )
        ]
    )


    def clean(self):
        """Custom validation for Mechanic"""
        super().clean()
        
        # Business type validation - now optional to support incomplete profiles
        # Business name will be required during verification submission for business type
        
        # Contact validation
        if self.contact_email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.contact_email):
            raise ValidationError({'contact_email': 'Enter a valid email address'})
        
        # Availability validation
        if not self.available and self.current_job:
            raise ValidationError({'available': 'Cannot be unavailable while having a current job'})

    def save(self, *args, **kwargs):
        # Clean before saving
        self.full_clean()
        
        # Generate slug if business name provided
        if not self.slug and self.business_name:
            self.slug = slugify(self.business_name)
        
        # Normalize business name
        if self.business_name:
            self.business_name = self.business_name.strip()
        
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.business_name or self.user.name} (Mechanic)"
    
    def __repr__(self):
        return f"<Mechanic: {self.business_name or self.user.email} - {self.get_level_display()}>"
    
    @property
    def total_services(self):
        """Returns the total number of services offered"""
        return self.services.count()
    
    @property
    def completed_jobs(self):
        """Returns the number of completed jobs"""
        return self.job_history.filter(completed=True).count()
    
    @property
    def average_rating(self):
        """Returns the average rating from reviews"""
        if self.reviews.exists():
            total_rating = sum(review.avg_rating for review in self.reviews.all())
            return round(total_rating / self.reviews.count(), 1)
        return 0.0
    
    @property
    def availability_status(self):
        """Returns human-readable availability status"""
        if not self.available:
            return "Unavailable"
        elif self.current_job:
            return "Busy"
        else:
            return "Available"
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['business_name']),
            models.Index(fields=['slug']),
            models.Index(fields=['level']),
            models.Index(fields=['available']),
            models.Index(fields=['verified_business']),
            models.Index(fields=['business_type']),
        ]
        ordering = ['-date_created']
        verbose_name = 'Mechanic Profile'
        verbose_name_plural = 'Mechanic Profiles'

    def rating(self):
        return '0.0'
    
    @property
    def business_verification_status(self):
        """Returns the current business verification status"""
        try:
            return self.verification_submission.status
        except BusinessVerificationSubmission.DoesNotExist:
            return 'not_submitted'


class MechanicBoost(DbModel):
    mechanic = models.OneToOneField('Mechanic', on_delete=models.CASCADE, related_name='boosted')
    start_date = models.DateField()
    end_date = models.DateField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)  # Tracks payment amount
    active = models.BooleanField(default=True)  # Auto-updated by cron job

    def is_active(self):
        return self.start_date <= now().date() <= self.end_date

    def save(self, *args, **kwargs):
        """Ensure `active` is updated before saving."""
        self.active = self.is_active()
        super().save(*args, **kwargs)

    def __str__(self):
        status = "Active" if self.is_active() else "Expired"
        return f"Boost: {self.mechanic.business_name or self.mechanic.user.name} - {status}"
    
    def __repr__(self):
        return f"<MechanicBoost: {self.mechanic.business_name} - {self.start_date} to {self.end_date}>"
    
    @property
    def days_remaining(self):
        """Returns the number of days remaining for the boost"""
        if not self.is_active():
            return 0
        return (self.end_date - now().date()).days
    
    @property
    def duration_days(self):
        """Returns the total duration of the boost in days"""
        return (self.end_date - self.start_date).days
    
    class Meta:
        indexes = [
            models.Index(fields=['mechanic']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['active']),
        ]
        ordering = ['-start_date']
        verbose_name = 'Mechanic Boost'
        verbose_name_plural = 'Mechanic Boosts'



class Dealership(UserProfile):
    """
    Dealership profile for car dealers.
    
    Relationships:
        - Has a OneToOneField reverse relationship from BusinessVerificationSubmission
          (related_name='verification_submission')
          Access via: dealership.verification_submission
          When this Dealership is deleted, the associated BusinessVerificationSubmission
          is automatically deleted due to CASCADE behavior.
    """
    LEVELS = {
        'new': 'New Seller',
        'level-1': 'Trusted Dealer',
        'star': 'Star Host',
        'top': 'Top Dealer',
    }
    
    about = models.TextField(
        blank=True, 
        null=True,
        validators=[MaxLengthValidator(2000, message="About section cannot exceed 2000 characters")]
    )
    slug = models.SlugField(blank=True, null=True, unique=True)
    logo = CloudinaryField('logo', folder='dealerships/logos/', blank=True, null=True)
    business_name = models.CharField(
        max_length=300, 
        blank=True, 
        null=True,
        validators=[
            MinLengthValidator(2, message="Business name must be at least 2 characters long"),
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s\-\'\.&]+$',
                message="Business name can only contain letters, numbers, spaces, hyphens, apostrophes, periods, and ampersands"
            )
        ]
    )
    headline = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        validators=[MaxLengthValidator(200, message="Headline cannot exceed 200 characters")]
    )
    contact_email = models.EmailField(
        blank=True, 
        null=True,
        validators=[EmailValidator(message="Enter a valid email address")]
    )
    contact_phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[1-9]\d{1,14}$',
                message="Enter a valid phone number"
            )
        ]
    )

    # verifications
    cac_number = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{2}\d{6,8}$',
                message="Enter a valid CAC number (e.g., RC123456)"
            )
        ]
    )
    tin_number = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\d{8}-\d{4}$',
                message="Enter a valid TIN number (format: 12345678-1234)"
            )
        ]
    )

    level = models.CharField(max_length=20, default='new', choices=LEVELS)

    verified_business = models.BooleanField(default=False) # cac / business verification
    verified_tin = models.BooleanField(default=False) # verified tax number
    verified_location = models.BooleanField(default=False) # verified proof of address

    listings = models.ManyToManyField('listings.Listing', blank=True, related_name='dealership_listings')
    vehicles = models.ManyToManyField('listings.Vehicle', blank=True, related_name='dealership_vehicles')
    reviews = models.ManyToManyField('feedback.Review', blank=True, related_name='dealership_reviews')
    orders = models.ManyToManyField('listings.Order', blank=True, related_name='dealership_orders')

    # service scope
    offers_rental = models.BooleanField(default=False) # rents?
    offers_purchase = models.BooleanField(default=True) # sells cars, by default yes
    offers_drivers = models.BooleanField(default=False) # provide driver services
    offers_trade_in = models.BooleanField(default=False) # can customers trade in
    extended_services = models.JSONField(default=list, blank=True) # additional services beyond core boolean fields

    def clean(self):
        """Custom validation for Dealership"""
        super().clean()
        
        # Business name validation - now optional to support incomplete profiles
        # Business name will be required during verification submission
        
        # Contact validation
        if self.contact_email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.contact_email):
            raise ValidationError({'contact_email': 'Enter a valid email address'})
        
        # Service validation - at least one service must be offered
        has_core_service = any([self.offers_rental, self.offers_purchase, self.offers_drivers, self.offers_trade_in])
        has_extended_service = bool(self.extended_services and len(self.extended_services) > 0)
        
        if not (has_core_service or has_extended_service):
            raise ValidationError('Dealership must offer at least one service')

    def save(self, *args, **kwargs):
        # Clean before saving
        self.full_clean()
        
        # Generate slug if business name provided
        if not self.slug and self.business_name:
            self.slug = slugify(self.business_name)
        
        # Normalize business name
        if self.business_name:
            self.business_name = self.business_name.strip()
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.business_name or self.user.name} (Dealership)"
    
    def __repr__(self):
        return f"<Dealership: {self.business_name or self.user.email} - {self.get_level_display()}>"
    
    @property
    def total_listings(self):
        """Returns the total number of listings"""
        return self.listings.count()
    
    @property
    def total_vehicles(self):
        """Returns the total number of vehicles"""
        return self.vehicles.count()
    
    @property
    def completed_orders(self):
        """Returns the number of completed orders"""
        return self.orders.filter(order_status='completed').count()
    
    @property
    def verification_completeness(self):
        """Returns verification completeness percentage"""
        verifications = [
            self.verified_business,
            self.verified_tin,
            self.verified_location,
            bool(self.cac_number),
            bool(self.tin_number)
        ]
        completed = sum(verifications)
        return round((completed / len(verifications)) * 100, 1)
    
    class Meta:
        verbose_name = 'Dealership'
        verbose_name_plural = 'Dealerships'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['business_name']),
            models.Index(fields=['slug']),
            models.Index(fields=['level']),
            models.Index(fields=['verified_business']),
            models.Index(fields=['offers_rental', 'offers_purchase']),
            models.Index(fields=['cac_number']),
            models.Index(fields=['tin_number']),
        ]
        ordering = ['-date_created']

    def rating(self):
        avg = 0
        for review in self.reviews.all():
            avg += review.avg_rating
        if avg > 0:
            avg = avg/self.reviews.count()
        return round(avg, 1)
    
    @property
    def business_verification_status(self):
        """Returns the current business verification status"""
        try:
            return self.verification_submission.status
        except BusinessVerificationSubmission.DoesNotExist:
            return 'not_submitted'

    @property
    def services(self):
        servs = []
        if self.offers_purchase:
            servs.append('Car Sale')
        if self.offers_rental:
            servs.append('Car Leasing')
        if self.offers_drivers:
            servs.append('Drivers')
        if self.offers_trade_in:
            servs.append('Sell-Your-Car')
            servs.append('Car Trade-in')
        
        # Add extended services
        if self.extended_services:
            servs.extend(self.extended_services)
        
        return servs


class PayoutInformation(DbModel):
    CHANNEL_CHOICES = [
        ('bank', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('wallet', 'Digital Wallet'),
    ]
    
    user = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='payout_accounts')
    channel = models.CharField(max_length=200, default='bank', choices=CHANNEL_CHOICES)
    bank_name = models.CharField(
        max_length=200,
        validators=[
            MinLengthValidator(2, message="Bank name must be at least 2 characters long"),
            RegexValidator(
                regex=r'^[a-zA-Z\s\-\'\.&]+$',
                message="Bank name can only contain letters, spaces, hyphens, apostrophes, periods, and ampersands"
            )
        ]
    )
    account_holder_name = models.CharField(
        max_length=200,
        validators=[
            MinLengthValidator(2, message="Account holder name must be at least 2 characters long"),
            RegexValidator(
                regex=r'^[a-zA-Z\s\-\'\.]+$',
                message="Account holder name can only contain letters, spaces, hyphens, apostrophes, and periods"
            )
        ]
    )
    account_number = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\d{10,20}$',
                message="Account number must be 10-20 digits"
            )
        ]
    )

    def clean(self):
        """Custom validation for PayoutInformation"""
        super().clean()
        
        # Validate account number format based on channel
        if self.channel == 'bank' and self.account_number:
            if not re.match(r'^\d{10}$', self.account_number):
                raise ValidationError({'account_number': 'Bank account number must be exactly 10 digits'})

    def save(self, *args, **kwargs):
        # Clean before saving
        self.full_clean()
        
        # Normalize names
        if self.account_holder_name:
            self.account_holder_name = self.account_holder_name.strip().title()
        if self.bank_name:
            self.bank_name = self.bank_name.strip().title()
        
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.account_holder_name} - {self.bank_name} ({self.get_channel_display()})'
    
    def __repr__(self):
        return f"<PayoutInfo: {self.user.email} - {self.bank_name} {self.account_number[-4:]}>"
    
    @property
    def masked_account_number(self):
        """Returns masked account number for security"""
        if len(self.account_number) > 4:
            return f"****{self.account_number[-4:]}"
        return self.account_number
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['channel']),
            models.Index(fields=['account_number']),
        ]
        ordering = ['-date_created']
        verbose_name = 'Payout Information'
        verbose_name_plural = 'Payout Information'


class BillingInformation(DbModel):
    user = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='billing_accounts')
    billing_address = models.ForeignKey('Location', on_delete=models.CASCADE, related_name='billing_locations')
    card_holder_name = models.CharField(max_length=200)
    card_number = models.CharField(max_length=20)
    card_exp_month = models.CharField(max_length=2)
    card_exp_year = models.CharField(max_length=4)
    card_cvv = models.CharField(max_length=3)
    is_primary = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.card_holder_name} - ****{self.card_number[-4:] if len(self.card_number) > 4 else self.card_number}"
    
    def __repr__(self):
        return f"<BillingInfo: {self.user.email} - {self.card_holder_name}>"
    
    @property
    def masked_card_number(self):
        """Returns masked card number for security"""
        if len(self.card_number) > 4:
            return f"****-****-****-{self.card_number[-4:]}"
        return self.card_number
    
    @property
    def expiry_date(self):
        """Returns formatted expiry date"""
        return f"{self.card_exp_month}/{self.card_exp_year}"
    
    @property
    def is_expired(self):
        """Check if the card has expired"""
        try:
            from datetime import datetime
            current_year = datetime.now().year
            current_month = datetime.now().month
            exp_year = int(self.card_exp_year)
            exp_month = int(self.card_exp_month)
            
            if exp_year < current_year:
                return True
            elif exp_year == current_year and exp_month < current_month:
                return True
            return False
        except (ValueError, TypeError):
            return True
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_primary']),
        ]
        ordering = ['-is_primary', '-date_created']
        verbose_name = 'Billing Information'
        verbose_name_plural = 'Billing Information'


class Location(DbModel):
    COUNTRY_CHOICES = [
        ('NG', 'Nigeria'),
        ('GH', 'Ghana'),
        ('KE', 'Kenya'),
        ('ZA', 'South Africa'),
    ]
    
    user = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='locations')
    country = models.CharField(max_length=2, default='NG', choices=COUNTRY_CHOICES)
    state = models.CharField(
        max_length=200,
        validators=[
            MinLengthValidator(2, message="State name must be at least 2 characters long"),
            RegexValidator(
                regex=r'^[a-zA-Z\s\-\'\.]+$',
                message="State name can only contain letters, spaces, hyphens, apostrophes, and periods"
            )
        ]
    )
    city = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s\-\'\.]+$',
                message="City name can only contain letters, spaces, hyphens, apostrophes, and periods"
            )
        ]
    )
    address = models.CharField(
        max_length=300,
        validators=[
            MinLengthValidator(5, message="Address must be at least 5 characters long")
        ]
    )
    zip_code = models.CharField(
        max_length=10, 
        blank=True, 
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\d{3,10}$',
                message="Zip code must be 3-10 digits"
            )
        ]
    )
    lat = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        blank=True, 
        null=True,
        validators=[
            RegexValidator(
                regex=r'^-?([0-8]?[0-9]|90)(\.[0-9]{1,7})?$',
                message="Enter a valid latitude (-90 to 90)"
            )
        ]
    )
    lng = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        blank=True, 
        null=True,
        validators=[
            RegexValidator(
                regex=r'^-?(1[0-7][0-9]|[0-9]?[0-9])(\.[0-9]{1,7})?$',
                message="Enter a valid longitude (-180 to 180)"
            )
        ]
    )
    google_place_id = models.CharField(max_length=100, blank=True, null=True)

    def clean(self):
        """Custom validation for Location"""
        super().clean()
        
        # Validate coordinates if provided
        if self.lat is not None:
            try:
                lat_val = float(self.lat)
                if not (-90 <= lat_val <= 90):
                    raise ValidationError({'lat': 'Latitude must be between -90 and 90'})
            except (ValueError, TypeError):
                raise ValidationError({'lat': 'Enter a valid latitude'})
        
        if self.lng is not None:
            try:
                lng_val = float(self.lng)
                if not (-180 <= lng_val <= 180):
                    raise ValidationError({'lng': 'Longitude must be between -180 and 180'})
            except (ValueError, TypeError):
                raise ValidationError({'lng': 'Enter a valid longitude'})

    def save(self, *args, **kwargs):
        # Clean before saving
        self.full_clean()
        
        # Normalize location names
        if self.state:
            self.state = self.state.strip().title()
        if self.city:
            self.city = self.city.strip().title()
        if self.address:
            self.address = self.address.strip()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        parts = []
        if self.city:
            parts.append(self.city)
        parts.append(self.state)
        parts.append(self.get_country_display())
        return f"{', '.join(parts)} - {self.user.name}"
    
    def __repr__(self):
        return f"<Location: {self.user.email} - {self.city or 'Unknown'}, {self.state}>"
    
    @property
    def full_address(self):
        """Returns the complete formatted address"""
        parts = [self.address]
        if self.city:
            parts.append(self.city)
        parts.append(self.state)
        parts.append(self.get_country_display())
        if self.zip_code:
            parts.append(self.zip_code)
        return ', '.join(parts)
    
    @property
    def has_coordinates(self):
        """Check if location has GPS coordinates"""
        return self.lat is not None and self.lng is not None
    
    @property
    def coordinates(self):
        """Returns coordinates as a tuple (lat, lng) or None"""
        if self.has_coordinates:
            return (float(self.lat), float(self.lng))
        return None
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['country', 'state']),
            models.Index(fields=['city']),
            models.Index(fields=['lat', 'lng']),
        ]
        ordering = ['-date_created']
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'

    def __str__(self):
        return f'{self.country}, {self.state}'
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['country', 'state']),
            models.Index(fields=['city']),
            models.Index(fields=['lat', 'lng']),
        ]



class OTP(DbModel):
    valid_for = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=8, default=make_random_otp)
    used = models.BooleanField(default=False)
    channel = models.CharField(max_length=20, default='email', choices=(('email', 'Email'), ('sms', 'SMS')))
    expires_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    purpose = models.CharField(max_length=50, default='verification', choices=(
        ('verification', 'Account Verification'),
        ('password_reset', 'Password Reset'),
        ('login', 'Login Verification'),
        ('phone_verification', 'Phone Verification'),
    ))

    class Meta:
        verbose_name = 'One Time Pin (OTP)'
        verbose_name_plural = 'One Time Pins (OTPs)'
        indexes = [
            models.Index(fields=['valid_for', 'channel', 'used']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['code', 'used']),
            models.Index(fields=['purpose', 'channel']),
            models.Index(fields=['date_created']),
        ]
        ordering = ['-date_created']

    def clean(self):
        """Custom validation for OTP"""
        super().clean()
        
        # Validate OTP code format
        if self.code and not re.match(r'^\d{4,8}$', self.code):
            raise ValidationError({'code': 'OTP code must be 4-8 digits'})
        
        # Validate max attempts
        if self.max_attempts < 1 or self.max_attempts > 10:
            raise ValidationError({'max_attempts': 'Max attempts must be between 1 and 10'})
        
        # Validate attempts don't exceed max
        if self.attempts > self.max_attempts:
            raise ValidationError({'attempts': 'Attempts cannot exceed max attempts'})

    def save(self, *args, **kwargs):
        # Clean before saving
        self.full_clean()
        
        # Set expiration time if not set (10 minutes from creation)
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_expired(self):
        """Check if the OTP has expired."""
        if not self.expires_at:
            return True
        return timezone.now() > self.expires_at

    def is_valid_for_verification(self):
        """Check if OTP is valid for verification (not used, not expired, attempts not exceeded)."""
        return (
            not self.used and 
            not self.is_expired() and 
            self.attempts < self.max_attempts
        )

    def verify(self, code, user=None):
        """Verify the OTP code and update user verification status if successful."""
        from utils.otp import validate_otp_format
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Increment attempt counter
        self.attempts += 1
        self.save()
        
        # Validate format first
        if not validate_otp_format(code):
            logger.warning(f"Invalid OTP format attempted for user {self.valid_for.email}")
            return False
        
        # Check if OTP is still valid
        if not self.is_valid_for_verification():
            logger.warning(f"Invalid OTP verification attempt for user {self.valid_for.email}: expired or max attempts reached")
            return False
        
        # Check if code matches
        if self.code != code:
            logger.warning(f"Incorrect OTP code attempted for user {self.valid_for.email}")
            return False
        
        # Check if user matches (if provided)
        if user and user != self.valid_for:
            logger.warning(f"OTP user mismatch for {self.valid_for.email}")
            return False
        
        # Mark as used
        self.used = True
        self.save()
        
        # Update user verification status
        try:
            if self.channel == 'email' and self.purpose == 'verification':
                self.valid_for.verified_email = True
                self.valid_for.save()
                logger.info(f"Email verified for user {self.valid_for.email}")
            elif self.channel == 'sms' and self.purpose == 'phone_verification':
                user_profile = self.get_user_profile()
                if user_profile:
                    user_profile.verified_phone_number = True
                    user_profile.save()
                    logger.info(f"Phone verified for user {self.valid_for.email}")
        except Exception as e:
            logger.error(f"Error updating verification status for user {self.valid_for.email}: {str(e)}")
        
        return True

    def get_user_profile(self):
        """Get the user profile based on user type."""
        try:
            if self.valid_for.user_type == 'customer':
                return Customer.objects.get(user=self.valid_for)
            elif self.valid_for.user_type == 'dealer':
                return Dealership.objects.get(user=self.valid_for)
            elif self.valid_for.user_type == 'mechanic':
                return Mechanic.objects.get(user=self.valid_for)
        except (Customer.DoesNotExist, Dealership.DoesNotExist, Mechanic.DoesNotExist):
            pass
        return None

    def mark_as_used(self):
        """Mark the OTP as used."""
        self.used = True
        self.save()

    def __str__(self) -> str:
        status = "Used" if self.used else ("Expired" if self.is_expired() else "Active")
        return f"OTP {self.code} for {self.valid_for.name} ({self.get_channel_display()}) - {status}"
    
    def __repr__(self):
        return f"<OTP: {self.code} - {self.valid_for.email} - {self.get_purpose_display()}>"
    
    @property
    def time_remaining(self):
        """Returns time remaining before expiration"""
        if self.is_expired():
            return "Expired"
        if self.expires_at:
            remaining = self.expires_at - timezone.now()
            minutes = int(remaining.total_seconds() / 60)
            return f"{minutes} minutes" if minutes > 0 else "Less than 1 minute"
        return "No expiration set"
    
    @property
    def attempts_remaining(self):
        """Returns number of attempts remaining"""
        return max(0, self.max_attempts - self.attempts)

    @classmethod
    def cleanup_expired(cls):
        """
        Clean up expired OTPs across the system.
        
        Returns:
            Dict with cleanup statistics
        """
        from django.utils import timezone
        
        now = timezone.now()
        
        # Delete expired OTPs
        expired_otps = cls.objects.filter(expires_at__lt=now)
        expired_count = expired_otps.count()
        expired_otps.delete()
        
        # Delete used OTPs older than 7 days
        old_used_otps = cls.objects.filter(
            used=True,
            date_created__lt=now - timezone.timedelta(days=7)
        )
        old_used_count = old_used_otps.count()
        old_used_otps.delete()
        
        return {
            'expired_deleted': expired_count,
            'old_used_deleted': old_used_count,
            'total_deleted': expired_count + old_used_count
        }

    @classmethod
    def get_rate_limit_status(cls, user, channel='email', purpose='verification'):
        """
        Check rate limit status for a user.
        
        Args:
            user: User instance
            channel: OTP channel (default: 'email')
            purpose: OTP purpose (default: 'verification')
            
        Returns:
            Dict with rate limit information
        """
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        # Count recent OTPs
        recent_hour_count = cls.objects.filter(
            valid_for=user,
            channel=channel,
            purpose=purpose,
            date_created__gte=hour_ago
        ).count()
        
        recent_day_count = cls.objects.filter(
            valid_for=user,
            channel=channel,
            purpose=purpose,
            date_created__gte=day_ago
        ).count()
        
        # Check for recent OTP (cooldown period)
        recent_otp = cls.objects.filter(
            valid_for=user,
            channel=channel,
            purpose=purpose,
            date_created__gte=now - timedelta(minutes=2)
        ).first()
        
        cooldown_remaining = 0
        if recent_otp:
            cooldown_remaining = max(0, int((recent_otp.date_created + timedelta(minutes=2) - now).total_seconds()))
        
        return {
            'hour_count': recent_hour_count,
            'hour_limit': 3,
            'day_count': recent_day_count,
            'day_limit': 10,
            'cooldown_remaining': cooldown_remaining,
            'can_request': (
                recent_hour_count < 3 and 
                recent_day_count < 10 and 
                cooldown_remaining == 0
            )
        }


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
        return types.get(ext, f"Unknown Document type => {ext}")
    
    def __str__(self):
        return f"{self.name or 'Unnamed File'} ({self.file_type()})"
    
    def __repr__(self):
        return f"<File: {self.name or self.file.name}>"
    
    @property
    def file_size(self):
        """Returns file size in human readable format"""
        try:
            size = self.file.size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except (AttributeError, OSError):
            return "Unknown size"
    
    @property
    def file_extension(self):
        """Returns the file extension"""
        if self.file and self.file.name:
            return self.file.name.split('.')[-1].upper()
        return "Unknown"
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]
        ordering = ['-date_created']
        verbose_name = 'File'
        verbose_name_plural = 'Files'


class Document(DbModel):
    DOCTYPES = [
        ('drivers-license', "Driver's License"),
        ('nin', "National Identification"),
        ('proof-of-address', "Proof of Address"),
    ]

    owner = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='owned_documents')
    doctype = models.CharField(max_length=200, choices=DOCTYPES)
    files = models.ManyToManyField('File', blank=True, related_name='document_files')
    
    def __str__(self):
        file_count = self.files.count()
        return f"{self.get_doctype_display()} for {self.owner.name} ({file_count} file{'s' if file_count != 1 else ''})"
    
    def __repr__(self):
        return f"<Document: {self.get_doctype_display()} - {self.owner.email}>"
    
    @property
    def total_files(self):
        """Returns the total number of files attached"""
        return self.files.count()
    
    @property
    def has_files(self):
        """Check if document has any files attached"""
        return self.files.exists()
    
    class Meta:
        indexes = [
            models.Index(fields=['owner']),
            models.Index(fields=['doctype']),
        ]
        ordering = ['-date_created']
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'



class BusinessVerificationSubmission(DbModel):
    """
    Stores business verification details submitted by dealers/mechanics
    for manual admin approval.
    
    Relationships:
        - OneToOneField to Dealership (on_delete=CASCADE, related_name='verification_submission')
          When a Dealership is deleted, the associated BusinessVerificationSubmission is automatically deleted.
          Access via: dealership.verification_submission
          
        - OneToOneField to Mechanic (on_delete=CASCADE, related_name='verification_submission')
          When a Mechanic is deleted, the associated BusinessVerificationSubmission is automatically deleted.
          Access via: mechanic.verification_submission
          
    Each business profile (Dealership or Mechanic) can have at most one verification submission.
    The CASCADE deletion ensures data integrity when business profiles are removed.
    """
    VERIFICATION_STATUS_CHOICES = {
        'not_submitted': 'Not Submitted',
        'pending': 'Pending Review',
        'verified': 'Verified',
        'rejected': 'Rejected',
    }
    
    BUSINESS_TYPE_CHOICES = {
        'dealership': 'Dealership',
        'mechanic': 'Mechanic',
    }
    
    # Link to the business profile
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPE_CHOICES)
    dealership = models.OneToOneField('Dealership', on_delete=models.CASCADE, null=True, blank=True, related_name='verification_submission')
    mechanic = models.OneToOneField('Mechanic', on_delete=models.CASCADE, null=True, blank=True, related_name='verification_submission')
    
    # Verification status
    status = models.CharField(max_length=20, default='pending', choices=VERIFICATION_STATUS_CHOICES)
    
    # Business details
    business_name = models.CharField(
        max_length=300,
        validators=[
            MinLengthValidator(2, message="Business name must be at least 2 characters long"),
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s\-\'\.&]+$',
                message="Business name can only contain letters, numbers, spaces, hyphens, apostrophes, periods, and ampersands"
            )
        ]
    )
    cac_number = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        help_text="Corporate Affairs Commission Number",
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{2}\d{6,8}$',
                message="Enter a valid CAC number (e.g., RC123456)"
            )
        ]
    )
    tin_number = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        help_text="Tax Identification Number",
        validators=[
            RegexValidator(
                regex=r'^\d{8}-\d{4}$',
                message="Enter a valid TIN number (format: 12345678-1234)"
            )
        ]
    )
    business_address = models.TextField(
        validators=[
            MinLengthValidator(10, message="Business address must be at least 10 characters long")
        ]
    )
    business_email = models.EmailField(
        validators=[EmailValidator(message="Enter a valid email address")]
    )
    business_phone = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?[1-9]\d{1,14}$',
                message="Enter a valid phone number"
            )
        ]
    )
    
    # Documents (uploaded files) - using Cloudinary for secure storage
    cac_document = CloudinaryField(
        'business_documents',
        folder='verification/cac',
        blank=True,
        null=True,
        resource_type='auto',
        help_text="CAC registration certificate (PDF, JPG, PNG - max 5MB)"
    )
    tin_document = CloudinaryField(
        'business_documents',
        folder='verification/tin',
        blank=True,
        null=True,
        resource_type='auto',
        help_text="TIN certificate (PDF, JPG, PNG - max 5MB)"
    )
    proof_of_address = CloudinaryField(
        'business_documents',
        folder='verification/address',
        blank=True,
        null=True,
        resource_type='auto',
        help_text="Proof of business address (PDF, JPG, PNG - max 5MB)"
    )
    business_license = CloudinaryField(
        'business_documents',
        folder='verification/license',
        blank=True,
        null=True,
        resource_type='auto',
        help_text="Business license or permit (PDF, JPG, PNG - max 5MB)"
    )
    
    # Document metadata tracking fields
    cac_document_uploaded_at = models.DateTimeField(null=True, blank=True)
    cac_document_original_name = models.CharField(max_length=255, blank=True)
    tin_document_uploaded_at = models.DateTimeField(null=True, blank=True)
    tin_document_original_name = models.CharField(max_length=255, blank=True)
    proof_of_address_uploaded_at = models.DateTimeField(null=True, blank=True)
    proof_of_address_original_name = models.CharField(max_length=255, blank=True)
    business_license_uploaded_at = models.DateTimeField(null=True, blank=True)
    business_license_original_name = models.CharField(max_length=255, blank=True)
    
    # Migration tracking
    migrated_to_cloudinary = models.BooleanField(default=False)
    migration_date = models.DateTimeField(null=True, blank=True)
    
    # Admin review
    reviewed_by = models.ForeignKey('Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_reviewed_verifications')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, null=True, help_text="Internal notes from admin review")
    rejection_reason = models.TextField(blank=True, null=True, help_text="Reason for rejection (shown to user)")
    
    def get_document_secure_url(self, document_field, expires_in=3600):
        """
        Generate secure, time-limited URL for document viewing
        
        Args:
            document_field: Name of the document field (e.g., 'cac_document')
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Secure URL string or None if document doesn't exist
        """
        try:
            from accounts.utils.document_storage import CloudinaryDocumentStorage
            
            document = getattr(self, document_field, None)
            if document and hasattr(document, 'public_id'):
                storage = CloudinaryDocumentStorage()
                return storage.get_secure_url(document.public_id, expires_in)
            return None
        except Exception:
            return None
    
    def get_document_thumbnail_url(self, document_field, width=150, height=150):
        """
        Generate thumbnail URL for document preview in admin
        
        Args:
            document_field: Name of the document field (e.g., 'cac_document')
            width: Thumbnail width in pixels
            height: Thumbnail height in pixels
            
        Returns:
            Thumbnail URL string or None if document doesn't exist
        """
        try:
            import cloudinary
            
            document = getattr(self, document_field, None)
            if document and hasattr(document, 'public_id'):
                # Generate thumbnail with transformation
                return cloudinary.CloudinaryImage(document.public_id).build_url(
                    width=width,
                    height=height,
                    crop='fill',
                    quality='auto',
                    format='auto'
                )
            return None
        except Exception:
            return None

    class Meta:
        verbose_name = 'Business Verification Submission'
        verbose_name_plural = 'Business Verification Submissions'
        ordering = ['-date_created']
        indexes = [
            models.Index(fields=['business_type']),
            models.Index(fields=['status']),
            models.Index(fields=['migrated_to_cloudinary']),
            models.Index(fields=['reviewed_at']),
        ]
    
    def __str__(self):
        return f"{self.business_name} ({self.get_business_type_display()}) - {self.get_status_display()}"
    
    def __repr__(self):
        return f"<BusinessVerification: {self.business_name} - {self.status}>"
    
    @property
    def documents_uploaded(self):
        """Returns count of uploaded documents"""
        docs = [self.cac_document, self.tin_document, self.proof_of_address, self.business_license]
        return sum(1 for doc in docs if doc and hasattr(doc, 'public_id') and doc.public_id)
    
    @property
    def required_documents_count(self):
        """Returns total number of required documents"""
        return 4  # CAC, TIN, Proof of Address, Business License
    
    @property
    def documents_completion_percentage(self):
        """Returns percentage of documents uploaded"""
        return round((self.documents_uploaded / self.required_documents_count) * 100, 1)
    
    @property
    def is_complete(self):
        """Check if all required information is provided"""
        return (
            self.business_name and
            self.business_address and
            self.business_email and
            self.business_phone and
            self.documents_uploaded >= 2  # At least 2 documents required
        )
    
    @property
    def days_since_submission(self):
        """Returns days since submission"""
        return (now().date() - self.date_created.date()).days
    
    @property
    def business_profile(self):
        """Returns the associated business profile (dealership or mechanic)"""
        return self.dealership if self.dealership else self.mechanic
    
    @property
    def documents_uploaded(self):
        """Returns count of uploaded documents"""
        count = 0
        document_fields = ['cac_document', 'tin_document', 'proof_of_address', 'business_license']
        for field_name in document_fields:
            document = getattr(self, field_name, None)
            if document and hasattr(document, 'public_id') and document.public_id:
                count += 1
        return count
    
    @property
    def required_documents_count(self):
        """Returns total number of required documents"""
        return 4  # cac_document, tin_document, proof_of_address, business_license
    
    @property
    def documents_completion_percentage(self):
        """Returns percentage of documents uploaded"""
        if self.required_documents_count == 0:
            return 100
        return int((self.documents_uploaded / self.required_documents_count) * 100)
    
    def approve(self, admin_user):
        """Approve the verification and update the business profile"""
        old_status = self.status
        self.status = 'verified'
        self.reviewed_by = admin_user
        self.reviewed_at = now()
        self.save()
        
        # Update the business profile
        business = self.business_profile
        if business:
            business.verified_business = True
            business.save()
        
        # Send notification email if status changed
        if old_status != 'verified':
            self._send_status_notification()
    
    def reject(self, admin_user, reason):
        """Reject the verification"""
        old_status = self.status
        self.status = 'rejected'
        self.reviewed_by = admin_user
        self.reviewed_at = now()
        self.rejection_reason = reason
        self.save()
        
        # Send notification email if status changed
        if old_status != 'rejected':
            self._send_status_notification()
    
    def _send_status_notification(self):
        """Send status change notification email"""
        try:
            from accounts.utils.email_notifications import send_business_verification_status
            
            # Get the user from the business profile
            business = self.business_profile
            if business and business.user:
                send_business_verification_status(
                    user=business.user,
                    status=self.status,
                    reason=self.rejection_reason or '',
                    business_name=self.business_name
                )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send verification status notification: {str(e)}")
    
    def clean(self):
        """Custom validation for BusinessVerificationSubmission"""
        super().clean()
        
        # Validate business type matches profile
        if self.business_type == 'dealership' and not self.dealership:
            raise ValidationError({'dealership': 'Dealership profile is required for dealership verification'})
        
        if self.business_type == 'mechanic' and not self.mechanic:
            raise ValidationError({'mechanic': 'Mechanic profile is required for mechanic verification'})
        
        # Validate email format
        if self.business_email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.business_email):
            raise ValidationError({'business_email': 'Enter a valid email address'})

    def save(self, *args, **kwargs):
        """Override save to track status changes"""
        # Clean before saving
        self.full_clean()
        
        # Normalize business details
        if self.business_name:
            self.business_name = self.business_name.strip()
        if self.business_address:
            self.business_address = self.business_address.strip()
        
        # Track if this is a status change
        if self.pk:
            try:
                old_instance = BusinessVerificationSubmission.objects.get(pk=self.pk)
                if old_instance.status != self.status and self.status in ['verified', 'rejected']:
                    # Status changed to final state, send notification
                    super().save(*args, **kwargs)
                    self._send_status_notification()
                    return
            except BusinessVerificationSubmission.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)


class DocumentAccessLog(DbModel):
    """
    Track document access attempts for security auditing and compliance.
    Logs all views, downloads, and thumbnail generations for business verification documents.
    """
    ACCESS_TYPE_CHOICES = [
        ('view', 'View'),
        ('download', 'Download'),
        ('thumbnail', 'Thumbnail'),
    ]
    
    submission = models.ForeignKey(
        'BusinessVerificationSubmission',
        on_delete=models.CASCADE,
        related_name='access_logs',
        help_text="The verification submission being accessed"
    )
    document_type = models.CharField(
        max_length=50,
        help_text="Type of document accessed (e.g., 'cac_document', 'tin_document')"
    )
    accessed_by = models.ForeignKey(
        'Account',
        on_delete=models.CASCADE,
        related_name='document_accesses',
        help_text="User who accessed the document"
    )
    access_type = models.CharField(
        max_length=20,
        choices=ACCESS_TYPE_CHOICES,
        default='view',
        help_text="Type of access performed"
    )
    ip_address = models.GenericIPAddressField(
        help_text="IP address of the user accessing the document"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="Browser user agent string"
    )
    success = models.BooleanField(
        default=True,
        help_text="Whether the access attempt was successful"
    )
    failure_reason = models.CharField(
        max_length=255,
        blank=True,
        help_text="Reason for access failure (if applicable)"
    )
    
    class Meta:
        verbose_name = 'Document Access Log'
        verbose_name_plural = 'Document Access Logs'
        ordering = ['-date_created']
        indexes = [
            models.Index(fields=['submission', 'document_type']),
            models.Index(fields=['accessed_by', 'date_created']),
            models.Index(fields=['access_type']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['success']),
            models.Index(fields=['date_created']),
        ]
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.accessed_by.email} - {self.get_access_type_display()} {self.document_type} ({status})"
    
    def __repr__(self):
        return f"<DocumentAccessLog: {self.accessed_by.email} - {self.document_type} - {self.access_type}>"
    
    @property
    def access_time_ago(self):
        """Returns human-readable time since access"""
        return timesince(self.date_created)
    
    @classmethod
    def log_access(cls, submission, document_type, user, access_type, ip_address, user_agent='', success=True, failure_reason=''):
        """
        Convenience method to log document access
        
        Args:
            submission: BusinessVerificationSubmission instance
            document_type: Type of document (e.g., 'cac_document')
            user: User who accessed the document
            access_type: Type of access ('view', 'download', 'thumbnail')
            ip_address: IP address of the user
            user_agent: Browser user agent string
            success: Whether the access was successful
            failure_reason: Reason for failure if applicable
            
        Returns:
            DocumentAccessLog instance
        """
        return cls.objects.create(
            submission=submission,
            document_type=document_type,
            accessed_by=user,
            access_type=access_type,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else '',  # Truncate user agent
            success=success,
            failure_reason=failure_reason
        )
    
    @property
    def document_display_name(self):
        """Returns human-readable document name"""
        display_names = {
            'cac_document': 'CAC Document',
            'tin_document': 'TIN Document',
            'proof_of_address': 'Proof of Address',
            'business_license': 'Business License',
        }
        return display_names.get(self.document_type, self.document_type.replace('_', ' ').title())
    
    @classmethod
    def log_access(cls, submission, document_type, user, access_type, ip_address, user_agent='', success=True, failure_reason=''):
        """
        Convenience method to create an access log entry
        
        Args:
            submission: BusinessVerificationSubmission instance
            document_type: String name of the document field
            user: Account instance accessing the document
            access_type: Type of access ('view', 'download', 'thumbnail')
            ip_address: IP address of the user
            user_agent: Browser user agent string (optional)
            success: Whether the access was successful (default: True)
            failure_reason: Reason for failure if success=False (optional)
            
        Returns:
            DocumentAccessLog instance
        """
        return cls.objects.create(
            submission=submission,
            document_type=document_type,
            accessed_by=user,
            access_type=access_type,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            failure_reason=failure_reason
        )
    
    @classmethod
    def get_recent_accesses(cls, submission, limit=10):
        """Get recent access logs for a submission"""
        return cls.objects.filter(submission=submission).order_by('-date_created')[:limit]
    
    @classmethod
    def get_failed_accesses(cls, submission=None, days=7):
        """Get failed access attempts within the specified days"""
        from datetime import timedelta
        cutoff_date = now() - timedelta(days=days)
        
        queryset = cls.objects.filter(success=False, date_created__gte=cutoff_date)
        if submission:
            queryset = queryset.filter(submission=submission)
        
        return queryset.order_by('-date_created')
    
    @classmethod
    def get_user_access_count(cls, user, days=30):
        """Get total document accesses by a user within specified days"""
        from datetime import timedelta
        cutoff_date = now() - timedelta(days=days)
        
        return cls.objects.filter(
            accessed_by=user,
            date_created__gte=cutoff_date
        ).count()


# use as ref to old imports for now
# TODO: rename old imports before staging
Dealer = Dealership

class ReferralSetting(DbModel):
    """
    Singleton model to store referral program configuration.
    """
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, default=5000.00, help_text="Amount to reward the referrer")
    currency = models.CharField(max_length=3, default='NGN', help_text="Currency of the reward")
    is_active = models.BooleanField(default=True, help_text="Enable or disable the referral program")
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Minimum purchase amount required to trigger reward")

    class Meta:
        verbose_name = "Referral Setting"
        verbose_name_plural = "Referral Settings"

    def __str__(self):
        return f"Referral Reward: {self.currency} {self.reward_amount}"

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj


class ReferralReward(DbModel):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    )

    referrer = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='referral_rewards_earned')
    referred_user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='referral_rewards_triggered')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='NGN')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    transaction_ref = models.CharField(max_length=100, blank=True, null=True, help_text="Reference of the qualifying transaction")
    
    class Meta:
        verbose_name = "Referral Reward"
        verbose_name_plural = "Referral Rewards"
        unique_together = ('referrer', 'referred_user')  # One reward per referred user

    def __str__(self):
        return f"{self.referrer.email} earned {self.currency} {self.amount} from {self.referred_user.email}"
