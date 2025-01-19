from django.db import models
from utils.models import DbModel
from decimal import Decimal, InvalidOperation
from django.utils import timezone


class VehicleImage(DbModel):
    image = models.ImageField(upload_to='vehicles/images/')
    vehicle = models.ForeignKey('Vehicle', on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.id:
            ext = self.image.name.split('.')[-1]
            count = self.vehicle.images.count()
            self.image.name = f'{self.vehicle.slug}_image-{count}.{ext}'
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
        ('Electric', 'Electric'),
        ('petrol', 'Petrol'),
        ('hybrid', 'Hybrid'),
    ]
    VEHICLE_TYPE = [
        ('sedan', 'Sedan'),
        ('convertible', 'Convertible'),
        ('suv', 'Sub-Urban Vehicle'),
        ('truck', 'Truck'),
    ]

    dealer = models.ForeignKey('accounts.Dealer', blank=True, null=True, on_delete=models.SET_NULL, related_name='dealer')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True, null=True)
    
    # car details
    color = models.CharField(max_length=200)
    brand = models.CharField(max_length=200) # aka make
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='used_uk')
    type = models.CharField(max_length=200, choices=VEHICLE_TYPE, default='sedan')
    mileage = models.CharField(max_length=200, blank=True, null=True)
    transmission = models.CharField(max_length=200, blank=True, null=True, choices=TRANSMISSION)
    fuel_system = models.CharField(max_length=200, blank=True, null=True, choices=FUEL_SYSTEM)
    images = models.ManyToManyField(VehicleImage, blank=True, related_name='images')
    video = models.FileField(upload_to='vehicles/videos/', blank=True, null=True)
    tags = models.ManyToManyField('VehicleTag', blank=True)
    custom_duty = models.BooleanField(default=False)
    
    
    # rental history
    last_rental = models.ForeignKey('CarRental', blank=True, null=True, on_delete=models.SET_NULL, related_name='last_rental')
    current_rental = models.ForeignKey('CarRental', blank=True, null=True, on_delete=models.SET_NULL, related_name='current_rental')
    rentals = models.ManyToManyField('CarRental', blank=True, related_name='rentals')
    
    # availability
    available = models.BooleanField(default=True)
    for_sale = models.BooleanField(default=False)
    for_rent = models.BooleanField(default=False)
    sold = models.BooleanField(default=False) # sold items can't be listed


    def __str__(self):
        return self.name or 'Unnamed Vehicle'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.name.replace(' ', '-').replace('.', '').replace("'", '').lower().strip()
        return super().save(*args, **kwargs)

class VehicleCategory(DbModel):
    name = models.CharField(max_length=200)

    class Meta:
        verbose_name_plural = 'Vehicle Categories'

    def __str__(self):
        return self.name

class VehicleTag(DbModel):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name or 'Unnamed Vehicle'

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


class Order(DbModel):
    ORDER_TYPES  = {'rental': 'Car Rental', 'sale': 'Car Sale'}
    ORDER_STATUS  = {
        'awaiting-inspection': 'Awaiting Inspection',
        'inspecting': 'Inspecting',
        'pending': 'Pending',
        'successful': 'Successful',
    }
    PAYMENT_OPTION  = {
        'pay-after-inspection': 'Inspecting',
        'card': 'Credit Card',
        'financial-aid': 'Financing Aid',
    }

    order_type = models.CharField(max_length=20, choices=ORDER_TYPES)
    order_items = models.ManyToManyField('OrderItem', blank=True)
    payment_option = models.CharField(max_length=20, choices=ORDER_TYPES, default="Not Available")
    sub_total = models.DecimalField(decimal_places=2, max_digits=100, blank=True, null=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=10.00, blank=True, null=True)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE)
    paid = models.BooleanField(default=False)

    # def save(self, *args, **kwargs):
    #     try:
    #         # Ensure sub_total is a valid Decimal value
    #         if self.sub_total and not self.pk:
    #             # self.sub_total = Decimal(self.sub_total)

    #             # Calculate commission using Decimal to avoid rounding issues
    #             self.commission = Decimal('0.02') * self.sub_total

    #         super().save(*args, **kwargs)

    #     except InvalidOperation as e:
    #         raise ValueError(f"Invalid decimal value: {e}")

    @property
    def total(self):
        amt = self.sub_total
        if self.discount:
            amt -= ((self.discount / 100) * amt)
        if self.commission:
            amt += ((self.commission / 100) * self.sub_total)
        return amt

    def __str__(self):
        return f"Order #{self.id} - {self.ORDER_TYPES.get(self.order_type, 'Unknown')}"



class Listing(DbModel):
    LISTING_TYPES  = {'rental': 'Car Rental', 'sale': 'Car Sale'}
    PAYMENT_CYCLES = [
        ('weekly', 'Weekly Payments'),
        ('bi-weekly', 'Bi-Weekly Payments'),
        ('monthly', 'Monthly Payments'),
        ('bi-monthly', 'Bi-Monthly Payments'),
        ('quarterly', 'Quarterly Payments'),
        ('semi-annually', 'Semi-Annual Payments'),
        ('annually', 'Annual Payments'),
    ]

    listing_type = models.CharField(max_length=20, choices=LISTING_TYPES, default='sale')
    verified = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, blank=True, null=True, related_name='approved_by')
    created_by = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='created_by')
    vehicle = models.ForeignKey('Vehicle', on_delete=models.CASCADE)
    price = models.DecimalField(decimal_places=2, max_digits=10000, blank=True, null=True)
    title = models.CharField(max_length=400, blank=True, null=True)
    views = models.PositiveIntegerField(default=0)
    viewers = models.ManyToManyField('accounts.Account', limit_choices_to={'user_type': 'customer'}, blank=True, related_name='viewers')
    offers = models.ManyToManyField('PurchaseOffer', blank=True, related_name='offers')
    testdrives = models.ManyToManyField('TestDriveRequest', blank=True, related_name='testdrives')
    payment_cycle = models.CharField(max_length=20, choices=PAYMENT_CYCLES, default='monthly', blank=True,)

    def __str__(self):
        return f'{self.title}'
    
    def save(self, *args, **kwargs):
        if not self.title and self.vehicle:
            self.title = self.vehicle.name
        super().save(*args, **kwargs)


class PurchaseOffer(DbModel):
    bidder = models.ForeignKey('accounts.Customer', models.CASCADE, related_name='bidder')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='listing')
    amount = models.DecimalField(decimal_places=2, max_digits=10000)


class TestDriveRequest(DbModel):
    requested_by = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE)
    requested_to = models.ForeignKey('accounts.Dealer', on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    granted = models.BooleanField(default=False)
    testdrive_complete = models.BooleanField(default=False)


class TradeInRequest(DbModel):
    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE)
    vehicle = models.ForeignKey('Vehicle', on_delete=models.CASCADE)
    estimated_value = models.DecimalField(decimal_places=2, max_digits=10000)
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Trade-in Request from {self.customer.account.email}'



class OrderItem(DbModel):
    ORDER_ITEM_TYPES = {
        'car': 'Car',
        'service': 'Service',
        'rental': 'Rental',
    }
    cart = models.ForeignKey('accounts.CustomerCart', on_delete=models.CASCADE)
    listing = models.ForeignKey("Listing", on_delete=models.CASCADE, blank=True, null=True)
    service = models.ForeignKey("bookings.ServiceOffering", on_delete=models.CASCADE, blank=True, null=True)
    item_type = models.CharField(max_length=50, default='car', choices=ORDER_ITEM_TYPES)


