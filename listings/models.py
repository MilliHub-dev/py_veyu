from django.db import models
from utils.models import DbModel, ArrayField
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from django.utils.timezone import now
from django.db.models import Q
from cloudinary.models import CloudinaryField

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
    image = CloudinaryField('image', folder='vehicles/images/', blank=True, null=True)
    vehicle = models.ForeignKey('Vehicle', on_delete=models.CASCADE, related_name='vehicle_images')

    def save(self, *args, **kwargs):
        # if not self.id:
            # print("Image saving...", self.image)
            # ext = self.image.name.split('.')[-1]
            # count = self.vehicle.images.count()
            # self.image.name = f'{self.vehicle.slug}_image-{count}.{ext}'
        super().save(*args, **kwargs)


    def __str__(self):
        # Return the public_id or URL of the Cloudinary image
        if hasattr(self.image, 'public_id'):
            return f"Image for {self.vehicle.name}: {self.image.public_id}"
        return f"Image for {self.vehicle.name}: {str(self.image)}"
    
    def __repr__(self):
        return f"<VehicleImage: {self.vehicle.name} - {self.image}>"
    
    class Meta:
        indexes = [
            models.Index(fields=['vehicle']),
        ]
        ordering = ['id']
        verbose_name = 'Vehicle Image'
        verbose_name_plural = 'Vehicle Images'


class Vehicle(DbModel):
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('used-foreign', 'Foreign Used'),
        ('used-local', 'Local Used'),
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

    dealer = models.ForeignKey('accounts.Dealership', blank=True, null=True, on_delete=models.SET_NULL, related_name='owned_vehicles')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True, null=True)
    brand = models.CharField(max_length=200)
    model = models.CharField(max_length=200, blank=True, null=True)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='used-foreign')
    fuel_system = models.CharField(max_length=200, blank=True, null=True, choices=FUEL_SYSTEM)
    transmission = models.CharField(max_length=200, blank=True, null=True, choices=TRANSMISSION)
    color = models.CharField(max_length=200)
    mileage = models.CharField(max_length=200, blank=True, null=True)

    for_sale = models.BooleanField(default=False)
    for_rent = models.BooleanField(default=False)
    available = models.BooleanField(default=True)

    images = models.ManyToManyField(VehicleImage, blank=True, related_name='vehicle_gallery')
    video = models.FileField(upload_to='vehicles/videos/', blank=True, null=True)
    tags = ArrayField(blank=True, null=True, data_type=str, default=list)
    features = ArrayField(blank=True, null=True, data_type=str, default=list)
    custom_duty = models.BooleanField(default=False)

    last_rental = models.ForeignKey('RentalOrder', blank=True, null=True, on_delete=models.SET_NULL, related_name='last_rental_vehicle')
    current_rental = models.ForeignKey('RentalOrder', blank=True, null=True, on_delete=models.SET_NULL, related_name='current_rental_vehicle')
    rentals = models.ManyToManyField('RentalOrder', blank=True, related_name='rental_vehicles')

    def __str__(self):
        availability = "Available" if self.available else "Unavailable"
        return f"{self.name or 'Unnamed Vehicle'} ({self.brand} {self.model or ''}) - {availability}".strip()
    
    def __repr__(self):
        return f"<Vehicle: {self.name} - {self.brand} {self.model}>"
    
    @property
    def full_name(self):
        """Returns full vehicle name with brand and model"""
        parts = [self.brand]
        if self.model:
            parts.append(self.model)
        if self.name and self.name not in ' '.join(parts):
            parts.append(f"({self.name})")
        return ' '.join(parts)
    
    @property
    def total_images(self):
        """Returns total number of images"""
        return self.images.count()
    
    @property
    def rental_status(self):
        """Returns current rental status"""
        if self.current_rental:
            return "Currently Rented"
        elif self.for_rent:
            return "Available for Rent"
        else:
            return "Not for Rent"

    def save(self, *args, **kwargs):
        # Ensure tags and features are lists before saving
        if self.tags is None:
            self.tags = []
        if self.features is None:
            self.features = []
            
        if not self.slug:
            self.slug = self.name.replace(' ', '-').replace('.', '').replace("'", '').lower().strip()
        return super().save(*args, **kwargs)

    def trips(self):
        return self.rentals.count()
    
    class Meta:
        indexes = [
            models.Index(fields=['dealer']),
            models.Index(fields=['brand', 'model']),
            models.Index(fields=['condition']),
            models.Index(fields=['fuel_system']),
            models.Index(fields=['transmission']),
            models.Index(fields=['for_sale', 'for_rent']),
            models.Index(fields=['available']),
            models.Index(fields=['slug']),
            models.Index(fields=['date_created']),
        ]
        ordering = ['-date_created']


