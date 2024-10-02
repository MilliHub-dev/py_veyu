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


admin.site.register(Listing)
admin.site.register(Order)
admin.site.register(CarRental)
admin.site.register(Vehicle)
admin.site.register(VehicleTag)
admin.site.register(VehicleCategory)
admin.site.register(VehicleImage)
admin.site.register(TestDriveRequest)
admin.site.register(TradeInRequest)
admin.site.register(PurchaseOffer)
admin.site.register(CarPurchase)




