from django.contrib import admin
from .models import (
    ChatAttachment,    
    ChatMessage,    
    ChatRoom,
)
from utils.admin import veyu_admin
# Register your models here.

veyu_admin.register(ChatAttachment)
veyu_admin.register(ChatMessage)
veyu_admin.register(ChatRoom)