class Car(Vehicle):
    DRIVETRAIN = [
        ('4WD', 'Four Wheel Drive'),
        ('AWD', 'All Wheel Drive'),
        ('FWD', 'Front Wheel Drive'),
        ('RWD', 'Rear Wheel Drive'),
    ]

    BODY_TYPE_CHOICES = [
        ('suv', 'SUV'),
        ('sedan', 'Sedan'),
        ('hatchback', 'Hatchback'),
        ('coupe', 'Coupe'),
        ('convertible', 'Convertible'),
        ('pickup', 'Pickup Truck'),
        ('van', 'Van/Minivan'),
        ('wagon', 'Wagon'),
        ('luxury', 'Luxury'),
        ('sport', 'Sports Car'),
    ]

    doors = models.PositiveIntegerField(blank=True, null=True, default=4)
    seats = models.PositiveIntegerField(blank=True, null=True, default=5)
    drivetrain = models.CharField(max_length=200, blank=True, null=True, choices=DRIVETRAIN)
    body_type = models.CharField(max_length=50, blank=True, null=True, choices=BODY_TYPE_CHOICES)
    vin = models.CharField(max_length=200, blank=True, null=True)


class Boat(Vehicle):
    hull_material = models.CharField(max_length=100, blank=True, null=True)
    engine_count = models.PositiveIntegerField(blank=True, null=True)
    propeller_type = models.CharField(max_length=100, blank=True, null=True)
    length = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)  # in feet/meters
    beam_width = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    draft = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)


class Plane(Vehicle):
    AIRCRAFT_TYPE_CHOICES = [
        ('jet', 'Jet'),
        ('propeller', 'Propeller'),
        ('glider', 'Glider'),
        ('helicopter', 'Helicopter'),
    ]

    registration_number = models.CharField(max_length=100, blank=True, null=True)
    engine_type = models.CharField(max_length=100, blank=True, null=True)
    aircraft_type = models.CharField(max_length=50, choices=AIRCRAFT_TYPE_CHOICES, blank=True, null=True)
    max_altitude = models.PositiveIntegerField(blank=True, null=True)  # in feet
    wing_span = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    range = models.PositiveIntegerField(blank=True, null=True)  # in kilometers or nautical miles


class Bike(Vehicle):
    BIKE_TYPE_CHOICES = [
        ('cruiser', 'Cruiser'),
        ('sport', 'Sport'),
        ('touring', 'Touring'),
        ('offroad', 'Off-Road'),
    ]

    engine_capacity = models.PositiveIntegerField(blank=True, null=True)  # in cc
    bike_type = models.CharField(max_length=50, choices=BIKE_TYPE_CHOICES, blank=True, null=True)
    saddle_height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)  # in inches or cm


