from django.db import models
from utils.models import DbModel


# Create your models here.
class Review(DbModel):
    REVIEW_OBJECTS = {
        'vehicle': 'Vehicle Review', # for rentals
        'dealer': 'Delearship Review',
        'mechanic': 'Mechanic',
        'support_ticket': 'Support Ticket',
        'purchase': 'Car Purchase',
        'service': 'Service', # for bookings
    }

    stars = models.ManyToManyField("ReviewArea", blank=True)
    comment = models.TextField(max_length=1200, blank=True, null=True)
    reviewer = models.ForeignKey('accounts.Account', on_delete=models.CASCADE)
    object_type = models.CharField(max_length=200, choices=REVIEW_OBJECTS)
    related_object = models.UUIDField(blank=True, null=True) # e.g related dealership


class ReviewArea(DbModel):
    REVIEW_ARES = {
        'communication': 'Communication',
        'service-delivery': 'Service Delivery', # for mechs
        'car-quality': 'Car Quality', # for dealers
        'car-cleanliness': 'Car Cleanliness',
    }
    reviewId = models.ForeignKey(Review, on_delete=models.CASCADE)
    area = models.CharField(max_length=200)
    stars = models.PositiveSmallIntegerField()



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
    chat_room = models.ForeignKey('chat.ChatRoom', blank=True, related_name='chat_room', null=True, on_delete=models.CASCADE)
    correspondents = models.ManyToManyField('accounts.Account', blank=True, limit_choices_to={'is_staff': True}) # staff that have been added to this chat
    


class Tag(DbModel):
    name = models.CharField(max_length=200)

    def __str__(self):return self.name



class TicketCategory(DbModel):
    name = models.CharField(max_length=200)

    def __str__(self):return self.name



class Notification(DbModel):
    CHANNELS = {
        'email': 'Email Notification',
        'in-app': 'In-App Notification',
        'sms': 'SMS Notification',
    }
    LEVELS = {
        'info': 'Info',
        'warning': 'Warning',
        'error': 'Error',
        'success': 'Success',
    }
    user = models.ForeignKey('accounts.Account', on_delete=models.CASCADE)
    subject = models.CharField(max_length=350)
    message = models.TextField()
    level = models.CharField(max_length=10, choices=LEVELS, default='info')
    channel = models.CharField(max_length=10, default='in-app', choices=CHANNELS)
    cta_text = models.CharField(max_length=20, blank=True, null=True)
    cta_link = models.URLField(blank=True, null=True)

    def send(self):
        if self.channel =='sms':
            # TODO: send sms and delete instance
            pass
        elif self.channel == 'email':
            # TODO: send email and delete instance
            pass
        # else do nothing, they'll see this notification in notifications tab
        return



