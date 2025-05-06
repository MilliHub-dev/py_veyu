from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now
from django.db.models import Q
from rest_framework.response import Response
from django.db.models import QuerySet
from django.contrib.auth import authenticate, login, logout
from utils.sms import send_sms
from utils.mail import send_email
from rest_framework.parsers import (
    MultiPartParser,
    JSONParser,
)
from django_filters.rest_framework import DjangoFilterBackend
from utils import OffsetPaginator
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
    IsAuthenticated,
)
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
)
from .serializers import(
    CreateBookingSerializer,
    ViewBookingSerializer,
    UpdateBookingSerializer,
    MechanicServiceHistorySerializer
)
from accounts.api.serializers import (
    MechanicSerializer,
)
from utils.dispatch import (
    user_just_registered,
)
from utils import (
    IsMechanicOnly,
)
from rest_framework.authentication import (
    TokenAuthentication,
    SessionAuthentication
)
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    APIView
)
from accounts.models import (
    Account,
    Mechanic,
    Customer,
)
from ..models import(
    Service,
    ServiceBooking,
)
from accounts.api.filters import (
    MechanicFilter,
)

class MechanicOverview(ListAPIView):
    serializer_class = MechanicSerializer
    allowed_methods = ['GET']
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get(self, request, *args, **kwargs):
        mechanic = request.user.mechanic
        serializer = self.serializer_class(mechanic, context={'request': request})

        data = {
            'error': False,
            'message': '',
            'data': serializer.data
        }
        return Response(data, 200)


class MechanicDashboardView(ListAPIView):
    allowed_methods = ['GET']
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get(self, request, *args, **kwargs):
        mechanic = request.user.mechanic
        booking_history = mechanic.job_history.filter(
            Q(completed=True) |
            Q(booking_status='accepted') |
            Q(booking_status='declined') 
        )
        pending_requests = ServiceBooking.objects.filter(
            Q(mechanic=mechanic) &
            Q(booking_status='pending') |
            Q(booking_status='requested')
        )
        
        current_job = mechanic.current_job
        impressions = 0
        revenue = 0

        data = {
            'error': False,
            'message': 'Got Data',
            'data': {
                'total_revenue': revenue,
                'total_bookings': booking_history.count(),
                'total_impressions': impressions,
                'current_job': ViewBookingSerializer(current_job, context={'request': request}).data,
                'booking_history': ViewBookingSerializer(booking_history, many=True, context={'request': request}).data,
                'pending_requests': ViewBookingSerializer(pending_requests, many=True, context={'request': request}).data,
            }
        }
        return Response(data, 200)


class BookingsView(APIView):
    view_name = "Bookings View"
    allowed_methods = ['GET', 'POST']
    permission_classes = [IsAuthenticated, IsMechanicOnly,]
    serializer_class = ViewBookingSerializer

    
    def get(self, request, *args, **kwargs):
        mechanic:Mechanic = request.user.mechanic
        history = mechanic.job_history.all().exclude(booking_status='requested')
        requests = ServiceBooking.objects.filter(mechanic=mechanic, booking_status='requested')

        data = {
            'error': False,
            'message': 'Successfully got bookings',
            'bookings': {
                'history': self.serializer_class(history, many=True, context={'request': request}).data,
                'requests': self.serializer_class(requests, many=True, context={'request': request}).data
            }
        }
        return Response(data, 200)



class MechanicSearchView(ListAPIView):
    pagination_class = OffsetPaginator
    serializer_class = MechanicSerializer
    allowed_methods = ['GET']
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    # Add both the filter and ordering backends
    filter_backends = [DjangoFilterBackend,]
    filterset_class = MechanicFilter  # Use the filter class
    
    ordering = ['?']  # Random ordering

    def get_queryset(self):
        find = self.request.GET.get('find', None)
        qs = Mechanic.objects.all()
        if find:
            qs = qs.filter(
                Q(user__first_name__icontains=find) |
                Q(user__last_name__icontains=find) |
                Q(services__service__title__icontains=find)
            ).distinct()
        return qs

            

    def get(self, request, *args, **kwargs):
        queryset = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = self.serializer_class(queryset, context={'request': request}, many=True)

        data = {
            'error': False,
            'message': '',
            'data': {
                'pagination': {
                    'offset': self.paginator.offset,
                    'limit': self.paginator.limit,
                    'count': self.paginator.count,
                    'next': self.paginator.get_next_link(),
                    'previous': self.paginator.get_previous_link()
                },
                'results': serializer.data
            }
        }
        return Response(data, 200)


