from utils.admin import veyu_admin
from django.contrib import admin
from .models import (
    RentalOrder,
    PurchaseOrder,
    Listing,
    Order,
    Vehicle,
    Car,
    Boat,
    Plane,
    Bike,
    UAV,
    VehicleImage,
    TestDriveRequest,
    TradeInRequest,
    OrderInspection,
    PurchaseOffer,
    BoostPricing,
    ListingBoost,
    PlatformFeeSettings,
)


# @veyu_admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'listing_type', 'approved', 'verified', 'title', 'currency', 'price']
    list_filter = ['listing_type', 'approved', 'approved_by', 'vehicle__brand']
    search_fields = ['vehicle__name', 'title', 'vehicle__brand']
    list_editable = ['approved', 'verified']
    actions = ['approve_selected_listings']

    def approve_selected_listings(self, request, queryset, *args, **kwargs):
        updated = queryset.update(approved=True, verified=True)
        # send email to each dealer for approved listings
        for listing in queryset:
            dealer = listing.vehicle.dealer
            if dealer and dealer.user and dealer.user.email:
                try:
                    from utils.mail import send_email
                    send_email(
                        subject="Your listing is now live",
                        recipients=[dealer.user.email],
                        template="utils/templates/listing_published.html",
                        context={
                            "dealer_name": dealer.user.first_name or dealer.user.email,
                            "listing_title": listing.title,
                            "vehicle_name": listing.vehicle.name,
                            "price": listing.price,
                        }
                    )
                except Exception:
                    pass
        self.message_user(request, f"Successfully approved {updated} listings")


# @veyu_admin.register(CarRental)
class CarRentalAdmin(admin.ModelAdmin):
    list_display = ['customer',]
    search_fields = ['customer__account__email', ]



# @veyu_admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_type', 'paid', 'customer']
    list_filter = ['order_type', 'paid']
    search_fields = ['customer__account__email', 'sub_total']


# @veyu_admin.register(TradeInRequest)
class TradeInRequestAdmin(admin.ModelAdmin):
    list_display = ['customer', 'vehicle', 'estimated_value']
    search_fields = ['customer__account__email', 'vehicle__name']


# @veyu_admin.register(CarPurchase)
class CarPurchaseAdmin(admin.ModelAdmin):
    list_display = ['customer', ]
    search_fields = ['customer__account__email',]

# 
# @veyu_admin.register(PurchaseOffer)
class PurchaseOfferAdmin(admin.ModelAdmin):
    list_display = ['bidder', 'listing', 'amount']
    list_filter = ['bidder', 'listing']
    search_fields = ['bidder__account__email', 'listing__vehicle__name', 'amount']


# @veyu_admin.register(TestDriveRequest)
class TestDriveRequestAdmin(admin.ModelAdmin):
    list_display = ['requested_by', 'requested_to', 'listing', 'granted', 'testdrive_complete']
    list_filter = ['granted', 'testdrive_complete', 'requested_to']
    search_fields = ['requested_by__account__email', 'listing__title']


# @veyu_admin.register(VehicleImage)
class VehicleImageAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'image', 'vehicle']
    list_display_links = ['__str__', 'vehicle']
    list_filter = ['vehicle']
    search_fields = ['vehicle__name']



# Inline to manage images on the vehicle edit page
class VehicleImageInline(admin.TabularInline):
    model = VehicleImage
    extra = 1


# @veyu_admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'condition', 'available',]
    list_filter = ['brand', 'condition', 'available', 'dealer']
    search_fields = ['name', 'brand', 'dealer__user__email']
    inlines = [VehicleImageInline]


class CarAdmin(VehicleAdmin):
    list_display = ['name', 'brand', 'body_type', 'doors', 'seats', 'drivetrain', 'available']
    list_filter = VehicleAdmin.list_filter + ['drivetrain', 'body_type']


class BoatAdmin(VehicleAdmin):
    list_display = ['name', 'brand', 'hull_material', 'engine_count', 'available']
    list_filter = VehicleAdmin.list_filter + ['hull_material']


