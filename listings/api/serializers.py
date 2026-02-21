import json
from ..models import (
    RentalOrder,
    Listing,
    Order,
    Vehicle,
    Car,
    Boat,
    Plane,
    Bike,
    UAV,
    OrderInspection,
    VehicleImage,
    TestDriveRequest,
    TradeInRequest,
    PurchaseOffer,
    BoostPricing,
    ListingBoost,
)
from rest_framework.serializers import (
    ModelSerializer,
    ModelField,
    StringRelatedField,
    SerializerMethodField,
    HyperlinkedRelatedField,
    RelatedField,
)
from rest_framework import serializers
from rest_framework.parsers import MultiPartParser, FormParser
from decimal import Decimal
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from django.db import models
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from feedback.api.serializers import (ReviewSerializer,)

User = get_user_model()

class DealerSerializer(ModelSerializer):
    location = StringRelatedField()
    logo = SerializerMethodField()
    reviews = ReviewSerializer(many=True)
    owner = SerializerMethodField()
    services = serializers.ListField(read_only=True)  # Read-only property from model
    extended_services = serializers.JSONField(read_only=True)

    class Meta:
        from accounts.models import Dealer
        model = Dealer
        fields = [
            'location',
            'business_name',
            'uuid',
            'logo',
            'owner',
            'rating',
            'about',
            'reviews',
            'headline',
            'cac_number',
            'tin_number',
            'services',
            'offers_drivers',
            'offers_trade_in',
            'contact_email',
            'contact_phone',
            'offers_rental',
            'offers_purchase',
            'extended_services',
        ]

    def get_logo(self, obj, *args, **kwargs):
        request = self.context.get('request')
        if obj.logo:
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None

    def get_owner(self, obj):
        user = obj.user
        return {
            'user_id': user.uuid,
            'email': user.email,
            'name': user.name,
            'phone_number': obj.phone_number,
        }



class VehicleImageSerializer(ModelSerializer):
    url = serializers.SerializerMethodField(method_name='get_image_url')
    class Meta:
        model = VehicleImage
        fields = ['id', 'uuid', 'url']
        extra_kwargs = {'vehicle': {'required': False}}

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return ""

