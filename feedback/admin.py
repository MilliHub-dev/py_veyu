from django.contrib import admin
from .models import (
    ChatMessage,
    ChatRoom,
    ChatAttachments,
    SupportTicket,
    Rating,
    Tag,
    TicketCategory,
    Notification,
)

# Register your models here.
admin.site.register(ChatAttachments)
admin.site.register(ChatMessage)
admin.site.register(ChatRoom)
admin.site.register(Notification)
admin.site.register(Rating)
admin.site.register(SupportTicket)
admin.site.register(Tag)
admin.site.register(TicketCategory)


