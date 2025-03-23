from django.contrib import admin
from .models import (
    ChatAttachment,    
    ChatMessage,    
    ChatRoom,
)
from utils.admin import motaa_admin
# Register your models here.

motaa_admin.register(ChatAttachment)
motaa_admin.register(ChatMessage)
motaa_admin.register(ChatRoom)