class VehicleSerializer(serializers.ModelSerializer):
    features = serializers.StringRelatedField(many=True)
    images = VehicleImageSerializer(many=True)
    dealer = DealerSerializer()
    condition = serializers.SerializerMethodField()
    transmission = serializers.SerializerMethodField()
    fuel_system = serializers.SerializerMethodField()
    trips = serializers.SerializerMethodField()
    kind = serializers.SerializerMethodField()
    body_type = serializers.SerializerMethodField()
    seats = serializers.SerializerMethodField()
    doors = serializers.SerializerMethodField()
    hull_material = serializers.SerializerMethodField()
    engine_count = serializers.SerializerMethodField()
    propeller_type = serializers.SerializerMethodField()
    length = serializers.SerializerMethodField()
    beam_width = serializers.SerializerMethodField()
    draft = serializers.SerializerMethodField()
    registration_number = serializers.SerializerMethodField()
    engine_type = serializers.SerializerMethodField()
    aircraft_type = serializers.SerializerMethodField()
    max_altitude = serializers.SerializerMethodField()
    wing_span = serializers.SerializerMethodField()
    range = serializers.SerializerMethodField()
    engine_capacity = serializers.SerializerMethodField()
    bike_type = serializers.SerializerMethodField()
    saddle_height = serializers.SerializerMethodField()
    uav_type = serializers.SerializerMethodField()
    purpose = serializers.SerializerMethodField()
    max_flight_time = serializers.SerializerMethodField()
    max_range = serializers.SerializerMethodField()
    max_speed = serializers.SerializerMethodField()
    camera_resolution = serializers.SerializerMethodField()
    payload_capacity = serializers.SerializerMethodField()
    weight = serializers.SerializerMethodField()
    rotor_count = serializers.SerializerMethodField()
    has_obstacle_avoidance = serializers.SerializerMethodField()
    has_gps = serializers.SerializerMethodField()
    has_return_to_home = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = '__all__'
        extra_kwargs = {'dealer': {'read_only': True},
                        'slug': {'read_only': True},
                        'uuid': {'read_only': True},
                        'last_rented': {'read_only': True},
                        'current_rental': {'read_only': True},
                        'sold': {'read_only': True},
                        'tags': {'read_only': True},
                        'images': {'read_only': True},
                        'video': {'read_only': True}
        }

    def get_condition(self, obj):
        return obj.get_condition_display()

    def get_trips(self, obj):
        return obj.trips()

    def get_transmission(self, obj):
        return obj.get_transmission_display()

    def get_fuel_system(self, obj):
        return obj.get_fuel_system_display()

    def get_kind(self, obj):
        return obj.__class__.__name__.lower()

    def _as_car(self, obj):
        from ..models import Car
        if isinstance(obj, Car):
            return obj
        try:
            return obj.car
        except ObjectDoesNotExist:
            return None
        except AttributeError:
            return None

    def get_body_type(self, obj):
        car = self._as_car(obj)
        if car and getattr(car, 'body_type', None):
            return car.get_body_type_display()
        return None

    def get_seats(self, obj):
        car = self._as_car(obj)
        if car and getattr(car, 'seats', None) is not None:
            return car.seats
        return None

    def get_doors(self, obj):
        car = self._as_car(obj)
        if car and getattr(car, 'doors', None) is not None:
            return car.doors
        return None

    def _get_attr_from_related(self, obj, attr_name, related_name):
        if hasattr(obj, attr_name):
            return getattr(obj, attr_name)
        try:
            related = getattr(obj, related_name)
        except ObjectDoesNotExist:
            return None
        except AttributeError:
            return None
        if related is None:
            return None
        return getattr(related, attr_name, None)

    def get_hull_material(self, obj):
        return self._get_attr_from_related(obj, 'hull_material', 'boat')

    def get_engine_count(self, obj):
        return self._get_attr_from_related(obj, 'engine_count', 'boat')

    def get_propeller_type(self, obj):
        return self._get_attr_from_related(obj, 'propeller_type', 'boat')

    def get_length(self, obj):
        value = (
            self._get_attr_from_related(obj, 'length', 'boat')
            or self._get_attr_from_related(obj, 'length', 'plane')
        )
        return value

    def get_beam_width(self, obj):
        return self._get_attr_from_related(obj, 'beam_width', 'boat')

    def get_draft(self, obj):
        return self._get_attr_from_related(obj, 'draft', 'boat')

    def get_registration_number(self, obj):
        value = (
            self._get_attr_from_related(obj, 'registration_number', 'plane')
            or self._get_attr_from_related(obj, 'registration_number', 'uav')
        )
        return value

    def get_engine_type(self, obj):
        return self._get_attr_from_related(obj, 'engine_type', 'plane')

    def get_aircraft_type(self, obj):
        return self._get_attr_from_related(obj, 'aircraft_type', 'plane')

    def get_max_altitude(self, obj):
        value = (
            self._get_attr_from_related(obj, 'max_altitude', 'plane')
            or self._get_attr_from_related(obj, 'max_altitude', 'uav')
        )
        return value

    def get_wing_span(self, obj):
        return self._get_attr_from_related(obj, 'wing_span', 'plane')

    def get_range(self, obj):
        value = (
            self._get_attr_from_related(obj, 'range', 'plane')
            or self._get_attr_from_related(obj, 'range', 'uav')
        )
        return value

    def get_engine_capacity(self, obj):
        return self._get_attr_from_related(obj, 'engine_capacity', 'bike')

    def get_bike_type(self, obj):
        return self._get_attr_from_related(obj, 'bike_type', 'bike')

    def get_saddle_height(self, obj):
        return self._get_attr_from_related(obj, 'saddle_height', 'bike')

    def get_uav_type(self, obj):
        return self._get_attr_from_related(obj, 'uav_type', 'uav')

    def get_purpose(self, obj):
        return self._get_attr_from_related(obj, 'purpose', 'uav')

    def get_max_flight_time(self, obj):
        return self._get_attr_from_related(obj, 'max_flight_time', 'uav')

    def get_max_range(self, obj):
        return self._get_attr_from_related(obj, 'max_range', 'uav')

    def get_max_speed(self, obj):
        return self._get_attr_from_related(obj, 'max_speed', 'uav')

    def get_camera_resolution(self, obj):
        return self._get_attr_from_related(obj, 'camera_resolution', 'uav')

    def get_payload_capacity(self, obj):
        return self._get_attr_from_related(obj, 'payload_capacity', 'uav')

    def get_weight(self, obj):
        return self._get_attr_from_related(obj, 'weight', 'uav')

    def get_rotor_count(self, obj):
        return self._get_attr_from_related(obj, 'rotor_count', 'uav')

    def get_has_obstacle_avoidance(self, obj):
        return self._get_attr_from_related(obj, 'has_obstacle_avoidance', 'uav')

    def get_has_gps(self, obj):
        return self._get_attr_from_related(obj, 'has_gps', 'uav')

    def get_has_return_to_home(self, obj):
        return self._get_attr_from_related(obj, 'has_return_to_home', 'uav')

    # def get_features(self, obj):
    #     return json.dumps(obj.features)


