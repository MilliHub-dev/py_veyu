from ..models import (
    Rating,
    ChatMessage,
    ChatRoom,
    SupportTicket,
    TicketCategory,
    Tag,
    Notification
)

from rest_framework.serializers import (
    ModelSerializer,
    StringRelatedField
)


class RatingSerializer(ModelSerializer):
    reviewer = StringRelatedField()
    class Meta:
        model = Rating
        fields = ('id', 'uuid', 'stars', 'review', 'reviewer')



