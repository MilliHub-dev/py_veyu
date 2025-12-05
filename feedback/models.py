from django.db import models
from django.utils.timezone import now
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

    ratings = models.ManyToManyField("Rating", blank=True, related_name='review_ratings')
    comment = models.TextField(max_length=1200, blank=True, null=True)
    reviewer = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='submitted_reviews')
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
            rating = self.review_ratings.filter(area=key).first()
            if rating:
                categories[key] = rating.stars
        return categories
    
    def __str__(self):
        rating_text = f"{self.avg_rating}/5.0" if self.avg_rating > 0 else "No rating"
        return f"Review by {self.reviewer.name} - {self.get_object_type_display()} ({rating_text})"
    
    def __repr__(self):
        return f"<Review: {self.reviewer.email} - {self.object_type} - {self.avg_rating}/5.0>"
    
    @property
    def total_ratings(self):
        """Returns total number of rating categories"""
        return self.ratings.count()
    
    @property
    def has_comment(self):
        """Check if review has a comment"""
        return bool(self.comment and self.comment.strip())
    
    class Meta:
        indexes = [
            models.Index(fields=['reviewer']),
            models.Index(fields=['object_type']),
            models.Index(fields=['related_object']),
            models.Index(fields=['related_order']),
            models.Index(fields=['date_created']),
        ]
        ordering = ['-date_created']
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'


class Rating(DbModel):
    REVIEW_AREAS = {
        'communication': 'Communication',
        'support': 'Support',
        'service-delivery': 'Service Delivery', # for mechs
        'car-quality': 'Car Quality', # for dealers
        'car-cleanliness': 'Car Cleanliness',
    }
    reviewId = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='rating_items')
    area = models.CharField(max_length=200, choices=REVIEW_AREAS.items())
    stars = models.PositiveSmallIntegerField()
    
    def __str__(self):
        return f"{self.get_area_display()}: {self.stars}/5 stars"
    
    def __repr__(self):
        return f"<Rating: {self.area} - {self.stars}/5>"
    
    @property
    def star_percentage(self):
        """Returns star rating as percentage"""
        return (self.stars / 5) * 100
    
    class Meta:
        indexes = [
            models.Index(fields=['reviewId']),
            models.Index(fields=['area']),
            models.Index(fields=['stars']),
        ]
        unique_together = ['reviewId', 'area']
        ordering = ['-stars']
        verbose_name = 'Rating'
        verbose_name_plural = 'Ratings'


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

    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE, related_name='support_tickets')
    status = models.CharField(max_length=20, choices=TICKET_STATUS, blank=False)
    severity_level = models.CharField(max_length=20, choices=TICKET_SEVERITY, blank=False)
    subject = models.CharField(max_length=400) # title/reason of the ticket
    tags = models.ManyToManyField('Tag', blank=True, related_name='ticket_tags')
    category = models.ForeignKey('TicketCategory', on_delete=models.SET_NULL, blank=True, null=True, related_name='category_tickets')
    chat_room = models.ForeignKey('chat.ChatRoom', blank=True, related_name='support_chat', null=True, on_delete=models.CASCADE)
    correspondents = models.ManyToManyField('accounts.Account', blank=True, limit_choices_to={'is_staff': True}, related_name='assigned_tickets') # staff that have been added to this chat
    
    def __str__(self):
        return f"Ticket #{self.id}: {self.subject} ({self.get_status_display()}) - {self.get_severity_level_display()}"
    
    def __repr__(self):
        return f"<SupportTicket: #{self.id} - {self.status} - {self.customer.user.email}>"
    
    @property
    def days_open(self):
        """Returns number of days the ticket has been open"""
        return (now().date() - self.date_created.date()).days
    
    @property
    def total_correspondents(self):
        """Returns number of staff assigned to this ticket"""
        return self.correspondents.count()
    
    @property
    def is_overdue(self):
        """Check if ticket is overdue based on severity"""
        days_open = self.days_open
        if self.severity_level == 'high':
            return days_open > 1
        elif self.severity_level == 'moderate':
            return days_open > 3
        else:  # low
            return days_open > 7
    
    class Meta:
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['status']),
            models.Index(fields=['severity_level']),
            models.Index(fields=['category']),
            models.Index(fields=['date_created']),
        ]
        ordering = ['-date_created']
        verbose_name = 'Support Ticket'
        verbose_name_plural = 'Support Tickets'
    


class Tag(DbModel):
    # tags e.g Bug, Customer Reported Error
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f"<Tag: {self.name}>"
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'



class TicketCategory(DbModel):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f"<TicketCategory: {self.name}>"
    
    @property
    def total_tickets(self):
        """Returns total number of tickets in this category"""
        return self.category_tickets.count()
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Ticket Category'
        verbose_name_plural = 'Ticket Categories'



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
    user = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='notifications')
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
    
    def __str__(self):
        status = "Read" if self.read else "Unread"
        return f"{self.subject} for {self.user.name} ({self.get_level_display()}) - {status}"
    
    def __repr__(self):
        return f"<Notification: {self.user.email} - {self.level} - {self.read}>"
    
    @property
    def is_actionable(self):
        """Check if notification has a call-to-action"""
        return bool(self.cta_text and self.cta_link)
    
    @property
    def days_old(self):
        """Returns number of days since notification was created"""
        return (now().date() - self.date_created.date()).days
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['read']),
            models.Index(fields=['level']),
            models.Index(fields=['channel']),
            models.Index(fields=['date_created']),
        ]
        ordering = ['-date_created']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        





