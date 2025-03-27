from django.contrib import admin
from utils.admin import motaa_admin
from .models import (
    SupportTicket,
    Review,
    Tag,
    TicketCategory,
    Notification,
    Rating,
)


class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'reviewer',
        'object_type',
        'avg_rating',
    ]
    list_display_links = [
        'id',
        'reviewer'
    ]


# Register your models here.
motaa_admin.register(Rating)
motaa_admin.register(Notification)
motaa_admin.register(Review, ReviewAdmin)
motaa_admin.register(SupportTicket)
motaa_admin.register(Tag)
motaa_admin.register(TicketCategory)