class UAV(Vehicle):
    """Unmanned Aerial Vehicle (Drone)"""
    UAV_TYPE_CHOICES = [
        ('quadcopter', 'Quadcopter'),
        ('hexacopter', 'Hexacopter'),
        ('octocopter', 'Octocopter'),
        ('fixed-wing', 'Fixed-Wing'),
        ('hybrid', 'Hybrid VTOL'),
    ]
    
    UAV_PURPOSE_CHOICES = [
        ('recreational', 'Recreational'),
        ('photography', 'Photography/Videography'),
        ('surveying', 'Surveying/Mapping'),
        ('agriculture', 'Agriculture'),
        ('delivery', 'Delivery'),
        ('inspection', 'Industrial Inspection'),
        ('racing', 'Racing'),
        ('military', 'Military/Defense'),
    ]

    registration_number = models.CharField(max_length=100, blank=True, null=True)
    uav_type = models.CharField(max_length=50, choices=UAV_TYPE_CHOICES, blank=True, null=True)
    purpose = models.CharField(max_length=50, choices=UAV_PURPOSE_CHOICES, blank=True, null=True)
    max_flight_time = models.PositiveIntegerField(blank=True, null=True)  # in minutes
    max_range = models.PositiveIntegerField(blank=True, null=True)  # in kilometers
    max_altitude = models.PositiveIntegerField(blank=True, null=True)  # in meters
    max_speed = models.PositiveIntegerField(blank=True, null=True)  # in km/h
    camera_resolution = models.CharField(max_length=50, blank=True, null=True)  # e.g., "4K", "8K"
    payload_capacity = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)  # in kg
    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)  # in kg
    rotor_count = models.PositiveIntegerField(blank=True, null=True)
    has_obstacle_avoidance = models.BooleanField(default=False)
    has_gps = models.BooleanField(default=True)
    has_return_to_home = models.BooleanField(default=True)


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
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='inspections')
    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE, related_name='order_inspections')
    inspection_date = models.DateField(blank=True, null=True)
    inspection_time = models.TimeField(blank=True, null=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        status = "Completed" if self.completed else "Scheduled"
        item_name = self.order.order_item.title if self.order.order_item else 'Unknown Item'
        return f"{status} Inspection for {item_name} - {self.customer.user.name}"
    
    def __repr__(self):
        return f"<OrderInspection: Order #{self.order.id} - {self.customer.user.email}>"
    
    @property
    def is_scheduled(self):
        """Check if inspection has a scheduled date and time"""
        return bool(self.inspection_date and self.inspection_time)
    
    @property
    def days_until_inspection(self):
        """Returns days until inspection (negative if overdue)"""
        if self.inspection_date:
            return (self.inspection_date - now().date()).days
        return None
    
    class Meta:
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['customer']),
            models.Index(fields=['inspection_date']),
            models.Index(fields=['completed']),
        ]
        ordering = ['inspection_date', 'inspection_time']
        verbose_name = 'Order Inspection'
        verbose_name_plural = 'Order Inspections'


class Order(DbModel):
    ORDER_TYPES  = {'rental': 'Rental', 'sale': 'Sale'}
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
        'wallet': 'Veyu Wallet',
        'card': 'Credit / Debit Card',
        'financial-aid': 'Financing Aid',
    }

    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE, related_name='customer_orders')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES)
    order_item = models.ForeignKey('Listing', blank=True, null=True, on_delete=models.CASCADE, related_name='listing_orders')
    payment_option = models.CharField(max_length=20, choices=PAYMENT_OPTION, default='pay-after-inspection')
    paid = models.BooleanField(default=False)
    order_status = models.CharField(max_length=50, choices=ORDER_STATUS, default='pending')
    applied_coupons = models.ManyToManyField('Coupon', blank=True, related_name='coupon_orders')
    # for rentals

    @property
    def sub_total(self):
        amt = to_decimal(0.00)
        if self.is_recurring:
            cycle = 1
            days = 30 # count days
            amt += (self.order_item.price/30) * days
        else:
            amt += self.order_item.price

        # 0.5% added fees
        amt += (to_decimal(0.5/100) * amt)
        return amt

    @property
    def total(self):
        amt = self.sub_total
        # add discounts from coupons
        for coupon in self.applied_coupons.all():
            val = coupon.discount_value
            if coupon.discount_type == 'percentage':
                val = (to_decimal(coupon.discount_value/100) * amt)
            amt -= val
        # add 0.5% commission
        amt += to_decimal(0.5 / 100) * amt
        return amt

    def __str__(self):
        item_name = self.order_item.title if self.order_item else 'No Item'
        payment_status = "Paid" if self.paid else "Unpaid"
        return f"Order #{self.id}: {self.ORDER_TYPES.get(self.order_type, 'Unknown')} - {item_name} ({payment_status})"
    
    def __repr__(self):
        return f"<Order: #{self.id} - {self.order_type} - {self.customer.user.email}>"
    
    @property
    def total_amount(self):
        """Returns formatted total amount"""
        return f"₦{self.total:,.2f}"
    
    @property
    def days_since_order(self):
        """Returns days since order was placed"""
        return (now().date() - self.date_created.date()).days
    
    @property
    def coupon_count(self):
        """Returns number of applied coupons"""
        return self.applied_coupons.count()
    
    class Meta:
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['order_type']),
            models.Index(fields=['order_status']),
            models.Index(fields=['paid']),
            models.Index(fields=['date_created']),
            models.Index(fields=['order_item']),
        ]
        ordering = ['-date_created']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'



