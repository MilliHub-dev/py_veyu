from django.contrib import admin
from .models import (
    SupportTicket,
    Rating,
    Tag,
    TicketCategory,
    Notification,
)

# Register your models here.
admin.site.register(Notification)
admin.site.register(Rating)
admin.site.register(SupportTicket)
admin.site.register(Tag)
admin.site.register(TicketCategory)


