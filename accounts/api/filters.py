from django_filters.rest_framework import (
    FilterSet,
    BooleanFilter,
    CharFilter,
    ChoiceFilter,
    DateFilter,
    RangeFilter,
    NumberFilter,
)
from ..models import (
    Mechanic,
    Account,
)
# from bookings.models import (
#     Service
# )
from django.db.models import Q
from listings.models import Listing




class AgentAccountFilter(FilterSet):
    is_staff = BooleanFilter(field_name='is_staff')
    is_agent = BooleanFilter(method='filter_is_agent')

    class Meta:
        model = Account
        fields = ['is_staff', 'is_agent']

    def filter_is_agent(self, queryset, name, value):
        if value:
            return queryset.filter(user_type='staff')
        return queryset.exclude(user_type='staff')


class MechanicFilter(FilterSet):
    available = BooleanFilter(field_name='available')
    verified_phone_number = BooleanFilter(field_name='verified_phone_number')
    verified_email = BooleanFilter(field_name='account__verified_email')
    rating = NumberFilter(method='filter_rating')
    location = CharFilter(method='filter_location')
    services = CharFilter(method='filter_services')

    class Meta:
        model = Mechanic
        fields = ['available', 'verified_phone_number', 'verified_email']
    
    def filter_rating(self, request, name, value):
        if value:
            return
        return
    
    def filter_location(self, request, name, value):
        if value:
            return
        return
    
    def filter_services(self, queryset, name, value):
        # Split the services by commas and strip any extra spaces
        service_list = [service.strip() for service in value.split(',')]

        q = Q()
        
        # Add each service title to the Q object as an OR condition
        for service_title in service_list:
            q |= Q(services__service__title__iexact=service_title)

        # Filter mechanics who offer at least one of the specified services
        return queryset.filter(q).distinct()



class CarSaleFilter(FilterSet):
    make = CharFilter(method='filter_brand')
    model = CharFilter(method='filter_model')
    price = RangeFilter(method='filter_price')
    usage = RangeFilter(method='filter_usage')
    mileage = RangeFilter(method='filter_mileage')
    vehicle_type = RangeFilter(method='filter_vehicle_type')
    location = CharFilter(method='filter_location')

    class Meta:
        model = Listing
        fields = ['mileage', 'location', 'usage', 'price']

    def filter_brand(self, queryset, name, value):
        return
    
    def filter_model(self, queryset, name, value):
        return
    
    def filter_price(self, queryset, name, value):
        return
    
    def filter_usage(self, queryset, name, value):
        return
    
    def filter_ileage(self, queryset, name, value):
        return
    
    def filter_vehicle_type(self, queryset, name, value):
        return
    
    def filter_location(self, queryset, name, value):
        return
    



