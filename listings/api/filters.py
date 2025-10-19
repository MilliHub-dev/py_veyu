from django_filters.rest_framework import (
    FilterSet,
    CharFilter,
)
from ..models import (
   Listing,
   Vehicle,
   to_decimal
)
# from bookings.models import (
#     Service
# )
from django.db.models import Q
from listings.models import Listing


class CarSaleFilter(FilterSet):
    brands = CharFilter(method='filter_brands', label='Car Make / Brand')
    transmission = CharFilter(method='filter_transmission', label="Transmission")
    fuel_system = CharFilter(method='filter_fuel_system', label="Fuel System")
    price = CharFilter(method='filter_price', label="Listing Price (min-max)")

    class Meta:
        model = Listing
        fields = ['brands', 'price', 'transmission', 'fuel_system']

    def filter_brands(self, queryset, name, value):
        # Filter listing by car brands
        q = Q()
        filters = [_type.strip() for _type in value.split(',')]

        for item in filters:
            q |= Q(vehicle__brand__iexact=item)
        return queryset.filter(q).distinct()

    def filter_transmission(self, queryset, name, value):
        # Filter listing by car transmission
        q = Q()
        filters = [_type.strip() for _type in value.split(',')]

        for item in filters:
            q |= Q(vehicle__transmission__iexact=item)
        return queryset.filter(q).distinct()

    def filter_fuel_system(self, queryset, name, value):
        # Filter listing by car fuel_system
        q = Q()
        filters = [_type.strip() for _type in value.split(',')]

        for item in filters:
            q |= Q(vehicle__fuel_system__iexact=item)
        return queryset.filter(q).distinct()

    def filter_price(self, queryset, name, value):
        # expects value like "min-max"
        q = Q()
        parts = [p.strip() for p in value.split('-') if p.strip() != '']
        min_price = to_decimal(parts[0]) if len(parts) > 0 else None
        max_price = to_decimal(parts[1]) if len(parts) > 1 else None

        if min_price is not None and max_price is not None:
            q = Q(price__gte=min_price, price__lte=max_price)
        elif min_price is not None:
            q = Q(price__gte=min_price)
        elif max_price is not None:
            q = Q(price__lte=max_price)
        else:
            return queryset
        return queryset.filter(q).distinct()

    def filter_mileage(self, queryset, name, value):
        return
    
    def filter_location(self, queryset, name, value):
        return
    


class CarRentalFilter(FilterSet):
    make = CharFilter(method='filter_make', label='Car Make / Brand')
    transmission = CharFilter(method='filter_transmission', label="Transmission")
    fuel_system = CharFilter(method='filter_fuel_system', label="Fuel System")
    price = CharFilter(method='filter_price', label="Listing Price (min-max)")

    class Meta:
        model = Listing
        fields = [ ]

    def filter_make(self, queryset, name, value):
        # Filter listing by car brands
        q = Q()
        filters = [_type.strip() for _type in value.split(',')]

        for item in filters:
            q |= Q(vehicle__brand__iexact=item)
        return queryset.filter(q).distinct()

    def filter_transmission(self, queryset, name, value):
        # Filter listing by car transmission
        q = Q()
        filters = [_type.strip() for _type in value.split(',')]

        for item in filters:
            q |= Q(vehicle__transmission__iexact=item)
        return queryset.filter(q).distinct()

    def filter_fuel_system(self, queryset, name, value):
        # Filter listing by car fuel_system
        q = Q()
        filters = [_type.strip() for _type in value.split(',')]

        for item in filters:
            q |= Q(vehicle__fuel_system__iexact=item)
        return queryset.filter(q).distinct()

    def filter_model(self, queryset, name, value):
        return
    

    def filter_price(self, queryset, name, value):
        # expects value like "min-max"
        q = Q()
        parts = [p.strip() for p in value.split('-') if p.strip() != '']
        min_price = to_decimal(parts[0]) if len(parts) > 0 else None
        max_price = to_decimal(parts[1]) if len(parts) > 1 else None

        if min_price is not None and max_price is not None:
            q = Q(price__gte=min_price, price__lte=max_price)
        elif min_price is not None:
            q = Q(price__gte=min_price)
        elif max_price is not None:
            q = Q(price__lte=max_price)
        else:
            return queryset
        return queryset.filter(q).distinct()

    def filter_mileage(self, queryset, name, value):
        return
    
    def filter_location(self, queryset, name, value):
        return
    



