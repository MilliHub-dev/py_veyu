from django.shortcuts import redirect, resolve_url
from rest_framework.response import Response
import decimal
from django.db.models import Q
from utils import (
    OffsetPaginator,
    IsAgentOrStaff,
    IsDealerOrStaff,
    convert_js_date_to_django,
)
from rest_framework.parsers import (
    MultiPartParser,
    JSONParser,
)
from rest_framework.decorators import (
    authentication_classes,
    parser_classes,
    permission_classes,
    api_view,
)
from rest_framework.authentication import (
    TokenAuthentication,
    SessionAuthentication
)
from rest_framework.permissions import (
    BasePermission,
    IsAuthenticated,
    IsAdminUser,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
)
from .serializers import (
    ListingSerializer,
    CreateListingSerializer,
    OrderSerializer,
    VehicleSerializer,
    BookCarRentalSerializer,
    TestDriveRequestSerializer,
    TradeInRequestSerializer,
    CompleteOrderSerializer,
    OrderInspectionSerializer,
    PurchaseOfferSerializer,
)
from ..models import (
    Vehicle,
    Listing,
    Order,
    CarRental,
    OrderInspection,
    PurchaseOffer,
)
from accounts.api.serializers import (
    DealershipSerializer,
)
from accounts.models import (
    Customer,
    Dealership,
)
from .filters import (
    CarSaleFilter,
    CarRentalFilter,
)
from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from wallet.models import Wallet
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from utils import OffsetPaginator
from utils.dispatch import (on_checkout_success, on_inspection_created)
User = get_user_model()




def typer(obj):
    if type(obj) == list:
        for item in obj:
            typer(obj)
    elif type(obj) == dict:
        for key in list(obj.keys()):
            typer(obj[key])
    else:
        print(f"{obj} is a {type(obj)}")


def get_inspection_fee(listing):
    if listing.listing_type == 'sale':
        return (decimal.Decimal(0.1/100) * listing.price)
    return (decimal.Decimal(2/100) * listing.price)



# Customer Views
class ListingSearchView(ListAPIView):
    allowed_methods = ['GET']
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    queryset = Listing.objects.filter(
        approved=True,
        verified=True,
        vehicle__available=True,
        vehicle__dealer__verified_business=True,
        vehicle__dealer__verified_id=True,
    ).distinct() # serach all listings sale & rent
    filter_backends = [DjangoFilterBackend,]
    filterset_class = CarRentalFilter # Use the filter class
    pagination_class = OffsetPaginator

    def get_queryset(self):
        find = self.request.GET.get('find', None)
        qs = self.queryset
        if find:
            qs = qs.filter(
                Q(vehicle__name__icontains=find) |
                Q(vehicle__brand__icontains=find) |
                Q(vehicle__brand__icontains=find)
            )

        return qs

    def get(self, request, *args, **kwargs):
        queryset = self.paginate_queryset(
            self.filter_queryset(
                self.get_queryset()
            )
        )
        serializer = self.serializer_class(queryset, many=True, context={'request': request})

        data = {
            'error': False,
            'message': '',
            'data': {
                'pagination': {
                    'offset': self.paginator.offset,
                    'limit': self.paginator.limit,
                    'count': self.paginator.count,
                    'next': self.paginator.get_next_link(),
                    'previous': self.paginator.get_previous_link(),
                },
                'results': serializer.data
            }
        }
        return Response(data, 200)


class MyListingsView(ListAPIView):
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticated]
    queryset = queryset = Listing.objects.filter(
        approved=True,
        verified=True,
        vehicle__available=True,
        vehicle__dealer__verified_business=True,
        vehicle__dealer__verified_id=True,
    ).distinct() # serach all listings sale & rent

    def get(self, request, *args, **kwargs):
        scope = request.GET.get('scope')
        scope = scope.split(';')
        qs = self.get_queryset()

        data = {
            'error': False,
        }

        if 'recents' in scope:
            recents = self.serializer_class(
                qs.filter(viewers__in=[self.request.user,]),
                many=True, context={'request': request}
            ).data[::6]
            data['recents'] = recents
        
        if 'favorites' in scope:
            pass

        if 'top-deals' in scope:
            rentals = self.serializer_class(
                qs.filter(listing_type='rental').order_by('-id'),
                many=True, context={'request': request}
            ).data[::6]

            sales = self.serializer_class(
                qs.filter(listing_type='sale').order_by('-id'),
                many=True, context={'request': request}
            ).data[::6]

            data['top_deals'] = {
                'services': [],
                'sales': sales,
                'rentals': rentals
            }
        return Response(data)


