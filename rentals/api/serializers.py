from ..models import (
    CarRental,
    Listing,
    Order,
    Vehicle,
    VehicleTag,
    VehicleCategory,
    VehicleImage,
)
from rest_framework.serializers import (
    ModelSerializer,
    ModelField,
    StringRelatedField,
    HyperlinkedRelatedField,
    RelatedField,
)
from rest_framework import serializers



class VehicleImageSerializer(ModelSerializer):
    class Meta:
        model = VehicleImage
        fields ='__all__'
        extra_kwargs = {'vehicle': {'required': False}}

class VehicleSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True
    )
    
    class Meta:
        model = Vehicle
        fields = ['name', 'color', 'brand', 'condition', 'images']
    
    def create(self, validated_data):
        images_data = validated_data.pop('images')
        vehicle = Vehicle.objects.create(**validated_data)
        
        for image_data in images_data:
            VehicleImage.objects.create(vehicle=vehicle, image=image_data)
        
        return vehicle
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

class BookCarRentalSerializer(ModelSerializer):
    # This is to only show the users' cars that are available for rent, not for sale or currently being rented out.
    order_items = serializers.PrimaryKeyRelatedField(
        queryset=Listing.objects.filter(vehicle__available=True, vehicle__for_sale=False, vehicle__current_rental=None),
        many=True
    )
    
    sub_total = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['order_type', 'order_items', 'customer', 'sub_total', 'discount', 'commission']

        extra_kwargs = {
            'discount': {'read_only': True}
        }

    def get_sub_total(self, obj):
        order_items = obj.order_items.all() if obj.pk else []
        sub_total = sum(item.rental_price for item in order_items)
        return sub_total

