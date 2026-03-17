from django.db import models
from django.utils.timezone import now
from utils.models import DbModel
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import logging
from utils.mail import send_email
from utils.sms import sms_service, normalize_phone_number

logger = logging.getLogger(__name__)

# Initialize Firebase App
def initialize_firebase():
    try:
        # Check if default app is already initialized
        try:
            firebase_admin.get_app()
            return True
        except ValueError:
            # Not initialized, proceed with initialization
            cred_dict = getattr(settings, 'FIREBASE_CREDENTIALS_DICT', None)
            if cred_dict:
                # Use dictionary config if available (better for cloud deployment)
                cred = credentials.Certificate(cred_dict)
            else:
                # Fallback to file path
                import os
                cred_path = getattr(settings, 'FIREBASE_CREDENTIALS', 'serviceAccountKey.json')
                if not os.path.isabs(cred_path):
                    base_dir = getattr(settings, 'BASE_DIR', None)
                    if base_dir:
                        cred_path = os.path.join(str(base_dir), cred_path)
                cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            return True
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        return False

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
            rating = self.rating_items.filter(area=key).first()
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
        return self.rating_items.count()
    
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
        'push': 'Push Notification',
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
    cta_link = models.CharField(max_length=500, blank=True, null=True)

    def send(self):
        """
        Sends the notification via the specified channel.
        Note: The notification instance is NOT deleted after sending, allowing it to remain
        in the user's in-app notification history.
        """
        if self.channel =='sms':
            if sms_service and self.user.phone:
                phone = normalize_phone_number(self.user.phone)
                if phone:
                    try:
                        response = sms_service.send(self.message, [phone])
                        logger.info(f"SMS sent to {phone}: {response}")
                        return
                    except Exception as e:
                        logger.error(f"Failed to send SMS to {phone}: {e}")
            
        elif self.channel == 'email':
            try:
                context = {
                    'subject': self.subject,
                    'message': self.message,
                    'cta_text': self.cta_text,
                    'cta_link': self.cta_link,
                    'user_name': self.user.name if hasattr(self.user, 'name') else 'User'
                }
                sent = send_email(
                    subject=self.subject,
                    recipients=[self.user.email],
                    template='generic_notification.html',
                    context=context
                )
                if sent:
                    logger.info(f"Email sent to {self.user.email}")
                    return
            except Exception as e:
                logger.error(f"Failed to send email to {self.user.email}: {e}")

        elif self.channel == 'push':
            from accounts.models import FCMDevice
            
            # Initialize Firebase if needed
            if not initialize_firebase():
                return
            
            devices = FCMDevice.objects.filter(user=self.user, active=True)
            if devices.exists():
                registration_ids = list(devices.values_list('registration_id', flat=True))
                
                # Construct the message
                # Note: 'data' is for background handling, 'notification' is for foreground/system tray
                message = messaging.MulticastMessage(
                    notification=messaging.Notification(
                        title=self.subject,
                        body=self.message,
                    ),
                    data={
                        'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                        'sound': 'default', 
                        'status': 'done',
                        'screen': self.cta_link if self.cta_link else '/notifications',
                        'channel': self.channel,
                        'level': self.level,
                        'notification_id': str(self.id),
                    },
                    tokens=registration_ids,
                )
                
                try:
                    response = messaging.send_multicast(message)
                    if response.failure_count > 0:
                        responses = response.responses
                        failed_tokens = []
                        for idx, resp in enumerate(responses):
                            if not resp.success:
                                # The order of responses corresponds to the order of the registration tokens.
                                failed_tokens.append(registration_ids[idx])
                                logger.warning(f"Failed to send to token {registration_ids[idx]}: {resp.exception}")
                        
                        # Deactivate invalid tokens
                        # The error code for invalid token is usually 'registration-token-not-registered'
                        # But for now, we just log it.
                        
                except Exception as e:
                    logger.error(f"Error sending FCM message: {e}")

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
        





