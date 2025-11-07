from django.db import models
from utils.models import DbModel
# Create your models here.
 

class Service(DbModel):
    title = models.CharField(max_length=400, unique=True)
    description = models.TextField(max_length=1200, blank=True, null=True)

    def __str__(self):
        return self.title
    
    def __repr__(self):
        return f"<Service: {self.title}>"
    
    @property
    def total_bookings(self):
        """Returns total number of bookings for this service"""
        return self.service_offerings.aggregate(
            total=models.Count('service_bookings')
        )['total'] or 0
    
    class Meta:
        indexes = [
            models.Index(fields=['title']),
        ]
        ordering = ['title']
        verbose_name = 'Service'
        verbose_name_plural = 'Services'

    

class ServiceBooking(DbModel):
    SERVICE_DELIVERY = {
        'emergency': 'Emergency Assistance',
        'routine': 'Routine Check',
    }
    BOOKING_STATUS = {
        'accepted': 'Accepted',
        'canceled': 'Canceled',
        'completed': 'Completed',
        'declined': 'Declined',
        'expired': 'Expired',
        'requested': 'Requested',
        'working': 'Working',
    }
    type = models.CharField(max_length=20, default='routine', choices=SERVICE_DELIVERY)
    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE, related_name='service_bookings')
    mechanic = models.ForeignKey('accounts.Mechanic', on_delete=models.CASCADE, related_name='mechanic_bookings')
    client_feedback = models.ForeignKey('feedback.Review', blank=True, null=True, on_delete=models.SET_NULL, related_name='booking_feedback')
    services = models.ManyToManyField('ServiceOffering', blank=True, related_name='service_bookings')
    problem_description = models.TextField(blank=True, null=True)

    completed = models.BooleanField(default=False) # marked by client approval
    booking_status = models.CharField(max_length=20, default='requested', choices=BOOKING_STATUS)
    started_on = models.DateTimeField(blank=True, null=True) # date of contract start
    responded_on = models.DateTimeField(blank=True, null=True) # accept/decline request date
    ended_on = models.DateTimeField(blank=True, null=True) # date of service completion
    completed_date = models.DateTimeField(blank=True, null=True) # date of service payout approval
    conversation = models.ForeignKey('chat.ChatRoom', on_delete=models.SET_NULL, blank=True, null=True, related_name='service_conversation')

    def __str__(self) -> str:
        return f"Booking #{self.id}: {self.get_booking_status_display()} - {self.get_type_display()} for {self.customer.user.name}"
    
    def __repr__(self):
        return f"<ServiceBooking: #{self.id} - {self.booking_status} - {self.customer.user.email}>"
    
    @property
    def duration_days(self):
        """Returns duration of the booking in days"""
        if self.started_on and self.ended_on:
            return (self.ended_on.date() - self.started_on.date()).days
        return 0
    
    @property
    def is_active(self):
        """Check if booking is currently active"""
        return self.booking_status in ['accepted', 'working']
    
    @property
    def total_services(self):
        """Returns total number of services in this booking"""
        return self.services.count()
    
    @property
    def status(self):
        return self.booking_status

    @property
    def messages(self):
        if self.conversation:
            return self.conversation.room_messages.all()
        return []

    @property
    def sub_total(self):
        amt = 0
        for service in self.services.all():
            amt += service.charge or 0
        return amt
    
    class Meta:
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['mechanic']),
            models.Index(fields=['booking_status']),
            models.Index(fields=['type']),
            models.Index(fields=['completed']),
            models.Index(fields=['date_created']),
            models.Index(fields=['started_on']),
            models.Index(fields=['ended_on']),
        ]
        ordering = ['-date_created']


class ServiceOffering(DbModel):
    RATES = {
        'flat': 'Flat Rate', 
        'hourly': 'Hourly Rate', 
    }
    offered_by = models.ForeignKey('accounts.Mechanic', on_delete=models.CASCADE, related_name='service_offerings')
    service = models.ForeignKey('Service', on_delete=models.CASCADE, related_name='service_offerings')
    charge = models.DecimalField(blank=True, null=True, max_digits=1000, decimal_places=2)
    charge_rate = models.CharField(default='flat', max_length=20, choices=RATES)
    
    def __str__(self) -> str:
        return f"{self.service.title} by {self.offered_by.business_name or self.offered_by.user.name} - {self.charge or 'Free'} ({self.get_charge_rate_display()})"
    
    def __repr__(self):
        return f"<ServiceOffering: {self.service.title} - {self.offered_by.user.email}>"
    
    @property
    def formatted_charge(self):
        """Returns formatted charge with currency"""
        if self.charge:
            return f"₦{self.charge:,.2f}"
        return "Free"

    @property
    def hires(self):
        return ServiceBooking.objects.filter(
            mechanic=self.offered_by,
            services=self
        ).count()
    
    class Meta:
        indexes = [
            models.Index(fields=['offered_by']),
            models.Index(fields=['service']),
            models.Index(fields=['charge_rate']),
        ]
        unique_together = ['offered_by', 'service']
        


