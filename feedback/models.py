from django.db import models
from utils.models import DbModel

# Create your models here.
class Review(DbModel):
    REVIEW_OBJECTS = {
        'vehicle': 'Vehicle Review', # for rentals
        'dealer': 'Dealership Review',
        'mechanic': 'Mechanic',
        'support_ticket': 'Support Ticket',
        'purchase': 'Car Purchase',
        'service': 'Service', # for bookings
    }

    ratings = models.ManyToManyField("Rating", blank=True)
    comment = models.TextField(max_length=1200, blank=True, null=True)
    reviewer = models.ForeignKey('accounts.Account', on_delete=models.CASCADE)
    object_type = models.CharField(max_length=200, choices=REVIEW_OBJECTS.items())
    related_object = models.UUIDField(blank=True, null=True) # e.g related dealership
    related_order = models.UUIDField(blank=True, null=True) # for order/booking

    @property
    def avg_rating(self):
        ratings = self.get_ratings()
        if not ratings:
            return 0  # Return 0 if there are no ratings
        total_stars = sum(ratings[key] for key in ratings.keys())
        total_count = len(ratings.keys())
        return round(total_stars / total_count, 1) if total_count > 0 else 0


    def get_ratings(self):
        keys = [
            'communication',
            'support',
            'service-delivery',
            'car-quality',
            'car-cleanliness',
        ]
        categories = {}
        for key in keys:
            rating = self.ratings.filter(area=key).first()
            if rating:
                categories[key] = rating.stars
        return categories


class Rating(DbModel):
    REVIEW_AREAS = {
        'communication': 'Communication',
        'support': 'Support',
        'service-delivery': 'Service Delivery', # for mechs
        'car-quality': 'Car Quality', # for dealers
        'car-cleanliness': 'Car Cleanliness',
    }
    reviewId = models.ForeignKey(Review, on_delete=models.CASCADE)
    area = models.CharField(max_length=200, choices=REVIEW_AREAS.items())
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
    # tags e.g Bug, Customer Reported Error
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
    read = models.BooleanField(default=False)
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

    def mark_as_read(self):
        self.read = True
        self.save()
        