class DealershipView(APIView):
    allowed_methods = ["GET"]
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        dealer = Dealership.objects.get(uuid=uuid)
        data = {
            'error': False,
            'data': DealershipSerializer(dealer, context={'request': request}).data
        }
        return Response(data, 200)


# Rentals
class RentListingView(ListAPIView):
    allowed_methods = ['GET']
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    queryset = Listing.objects.filter(
        approved=True,
        verified=True,
        listing_type='rental',
        vehicle__available=True,
        vehicle__dealer__verified_id=True,
        vehicle__dealer__verified_business=True,
    ).distinct()
    filter_backends = [DjangoFilterBackend,]
    filterset_class = CarRentalFilter # Use the filter class
    pagination_class = OffsetPaginator

    def get(self, request, *args, **kwargs):
        queryset = self.paginate_queryset(
            self.filter_queryset(
                self.get_queryset()
            )
        )
        serializer = self.serializer_class(queryset, many=True, context={'request': request})

        data = {
            'error': False,
            'message': '',
            'data': {
                'pagination': {
                    'offset': self.paginator.offset,
                    'limit': self.paginator.limit,
                    'count': self.paginator.count,
                    'next': self.paginator.get_next_link(),
                    'previous': self.paginator.get_previous_link(),
                },
                'results': serializer.data
            }
        }
        return Response(data, 200)


class RentListingDetailView(RetrieveUpdateDestroyAPIView):
    allowed_methods = ['GET', 'PUT', 'DELETE']
    permission_classes = [IsAuthenticatedOrReadOnly]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    queryset = Listing.objects.filter(
        verified=True,
        approved=False,
        listing_type='rental',
        vehicle__available=True
    ).distinct()
    serializer_class = ListingSerializer
    lookup_field = 'uuid'

    def get(self, request, *args, **kwargs):
        listing = Listing.objects.get(uuid=self.kwargs['uuid'])

        if not request.user in listing.viewers.all():
            listing.viewers.add(request.user,)
            listing.save()

        # count impressions here

        small_change = (decimal.Decimal(25/100) * listing.price)

        recommended = self.queryset.filter(
            Q(price__gte=(listing.price - small_change)) |
            Q(price__lte=(listing.price + small_change)) |
            Q(vehicle__brand__iexact=listing.vehicle.brand) |
            Q(payment_cycle__iexact=listing.payment_cycle)
            # Q(vehicle__dealer=listing.vehicle.dealer)
            # Q(price=listing.price) |
        ).exclude(uuid=listing.uuid).distinct()

        print("Recommended Listings:", recommended)


        serializer = self.serializer_class(listing, context={'request': request})
        recommended = self.serializer_class(recommended, many=True, context={'request': request})
        data = {
            'error': False,
            'message': '',
            'data': {
                'listing': serializer.data,
                'recommended': recommended.data
            }
        }
        return Response(data, 200)