class CarSerializer(VehicleSerializer):
    class Meta:
        model = Car
        fields = '__all__'

class BoatSerializer(VehicleSerializer):
    class Meta:
        model = Boat
        fields = '__all__'

class PlaneSerializer(VehicleSerializer):
    class Meta:
        model = Plane
        fields = '__all__'

class BikeSerializer(VehicleSerializer):
    class Meta:
        model = Bike
        fields = '__all__'

class UAVSerializer(VehicleSerializer):
    class Meta:
        model = UAV
        fields = '__all__'

class OrderInspectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderInspection
        fields = '__all__'


class CreateVehicleSerializer(serializers.ModelSerializer):
    images = VehicleImageSerializer(many=True)
    dealer = DealerSerializer()
    class Meta:
        model = Vehicle
        fields = '__all__'


class ListingSerializer(ModelSerializer):
    vehicle = VehicleSerializer()
    cycle = serializers.SerializerMethodField()
    total_views = serializers.SerializerMethodField()
    date_listed = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = '__all__'

    def get_cycle(self, obj):
        return obj.get_payment_cycle_display()
    
    def get_total_views(self, obj):
        """Returns total number of viewers"""
        return obj.viewers.count()
    
    def get_date_listed(self, obj):
        """Returns the date when listing was created"""
        return obj.date_created.isoformat() if obj.date_created else None
    
    def get_total_reviews(self, obj):
        """Returns total number of reviews for this listing"""
        from feedback.models import Review
        return Review.objects.filter(
            object_type='vehicle',
            related_object=obj.uuid
        ).count()
    
    def get_average_rating(self, obj):
        """Returns average rating from all reviews"""
        from feedback.models import Review
        reviews = Review.objects.filter(
            object_type='vehicle',
            related_object=obj.uuid
        )
        if not reviews.exists():
            return 0.0
        
        total_rating = sum(review.avg_rating for review in reviews)
        return round(total_rating / reviews.count(), 1) if reviews.count() > 0 else 0.0


class CreateListingSerializer(ModelSerializer):
    vehicle = CreateVehicleSerializer()
    class Meta:
        model = Listing
        fields = '__all__'


class OrderItemSerializer(ModelSerializer):
    class Meta:
        model = Listing
        fields = '__all__'



class OrderSerializer(ModelSerializer):
    order_item = ListingSerializer()
    customer = SerializerMethodField()

    class Meta:
        model = Order
        fields = '__all__'

    def get_customer(self, obj):
        return obj.customer.user.name

