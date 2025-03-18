from utils.admin import motaa_admin
from django.contrib import admin
from .models import (
    CarRental,
    Listing,
    Order,
    Vehicle,
    VehicleCategory,
    VehicleTag,
    VehicleImage,
    TestDriveRequest,
    TradeInRequest,
    PurchaseOffer,
    CarPurchase,
)


# @motaa_admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'listing_type', 'approved', 'verified', 'title']
    list_filter = ['listing_type', 'approved', 'approved_by', 'vehicle__brand']
    search_fields = ['vehicle__name', 'title', 'vehicle__brand']
    list_editable = ['approved', 'verified']
    actions = ['approve_selected_listings']

    def approve_selected_listings(self, request, queryset, *args, **kwargs):
        queryset.update(approved=True, verified=True)
        self.message_user(request, f"Successfully approved {queryset.count()} listings")


# @motaa_admin.register(CarRental)
class CarRentalAdmin(admin.ModelAdmin):
    list_display = ['customer', 'order']
    search_fields = ['customer__account__email', 'order__id']



# @motaa_admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_type', 'paid', 'customer']
    list_filter = ['order_type', 'paid']
    search_fields = ['customer__account__email', 'sub_total']


# @motaa_admin.register(TradeInRequest)
class TradeInRequestAdmin(admin.ModelAdmin):
    list_display = ['customer', 'vehicle', 'estimated_value']
    search_fields = ['customer__account__email', 'vehicle__name']


# @motaa_admin.register(CarPurchase)
class CarPurchaseAdmin(admin.ModelAdmin):
    list_display = ['customer', 'order']
    search_fields = ['customer__account__email', 'order__id']

# 
# @motaa_admin.register(PurchaseOffer)
class PurchaseOfferAdmin(admin.ModelAdmin):
    list_display = ['bidder', 'listing', 'amount']
    list_filter = ['bidder', 'listing']
    search_fields = ['bidder__account__email', 'listing__vehicle__name', 'amount']


# @motaa_admin.register(TestDriveRequest)
class TestDriveRequestAdmin(admin.ModelAdmin):
    list_display = ['requested_by', 'requested_to', 'listing', 'granted', 'testdrive_complete']
    list_filter = ['granted', 'testdrive_complete', 'requested_to']
    search_fields = ['requested_by__account__email', 'listing__title']


# @motaa_admin.register(VehicleImage)
class VehicleImageAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'image', 'vehicle']
    list_display_links = ['__str__', 'vehicle']
    list_filter = ['vehicle']
    search_fields = ['vehicle__name']


# @motaa_admin.register(VehicleTag)
class VehicleTagAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


# @motaa_admin.register(VehicleCategory)
class VehicleCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


# @motaa_admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'condition', 'available',]
    list_filter = ['brand', 'condition', 'available', 'dealer']
    search_fields = ['name', 'brand', 'dealer__user__email']






motaa_admin.register(Listing, ListingAdmin)
motaa_admin.register(CarRental, CarRentalAdmin)
motaa_admin.register(Order, OrderAdmin)
motaa_admin.register(TradeInRequest, TradeInRequestAdmin)
motaa_admin.register(CarPurchase, CarPurchaseAdmin)
motaa_admin.register(PurchaseOffer, PurchaseOfferAdmin)
motaa_admin.register(TestDriveRequest, TestDriveRequestAdmin)
motaa_admin.register(VehicleImage, VehicleImageAdmin)
motaa_admin.register(VehicleTag, VehicleTagAdmin)
motaa_admin.register(VehicleCategory, VehicleCategoryAdmin)
motaa_admin.register(Vehicle, VehicleAdmin)








