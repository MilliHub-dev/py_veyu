from ..models import (
    Review,
    Rating,
    SupportTicket,
    TicketCategory,
    Tag,
    Notification,
)

from rest_framework.serializers import (
    ModelSerializer,
    StringRelatedField,
    SerializerMethodField,
    PrimaryKeyRelatedField,
    CharField,
    DictField,
    IntegerField,
    ValidationError,
)

from django.contrib.auth import get_user_model

Account = get_user_model()



class RatingSerializer(ModelSerializer):    
    class Meta:
        model = Rating
        fields = '__all__' # area, stars,


class ReviewSerializer(ModelSerializer):
    reviewer = SerializerMethodField()
    ratings = SerializerMethodField()
    date = SerializerMethodField()

    class Meta:
        model = Review
        fields = ('id', 'uuid', 'ratings', 'comment', 'reviewer', 'avg_rating', 'date')

    def get_ratings(self, obj):
        return obj.get_ratings()

    def get_date(self, obj):
        return obj.date_created.date()

    def get_reviewer(self, obj):
        request = self.context.get('request', None)
        data = {
            'name': obj.reviewer.name,
            'image': None
        }

        if not request: return data
        if obj.reviewer.user_type == 'customer':
            if obj.reviewer.customer.image:
                data['image'] = request.build_absolute_uri(obj.reviewer.customer.image.url)
        elif obj.reviewer.user_type == 'dealer':
            if obj.reviewer.dealership.logo:
                data['image'] = request.build_absolute_uri(obj.reviewer.dealership.logo.url)
        elif obj.reviewer.user_type == 'mechanic':
            if obj.reviewer.mechanic.logo:
                data['image'] = request.build_absolute_uri(obj.reviewer.mechanic.logo.url)
        return data


class ReviewCreateSerializer(ModelSerializer):
    ratings = DictField(
        child=IntegerField(min_value=1, max_value=5),
        write_only=True
    )
    
    class Meta:
        model = Review
        fields = ('object_type', 'related_object', 'comment', 'ratings', 'related_order')
        extra_kwargs = {
            'related_order': {'required': False},
            'comment': {'required': False}
        }

    def validate(self, attrs):
        ratings = attrs.get('ratings', {})
        valid_areas = [choice[0] for choice in Rating.REVIEW_AREAS.items()]
        for area in ratings.keys():
            if area not in valid_areas:
                raise ValidationError(f"Invalid rating area: {area}. Valid areas are: {', '.join(valid_areas)}")
        return attrs

    def create(self, validated_data):
        ratings_data = validated_data.pop('ratings', {})
        reviewer = self.context['request'].user
        
        review = Review.objects.create(reviewer=reviewer, **validated_data)
        
        for area, stars in ratings_data.items():
            rating = Rating.objects.create(reviewId=review, area=area, stars=stars)
            
        # Link review to the related object (Dealership, etc.)
        if review.object_type == 'dealer' and review.related_object:
            try:
                from accounts.models import Dealership
                dealer = Dealership.objects.get(uuid=review.related_object)
                dealer.reviews.add(review)
            except Dealership.DoesNotExist:
                pass
        
        return review



class NotificationSerializer(ModelSerializer):
    user = StringRelatedField()
    class Meta:
        model = Notification
        fields = '__all__'


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'uuid', 'name', 'date_created')


class TicketCategorySerializer(ModelSerializer):
    total_tickets = SerializerMethodField()
    
    class Meta:
        model = TicketCategory
        fields = ('id', 'uuid', 'name', 'total_tickets', 'date_created')
    
    def get_total_tickets(self, obj):
        return obj.total_tickets


class SupportTicketSerializer(ModelSerializer):
    customer_name = SerializerMethodField()
    customer_email = SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    category = TicketCategorySerializer(read_only=True)
    correspondents = SerializerMethodField()
    status_display = SerializerMethodField()
    severity_display = SerializerMethodField()
    
    class Meta:
        model = SupportTicket
        fields = (
            'id', 'uuid', 'customer', 'customer_name', 'customer_email',
            'status', 'status_display', 'severity_level', 'severity_display',
            'subject', 'tags', 'category', 'chat_room', 'correspondents',
            'days_open', 'is_overdue', 'total_correspondents', 'date_created', 'last_updated'
        )
        read_only_fields = ('customer', 'chat_room', 'days_open', 'is_overdue', 'total_correspondents')
    
    def get_customer_name(self, obj):
        return obj.customer.user.name if obj.customer and obj.customer.user else None
    
    def get_customer_email(self, obj):
        return obj.customer.user.email if obj.customer and obj.customer.user else None
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_severity_display(self, obj):
        return obj.get_severity_level_display()
    
    def get_correspondents(self, obj):
        return [
            {
                'id': c.id,
                'name': c.name,
                'email': c.email
            } for c in obj.correspondents.all()
        ]


class SupportTicketCreateSerializer(ModelSerializer):
    tag_ids = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False,
        write_only=True
    )
    category_id = PrimaryKeyRelatedField(
        queryset=TicketCategory.objects.all(),
        required=False,
        write_only=True,
        allow_null=True
    )
    
    class Meta:
        model = SupportTicket
        fields = ('subject', 'severity_level', 'tag_ids', 'category_id')
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        category_id = validated_data.pop('category_id', None)
        
        # Get customer from context (should be set by view)
        customer = self.context.get('customer')
        if not customer:
            raise ValueError("Customer must be provided in serializer context")
        
        ticket = SupportTicket.objects.create(
            customer=customer,
            status='open',
            category=category_id,
            **validated_data
        )
        
        if tag_ids:
            ticket.tags.set(tag_ids)
        
        return ticket


class SupportTicketUpdateSerializer(ModelSerializer):
    tag_ids = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False,
        write_only=True
    )
    category_id = PrimaryKeyRelatedField(
        queryset=TicketCategory.objects.all(),
        required=False,
        write_only=True,
        allow_null=True
    )
    correspondent_ids = PrimaryKeyRelatedField(
        queryset=Account.objects.filter(is_staff=True),
        many=True,
        required=False,
        write_only=True,
        allow_null=True
    )
    
    class Meta:
        model = SupportTicket
        fields = ('status', 'severity_level', 'subject', 'tag_ids', 'category_id', 'correspondent_ids')
    
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        category_id = validated_data.pop('category_id', None)
        correspondent_ids = validated_data.pop('correspondent_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if category_id is not None:
            instance.category = category_id
        
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        
        if correspondent_ids is not None:
            instance.correspondents.set(correspondent_ids)
        
        instance.save()
        return instance



