from django.contrib import admin
from .models import (
    Service,
    ServiceOffering,
    ServiceBooking,
)




# Register your models here.
admin.site.register(Service)
admin.site.register(ServiceOffering)
admin.site.register(ServiceBooking)
