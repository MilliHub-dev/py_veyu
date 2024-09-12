from django.contrib import admin
from .models import (
    CarRental,
    Listing,
    Order,
    Vehicle,
    VehicleCategory,
    VehicleTag,
    VehicleImage,
)


admin.site.register(Listing)
admin.site.register(Order)
admin.site.register(CarRental)
admin.site.register(Vehicle)
admin.site.register(VehicleTag)
admin.site.register(VehicleCategory)
admin.site.register(VehicleImage)