# Buying
class BuyListingView(ListAPIView):
    allowed_methods = ['GET']
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    queryset = Listing.objects.filter(
        verified=True,
        approved=True,
        vehicle__available=True,
        vehicle__dealer__verified_id=True,
        vehicle__dealer__verified_business=True,
        listing_type='sale'
    ).distinct()
    filter_backends = [DjangoFilterBackend,]
    filterset_class = CarSaleFilter  # Use the filter class
    # ordering = ['']  # Default ordering if none specified by the user
    pagination_class = OffsetPaginator

    @swagger_auto_schema(
        operation_summary="Get Car Listings for Sale",
        responses={'200': ListingSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        queryset = self.paginate_queryset(
            self.filter_queryset(
                self.get_queryset()
            )
        )
        serializer = self.serializer_class(queryset, many=True, context={'request': request})

        data = {
            'error': False,
            'message': '',
            'data': {
                'pagination': {
                    'offset': self.paginator.offset,
                    'limit': self.paginator.limit,
                    'results_count': self.paginator.count,
                    'next': self.paginator.get_next_link(),
                    'previous': self.paginator.get_previous_link(),
                },
                'results': serializer.data
            }
        }
        return Response(data, 200)


class BuyListingDetailView(RetrieveAPIView):
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticated,]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    allowed_methods = ['GET', 'POST']
    lookup_field = 'uuid'
    queryset = Listing.objects.filter(verified=True, approved=True, listing_type='sale').distinct()

    def get(self, request, *args, **kwargs):
        listing = self.get_object()

        if not request.user in listing.viewers.all():
            listing.viewers.add(request.user,)
            listing.save()

        small_change = (decimal.Decimal(7.5/100) * listing.price)

        recommended = self.queryset.filter(
            Q(vehicle__brand__iexact=listing.vehicle.brand) |
            Q(price__gte=(listing.price - small_change)) |
            Q(price__lte=(listing.price + small_change))
        ).exclude(uuid=listing.uuid).distinct()

        data = {
            'error': False,
            'message': '',
            'data': {
                'recommended': self.serializer_class(recommended, context={'request': request}, many=True).data,
                'listing': self.serializer_class(listing, context={'request': request}).data
            }
        }
        return Response(data=data, status=200, content_type="text/json")

    def count_view(self, user, listing):
        if user and user.is_authenticated:
            if not user in listing.viewers.all():
                listing.viewers.add(user,)
        listing.views += 1
        listing.save()


    def post(self, request, *args, **kwargs):
        data = request.data
        action = data['action']
        listing = self.get_object()

        try:
            response = {
                'error': False,
            }
            customer = Customer.objects.get(user=request.user)
            cart = customer.cart
            if action == 'add-to-cart':
                cart.add(listing,)
                customer.save()
                response['message'] = 'Successfully added to your cart'
            elif action == 'buy-now':
                order = Order(customer=customer,)
                order.order_items.add(listing,)
                order.save()
                response['message'] = 'Successfully added to your cart'
            return Response(response, status=200)
        except Exception as error:
            return Response({'error': True, 'message': str(error)}, status=500)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    queryset = Listing.objects.all()
    lookup_field = 'uuid'


    def get(self, request, *args, **kwargs):
        listing = Listing.objects.get(uuid=kwargs['listingId'])

        data = {
            'error': False,
            'total': 0,
            'fees': {
                'tax': (0.075 * float(listing.price)),
                'inspection_fee': get_inspection_fee(listing),
                'motaa_fee': (0.02 * float(listing.price)),
            },
            'listing': ListingSerializer(listing, context={'request': request}).data,
        }
        return Response(data)

    def post(self, request, *args, **kwargs):
        data = request.data
        listing = Listing.objects.get(uuid=kwargs['listingId'])
        order = Order(
            payment_option=data['payment_option'],
            customer=request.user.customer,
            order_type=listing.listing_type,
            order_item=listing,
            paid= True if data['payment_option'] == 'card' else False
        )
        order.save()
        listing.vehicle.available = False
        listing.vehicle.save()
        request.user.customer.orders.add(order,)
        listing.vehicle.dealer.orders.add(order,)
        request.user.customer.save()
        listing.vehicle.dealer.save()

        on_checkout_success.send(order, listing=listing, customer=request.user.customer,)
        # create a new order
        # create a notification for both dealer and customer
        # register a sale in dealer's dashboard
        return Response({'error': False, 'message': 'Your order was created', 'data': OrderSerializer(order).data}, 200)


class BookInspectionView(APIView):
    allowed_methods = ['GET', 'POST']
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data
            listing = Listing.objects.get(uuid=request.data['listing_id'])
            order = Order.objects.get(customer=request.user.customer, order_item=listing)
            order.order_status = 'awaiting-inspection'
            order.save()
            date = convert_js_date_to_django(data['date'])
            time = data['time']

            inspection = OrderInspection(
                order=order,
                customer=request.user.customer,
                inspection_date=date,
                inspection_time=time,
            )
            inspection.save()
            on_inspection_created.send(request.user.customer, date=date, time=time)
            return Response({'error': False, 'data': 'Inspection Scheduled'}, 200)
        except Exception as error:
            # raise error
            return Response({'error': True, 'message': str(error)}, 500)


class TestDriveRequestView(CreateAPIView):
    allowed_methods = ['POST']
    serializer_class = TestDriveRequestSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TradeInRequestViewSet(CreateAPIView):
    allowed_methods = ['POST']
    serializer_class = TradeInRequestSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer_main = Customer.objects.get(user=self.request.user)
        serializer.save(customer=customer_main)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CompleteOrderView(APIView):
    allowed_methods = ['POST']
    permission_classes = [IsAuthenticatedOrReadOnly,]

    @swagger_auto_schema(operation_summary="Endpoint to complete order")
    def post(self, request):
        serializer = CompleteOrderSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            order_id = validated_data['order_id']
            recipient_email = validated_data['recipient']


            order = get_object_or_404(Order, uuid=order_id)

            recipient = get_object_or_404(User, email=recipient_email)
            sender_wallet = get_object_or_404(Wallet, user=request.user)
            recipient_wallet = get_object_or_404(Wallet, user=recipient)

            if sender_wallet.balance < order.total:
                return Response({'error': 'Insufficient funds'}, status=status.HTTP_403_FORBIDDEN)

            if sender_wallet.complete_order(amount=order.total, recipient_wallet=recipient_wallet):
                order.paid = True
                order.save()
                return Response(f'Order completed successfully', status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Unable to perform this operation'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

