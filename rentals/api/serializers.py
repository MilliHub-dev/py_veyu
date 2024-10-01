from ..models import (
    CarRental,
    Listing,
    Order,
    Vehicle,
    VehicleTag,
    VehicleCategory,
    VehicleImage,
    VehicleCategory,
    TestDriveRequest,
    TradeInRequest,
)
from rest_framework.serializers import (
    ModelSerializer,
    ModelField,
    StringRelatedField,
    HyperlinkedRelatedField,
    RelatedField,
)
from rest_framework import serializers
from rest_framework.parsers import MultiPartParser, FormParser
from decimal import Decimal
from django.db import models
from decimal import Decimal
from django.contrib.auth import get_user_model

User = get_user_model()


class VehicleImageSerializer(ModelSerializer):
    class Meta:
        model = VehicleImage
        fields ='__all__'
        extra_kwargs = {'vehicle': {'required': False}}

class VehicleSerializer(serializers.ModelSerializer):
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

class ListingSerializer(ModelSerializer):
    vehicle = VehicleSerializer()
    class Meta:
        model = Listing
        fields = '__all__'

class CreateListingSerializer(ModelSerializer):
    class Meta:
        model = Listing
        fields = '__all__'

class OrderSerializer(ModelSerializer):
    order_items = ListingSerializer(many=True)

    class Meta:
        model = Order
        fields = '__all__'

# English or Spanish 😊
class VehicleUpdateSerializer(ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'
        extra_kwargs = {
            'uuid': {'read_only': True},
        }

class BookCarRentalSerializer(serializers.ModelSerializer):
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
    order_id = serializers.IntegerField(required=True)

    def validate(self, data):
        """
        Check that the recipient and order exists.
        """
        email = data['recipient']
        order_id = data['order_id']
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Recipient not found")
        
        if not Order.objects.filter(id=order_id).exists():
            raise serializers.ValidationError("Order not found")

        return data
