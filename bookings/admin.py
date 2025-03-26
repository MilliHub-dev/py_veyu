from django.contrib import admin
from .models import (
    Service,
    ServiceOffering,
    ServiceBooking,
)
from utils.admin import motaa_admin



# Register your models here.
motaa_admin.register(Service)
motaa_admin.register(ServiceOffering)
motaa_admin.register(ServiceBooking)
