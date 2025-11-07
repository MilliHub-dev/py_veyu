from ..models import (
    Account,
    Customer,
    Dealer,
    Mechanic,
    PayoutInformation,
)
from feedback.api.serializers import (
    RatingSerializer,
    ReviewSerializer,
)

from listings.api.serializers import (
    OrderItemSerializer,
    ListingSerializer,
)

from bookings.api.serializers import (
    # ViewBookingSerializer,
    ServiceSerializer,
    MechanicServiceSerializer
)
from rest_framework.serializers import (
    ModelSerializer,
    StringRelatedField,
    SerializerMethodField,
    Serializer,
    EmailField,
    CharField
)
from rest_framework import serializers
from django.contrib.auth.password_validation import password_changed, validate_password
from typing import Any
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from utils.location import haversine
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class SignupSerializer(Serializer):
    """
    User registration serializer for creating new Veyu accounts.
    
    Supports multiple user types: customer, mechanic, dealer.
    Handles both Veyu native accounts and social media authentication.
    """
    
    email = EmailField(
        required=True,
        help_text="User's email address (must be unique)",
        style={'placeholder': 'user@example.com'}
    )
    first_name = CharField(
        required=True, 
        max_length=50,
        help_text="User's first name",
        style={'placeholder': 'John'}
    )
    last_name = CharField(
        required=True, 
        max_length=50,
        help_text="User's last name",
        style={'placeholder': 'Doe'}
    )
    password = CharField(
        required=True, 
        min_length=8,
        max_length=128,
        write_only=True,
        help_text="Strong password (min 8 characters)",
        style={'input_type': 'password', 'placeholder': '••••••••'}
    )
    confirm_password = CharField(
        required=True,
        write_only=True,
        help_text="Password confirmation (must match password)",
        style={'input_type': 'password', 'placeholder': '••••••••'}
    )
    user_type = CharField(
        required=True,
        help_text="Type of user account: customer, mechanic, or dealer"
    )
    provider = CharField(
        required=False,
        default='veyu',
        help_text="Authentication provider: veyu, google, apple, facebook"
    )
    phone_number = CharField(
        required=False,
        max_length=20,
        help_text="User's phone number (optional)",
        style={'placeholder': '+234XXXXXXXXXX'}
    )
    api_token = StringRelatedField(read_only=True)

    class Meta:
        swagger_schema_fields = {
            "example": {
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!",
                "user_type": "customer",
                "provider": "veyu",
                "phone_number": "+2348123456789"
            }
        }

    def validate(self, attrs):
        """Validate password confirmation and user type."""
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError("Passwords do not match.")
        
        if attrs.get('user_type') not in ['customer', 'mechanic', 'dealer']:
            raise serializers.ValidationError("Invalid user type.")
        
        return attrs

    def validate_provider(self, value):
        """Validate that the provider is valid."""
        if value not in ['google', 'apple', 'veyu', 'facebook']:
            raise serializers.ValidationError(
                detail={'message': 'Invalid Provider'}
            )
        return value

    def validate_email(self, value):
        """Validate email uniqueness."""
        if Account.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def create(self, validated_data):
        """Create new user account with proper authentication setup."""
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password')
        
        try:
            user = Account.objects.create_user(
                password=password if validated_data.get('provider') == 'veyu' else None,
                **validated_data
            )
            
            # Create user type specific profile
            user_type = validated_data.get('user_type')
            if user_type == 'customer':
                Customer.objects.create(user=user)
            elif user_type == 'mechanic':
                Mechanic.objects.create(user=user)
            elif user_type == 'dealer':
                Dealer.objects.create(user=user)
                
            return user
        except Exception as e:
            raise serializers.ValidationError(f"Error creating account: {str(e)}")


class AccountSerializer(ModelSerializer):
    class Meta:
        model = Account
        fields = ['email', 'first_name', 'last_name', 'token', 'user_type', 'verified_email',]


class CustomerSerializer(ModelSerializer):
    cart = ListingSerializer(many=True)
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
    profile_model = {'customer': Customer, 'mechanic': Mechanic, 'dealer': Dealer,}.get(user_type)
    model = profile_model
    UserProfileSerializer.Meta.model = model
    return UserProfileSerializer


