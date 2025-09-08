from rest_framework.serializers import (
    ModelSerializer,
    StringRelatedField,
    ListField,
    UUIDField,
    SerializerMethodField,
)

from ..models import (
    Service,
    ServiceOffering,
    ServiceBooking,
)

class ServiceSerializer(ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'



class MechanicServiceSerializer(ModelSerializer):
    service = StringRelatedField()

    class Meta:
        model = ServiceOffering
        fields = ('service', 'charge_rate', 'charge', 'uuid', 'hires')


class MechanicServiceHistorySerializer(ModelSerializer):

    class Meta:
        model = ServiceBooking
        fields = '__all__'


class CreateBookingSerializer(ModelSerializer):
    class Meta:
        model = ServiceBooking
        fields = '__all__'


class UpdateBookingSerializer(ModelSerializer):
    # services = StringRelatedField(many=True)
    # customer = StringRelatedField()

    class Meta:
        model = ServiceBooking
        # fields = ('booking_status',)
        fields = '__all__'
        # read_only_fields = ('id', 'uuid', 'services', 'customer', 'date_created', )


class BookingSerializer(ModelSerializer):
    ended = SerializerMethodField('get_ended')
    started = SerializerMethodField('get_started')
    mechanic = StringRelatedField()
    customer = StringRelatedField()
    services = StringRelatedField(many=True)
    review = SerializerMethodField()
    rating = SerializerMethodField()
    sub_total = SerializerMethodField()

    class Meta:
        model = ServiceBooking
        fields = ['started', 'sub_total', 'ended', 'review', 'rating', 'customer', 'mechanic', 'status', 'date_created', 'services']

    def get_started(self, obj):
        if obj.started_on:
            return obj.started_on.date()
        return None

    def get_ended(self, obj):
        if obj.ended_on:
            return obj.ended_on.date()
        return None

    def get_review(self, obj):
        if obj.client_feedback:
            return obj.client_feedback.review
        return "No feedback given"

    def get_sub_total(self, obj):
        amt = 0
        for service in obj.services.all():
            amt += service.charge if service.charge else 0
        return amt

    def get_rating(self, obj):
        if obj.client_feedback:
            return obj.client_feedback.stars
        return None


class ViewBookingSerializer(ModelSerializer):
    ended = SerializerMethodField('get_ended')
    rating = SerializerMethodField('get_rating')
    started = SerializerMethodField('get_started')
    review = SerializerMethodField('get_review')
    mechanic = StringRelatedField()
    customer = SerializerMethodField()
    services = StringRelatedField(many=True)

    class Meta:
        model = ServiceBooking
        fields = [
            'uuid', 'started', 'ended', 'review', 'rating',
            'customer', 'mechanic', 'status', 'date_created', 'services',
        ]

    def get_started(self, obj):
        if obj.started_on:
            return obj.started_on.date()
        return None

    def get_customer(self, obj):
        data = {
            'name': obj.customer.user.name,
            'image': '',
        }
        request = self.context.get('request', None)
        if obj.customer.image:
            if request:
                data ['image'] = request.build_absolute_uri(obj.customer.image.url)
            data ['image'] = obj.customer.image.url
        return data

    def get_ended(self, obj):
        if obj.ended_on:
            return obj.ended_on.date()
        return None

    def get_review(self, obj):
        if obj.client_feedback:
            return obj.client_feedback.review
        return "No feedback given"

    def get_rating(self, obj):
        if obj.client_feedback:
            return obj.client_feedback.stars
        return None


class ServiceHistorySerializer(ModelSerializer):
    ended = SerializerMethodField('get_ended')
    rating = SerializerMethodField('get_rating')
    started = SerializerMethodField('get_started')
    review = SerializerMethodField('get_review')
    mechanic = StringRelatedField()
    customer = StringRelatedField()

    class Meta:
        model = ServiceBooking
        fields = ['started', 'ended', 'review', 'rating', 'customer', 'mechanic', 'status']

    def get_started(self, obj):
        if obj.started_on:
            return obj.started_on.date
        return None

    def get_ended(self, obj):
        if obj.ended_on:
            return obj.ended_on.date
        return None

    def get_review(self, obj):
        if obj.client_feedback:
            return obj.client_feedback.review
        return "No feedback given"

    def get_rating(self, obj):
        if obj.client_feedback:
            return obj.client_feedback.stars
        return None