class RentalOrder(Order):
    is_recurring = models.BooleanField(default=False)
    payment_cycle = models.CharField(max_length=20, choices=PAYMENT_CYCLES, default="month")
    rent_from = models.DateField(blank=True, null=True)
    rent_until = models.DateField(blank=True, null=True)
    last_payment = models.DateField(blank=True, null=True)
    next_payment = models.DateField(blank=True, null=True)
    

    def __str__(self):
        recurring_text = " (Recurring)" if self.is_recurring else ""
        return f'Rental Order #{self.id}: {self.customer.user.name}{recurring_text} - {self.get_payment_cycle_display()}'
    
    def __repr__(self):
        return f"<RentalOrder: #{self.id} - {self.customer.user.email}>"
    
    @property
    def rental_duration_days(self):
        """Returns rental duration in days"""
        if self.rent_from and self.rent_until:
            return (self.rent_until - self.rent_from).days
        return 0
    
    @property
    def is_active_rental(self):
        """Check if rental is currently active"""
        if not (self.rent_from and self.rent_until):
            return False
        today = now().date()
        return self.rent_from <= today <= self.rent_until
    
    class Meta:
        indexes = [
            models.Index(fields=['is_recurring']),
            models.Index(fields=['payment_cycle']),
            models.Index(fields=['rent_from', 'rent_until']),
            models.Index(fields=['next_payment']),
        ]
        ordering = ['-date_created']
        verbose_name = 'Rental Order'
        verbose_name_plural = 'Rental Orders'


class PurchaseOrder(Order):

    def __str__(self):
        return f'Purchase Order #{self.id}: {self.customer.user.name} - {self.get_order_status_display()}'
    
    def __repr__(self):
        return f"<PurchaseOrder: #{self.id} - {self.customer.user.email}>"



class Coupon(DbModel):
    # veyu can issue coupons that are valid in all dealerships
    issuer = models.CharField(max_length=20, default='dealership') # veyu | dealership
    valid_in = models.ManyToManyField('accounts.Dealership', blank=True, related_name='valid_coupons')
    expires = models.DateTimeField(blank=True, null=True)
    users = models.ManyToManyField('accounts.Customer', blank=True, related_name='available_coupons')
    discount_type = models.CharField(max_length=20, default='flat') # flat | percentage
    discount_value = models.DecimalField(decimal_places=2, default=0.00, max_digits=12)
    code = models.CharField(blank=True, null=True, max_length=20, unique=True)

    def __str__(self):
        discount_text = f"{self.discount_value}%" if self.discount_type == 'percentage' else f"₦{self.discount_value}"
        return f"Coupon {self.code}: {discount_text} off - {self.dealership}"
    
    def __repr__(self):
        return f"<Coupon: {self.code} - {self.discount_value} {self.discount_type}>"
    
    @property
    def is_expired(self):
        """Check if coupon has expired"""
        if self.expires:
            return now() > self.expires
        return False
    
    @property
    def formatted_discount(self):
        """Returns formatted discount value"""
        if self.discount_type == 'percentage':
            return f"{self.discount_value}% off"
        else:
            return f"₦{self.discount_value:,.2f} off"

    @property
    def dealership(self):
        if self.issuer == 'veyu':
            return 'Veyu'
        else:
            first_dealership = self.valid_in.first()
            return first_dealership.business_name if first_dealership else 'Unknown'
    
    class Meta:
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['issuer']),
            models.Index(fields=['expires']),
            models.Index(fields=['discount_type']),
        ]


