from django.db import models
from utils.models import DbModel, ArrayField
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from django.utils.timezone import now
from django.db.models import Q


PAYMENT_CYCLES = [
    ('single', 'One Time / Single Payment'),
    ('day', 'Daily Payments'),
    ('week', 'Weekly Payments'),
    ('month', 'Monthly Payments'),
    ('year', 'Annual Payments'),
]

VEHICLE_FEATURES = [
    'Air Conditioning',
    'Android Auto',
    'Auto Drive',
    'Keyless Entry',
    'Baby Seat',
    'Lane Assist',
    'Parking Camera',
    'Sun Roof',
]


class VehicleImage(DbModel):
    image = models.ImageField(upload_to='vehicles/images/', blank=True, null=True)
    vehicle = models.ForeignKey('Vehicle', on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        # if not self.id:
            # print("Image saving...", self.image)
            # ext = self.image.name.split('.')[-1]
            # count = self.vehicle.images.count()
            # self.image.name = f'{self.vehicle.slug}_image-{count}.{ext}'
        super().save(*args, **kwargs)


    def __str__(self):
        return self.image.name


class Vehicle(DbModel):
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('used_uk', 'Used (UK)'),
        ('used_ng', 'Used (Nigerian)'),
        ('used_be', 'Used (Belgium)'),
    ]
    TRANSMISSION = [
        ('auto', 'Automatic'),
        ('manual', 'Manual'),
    ]
    FUEL_SYSTEM = [
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('petrol', 'Petrol'),
        ('hybrid', 'Hybrid'),
    ]
    VEHICLE_TYPE = [
        ('sedan', 'Sedan'),
        ('convertible', 'Convertible'),
        ('suv', 'Sub-Urban Vehicle'),
        ('truck', 'Truck'),
    ]

    DRIVETRAIN = {
        '4WD' : 'Four Wheel Drive',
        'AWD' : 'All Wheel Drive',
        'FWD' : 'Front Wheel Drive',
    }

    dealer = models.ForeignKey('accounts.Dealership', blank=True, null=True, on_delete=models.SET_NULL, related_name='dealer')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True, null=True)

    # car details
    color = models.CharField(max_length=200)
    brand = models.CharField(max_length=200) # aka make
    model = models.CharField(max_length=200, blank=True, null=True) # aka make
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='used_uk')
    type = models.CharField(max_length=200, choices=VEHICLE_TYPE, default='sedan')
    mileage = models.CharField(max_length=200, blank=True, null=True)
    transmission = models.CharField(max_length=200, blank=True, null=True, choices=TRANSMISSION)
    fuel_system = models.CharField(max_length=200, blank=True, null=True, choices=FUEL_SYSTEM)
    drivetrain = models.CharField(max_length=200, blank=True, null=True, choices=DRIVETRAIN)
    seats = models.PositiveIntegerField(blank=True, null=True, default=5)
    doors = models.PositiveIntegerField(blank=True, null=True, default=4)
    vin = models.CharField(max_length=200, blank=True, null=True,)

    images = models.ManyToManyField(VehicleImage, blank=True, related_name='images')
    video = models.FileField(upload_to='vehicles/videos/', blank=True, null=True)
    tags = ArrayField(blank=True, null=True, data_type='str')
    custom_duty = models.BooleanField(default=False)
    features = ArrayField(blank=True, null=True, data_type='str')

    # rental history
    last_rental = models.ForeignKey('CarRental', blank=True, null=True, on_delete=models.SET_NULL, related_name='last_rental')
    current_rental = models.ForeignKey('CarRental', blank=True, null=True, on_delete=models.SET_NULL, related_name='current_rental')
    rentals = models.ManyToManyField('CarRental', blank=True, related_name='rentals')

    # availability
    available = models.BooleanField(default=True) # sold / rented items can't be listed
    for_sale = models.BooleanField(default=False)
    for_rent = models.BooleanField(default=False)

    def __str__(self):
        return self.name or 'Unnamed Vehicle'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.name.replace(' ', '-').replace('.', '').replace("'", '').lower().strip()
        return super().save(*args, **kwargs)

    def trips(self):
        return self.rentals.count()


class CarRental(DbModel):
    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE)
    order = models.ForeignKey('Order', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.customer.account.email}  - Order #{self.order.id}'


class CarPurchase(DbModel):
    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE)
    order = models.ForeignKey('Order', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.customer.account.email}  - Order #{self.order.id}'


def to_decimal(dig):
    """
    convert digit to decimal using decimal.Decimal
    """
    from decimal import Decimal
    dec = Decimal(str(dig))
    return dec


def float_decimal(dig, dec_places=2):
    """
    convert a number to a decimal-like float using float and round
    set dec_places to how many decimal places required
    """
    dec = round(float(dig), dec_places)
    return dec


