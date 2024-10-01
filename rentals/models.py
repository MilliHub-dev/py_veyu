from django.db import models
from utils.models import DbModel
from decimal import Decimal, InvalidOperation
from django.utils import timezone


class VehicleImage(DbModel):
    image = models.ImageField(upload_to='vehicles/images/')
    vehicle = models.ForeignKey('Vehicle', on_delete=models.CASCADE)


# Create your models here.
class Vehicle(DbModel):
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('used_uk', 'Used (UK)'),
        ('used_ng', 'Used (Nigerian)'),
        ('used_be', 'Used (Belgium)'),
    ]

    dealer = models.ForeignKey('accounts.Dealer', blank=True, null=True, on_delete=models.SET_NULL, related_name='dealer')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True, null=True)
    color = models.CharField(max_length=200)
    brand = models.CharField(max_length=200)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='used_uk')
    last_rented = models.DateTimeField(max_length=200, blank=True, null=True)
    current_rental = models.ForeignKey('CarRental', blank=True, null=True, on_delete=models.SET_NULL)
    available = models.BooleanField(default=True)
    for_sale = models.BooleanField(default=False)
    sold = models.BooleanField(default=False)
    category = models.ForeignKey('VehicleCategory', on_delete=models.SET_NULL, blank=True, null=True)
    tags = models.ManyToManyField('VehicleTag', blank=True)
    images = models.ManyToManyField(VehicleImage, blank=True, related_name='images')
    video = models.FileField(upload_to='vehicles/videos/', blank=True, null=True)
    # to update the listing when been created
    sale_price = models.DecimalField(decimal_places=2, max_digits=10000, blank=True, null=True)
    rental_price = models.DecimalField(decimal_places=2, max_digits=10000, null=False)
    listing_title = models.CharField(max_length=400, blank=True, null=True)

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
    # start_date = models.DateTimeField()
    # end_date = models.DateTimeField()
    # days = models.PositiveIntegerField()


    # # logic to calculate the number of days bases of the start and end date
    # def save(self, *args, **kwargs):
    #     if not self.days:
    #         self.days = (self.end_date - self.start_date).days
    #     return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.customer.account.email}  - Order #{self.order.id}'



class Order(DbModel):
    ORDER_TYPES  = {'rental': 'Car Rental', 'sale': 'Car Sale'}
    ORDER_STATUS  = {'rental': 'Car Rental', 'sale': 'Car Sale'}

    order_type = models.CharField(max_length=20, choices=[(key, value) for key, value in ORDER_TYPES.items()])
    order_items = models.ManyToManyField('Listing', blank=True)
    sub_total = models.CharField(max_length=13, blank=True, null=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=10.00, blank=True, null=True)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE)
    paid = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        try:
            # Ensure sub_total is a valid Decimal value
            if self.sub_total and not self.pk:
                self.sub_total = Decimal(self.sub_total)

                # Calculate commission using Decimal to avoid rounding issues
                self.commission = Decimal('0.02') * self.sub_total

            super().save(*args, **kwargs)

        except InvalidOperation as e:
            raise ValueError(f"Invalid decimal value: {e}")

    @property
    def total(self):
        # Use Decimal for all calculations
        amt = self.sub_total if self.sub_total else Decimal('0.00')

        # Apply the discount percentage if it exists
        if self.discount:
            discount_amount = (self.discount / Decimal('100.00')) * amt
            amt -= discount_amount

        # Add the commission
        amt += self.commission

        return amt

    def __str__(self):
        return f"Order #{self.id} - {self.ORDER_TYPES.get(self.order_type, 'Unknown')}"

class Listing(DbModel):
    LISTING_TYPES  = {'rental': 'Car Rental', 'sale': 'Car Sale'}

    listing_type = models.CharField(max_length=20, choices=LISTING_TYPES)
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, blank=True, null=True, related_name='approved_by')
    created_by = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='created_by')
    vehicle = models.ForeignKey('Vehicle', on_delete=models.CASCADE)
    sale_price = models.DecimalField(decimal_places=2, max_digits=10000, blank=True, null=True)
    rental_price = models.DecimalField(decimal_places=2, max_digits=10000, null=False)
    title = models.CharField(max_length=400, blank=True, null=True)
    views = models.PositiveIntegerField(default=0)
    viewers = models.ManyToManyField('accounts.Account', limit_choices_to={'user_type': 'customer'}, blank=True, related_name='viewers')
    offers = models.ManyToManyField('PurchaseOffer', blank=True, related_name='offers')
    testdrives = models.ManyToManyField('TestDriveRequest', blank=True, related_name='testdrives')

    def __str__(self):
        return f'{self.title}'

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

    