class Listing(DbModel):
    LISTING_TYPES  = {'rental': 'Car Rental', 'sale': 'Car Sale'}
    CURRENCY_CHOICES = [
        ('NGN', 'Naira'),
        ('USD', 'Dollar'),
    ]

    listing_type = models.CharField(max_length=20, choices=LISTING_TYPES, default='sale')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='NGN')
    verified = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, blank=True, null=True, related_name='approved_listings')
    created_by = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='created_listings')
    vehicle = models.ForeignKey('Vehicle', on_delete=models.CASCADE, related_name='vehicle_listings')
    price = models.DecimalField(decimal_places=2, max_digits=12, blank=True, null=True)
    title = models.CharField(max_length=400, blank=True, null=True)
    viewers = models.ManyToManyField('accounts.Account', limit_choices_to={'user_type': 'customer'}, blank=True, related_name='viewed_listings')
    offers = models.ManyToManyField('PurchaseOffer', blank=True, related_name='listing_offers')
    testdrives = models.ManyToManyField('TestDriveRequest', blank=True, related_name='listing_testdrives')
    payment_cycle = models.CharField(max_length=20, choices=PAYMENT_CYCLES, default='week', blank=True,)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        status = "Published" if self.published else "Draft"
        price_text = f"₦{self.price:,.2f}" if self.price else "Price not set"
        return f"{self.title} ({self.get_listing_type_display()}) - {price_text} [{status}]"
    
    def __repr__(self):
        return f"<Listing: {self.title} - {self.listing_type}>"
    
    @property
    def total_views(self):
        """Returns total number of viewers"""
        return self.viewers.count()
    
    @property
    def total_offers(self):
        """Returns total number of offers"""
        return self.offers.count()
    
    @property
    def formatted_price(self):
        """Returns formatted price with currency"""
        if self.price:
            return f"₦{self.price:,.2f}"
        return "Price not set"

    @property
    def published(self) -> bool: return self.verified

    def publish(self):
        self.verified = True
        self.save()

    def save(self, *args, **kwargs):
        if not self.title and self.vehicle:
            self.title = self.vehicle.name
        super().save(*args, **kwargs)
    
    class Meta:
        indexes = [
            models.Index(fields=['listing_type']),
            models.Index(fields=['verified', 'approved']),
            models.Index(fields=['created_by']),
            models.Index(fields=['vehicle']),
            models.Index(fields=['price']),
            models.Index(fields=['date_created']),
            models.Index(fields=['title']),
        ]
        ordering = ['-date_created']


