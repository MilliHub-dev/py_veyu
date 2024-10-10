from ..models import (
    Account,             
    Customer,
    Dealer,
    Mechanic,
    PayoutInformation,
)
from rest_framework.serializers import (
    ModelSerializer,
    StringRelatedField,
    SerializerMethodField,
    CharField,
    ChoiceField,
    Serializer,
    ManyRelatedField,
    EmailField,
)
from feedback.api.serializers import (
    RatingSerializer
)
from bookings.api.serializers import (
    ServiceSerializer,
    MechanicServiceSerializer,
)


class VerificationSerializer(Serializer):
    code = CharField()
    action = ChoiceField({
        'request-code': 'Request OTP',
        'confirm-code': 'Confirm OTP'
    })
    channel = ChoiceField({
        'email': 'Email address',
        'phone_number': 'Phone number'
    })

    class Meta:
        fields = ['code', 'channel', 'action']

class LoginSerializer(ModelSerializer):
    class Meta:
        model = Account
        fields = ('email', 'api_token', 'name', 'user_type', 'verified_email', 'is_staff', 'first_name', 'last_name')
        read_only_fields = (None)


class AccountSerializer(ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'
        # read_only_fields = ('uuid', 'name', 'email', 'image', 'first_name', 'location', 'api_token', )


class CustomerSerializer(ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'


class MechanicSerializer(ModelSerializer):
    account = SerializerMethodField()
    # rating = RatingSerializer(many=True)
    services = MechanicServiceSerializer(many=True)
    # account.fields = ('uuid', 'email')
    class Meta:
        model = Mechanic
        fields = (
            "id", "account", "date_created", "uuid", "last_updated", "phone_number",
            "verified_phone_number","available", "location","current_job", "services","job_history","reviews"
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



