from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from accounts.models import Mechanic, Dealer, Customer, Account
from bookings import define_request

class UserTypeMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.customer = None
        request.mechanic = None
        request.dealer = None

        define_request(request)

        if request.user.is_authenticated:
            try:
                if request.user.user_type == 'customer':
                    request.customer = Customer.objects.get(user=request.user)
                elif request.user.user_type == 'dealer':
                    request.dealer = Dealer.objects.get(user=request.user)
                elif request.user.user_type == 'mechanic':
                    request.mechanic = Mechanic.objects.get(user=request.user)
            except:
                pass