class BoostPricing(DbModel):
    """Admin-configurable pricing for listing boosts"""
    DURATION_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    duration_type = models.CharField(max_length=20, choices=DURATION_CHOICES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per duration unit")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.get_duration_type_display()} Boost - ₦{self.price:,.2f}"
    
    def __repr__(self):
        return f"<BoostPricing: {self.duration_type} - ₦{self.price}>"
    
    @property
    def formatted_price(self):
        """Returns formatted price"""
        return f"₦{self.price:,.2f}"
    
    class Meta:
        ordering = ['duration_type']
        verbose_name = 'Boost Pricing'
        verbose_name_plural = 'Boost Pricing'


class ListingBoost(DbModel):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('failed', 'Payment Failed'),
        ('refunded', 'Refunded'),
    ]
    
    listing = models.OneToOneField('Listing', on_delete=models.CASCADE, related_name='listing_boost')
    dealer = models.ForeignKey('accounts.Dealership', on_delete=models.CASCADE, related_name='listing_boosts', null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    duration_type = models.CharField(max_length=20, choices=BoostPricing.DURATION_CHOICES, default='weekly')
    duration_count = models.PositiveIntegerField(default=1, help_text="Number of duration units (e.g., 2 weeks)")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_reference = models.CharField(max_length=200, blank=True, null=True)
    active = models.BooleanField(default=False)  # Only active when paid and within date range

    def is_active(self):
        """Check if boost is currently active"""
        return (
            self.payment_status == 'paid' and
            self.start_date <= now().date() <= self.end_date
        )

    def save(self, *args, **kwargs):
        """Ensure `active` is updated before saving."""
        self.active = self.is_active()
        super().save(*args, **kwargs)

    def __str__(self):
        status = "Active" if self.is_active() else "Inactive"
        return f"Boost: {self.listing.title} - {status} (₦{self.amount_paid:,.2f})"
    
    def __repr__(self):
        return f"<ListingBoost: {self.listing.title} - {self.start_date} to {self.end_date}>"
    
    @property
    def days_remaining(self):
        """Returns days remaining for the boost"""
        if not self.is_active():
            return 0
        return (self.end_date - now().date()).days
    
    @property
    def duration_days(self):
        """Returns total duration in days"""
        return (self.end_date - self.start_date).days
    
    @property
    def formatted_amount(self):
        """Returns formatted amount paid"""
        return f"₦{self.amount_paid:,.2f}"
    
    class Meta:
        indexes = [
            models.Index(fields=['listing']),
            models.Index(fields=['dealer']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['active']),
            models.Index(fields=['payment_status']),
        ]
        ordering = ['-start_date']
        verbose_name = 'Listing Boost'
        verbose_name_plural = 'Listing Boosts'


class PurchaseOffer(DbModel):
    bidder = models.ForeignKey('accounts.Customer', models.CASCADE, related_name='purchase_offers')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='purchase_offers')
    amount = models.DecimalField(decimal_places=2, max_digits=12)
    
    def __str__(self):
        return f"Offer by {self.bidder.user.name} - ₦{self.amount:,.2f} for {self.listing.title}"
    
    def __repr__(self):
        return f"<PurchaseOffer: {self.bidder.user.email} - ₦{self.amount}>"
    
    @property
    def formatted_amount(self):
        """Returns formatted offer amount"""
        return f"₦{self.amount:,.2f}"
    
    @property
    def days_since_offer(self):
        """Returns days since offer was made"""
        return (now().date() - self.date_created.date()).days
    
    class Meta:
        indexes = [
            models.Index(fields=['bidder']),
            models.Index(fields=['listing']),
            models.Index(fields=['amount']),
            models.Index(fields=['date_created']),
        ]
        ordering = ['-amount', '-date_created']
        verbose_name = 'Purchase Offer'
        verbose_name_plural = 'Purchase Offers'


class TestDriveRequest(DbModel):
    requested_by = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE, related_name='testdrive_requests')
    requested_to = models.ForeignKey('accounts.Dealership', on_delete=models.CASCADE, related_name='received_testdrive_requests')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='testdrive_requests')
    granted = models.BooleanField(default=False)
    testdrive_complete = models.BooleanField(default=False)
    
    def __str__(self):
        status = "Completed" if self.testdrive_complete else ("Granted" if self.granted else "Pending")
        return f"Test Drive: {self.requested_by.user.name} → {self.listing.title} ({status})"
    
    def __repr__(self):
        return f"<TestDriveRequest: {self.requested_by.user.email} - {self.listing.title}>"
    
    @property
    def status_display(self):
        """Returns human-readable status"""
        if self.testdrive_complete:
            return "Completed"
        elif self.granted:
            return "Approved - Pending Drive"
        else:
            return "Awaiting Approval"
    
    @property
    def days_since_request(self):
        """Returns days since request was made"""
        return (now().date() - self.date_created.date()).days
    
    class Meta:
        indexes = [
            models.Index(fields=['requested_by']),
            models.Index(fields=['requested_to']),
            models.Index(fields=['listing']),
            models.Index(fields=['granted']),
            models.Index(fields=['testdrive_complete']),
            models.Index(fields=['date_created']),
        ]
        ordering = ['-date_created']
        verbose_name = 'Test Drive Request'
        verbose_name_plural = 'Test Drive Requests'


