from ..models import (
    Account,             
    Customer,
    Dealer,
    Mechanic,
    Agent,
    PayoutInformation,
)
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers


class AccountSerializer(ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'


class CustomerSerializer(ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'




class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = '__all__'
        read_only_fields = ('user',)

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        return instance

def get_user_serializer(user_type):
    
    profile_model = {'customer': Customer, 'mechanic': Mechanic, 'dealer': Dealer, 'agent': Agent}.get(user_type)
    model = profile_model
    
    UserProfileSerializer.Meta.model = model
   
    return UserProfileSerializer




class LoginSerializer(serializers.Serializer):

    email = serializers.EmailField()
    password = serializers.CharField(style={"input_type": "password"})

    def validate_email(self, value):
        """Validate that user with email exists."""
        user = Account.objects.filter(email=value).first()

        if not user:
            raise serializers.ValidationError(
                detail={'message':': user does not exist'}
            )
        if user.is_active is False:
            raise serializers.ValidationError(
                detail={'message':': user is not activated'}
            )

        return user


class MechanicSerializer(ModelSerializer):
    # account = SerializerMethodField()
    # ratings = RatingSerializer(many=True)
    # # services = StringRelatedField(many=True)
    # services = ServiceSerializer(many=True)
    # # account.fields = ('uuid', 'email')
    # class Meta:
    #     model = Mechanic
    #     fields = (
    #         "id", "account", "date_created", "uuid", "last_updated", "phone_number",
    #         "verified_phone_number","available", "location","current_job", "services","job_history","ratings"
    #     )
    
    # def get_account(self, obj):
    #     account = obj.account  # Get the related account instance

    #     # Define custom logic to exclude or modify fields
    #     return {
    #         'uuid': account.uuid,  # Show uuid
    #         'email': account.email,  # Show email
    #         'name': account.name,
    #         'last_seen': account.last_seen
    #     }
        pass


