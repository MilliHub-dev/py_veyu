from ..models import (
    Account,             
    Customer,
    Dealer,
    Mechanic,
    PayoutInformation,
    Service,
    ServiceBooking,
)
from rest_framework.serializers import (
    ModelSerializer,
    StringRelatedField,
    SerializerMethodField,
    ManyRelatedField,
)
from feedback.api.serializers import (
    RatingSerializer
)


class LoginSerializer(ModelSerializer):
    class Meta:
        model = Account
        fields = ('email', 'password')
        read_only_fields = None


class AccountSerializer(ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'
        read_only_fields = ('uuid', 'name', 'email', 'image', 'first_name', 'location', 'api_token', )


class ServiceSerializer(ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

class CustomerSerializer(ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'


class MechanicSerializer(ModelSerializer):
    account = SerializerMethodField()
    ratings = RatingSerializer(many=True)
    # services = StringRelatedField(many=True)
    services = ServiceSerializer(many=True)
    # account.fields = ('uuid', 'email')
    class Meta:
        model = Mechanic
        fields = (
            "id", "account", "date_created", "uuid", "last_updated", "phone_number",
            "verified_phone_number","available", "location","current_job", "services","job_history","ratings"
        )
    
    def get_account(self, obj):
        account = obj.account  # Get the related account instance

        # Define custom logic to exclude or modify fields
        return {
            'uuid': account.uuid,  # Show uuid
            'email': account.email,  # Show email
            'name': account.name,
            'last_seen': account.last_seen
        }



