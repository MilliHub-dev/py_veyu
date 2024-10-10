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
    CarPurchase
)


models = [
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
    CarPurchase
]


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'listing_type', 'approved', 'title']
    list_filter = ['listing_type', 'approved', 'approved_by', 'vehicle__brand']
    search_fields = ['vehicle__name', 'title', 'vehicle__brand']
    list_editable = ['approved']


@admin.register(CarRental)
class CarRentalAdmin(admin.ModelAdmin):
    list_display = ['customer', 'order']
    search_fields = ['customer__account__email', 'order__id']



@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_type', 'sub_total', 'discount', 'commission', 'paid', 'customer']
    list_filter = ['order_type', 'paid'] 
    search_fields = ['customer__account__email', 'sub_total']


@admin.register(TradeInRequest)
class TradeInRequestAdmin(admin.ModelAdmin):
    list_display = ['customer', 'vehicle', 'estimated_value']
    search_fields = ['customer__account__email', 'vehicle__name']


@admin.register(CarPurchase)
class CarPurchaseAdmin(admin.ModelAdmin):
    list_display = ['customer', 'order']
    search_fields = ['customer__account__email', 'order__id']


@admin.register(PurchaseOffer)
class PurchaseOfferAdmin(admin.ModelAdmin):
    list_display = ['bidder', 'listing', 'amount']
    list_filter = ['bidder', 'listing']
    search_fields = ['bidder__account__email', 'listing__vehicle__name', 'amount']


@admin.register(TestDriveRequest)
class TestDriveRequestAdmin(admin.ModelAdmin):
    list_display = ['requested_by', 'requested_to', 'listing', 'granted', 'testdrive_complete']
    list_filter = ['granted', 'testdrive_complete', 'requested_to']
    search_fields = ['requested_by__account__email', 'listing__title']


@admin.register(VehicleImage)
class VehicleImageAdmin(admin.ModelAdmin):
    list_display = ['image', 'vehicle']
    list_filter = ['vehicle']
    search_fields = ['vehicle__name']


@admin.register(VehicleTag)
class VehicleTagAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(VehicleCategory)
class VehicleCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'condition', 'available', 'for_sale', 'sold']
    list_filter = ['brand', 'condition', 'available', 'for_sale', 'sold', 'dealer']
    search_fields = ['name', 'brand', 'dealer__user__email']
    list_editable = ['available', 'for_sale', 'sold']