class PlaneAdmin(VehicleAdmin):
    list_display = ['name', 'brand', 'aircraft_type', 'engine_type', 'available']
    list_filter = VehicleAdmin.list_filter + ['aircraft_type']


class BikeAdmin(VehicleAdmin):
    list_display = ['name', 'brand', 'bike_type', 'engine_capacity', 'available']
    list_filter = VehicleAdmin.list_filter + ['bike_type']


class UAVAdmin(VehicleAdmin):
    list_display = ['name', 'brand', 'uav_type', 'purpose', 'max_flight_time', 'available']
    list_filter = VehicleAdmin.list_filter + ['uav_type', 'purpose']
    fieldsets = (
        ('Basic Information', {
            'fields': ('dealer', 'name', 'brand', 'model', 'condition', 'color', 'available')
        }),
        ('UAV Specifications', {
            'fields': ('registration_number', 'uav_type', 'purpose', 'rotor_count', 'weight')
        }),
        ('Performance', {
            'fields': ('max_flight_time', 'max_range', 'max_altitude', 'max_speed', 'payload_capacity')
        }),
        ('Camera & Features', {
            'fields': ('camera_resolution', 'has_obstacle_avoidance', 'has_gps', 'has_return_to_home')
        }),
        ('Additional', {
            'fields': ('features', 'tags', 'video')
        }),
    )


class BoostPricingAdmin(admin.ModelAdmin):
    list_display = ['duration_type', 'price', 'formatted_price', 'is_active']
    list_editable = ['price', 'is_active']
    list_filter = ['is_active', 'duration_type']
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of pricing records
        return False


class ListingBoostAdmin(admin.ModelAdmin):
    list_display = ['listing', 'dealer', 'start_date', 'end_date', 'duration_type', 
                    'duration_count', 'amount_paid', 'payment_status', 'active']
    list_filter = ['payment_status', 'active', 'duration_type', 'start_date']
    search_fields = ['listing__title', 'dealer__business_name', 'payment_reference']
    readonly_fields = ['active', 'date_created']
    list_editable = ['payment_status']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields + ['listing', 'dealer', 'start_date', 'end_date', 
                                          'duration_type', 'duration_count', 'amount_paid']
        return self.readonly_fields


class PlatformFeeSettingsAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'service_fee_percentage', 'inspection_fee_percentage', 
                    'tax_percentage', 'is_active', 'effective_date']
    list_filter = ['is_active', 'effective_date']
    list_editable = ['is_active']
    readonly_fields = ['effective_date']
    
    fieldsets = (
        ('Service Fee', {
            'fields': ('service_fee_percentage', 'service_fee_fixed')
        }),
        ('Inspection Fee', {
            'fields': ('inspection_fee_percentage', 'inspection_fee_minimum', 'inspection_fee_maximum')
        }),
        ('Tax', {
            'fields': ('tax_percentage',)
        }),
        ('Status', {
            'fields': ('is_active', 'effective_date')
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        # Allow deletion of inactive settings only
        if obj and obj.is_active:
            return False
        return True


veyu_admin.register(Listing, ListingAdmin)
veyu_admin.register(RentalOrder, CarRentalAdmin)
veyu_admin.register(Order, OrderAdmin)
veyu_admin.register(TradeInRequest, TradeInRequestAdmin)
veyu_admin.register(PurchaseOrder, CarPurchaseAdmin)
veyu_admin.register(PurchaseOffer, PurchaseOfferAdmin)
veyu_admin.register(TestDriveRequest, TestDriveRequestAdmin)
veyu_admin.register(VehicleImage, VehicleImageAdmin)
veyu_admin.register(Vehicle, VehicleAdmin)
veyu_admin.register(Car, CarAdmin)
veyu_admin.register(Boat, BoatAdmin)
veyu_admin.register(Plane, PlaneAdmin)
veyu_admin.register(Bike, BikeAdmin)
veyu_admin.register(UAV, UAVAdmin)
veyu_admin.register(OrderInspection)
veyu_admin.register(BoostPricing, BoostPricingAdmin)
veyu_admin.register(ListingBoost, ListingBoostAdmin)
veyu_admin.register(PlatformFeeSettings, PlatformFeeSettingsAdmin)

