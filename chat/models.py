from django.db import models
from utils.models import DbModel

# Create your models here.

class ChatRoom(DbModel):
    ROOM_TYPES = {
        'sales-chat': 'Booking / Sales Chat Room',
        'staff-chat': 'Staff Chat Room',
    }
    room_type = models.CharField(max_length=200, default='sales-chat', choices=ROOM_TYPES)
    members = models.ManyToManyField('accounts.Account', blank=True, related_name='members')
    messages = models.ManyToManyField('ChatMessage', blank=True, related_name='messages')

    def __str__(self) -> str:
        return f'{self.uuid}'


class ChatAttachment(DbModel):
    file = models.FileField(upload_to='chat/attachments', blank=True, null=True)


class ChatMessage(DbModel):
    MESSAGE_TYPES = {
        'system': 'System Message',
        'user': 'User Message'
    }

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    sender = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, blank=True, null=True)
    message_type = models.CharField(max_length=20, default='user', choices=MESSAGE_TYPES)
    text = models.TextField(blank=True, null=True)
    attachments = models.ManyToManyField(ChatAttachment, blank=True, related_name='attachments')
    
    def __str__(self) -> str:
        return self.message_type
    