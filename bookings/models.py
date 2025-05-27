from django.db import models
from utils.models import DbModel
# Create your models here.
 

class Service(DbModel):
    title = models.CharField(max_length=400, unique=True)
    description = models.TextField(max_length=1200, blank=True, null=True)

    def __str__(self):
        return self.title

    

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
    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE)
    mechanic = models.ForeignKey('accounts.Mechanic', on_delete=models.CASCADE)
    client_feedback = models.ForeignKey('feedback.Review', blank=True, null=True, on_delete=models.SET_NULL)
    services = models.ManyToManyField('ServiceOffering', blank=True)
    problem_description = models.TextField(blank=True, null=True)

    completed = models.BooleanField(default=False) # marked by client approval
    booking_status = models.CharField(max_length=20, default='requested', choices=BOOKING_STATUS)
    started_on = models.DateTimeField(blank=True, null=True) # date of contract start
    responded_on = models.DateTimeField(blank=True, null=True) # accept/decline request date
    ended_on = models.DateTimeField(blank=True, null=True) # date of service completion
    completed_date = models.DateTimeField(blank=True, null=True) # date of service payout approval
    conversation = models.ForeignKey('chat.ChatRoom', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self) -> str:
        return '%s - %s for %s' % (
            self.booking_status,
            self.type,
            self.customer.user.name
        )
    
    @property
    def status(self):
        return self.booking_status

    @property
    def messages(self):
        msg = self.conversation.messages.all()
        return msg

    @property
    def sub_total(self):
        amt = 0
        for service in self.services.all():
            amt += service.charge
        return amt


class ServiceOffering(DbModel):
    RATES = {
        'flat': 'Flat Rate', 
        'hourly': 'Hourly Rate', 
    }
    offered_by = models.ForeignKey('accounts.Mechanic', on_delete=models.CASCADE)
    service = models.ForeignKey('Service', on_delete=models.CASCADE)
    charge = models.DecimalField(blank=True, null=True, max_digits=1000, decimal_places=2)
    charge_rate = models.CharField(default='flat', max_length=20, choices=RATES)
    
    def __str__(self) -> str:
        return self.service.title

    @property
    def hires(self):
        amt = 0
        bookings = ServiceBooking.objects.filter(mechanic=self.offered_by)
        for booking in bookings:
            if self in booking.services.all():
                amt += 1
        return amt
        


