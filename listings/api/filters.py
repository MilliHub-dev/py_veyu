from django_filters.rest_framework import (
    FilterSet,
    BooleanFilter,
    CharFilter,
    ChoiceFilter,
    MultipleChoiceFilter,
    DateFilter,
    RangeFilter,
    NumberFilter,
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
    condition = ChoiceFilter(field_name='condition', label="Car condition",)
    type = CharFilter(method='filter_type', label="Type")
    transmission = CharFilter(method='filter_transmission', label="Transmission")
    fuel_system = CharFilter(method='filter_fuel_system', label="Fuel System")
    model = CharFilter(method='filter_model', label="Car Model")
    price = CharFilter(method='filter_price', label="Listing Price")
    location = CharFilter(method='filter_location', label="Dealer Location")
    mileage = RangeFilter(method='filter_mileage', label="Mileage")

    class Meta:
        model = Listing
        fields = [ 'brands', 'price' ]

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

    def filter_type(self, queryset, name, value):
        # Filter listing by car type
        q = Q()
        filters = [_type.strip() for _type in value.split(',')]

        for item in filters:
            q |= Q(vehicle__type__iexact=item)
        return queryset.filter(q).distinct()

    def filter_fuel_system(self, queryset, name, value):
        # Filter listing by car fuel_system
        q = Q()
        filters = [_type.strip() for _type in value.split(',')]

        for item in filters:
            q = Q(vehicle__fuel_system__iexact=item)
        return queryset.filter(q).distinct()

    def filter_price(self, queryset, name, value):
        # a price range must be supllied in a slice object
        # ie provided in the params as ?price_min=120000&price_max=5000000
        # Check if value is actually a slice
        q = Q()
        value = value.split('-')
        # # Get the start and stop values from the slice (i.e., min_price and max_price)
        min_price = to_decimal(value[0])
        max_price = to_decimal(value[1])

        print(f"Price range: {min_price} - {max_price}")
        # # Build the query based on whether min_price and max_price are set
        if min_price > 0 and max_price > 0:
            q = Q(Q(price__gte=min_price) & Q(price__lte=max_price))
        elif min_price > 0:
            q = Q(price__gte=min_price)
        elif max_price > 0 and max_price > min_price:
            q = Q(price__lte=max_price)
        return queryset.filter(q).distinct()

    def filter_mileage(self, queryset, name, value):
        return
    
    def filter_location(self, queryset, name, value):
        return
    


class CarRentalFilter(FilterSet):
    make = CharFilter(method='filter_make', label='Car Make / Brand')
    condition = ChoiceFilter(field_name='condition', label="Car condition",)
    type = CharFilter(method='filter_type', label="Type")
    transmission = CharFilter(method='filter_transmission', label="Transmission")
    fuel_system = CharFilter(method='filter_fuel_system', label="Fuel System")
    model = CharFilter(method='filter_model', label="Car Model")
    price = RangeFilter(method='filter_price', label="Listing Price")
    location = CharFilter(method='filter_location', label="Dealer Location")
    mileage = RangeFilter(method='filter_mileage', label="Mileage")

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

    def filter_type(self, queryset, name, value):
        # Filter listing by car type
        q = Q()
        filters = [_type.strip() for _type in value.split(',')]

        for item in filters:
            q |= Q(vehicle__type__iexact=item)
        return queryset.filter(q).distinct()

    def filter_fuel_system(self, queryset, name, value):
        # Filter listing by car fuel_system
        q = Q()
        filters = [_type.strip() for _type in value.split(',')]

        for item in filters:
            q = Q(vehicle__fuel_system__iexact=item)
        return queryset.filter(q).distinct()

    def filter_model(self, queryset, name, value):
        return
    

    def filter_price(self, queryset, name, value):
        # a price range must be supllied in a slice object
        # ie provided in the params as ?price_min=120000&price_max=5000000
        # Check if value is actually a slice
        q = Q()
        if isinstance(value, str):
            print('Value before:', value)
            value = slice(value.split('-'))
            print('Value after:', value)
        if not isinstance(value, slice):
            raise ValueError("Expected a slice object for price range filtering.")


        # Get the start and stop values from the slice (i.e., min_price and max_price)
        min_price = to_decimal(value.start) if value.start else None
        max_price = to_decimal(value.stop) if value.stop else None

        print(f"Price range: {min_price} - {max_price}")
        # Build the query based on whether min_price and max_price are set
        if min_price is not None and max_price is not None:
            q = Q(Q(price__gte=min_price) & Q(price__lte=max_price))
        elif min_price is not None:
            q = Q(price__gte=min_price)
        elif max_price is not None:
            q = Q(price__lte=max_price)
        else:
            # If both min_price and max_price are None, return the original queryset
            return queryset

        # Apply the filter
        return queryset.filter(q).distinct()

    def filter_mileage(self, queryset, name, value):
        return
    
    def filter_location(self, queryset, name, value):
        return
    



