from django.contrib import admin
from .models import (
    Account,
    Customer,
    Mechanic,
    Location,
    Service,
    ServiceBooking,
)

# Register your models here.
admin.site.register(Account)
admin.site.register(Customer)
admin.site.register(Mechanic)
admin.site.register(Location)
admin.site.register(Service)
admin.site.register(ServiceBooking)
