from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now
from django.db.models import Q
from rest_framework.response import Response
from django.db.models import QuerySet
from django.contrib.auth import authenticate, login, logout
from utils.sms import send_sms
from utils.location import haversine
from wallet.gateway.payment_adapter import PaystackAdapter
from utils.mail import send_email
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
    on_booking_requested,
    on_booking_completed,
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

class MechanicListView(ListAPIView):
    pagination_class = OffsetPaginator
    serializer_class = MechanicSerializer
    allowed_methods = ['GET']
    permission_classes = [IsAuthenticatedOrReadOnly]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    
    # Add both the filter and ordering backends
    filter_backends = [DjangoFilterBackend,]
    filterset_class = MechanicFilter  # Use the filter class
    
    ordering = ['account__first_name']  # Default ordering if none specified by the user

    def get_queryset(self):
        request = self.request
        
        # Base queryset with optimization for related objects
        queryset = Mechanic.objects.select_related('user', 'location').prefetch_related('services')

        lat_raw = request.GET.get('lat')
        lng_raw = request.GET.get('lng')

        if not lat_raw or not lng_raw:
            return queryset

        try:
            user_lat = float(lat_raw)
            user_lng = float(lng_raw)
        except (ValueError, TypeError):
            return queryset

        # 1. Bounding Box Optimization (Database Level)
        # Roughly 1 degree = 111km. 30km is approx 0.27 degrees.
        # This drastically reduces the O(n) loop in Python.
        delta = 0.3 

        # 2. Precise Haversine Filtering (Python Level)
        # Only loop through mechanics that actually have coordinates.
        coords_qs = queryset.filter(location__lat__isnull=False, location__lng__isnull=False)
        coords_qs = coords_qs.filter(
            location__lat__gte=user_lat - delta,
            location__lat__lte=user_lat + delta,
            location__lng__gte=user_lng - delta,
            location__lng__lte=user_lng + delta
        )

        exclude_uuids = []
        near_uuids = []
        for mech in coords_qs:
            dist = haversine(
                user_lat,
                user_lng,
                float(mech.location.lat),
                float(mech.location.lng),
            )
            if dist > 30:
                exclude_uuids.append(mech.uuid)
            else:
                near_uuids.append(mech.uuid)

        # Include:
        # - mechanics within 30km (near_uuids)
        # - mechanics without coordinates (fallback to location text filtering on frontend)
        return queryset.filter(
            Q(uuid__in=near_uuids)
            | Q(location__lat__isnull=True)
            | Q(location__lng__isnull=True)
        ).exclude(uuid__in=exclude_uuids)
                # results.append({
                #     "id": m.id,
                #     "name": m.name,
                #     "distance_km": round(dist, 2)
                # })

        # results.sort(key=lambda x: x["distance_km"])
        return mechanics

    def get(self, request, *args, **kwargs):
        try:
            lat_raw = request.GET.get('lat')
            lng_raw = request.GET.get('lng')
            
            lat = float(lat_raw) if lat_raw else None
            lng = float(lng_raw) if lng_raw else None
            
            ctx = {'request': request}
            if lat is not None and lng is not None:
                ctx['coords'] = (lat, lng)

            queryset = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
            
            # Optimization: Fetch all reviews for these mechanics in one batch
            # instead of doing it per-item in the serializer (N+1 fix)
            mechanic_uuids = [m.uuid for m in queryset]
            from feedback.models import Review
            reviews = Review.objects.filter(
                object_type='mechanic', 
                related_object__in=mechanic_uuids
            ).select_related('reviewer').prefetch_related('rating_items')
            
            # Group reviews by mechanic uuid
            reviews_by_mech = {}
            for review in reviews:
                mech_uuid = str(review.related_object)
                if mech_uuid not in reviews_by_mech:
                    reviews_by_mech[mech_uuid] = []
                reviews_by_mech[mech_uuid].append(review)
            
            ctx['mechanic_reviews'] = reviews_by_mech

            serializer = self.serializer_class(queryset, many=True, context=ctx)
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
        except Exception as error:
            raise error
            return Response({'error': True, 'message': str(error)}, 500)

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
        
        print("Matches:", qs)
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
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = MechanicSerializer
    paystack = PaystackAdapter()
    kwargs = ['mech_id']

    def get_view_name(self):
        return 'Mechanic Profile API View'
    
    # profile view of mechanic
    def get(self, request, *args, **kwargs):
        mech_id = kwargs.get('mech_id', None)
        if not mech_id:
            return Response({'error': True, 'message': "Required mech_id param missing."}, 400)

        try:
            mechanic = Mechanic.me(mech_id)
            if not mechanic:
                return Response(
                    {
                        'error': True,
                        'message': 'Mechanic profile not found. Please complete your mechanic profile setup.'
                    },
                    404
                )

            mech = MechanicSerializer(mechanic, context={'request': request}).data
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
        
        customer = Customer.objects.get(user=request.user)
        mech = Mechanic.me(mech_id)
        transaction = self.paystack.verify_transaction(data['transaction_id'])
        if transaction['status'] and transaction['data']['status'] == 'success':

            # create the booking request
            booking = ServiceBooking.objects.create(
                customer=customer,
                mechanic=mech,
                problem_description=data['problem_description'],
            )
            booking.save(using=None)

            for srvc in data['services']:
                service = mech.services.get(service__title=srvc)
                booking.services.add(service,)
            booking.save()

            # TODO : create and send a notification to the mech on the new request
            # NOTE : add the booking_request to mech status defaults to 'requested'
            # mech.job_history.add(booking,)
            # customer.service_history.add(booking,)
            
            # # save changes
            # mech.save()
            # customer.save()

            on_booking_requested.send(
                booking,
                customer=customer,
                services=data['services'],
                mechanic=mech
            )
            
            response = {
                'error': False,
                'message': 'Successfully sent a booking request',
                'data': self.serializer_class(booking).data
            }
            return Response(response, 200)
        
        response = {
            'error': True,
            'message': f'Payment failed: {transaction["message"]}',
        }
        return Response(response, 500)


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
            'data': CreateBookingSerializer(history, many=True).data
        }
        return Response(data, 200)