class MechanicSerializer(ModelSerializer):
    user = SerializerMethodField()
    reviews = ReviewSerializer(many=True)
    services = MechanicServiceSerializer(many=True)
    location = StringRelatedField()
    logo = SerializerMethodField()
    level = SerializerMethodField()
    price_start = SerializerMethodField()
    distance = SerializerMethodField()

    class Meta:
        model = Mechanic
        fields = (
            "id", "user", "date_created", "uuid", "last_updated", "phone_number",
            "verified_phone_number","available", "location","current_job", "services",
            "job_history","reviews", 'logo', 'level', 'business_name', 'slug', 'headline',
            'verified_business', 'verification_status', 'account_status', 'distance',
            'about', 'rating', 'contact_email', 'contact_phone', 'business_type', 'price_start',
        )

    def get_logo(self, obj):
        request = self.context.get('request', None)
        if obj.logo:
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return ''

    def get_level(self, obj):
        return obj.get_level_display()

    def get_price_start(self, obj):
        amt = obj.services.filter(charge__gt=0).order_by('charge').first().charge
        return amt

    def get_user(self, obj):
        account = obj.user  # Get the related account instance

        # Define custom logic to exclude or modify fields
        return {
            'uuid': account.uuid,  # Show uuid
            'email': account.email,  # Show email
            'name': account.name,
            'last_seen': account.last_seen
        }

    def get_distance(self, obj):
        coords = self.context.get('coords', None)
        if coords and obj.location:
            # if user coords is present in context and mech has set location
            # coords should be a tuple (lat, lng)
            # e.g MechanicSerializer(qs, context={'request': request, 'coords': (lat, lng)})
            dist = haversine(
                float(coords[0]),
                float(coords[1]),
                float(obj.location.lat),
                float(obj.location.lng),
            )
            return f"{dist}km"
        return None



class GetDealershipSerializer(ModelSerializer):
    logo = SerializerMethodField()
    verification_status = SerializerMethodField()
    account_status = SerializerMethodField()

    class Meta:
        model = Dealer
        fields = [
            'uuid', 'id', 'business_name', 'slug', 'logo',
            'verified_phone_number', 'account_status',
            'verified_business', 'verified_tin', 'verification_status',
            
        ]

    def get_logo(self, obj):
        request = self.context.get('request', None)
        if obj.logo:
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return ''

    def get_account_status(self, obj):
        return obj.get_account_status_display()

    def get_verification_status(self, obj):
        return obj.get_verification_status_display()


class DealershipSerializer(ModelSerializer):
    user = SerializerMethodField()
    reviews = ReviewSerializer(many=True)
    location = StringRelatedField()
    avg_rating = SerializerMethodField()
    ratings = SerializerMethodField()

    class Meta:
        model = Dealer
        fields = (
            "id", "user", "date_created", "uuid", "last_updated", "phone_number",
            "verified_phone_number", 'listings', "location", "reviews", 'logo',
            'business_name', 'slug', 'headline', 'about', 'ratings', 'services',
            'avg_rating', 'contact_email', 'contact_phone'
        )

    def get_avg_rating(self, obj):
        reviews = obj.reviews.all()
        if not reviews.exists():
            return 0  # Avoid division by zero

        total_rating = sum(review.avg_rating for review in reviews)
        return round(total_rating / reviews.count(), 1)

    def get_ratings(self, obj):
        reviews = obj.reviews.all()
        ratings = {}
        
        # Aggregate ratings from all reviews
        for review in reviews:
            _ratings = review.get_ratings()  # Call method, don't reference directly
            
            for key, stars in _ratings.items():
                if key not in ratings:
                    ratings[key] = {'total_stars': 0, 'count': 0}
                
                ratings[key]['total_stars'] += stars
                ratings[key]['count'] += 1

        # Compute average ratings per category
        avg_ratings = {
            key: round(value['total_stars'] / value['count'], 1)
            for key, value in ratings.items() if value['count'] > 0
        }

        return avg_ratings

    def get_user(self, obj):
        account = obj.user
        return {
            'uuid': account.uuid,
            'email': account.email,
            'name': account.name,
            'provider': account.provider,
            'last_seen': account.last_seen
        }

    def get_logo(self, obj):
        request = self.context.get('request', None)
        if obj.logo:
            return request.build_absolute_uri(obj.logo.url) if request else obj.logo.url
        return ''