# English or Spanish 😊
class VehicleUpdateSerializer(ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'
        extra_kwargs = {
            'uuid': {'read_only': True},
        }

class BookRentalOrderSerializer(serializers.ModelSerializer):
    order_items = serializers.SerializerMethodField()
    sub_total = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['order_type', 'order_items', 'customer', 'sub_total', 'discount']

        extra_kwargs = {
            'discount': {'read_only': True},
            'commission': {'read_only': True},
        }

    def get_order_items(self, obj):
        return [listing.id for listing in obj.order_items.all()]

    def create(self, validated_data):
        order_items_x = self.initial_data.get('order_items', [])

        if not isinstance(order_items_x, list):
            raise ValidationError({'error': 'Order items should be a list.'})

        order_items_queryset = Listing.objects.filter(
            id__in=order_items_x,
            vehicle__available=True,
            vehicle__for_sale=False,
            vehicle__current_rental=None
        )

        if order_items_queryset.count() != len(order_items_x):
            raise ValidationError({'error': 'Some listings are not available for rent or invalid.'})

        # Calculate the subtotal
        order_items_prices = [item.rental_price for item in order_items_queryset]
        sub_total = sum(order_items_prices)
        validated_data['sub_total'] = sub_total

        # Create the Order instance
        order = Order.objects.create(**validated_data)

        # Assign the selected order items
        order.order_items.set(order_items_queryset)

        print('Order created successfully with ID:', order.id)
        return order

    def get_sub_total(self, obj):
        return sum([item.rental_price for item in obj.order_items.all()])

    def update(self, instance, validated_data):
        order_items_x = self.initial_data.get('order_items', [])

        if not isinstance(order_items_x, list):
            raise serializers.ValidationError({'error': 'Order items should be a list.'})

        order_items_queryset = Listing.objects.filter(
            id__in=order_items_x,
            vehicle__available=True,
            vehicle__for_sale=False,
            vehicle__current_rental=None
        )

        if order_items_queryset.count() != len(order_items_x):
            raise serializers.ValidationError({'error': 'Some listings are not available for rent or invalid.'})

        # Calculate the subtotal
        order_items_prices = [item.rental_price for item in order_items_queryset]
        sub_total = sum(order_items_prices)
        validated_data['sub_total'] = sub_total

        instance.order_type = validated_data.get('order_type', instance.order_type)
        instance.order_items.set(order_items_queryset)

        instance.save()

        return instance

# task 3
class TestDriveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestDriveRequest
        fields = ['requested_by', 'requested_to', 'listing']

class TradeInRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeInRequest
        fields = ['vehicle', 'estimated_value', 'comments']

class CompleteOrderSerializer(serializers.Serializer):
    recipient = serializers.EmailField(required=True)
    order_id = serializers.CharField(required=True)

    def validate(self, data):
        """
        Check that the recipient and order exists.
        """
        email = data['recipient']
        order_id = data['order_id']
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Recipient not found")

        if not Order.objects.filter(uuid=order_id).exists():
            raise serializers.ValidationError("Order not found")

        return data

class PurchaseOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOffer
        fields = '__all__'


class BoostPricingSerializer(serializers.ModelSerializer):
    """Serializer for boost pricing configuration (admin only)"""
    formatted_price = serializers.ReadOnlyField()
    duration_display = serializers.CharField(source='get_duration_type_display', read_only=True)
    
    class Meta:
        model = BoostPricing
        fields = ['id', 'duration_type', 'duration_display', 'price', 'formatted_price', 'is_active']
        read_only_fields = ['id', 'formatted_price', 'duration_display']


class ListingBoostSerializer(serializers.ModelSerializer):
    """Serializer for viewing listing boost details"""
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    listing_uuid = serializers.CharField(source='listing.uuid', read_only=True)
    dealer_name = serializers.CharField(source='dealer.business_name', read_only=True)
    formatted_amount = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    duration_days = serializers.ReadOnlyField()
    duration_display = serializers.CharField(source='get_duration_type_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    
    class Meta:
        model = ListingBoost
        fields = [
            'id', 'listing', 'listing_title', 'listing_uuid', 'dealer', 'dealer_name',
            'start_date', 'end_date', 'duration_type', 'duration_display', 
            'duration_count', 'amount_paid', 'formatted_amount', 'payment_status',
            'payment_status_display', 'payment_reference', 'active', 'days_remaining',
            'duration_days', 'date_created'
        ]
        read_only_fields = [
            'id', 'dealer', 'active', 'formatted_amount', 'days_remaining',
            'duration_days', 'date_created', 'listing_title', 'listing_uuid',
            'dealer_name', 'duration_display', 'payment_status_display'
        ]


class CreateListingBoostSerializer(serializers.Serializer):
    """Serializer for creating a listing boost"""
    listing = serializers.UUIDField(required=True)
    duration_type = serializers.ChoiceField(
        choices=['daily', 'weekly', 'monthly'],
        required=True,
        help_text="Type of duration: daily, weekly, or monthly"
    )
    duration_count = serializers.IntegerField(
        required=True,
        min_value=1,
        max_value=12,
        help_text="Number of duration units (e.g., 2 for 2 weeks)"
    )
    
    def validate_listing(self, value):
        """Validate that the listing exists and belongs to the dealer"""
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required")
        
        try:
            from accounts.models import Dealership
            dealer = Dealership.objects.get(user=request.user)
            listing = Listing.objects.get(uuid=value, vehicle__dealer=dealer)
            
            # Check if listing already has an active boost
            if hasattr(listing, 'listing_boost') and listing.listing_boost.is_active():
                raise serializers.ValidationError(
                    f"This listing already has an active boost until {listing.listing_boost.end_date}"
                )
            
            return value
        except Dealership.DoesNotExist:
            raise serializers.ValidationError("Dealership profile not found")
        except Listing.DoesNotExist:
            raise serializers.ValidationError("Listing not found or does not belong to you")
    
    def validate_duration_type(self, value):
        """Validate that the duration type has active pricing"""
        try:
            pricing = BoostPricing.objects.get(duration_type=value, is_active=True)
        except BoostPricing.DoesNotExist:
            raise serializers.ValidationError(
                f"Boost pricing for {value} is not available. Please contact support."
            )
        return value
    
    def validate(self, data):
        """Calculate total cost and add to validated data"""
        duration_type = data['duration_type']
        duration_count = data['duration_count']
        
        try:
            pricing = BoostPricing.objects.get(duration_type=duration_type, is_active=True)
            total_cost = pricing.price * duration_count
            data['total_cost'] = total_cost
            data['pricing'] = pricing
        except BoostPricing.DoesNotExist:
            raise serializers.ValidationError("Boost pricing not found")
        
        return data
