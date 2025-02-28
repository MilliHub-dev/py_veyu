from ..models import (
    Review,
    SupportTicket,
    TicketCategory,
    Tag,
    Notification,
)

from rest_framework.serializers import (
    ModelSerializer,
    StringRelatedField
)


class RatingSerializer(ModelSerializer):
    reviewer = StringRelatedField()
    class Meta:
        model = Review
        fields = ('id', 'uuid', 'stars', 'comment', 'reviewer')


class NotificationSerializer(ModelSerializer):
    user = StringRelatedField()
    class Meta:
        model = Notification
        fields = '__all__'