class OrderInspection(DbModel):
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE)
    inspection_date = models.DateField(blank=True, null=True)
    inspection_time = models.TimeField(blank=True, null=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Scheduled Inspection for {self.order.listing.title}"


class Order(DbModel):
    ORDER_TYPES  = {'rental': 'Car Rental', 'sale': 'Car Sale'}
    ORDER_STATUS  = {
        'awaiting-inspection': 'Awaiting Inspection',
        'inspecting': 'Inspecting',
        'pending': 'Pending',
        'completed': 'Completed',
        'expired': 'Expired', # when a rental expires
        'renewed': 'Renewed', # when a rental is renewed
    }
    PAYMENT_OPTION  = {
        'pay-after-inspection': 'Payment after Inspection',
        'wallet': 'Motaa Wallet',
        'card': 'Credit / Debit Card',
        'financial-aid': 'Financing Aid',
    }

    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES)
    order_item = models.ForeignKey('Listing', blank=True, null=True, on_delete=models.CASCADE)
    payment_option = models.CharField(max_length=20, choices=PAYMENT_OPTION, default="Not Available")
    paid = models.BooleanField(default=False)
    order_status = models.CharField(max_length=50, choices=ORDER_STATUS, default='pending')
    applied_coupons = models.ManyToManyField('Coupon', blank=True)
    # for rentals
    is_recurring = models.BooleanField(default=False)
    payment_cycle = models.CharField(max_length=20, choices=PAYMENT_CYCLES, default="month")
    rent_from = models.DateField(blank=True, null=True)
    rent_until = models.DateField(blank=True, null=True)
    last_payment = models.DateField(blank=True, null=True)
    next_payment = models.DateField(blank=True, null=True)

    @property
    def sub_total(self):
        amt = 0
        if self.is_recurring:
            cycle = 1
            days = 30 # count days
            amt += (self.order_item.listing.price/30) * days
        else:
            amt += self.order_item.listing.price

        # 0.5% added fees
        amt += ((0.5/100) * amt)

    @property
    def total(self):
        amt = self.sub_total
        # add discounts from coupons
        for coupon in self.coupons.all():
            val = coupon.discount_value
            if coupon.discount_type == 'percentage':
                val = ((coupon.discount_value/100) * amt)
            amt -= val
        # add 0.5% commission
        amt += ((0.5 / 100) * amt)
        return amt

    def __str__(self):
        return f"Order #{self.id} - {self.ORDER_TYPES.get(self.order_type, 'Unknown')}"



class Coupon(DbModel):
    # motaa can issue coupons that are valid in all dealerships
    issuer = models.CharField(max_length=20, default='dealership') # motaa | dealership
    valid_in = models.ManyToManyField('accounts.Dealership', blank=True)
    expires = models.DateTimeField(blank=True, null=True)
    users = models.ManyToManyField('accounts.Customer', blank=True)
    discount_type = models.CharField(max_length=20, default='flat') # flat | percentage
    discount_value = models.DecimalField(decimal_places=2, default=0.00, max_digits=1000)
    code = models.CharField(blank=True, null=True, max_length=20)

    def __str__(self):
        return self.code

    @property
    def dealership(self):
        if self.issuer == 'motaa':
            return 'Motaa'
        else:
            return self.valid_in.first().business_name




class Listing(DbModel):
    LISTING_TYPES  = {'rental': 'Car Rental', 'sale': 'Car Sale'}

    listing_type = models.CharField(max_length=20, choices=LISTING_TYPES, default='sale')
    verified = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, blank=True, null=True, related_name='approved_by')
    created_by = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='created_by')
    vehicle = models.ForeignKey('Vehicle', on_delete=models.CASCADE)
    price = models.DecimalField(decimal_places=2, max_digits=10000, blank=True, null=True)
    title = models.CharField(max_length=400, blank=True, null=True)
    viewers = models.ManyToManyField('accounts.Account', limit_choices_to={'user_type': 'customer'}, blank=True, related_name='viewers')
    offers = models.ManyToManyField('PurchaseOffer', blank=True, related_name='offers')
    testdrives = models.ManyToManyField('TestDriveRequest', blank=True, related_name='testdrives')
    payment_cycle = models.CharField(max_length=20, choices=PAYMENT_CYCLES, default='week', blank=True,)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.title}'

    @property
    def published(self) -> bool: return self.verified

    def publish(self):
        self.verified = True
        self.save()

    def save(self, *args, **kwargs):
        if not self.title and self.vehicle:
            self.title = self.vehicle.name
        super().save(*args, **kwargs)


class ListingBoost(DbModel):
    listing = models.OneToOneField('Listing', on_delete=models.CASCADE, related_name='boosted')
    start_date = models.DateField()
    end_date = models.DateField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)  # Track payment amount
    active = models.BooleanField(default=True)  # Auto-updated by cron job

    def is_active(self):
        return self.start_date <= now().date() <= self.end_date

    def save(self, *args, **kwargs):
        """Ensure `active` is updated before saving."""
        self.active = self.is_active()
        super().save(*args, **kwargs)

    def __str__(self):
        status = "Active" if self.is_active() else "Expired"
        return f"{self.listing.title} - {status} ({self.start_date} to {self.end_date})"



class PurchaseOffer(DbModel):
    bidder = models.ForeignKey('accounts.Customer', models.CASCADE, related_name='bidder')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='listing')
    amount = models.DecimalField(decimal_places=2, max_digits=10000)


class TestDriveRequest(DbModel):
    requested_by = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE)
    requested_to = models.ForeignKey('accounts.Dealership', on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    granted = models.BooleanField(default=False)
    testdrive_complete = models.BooleanField(default=False)


class TradeInRequest(DbModel):
    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE)
    to = models.ForeignKey('accounts.Dealership', on_delete=models.CASCADE)
    vehicle = models.ForeignKey('Vehicle', on_delete=models.CASCADE)
    estimated_value = models.DecimalField(decimal_places=2, max_digits=10000)
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Trade-in Request from {self.customer.account.email}'


