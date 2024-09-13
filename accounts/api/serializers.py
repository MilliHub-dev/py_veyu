from ..models import (
    Account,             
    Customer,
    Dealer,
    Mechanic,
    PayoutInformation,
)
from rest_framework.serializers import ModelSerializer



class AccountSerializer(ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'


class CustomerSerializer(ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'




