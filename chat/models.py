from django.db import models
from utils.models import DbModel
from django.utils.timesince import timesince

# Create your models here.

class ChatRoom(DbModel):
    ROOM_TYPES = {
        'sales-chat': 'Booking / Sales Chat Room',
        'staff-chat': 'Staff Chat Room',
    }
    room_type = models.CharField(max_length=200, default='sales-chat', choices=ROOM_TYPES)
    members = models.ManyToManyField('accounts.Account', blank=True, related_name='chat_rooms')
    messages = models.ManyToManyField('ChatMessage', blank=True, related_name='chat_rooms')

    def __str__(self) -> str:
        member_count = self.members.count()
        return f'{self.get_room_type_display()} ({member_count} member{"s" if member_count != 1 else ""}) - {str(self.uuid)[:8]}'
    
    def __repr__(self):
        return f"<ChatRoom: {self.room_type} - {self.uuid}>"
    
    @property
    def total_members(self):
        """Returns total number of members"""
        return self.members.count()
    
    @property
    def total_messages(self):
        """Returns total number of messages"""
        return self.room_messages.count()
    
    @property
    def last_message_time(self):
        """Returns the time of the last message"""
        last_message = self.room_messages.last()
        return last_message.date_created if last_message else None
    
    class Meta:
        indexes = [
            models.Index(fields=['room_type']),
            models.Index(fields=['date_created']),
        ]
        ordering = ['-date_created']
        verbose_name = 'Chat Room'
        verbose_name_plural = 'Chat Rooms'


class ChatAttachment(DbModel):
    file = models.FileField(upload_to='chat/attachments', blank=True, null=True)
    
    def __str__(self):
        if self.file:
            return f"Attachment: {self.file.name}"
        return "Empty Attachment"
    
    def __repr__(self):
        return f"<ChatAttachment: {self.file.name if self.file else 'No file'}>"
    
    @property
    def file_size(self):
        """Returns file size in human readable format"""
        if not self.file:
            return "No file"
        try:
            size = self.file.size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except (AttributeError, OSError):
            return "Unknown size"
    
    @property
    def file_extension(self):
        """Returns the file extension"""
        if self.file and self.file.name:
            return self.file.name.split('.')[-1].upper()
        return "Unknown"


class ChatMessage(DbModel):
    MESSAGE_TYPES = {
        'system': 'System Message',
        'user': 'User Message'
    }

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='room_messages')
    sender = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, blank=True, null=True, related_name='sent_messages')
    message_type = models.CharField(max_length=20, default='user', choices=MESSAGE_TYPES)
    text = models.TextField(blank=True, null=True)
    attachments = models.ManyToManyField(ChatAttachment, blank=True, related_name='message_attachments')
    
    def __str__(self) -> str:
        sender_name = self.sender.name if self.sender else "System"
        text_preview = (self.text[:50] + "...") if self.text and len(self.text) > 50 else (self.text or "No text")
        return f"{sender_name}: {text_preview}"
    
    def __repr__(self):
        return f"<ChatMessage: {self.message_type} - {self.sender.email if self.sender else 'System'}>"
    
    @property
    def has_attachments(self):
        """Check if message has attachments"""
        return self.attachments.exists()
    
    @property
    def attachment_count(self):
        """Returns number of attachments"""
        return self.attachments.count()

    @property
    def sent(self):
        return timesince(self.date_created)
    
    class Meta:
        indexes = [
            models.Index(fields=['room']),
            models.Index(fields=['sender']),
            models.Index(fields=['message_type']),
            models.Index(fields=['date_created']),
        ]
        ordering = ['date_created']
    