class TradeInRequest(DbModel):
    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE, related_name='tradein_requests')
    to = models.ForeignKey('accounts.Dealership', on_delete=models.CASCADE, related_name='received_tradein_requests')
    vehicle = models.ForeignKey('Vehicle', on_delete=models.CASCADE, related_name='tradein_requests')
    estimated_value = models.DecimalField(decimal_places=2, max_digits=12)
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Trade-in: {self.vehicle.name} by {self.customer.user.name} → {self.to.business_name} (₦{self.estimated_value:,.2f})'
    
    def __repr__(self):
        return f"<TradeInRequest: {self.customer.user.email} - ₦{self.estimated_value}>"
    
    @property
    def formatted_value(self):
        """Returns formatted estimated value"""
        return f"₦{self.estimated_value:,.2f}"
    
    @property
    def days_since_request(self):
        """Returns days since request was made"""
        return (now().date() - self.date_created.date()).days
    
    class Meta:
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['to']),
            models.Index(fields=['vehicle']),
            models.Index(fields=['estimated_value']),
            models.Index(fields=['date_created']),
        ]
        ordering = ['-date_created']
        verbose_name = 'Trade-in Request'
        verbose_name_plural = 'Trade-in Requests'





class PlatformFeeSettings(DbModel):
    """
    Admin-configurable platform fees for transactions.
    Only one active instance should exist at a time.
    """
    # Service/Platform fee (Veyu fee)
    service_fee_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=2.00,
        help_text="Platform service fee as percentage (e.g., 2.00 for 2%)"
    )
    service_fee_fixed = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Fixed service fee amount in NGN (added to percentage)"
    )
    
    # Inspection fee
    inspection_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.00,
        help_text="Inspection fee as percentage of listing price (e.g., 5.00 for 5%)"
    )
    inspection_fee_minimum = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=10000,
        help_text="Minimum inspection fee in NGN"
    )
    inspection_fee_maximum = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=100000,
        help_text="Maximum inspection fee in NGN (0 for no limit)"
    )
    
    # Tax
    tax_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=7.5,
        help_text="Tax percentage (e.g., 7.5 for 7.5% VAT)"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    effective_date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = "Platform Fee Settings"
        verbose_name_plural = "Platform Fee Settings"
        ordering = ['-effective_date']
    
    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"Fee Settings ({status}) - Service: {self.service_fee_percentage}%, Inspection: {self.inspection_fee_percentage}%"
    
    def calculate_service_fee(self, amount):
        """Calculate service fee for a given amount"""
        percentage_fee = (Decimal(amount) * self.service_fee_percentage) / 100
        return float(percentage_fee + self.service_fee_fixed)
    
    def calculate_inspection_fee(self, listing_price):
        """Calculate inspection fee for a listing"""
        percentage_fee = (Decimal(listing_price) * self.inspection_fee_percentage) / 100
        fee = max(float(percentage_fee), float(self.inspection_fee_minimum))
        
        if self.inspection_fee_maximum > 0:
            fee = min(fee, float(self.inspection_fee_maximum))
        
        return fee
    
    def calculate_tax(self, amount):
        """Calculate tax for a given amount"""
        return float((Decimal(amount) * self.tax_percentage) / 100)
    
    @classmethod
    def get_active_settings(cls):
        """Get the currently active fee settings"""
        settings = cls.objects.filter(is_active=True).first()
        if not settings:
            # Create default settings if none exist
            settings = cls.objects.create(is_active=True)
        return settings
    
    def save(self, *args, **kwargs):
        # If this is being set as active, deactivate all others
        if self.is_active:
            PlatformFeeSettings.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)
