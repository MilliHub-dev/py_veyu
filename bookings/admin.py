from django.contrib import admin
from .models import (
    Service,
    ServiceOffering,
    ServiceBooking,
)
from utils.admin import veyu_admin



# Register your models here.
veyu_admin.register(Service)
veyu_admin.register(ServiceOffering)
veyu_admin.register(ServiceBooking)