class MechanicProfileView(APIView):
    allowed_methods = ['GET', 'POST']
    # serializer_class = CreateBookingSerializer
    kwargs = ['mech_id']

    def get_view_name(self):
        return 'Mechanic Profile API View'
    
    # profile view of mechanic
    def get(self, request, *args, **kwargs):
        mech_id = kwargs.get('mech_id', None)
        if not mech_id:
            return Response({'error': True, 'message': "Required mech_id param missing."}, 400)

        try:
            mech = MechanicSerializer(Mechanic.me(mech_id), context={'request': request}).data
            data = {
                'error': False,
                'message': 'Found mechanic',
                'data': mech,
            }
            return Response(data, 200)
        except Exception as error:
            data = {
                'error': True,
                'message': str(error),
            }
            return Response(data, 404)
        
    def post(self, request, *args, **kwargs):
        mech_id = kwargs.get('mech_id', None)
        data = request.data

        if not mech_id:
            return Response({'error': True, 'message': "Required mech_id param missing."}, 400)
        
        customer = Customer.me(data['customer'])
        mech = Mechanic.me(mech_id)

        # create the booking request
        booking = ServiceBooking.objects.create(
            customer=customer,
            mechanic=mech,
        )

        for srvc in data['services']:
            service = mech.services.get(service__name=srvc)
            booking.services.add(service,)
        booking.save()

        # TODO : create and send a notification to the mech on the new request
        # NOTE : add the booking_request to mech status defaults to 'requested'
        mech.job_history.add(booking,)
        customer.service_history.add(booking,)
        
        # save changes
        mech.save()
        customer.save()
        response = {
            'error': False,
            'message': 'Successfully sent a booking request',
            'data': self.serializer_class(booking).data
        }
        return Response(response, 200)


class MechanicServiceHistory(ListAPIView):
    allowed_methods = ['GET']
    permission_classes = [IsAuthenticated]
    kwargs = ['mech_id']
    serializer_class = MechanicServiceHistorySerializer

    def get(self, request, *args, **kwargs):
        mech = Mechanic.me(kwargs['mech_id'])
        history = mech.job_history.filter(completed=True).distinct()
        data = {
            'error': False,
            'message': 'Successfully got %s\' service history' % mech.account.first_name,
            'data': CreateBookingSerializer(history).data
        }
        return Response()


class BookingUpdateView(APIView):
    # mechanic responds to booking request
    view_name = "View / Update Booking"
    allowed_methods = ['GET', 'POST',]
    permission_classes = [IsAuthenticated, IsMechanicOnly,]
    serializer_class = ViewBookingSerializer
    
    def get(self, request, *args, **kwargs):
        mech:Mechanic = request.mechanic
        booking = mech.job_history.get(uuid=kwargs['booking_id'])
        data = {
            'error': False,
            'message': 'Successfully got booking',
            'data': ViewBookingSerializer(booking, read_only=True).data
        }
        return Response(data, 200)

    def post(self, request, booking_id, *args, **kwargs):
        mechanic:Mechanic = request.mechanic
        print('Booking Id:', booking_id)
        booking:ServiceBooking = ServiceBooking.objects.get(uuid=booking_id)

        action = request.data.get('action', 'respond')
        today = now()

        if not booking.responded_on:
            booking.started_on = today

        if action == 'accept':
            booking.booking_status = 'accepted'
        elif action == 'complete':
            booking.booking_status = 'completed'
            booking.ended_on = today
        elif action == 'decline':
            booking.booking_status = 'declined'
        elif action == 'respond':
            booking.responded_on = today
        booking.save()

        data = {
            'error': False,
            'message': f'Successfully {action}ed booking',
            'data': self.serializer_class(booking, context={'request': request}).data
        }
        return Response(data, 200)



class MechanicSettingsView(APIView):
    parser_classes = [MultiPartParser, JSONParser]
    permission_classes = [IsAuthenticated, IsMechanicOnly,]
    allowed_methods = ['GET', 'POST']

    def get(self, request):
        mechanic = Mechanic.objects.get(user=request.user)
        data = {
            'error': False,
            'data': MechanicSerializer(mechanic, context={'request': request}).data
        }
        return Response(data, 200)

    def post(self, request):
        mechanic = Mechanic.objects.get(user=request.user)
        data = request.data
        print("DATA:", data)

        mechanic.business_name = data['business_name']
        mechanic.about = data.get('about', "")
        mechanic.headline = data.get('headline', "")
        mechanic.cac_number = data.get('cac_number', "")
        mechanic.tin_number = data.get('tin_number', "")
        mechanic.contact_email = data.get('contact_email', "")
        mechanic.contact_phone = data.get('contact_phone', "")
        mechanic.slug = None

        if data.get('new-logo', None):
            mechanic.logo = data['new-logo']

        mechanic.save()
        data = {
            'error': False,
            'data': MechanicSerializer(mechanic, context={'request': request}).data
        }
        return Response(data, 200)


