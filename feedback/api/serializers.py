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

)



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



class NotificationSerializer(ModelSerializer):
    user = StringRelatedField()
    class Meta:
        model = Notification
        fields = '__all__'



