from django.db import models
from utils.models import DbModel
from decimal import Decimal


# Create your models here.
class Vehicle(DbModel):
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=200)
    brand = models.CharField(max_length=200)
    last_rented = models.DateTimeField(max_length=200)
    current_rental = models.ForeignKey('CarRental', blank=True, null=True, on_delete=models.SET_NULL)
    available = models.BooleanField(default=False)
    for_sale = models.BooleanField(default=False)
    sold = models.BooleanField(default=False)
    category = models.ForeignKey('VehicleCategory', on_delete=models.SET_NULL, blank=True, null=True)
    tags = models.ManyToManyField('VehicleTag', blank=True)


class VehicleCategory(DbModel):
    name = models.CharField(max_length=200)


class VehicleTag(DbModel):
    name = models.CharField(max_length=200)


class CarRental(DbModel):
    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE)
    order = models.ForeignKey('Order', on_delete=models.CASCADE)


class Order(DbModel):
    ORDER_TYPES  = {'rental': 'Car Rental', 'sale': 'Car Sale'}
    ORDER_STATUS  = {'rental': 'Car Rental', 'sale': 'Car Sale'}

    order_type = models.CharField(max_length=20, choices=ORDER_TYPES)
    order_items = models.ManyToManyField('Listing', blank=True)
    sub_total = models.DecimalField(max_digits=3, decimal_places=2)
    discount = models.DecimalField(max_digits=3, decimal_places=2, default=10.00, blank=True, null=True)
    tax = models.DecimalField(max_digits=3, decimal_places=2, default=10.00)
    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE)
    paid = models.BooleanField(default=False)

    @property
    def total(self):
        amt = self.sub_total
        if self.discount:
            amt -= self.discount
        amt += (self.tax/100 * amt)
        return amt


class Listing(DbModel):
    LISTING_TYPES  = {'rental': 'Car Rental', 'sale': 'Car Sale'}

    listing_type = models.CharField(max_length=20, choices=LISTING_TYPES)
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, blank=True, null=True, related_name='approved_by')
    created_by = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='created_by')
    vehicle = models.ForeignKey('Vehicle', on_delete=models.CASCADE)
    sale_price = models.DecimalField(decimal_places=2, max_digits=10000, blank=True, null=True)
    rental_price = models.DecimalField(decimal_places=2, max_digits=10000)
    title = models.CharField(max_length=400, blank=True, null=True)
    views = models.PositiveIntegerField(default=0)
    viewers = models.ManyToManyField('accounts.Account', limit_choices_to={'user_type': 'customer'}, blank=True, related_name='viewers')

    def __str__(self) -> str:
        return self.title


