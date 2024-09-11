from django.db import models
from utils.models import DbModel


# Create your models here.
class Rating(DbModel):
    REVIEW_OBJECTS = {
        'vehicle': 'Vehicle Review',
        'mechanic': 'Mechanic',
        'support_ticket': 'Support Ticket',
    }

    stars = models.PositiveSmallIntegerField()
    review = models.TextField(max_length=1200, blank=True, null=True)
    reviewer = models.ForeignKey('accounts.Account', on_delete=models.CASCADE)
    object_type = models.CharField(max_length=200, choices=REVIEW_OBJECTS)



class SupportTicket(DbModel):
    TICKET_SEVERITY = {
        'high': 'High Severity',
        'low': 'Low Severity',
        'moderate': 'Moderate Severity',
    }

    TICKET_STATUS = {
        'open': 'Open',
        'in-progress': 'In Progress',
        'awaiting-user': 'Awaiting Customer Response',
        'resolved': 'Resolved',
    }

    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=TICKET_STATUS, blank=False)
    severity_level = models.CharField(max_length=20, choices=TICKET_SEVERITY, blank=False)
    subject = models.CharField(max_length=400) # title/reason of the ticket
    tags = models.ManyToManyField('Tag', blank=True)
    category = models.ForeignKey('TicketCategory', on_delete=models.SET_NULL, blank=True, null=True)
    messages = models.ManyToManyField('ChatMessage', blank=True, related_name='messages')
    correspondents = models.ManyToManyField('accounts.Account', blank=True) # staff that have been added to this chat
    


class Tag(DbModel):
    name = models.CharField(max_length=200)

    def __str__(self):return self.name



class TicketCategory(DbModel):
    name = models.CharField(max_length=200)

    def __str__(self):return self.name



class ChatMessage(DbModel):
    sender = models.ForeignKey('accounts.Account', on_delete=models.CASCADE)
    message = models.TextField()
    chat_source = models.CharField(max_length=20, choices={'chat': 'Chat Room', 'email': 'Email'}, default='chat')
    ticket_id = models.ForeignKey(SupportTicket, on_delete=models.CASCADE)