class BookingUpdateView(RetrieveAPIView):
    # mechanic responds to booking request
    kwargs = ['booking_id']
    view_name = "View / Update Booking"
    allowed_methods = ['GET', 'POST', 'PUT']
    permission_classes = [IsMechanicOnly,]
    serializer_class = UpdateBookingSerializer
    
    def get(self, request, *args, **kwargs):
        mech:Mechanic = request.mechanic
        booking = mech.job_history.get(uuid=kwargs['booking_id'])
        data = {
            'error': False,
            'message': 'Successfully got booking',
            'data': ViewBookingSerializer(booking, read_only=True).data
        }
        return Response(data, 200)

    def post(self, request, *args, **kwargs):
        mech:Mechanic = request.mechanic
        booking:ServiceBooking = mech.job_history.get(uuid=kwargs['booking_id'])

        action = request.data.get('action', 'change-status')

        if action == 'accept':
            booking.started_on = now()
            booking.booking_status = 'accepted'
        elif action == 'complete':
            booking.ended_on = now()
            booking.booking_status = 'completed'
            on_booking_completed.send(booking)
        elif action == 'decline':
            booking.booking_status = 'declined'
            booking.responded_on = now()
        elif action == 'respond':
            booking.responded_on = now()
        booking.save()

        data = {
            'error': False,
            'message': 'Successfully updated booking',
            'data': ViewBookingSerializer(booking, read_only=True).data
        }
        return Response(data, 200)

    # def put(self, request, *args, **kwargs):
    #     response = self.post(request, *args, **kwargs)
    #     return response
    


