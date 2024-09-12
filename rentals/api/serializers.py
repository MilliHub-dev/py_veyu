from ..models import (
    CarRental,
    Listing,
    Order,
    Vehicle,
    VehicleTag,
    VehicleCategory,    
)
from rest_framework.serializers import (
    ModelSerializer,
    ModelField,
    StringRelatedField,
    HyperlinkedRelatedField,
    RelatedField,
)





class VehicleSerializer(ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'


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