class GetAccountSerializer(ModelSerializer):
    # password2 = serializers.CharField(write_only=True)
    # phone_number = serializers.CharField()
    id = serializers.IntegerField(read_only=True)
    user_type = serializers.ChoiceField(choices=['customer', 'mechanic', 'dealer', 'agent'])
    class Meta:
        model = Account
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "password",
            # "phone_number",
            'api_token',
            'user_type'
        ]

        extra_kwargs = {
            "password": {"write_only": True, "required": True},
        }

    def validate_user_type(self, value: str) -> str:
        """Validate user type."""
        valid_user_types = ['customer', 'mechanic', 'dealer', 'agent']
        if value not in valid_user_types:
            raise ValidationError(f"{value} is not a valid user type.")
        return value


    # def validate(self, data):
    #     """
    #     Check that the two password entries match.
    #     """
    #     if data['password'] != data['password2']:
    #         raise serializers.ValidationError({"Error": "Password fields didn't match."})

    #     # Validate the password and raise the exception if the validation fails
    #     validate_password(data['password'])
    #     return data


class LoginSerializer(Serializer):
    """
    User authentication serializer for Veyu platform.
    
    Supports both email/password and social media authentication.
    Returns JWT tokens and user profile information.
    """
    
    email = EmailField(
        required=True,
        help_text="User's registered email address",
        style={'placeholder': 'user@example.com'}
    )
    password = CharField(
        required=True,
        write_only=True,
        help_text="User's password (required for Veyu accounts)",
        style={'input_type': 'password', 'placeholder': '••••••••'}
    )
    provider = CharField(
        required=False,
        default='veyu',
        help_text="Authentication provider: veyu, google, apple, facebook"
    )

    class Meta:
        swagger_schema_fields = {
            "example": {
                "email": "john.doe@example.com",
                "password": "SecurePass123!",
                "provider": "veyu"
            }
        }

    def validate(self, attrs):
        """Authenticate user and return user object."""
        email = attrs.get('email')
        password = attrs.get('password')
        provider = attrs.get('provider', 'veyu')

        try:
            user = Account.objects.get(email=email)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        # Validate password for Veyu accounts
        if provider == "veyu" and not user.check_password(raw_password=password):
            raise serializers.ValidationError("Invalid email or password.")

        # Check if user is active
        if not user.is_active:
            raise serializers.ValidationError("Account is deactivated.")

        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()
    new_password2 = serializers.CharField()

    def validate(self):
        if self.new_password != self.new_password2:
            raise serializers.ValidationError("new_password1 doen't match with new_password2.")


class VerifyAccountSerializer(serializers.Serializer):
    email = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)


    CHANNEL_CHOICES = [
        ('email', 'email'),
        ('sms', 'sms'),
    ]

    ACTION_CHOICES = [
        ('request-code', 'request-code'),
        ('confirm-code', 'confirm-code'),
    ]

    channel = serializers.ChoiceField(choices=CHANNEL_CHOICES)
    action = serializers.ChoiceField(choices=ACTION_CHOICES)


    def validate(self, data):
        email = data.get('email')
        phone_number = data.get('phone_number')
        channel = data['channel']


        # Determine user model type based on the request.user instance
        if hasattr(self.context['request'].user, 'customer'):
            user_profile = self.context['request'].user.customer
        elif hasattr(self.context['request'].user, 'mechanic'):
            user_profile = self.context['request'].user.mechanic
        elif hasattr(self.context['request'].user, 'agent'):
            user_profile = self.context['request'].user.agent
        else:
            raise serializers.ValidationError("User type is not supported for this action.")


        if channel == 'email' and email:
            user = Account.objects.filter(email=data['email']).first()

            if not user:
                raise serializers.ValidationError(
                    detail={'message':': user does not exist'}
                )
            if not email:
                raise serializers.ValidationError("Email must be provided.")

        elif channel == 'sms' and phone_number:
            user = user_profile.__class__.objects.filter(phone_number=phone_number).first()

            if not user:
                raise serializers.ValidationError(
                    detail={'message':': user does not exist'}
                )
            if not phone_number:
                raise serializers.ValidationError("Phone number must be provided.")
        return data


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.CharField(required=False)
    code = serializers.CharField(required=False)
    ACTION_CHOICES = [
        ('request-code', 'request-code'),
        ('confirm-code', 'confirm-code'),
    ]
    action = serializers.ChoiceField(choices=ACTION_CHOICES)


    def validate(self, data):
        email = data.get('email')
        action = data.get('action')
        code = data.get('code', None)

        user = Account.objects.filter(email=data['email']).first()

        if not user:
            raise serializers.ValidationError(
                detail={'message':': user does not exist'}
            )
        if not email:
            raise serializers.ValidationError("Email must be provided.")

        if action == 'confirm-code' and not code:
            raise serializers.ValidationError("Code must be provided for confirmation.")

        return data


class VerifyPhoneNumberSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    code = serializers.CharField(required=False)
    ACTION_CHOICES = [
        ('request-code', 'request-code'),
        ('confirm-code', 'confirm-code'),
    ]
    action = serializers.ChoiceField(choices=ACTION_CHOICES)


    def validate(self, data):
        phone_number = data.get('phone_number')
        action = data.get('action')
        code = data.get('code', None)

        if phone_number:
            user = (
                Customer.objects.filter(phone_number=phone_number).first() or
                Mechanic.objects.filter(phone_number=phone_number).first() or
                Dealer.objects.filter(phone_number=phone_number).first() or
                Agent.objects.filter(phone_number=phone_number).first()
            )
        else:
            user = None

        if not user:
            raise serializers.ValidationError(
                detail={'message':'user does not exist'}
            )
        if not phone_number:
            raise serializers.ValidationError("Phone number must be provided.")

        if action == 'confirm-code' and not code:
            raise serializers.ValidationError("Code must be provided for confirmation.")

        return data


class BusinessVerificationSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for submitting business verification details"""
    business_verification_status = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        from accounts.models import BusinessVerificationSubmission
        model = BusinessVerificationSubmission
        fields = [
            'id', 'uuid', 'business_type', 'status', 'business_name',
            'cac_number', 'tin_number', 'business_address', 'business_email',
            'business_phone', 'cac_document', 'tin_document', 'proof_of_address',
            'business_license', 'rejection_reason', 'date_created', 'last_updated',
            'business_verification_status'
        ]
        read_only_fields = ['id', 'uuid', 'status', 'rejection_reason', 'date_created', 'last_updated']
    
    def get_business_verification_status(self, obj):
        return obj.get_status_display()
    
    def create(self, validated_data):
        from accounts.models import BusinessVerificationSubmission, Dealership, Mechanic
        
        # Get the authenticated user from context
        request = self.context.get('request')
        user = request.user
        
        # Determine business type and get the profile
        business_type = validated_data.get('business_type')
        
        if business_type == 'dealership':
            try:
                dealership = Dealership.objects.get(user=user)
                validated_data['dealership'] = dealership
                validated_data['mechanic'] = None
            except Dealership.DoesNotExist:
                raise serializers.ValidationError("Dealership profile not found for this user")
        elif business_type == 'mechanic':
            try:
                mechanic = Mechanic.objects.get(user=user)
                validated_data['mechanic'] = mechanic
                validated_data['dealership'] = None
            except Mechanic.DoesNotExist:
                raise serializers.ValidationError("Mechanic profile not found for this user")
        else:
            raise serializers.ValidationError("Invalid business_type. Must be 'dealership' or 'mechanic'")
        
        # Set status to pending for new submissions
        validated_data['status'] = 'pending'
        
        # Create new submission
        return BusinessVerificationSubmission.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Update existing submission and reset status to pending"""
        # Don't allow changing business type or profile links
        validated_data.pop('business_type', None)
        validated_data.pop('dealership', None)
        validated_data.pop('mechanic', None)
        
        # Reset status to pending on update
        validated_data['status'] = 'pending'
        validated_data['reviewed_by'] = None
        validated_data['reviewed_at'] = None
        validated_data['rejection_reason'] = None
        
        # Update fields
        for key, value in validated_data.items():
            setattr(instance, key, value)
        
        instance.save()
        return instance


class BusinessVerificationStatusSerializer(serializers.Serializer):
    """Serializer for checking verification status"""
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)
    submission_date = serializers.DateTimeField(read_only=True, source='date_created')
    rejection_reason = serializers.CharField(read_only=True)

