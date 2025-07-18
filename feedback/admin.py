from django.contrib import admin
from utils.admin import veyu_admin
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
veyu_admin.register(Rating)
veyu_admin.register(Notification)
veyu_admin.register(Review, ReviewAdmin)
veyu_admin.register(SupportTicket)
veyu_admin.register(Tag)
veyu_admin.register(TicketCategory)


