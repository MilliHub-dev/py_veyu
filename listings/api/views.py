from django.shortcuts import redirect, resolve_url
from rest_framework.response import Response
from django.db.models import Q
from utils import (
    OffsetPaginator,
    IsAgentOrStaff,
    IsDealerOrStaff,
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
    PurchaseOfferSerializer
)
from ..models import (
    Vehicle,
    Listing,
    Order,
    OrderItem,
    CarRental,
    PurchaseOffer,
)
from accounts.models import (
    Customer,
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
User = get_user_model()



# Customer Views
class ListingSearchView(ListAPIView):
    allowed_methods = ['GET']
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    queryset = Listing.objects.filter(approved=True, verified=True,).distinct() # serach all listings sale & rent
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
    queryset = Listing.objects.all()


    def get(self, request, *args, **kwargs):
        scope = request.GET.get('scope', 'recents') # defaults to recently viewed
        qs = self.get_queryset()
        listing = None
        print("Getting your listings", request.user)


        if scope == 'recents':
            listing = self.serializer_class(
                qs.filter(viewers=self.request.user),
                many=True, context={'request': request}
            ).data
        elif scope == 'favorites':
            # listing = self.serializer_class(
            #     qs.filter(viewers__account_id__icontains=self.request.user),
            #     many=True, context={'request': request}
            # ).data
            pass
        data = {
            'error': False,
            'data': listings
        }
        return Response(data)



# Rentals
class RentListingView(ListAPIView):
    allowed_methods = ['GET']
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    queryset = Listing.objects.filter(approved=True, verified=True, listing_type='rental').distinct()
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
    queryset = Listing.objects.filter(verified=True, approved=False, listing_type='rental').distinct()
    serializer_class = ListingSerializer
    lookup_field = 'uuid'
    
    def get(self, request, *args, **kwargs):
        obj = Listing.objects.get(uuid=self.kwargs['uuid'])

        if not request.user in obj.viewers.all():
            obj.viewers.add(request.user,)
            obj.save()

        serializer = self.serializer_class(obj, context={'request': request})
        data = {
            'error': False,
            'message': '',
            'data': {
                'listing': serializer.data,
                'recommended': []
            }
        }
        return Response(data, 200)


class BookCarRentalView(CreateAPIView):
    allowed_methods = ['POST']
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    serializer_class = BookCarRentalSerializer
    queryset = Order.objects.all()

    def perform_create(self, serializer):
        # order_items = serializer.validated_data.get('order_items', [])
        # print("Order items:", order_items)  # Debug log
        # print("serializer: ", serializer)

        try:
            print('self.request.user')
            customer_main = Customer.objects.get(user=self.request.user)
            print(f"Customer: {customer_main}")
        except Customer.DoesNotExist:
            # Return error response if customer profile doesn't exist
            raise ValidationError({'error': 'Customer profile does not exist for this account.'})

        # Save the order with the associated customer
        try:
            serializer.save(customer=customer_main)
            print('serializer Saved')

            order_instance = serializer.instance
            print(f"Order Items: {list(order_instance.order_items.all())}")
        except Exception as e:
            print(f"Error saving order: {e}") 
            raise ValidationError({'error': {e}})

    def create(self, request, *args, **kwargs):
        # Call the original create method to handle POST
        response = super().create(request, *args, **kwargs)

        # Customize the response
        return Response({
            'message': 'Car rental successfully booked',
            'order': response.data
        }, status=response.status_code)


class BookCarRentalViewDetailView(RetrieveUpdateDestroyAPIView):
    allowed_methods = ['GET', 'PUT', 'DELETE']
    permission_classes = [IsAuthenticatedOrReadOnly]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    serializer_class = BookCarRentalSerializer
    lookup_field = 'uuid'

    def get_queryset(self):
        user = Customer.objects.get(user = self.request.user)
        return Order.objects.filter(customer=user)


# Buying
class BuyListingView(ListAPIView):
    allowed_methods = ['GET']
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    queryset = Listing.objects.filter(verified=True, approved=True, listing_type='sale').distinct()
    filter_backends = [DjangoFilterBackend,]
    filterset_class = CarSaleFilter  # Use the filter class
    # ordering = ['']  # Default ordering if none specified by the user
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
                    'results_count': self.paginator.count,
                    # 'page_range': self.paginator.get_page_range(),
                    # 'num_pages': self.paginator.num_pages,
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
        uuid = self.kwargs['uuid']
        listing = self.get_object()
        
        if not request.user in listing.viewers.all():
            listing.viewers.add(request.user,)
            listing.save()

        data = {
            'error': False,
            'message': '',
            'data': {
                'recommended': None,
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
            print("Cart:", cart)

            order_item = OrderItem(
                cart=cart,
                listing=listing,
                item_type=data['item_type']
            )
            order_item.save()

            if action == 'add-to-cart':
                cart.cart_items.add(order_item,)
                cart.save()
                response['message'] = 'Successfully added to your cart'
            elif action == 'buy-now':
                order = Order(customer=customer,)
                order.order_items.add(order_item,)
                order.save()
                response['message'] = 'Successfully added to your cart'
            return Response(response, status=200)
        except Exception as error:
            return Response({'error': True, 'message': str(error)}, status=500)

class CheckoutView(APIView):
    def get(self, request, *args, **kwargs):
        data = {
            
        }
        return Response({ 'error': False, 'data': data})

    def post(self, request, *args, **kwargs):
        return Response()


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



# Dealership Views
class CreateListingView(CreateAPIView):
    allowed_methods = ['POST']
    parser_classes = [MultiPartParser, JSONParser]
    permission_classes = [IsAuthenticated, IsDealerOrStaff]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    serializer_class = CreateListingSerializer

    def post(self, request, **kwargs):
        data = request.data

        vehicle = Vehicle.objects.create(**request.data)

        if request.files:
            print("Files:", request.files)

        raise Exception

        listing = Listing(
            vehicle=vehicle,
            created_by=request.user,
            listing_type=data['listing_type'],
            rental_price=data['rental_price'],
            sale_price=data['sale_price'],
        )

        if not data['sale_price'] and not data['rental_price']:
            raise Exception('Sale Price or Rental Price must be provided for a listing')
        
        listing.save()
        data = {
            'error': False,
            'message': 'Successfully created new listing',
            'data': self.serializer_class(listing, context={'request': request}).data

        }
        return Response()


class ListingAdminView(ListAPIView):
    allowed_methods = ['GET', 'POST']

    def get(self, request, *args, **kwargs):
        dealer = Dealer.objects.get(uuid=kwargs['dealershipId'])

        listings = Listing.objects.filter(dealer=dealer)



class VehicleView(ListAPIView):
    allowed_methods = ['GET']
    permission_classes = [IsAuthenticatedOrReadOnly,]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer


# NOT DONE FOR NOW IMAGE STUFF STILL HANGING
class CreateVehicleView(CreateAPIView):
    allowed_methods = ['POST']
    permission_classes = [IsAuthenticated, IsAgentOrStaff]
    parser_classes = [JSONParser, MultiPartParser]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

    def post(self, request, *args, **kwargs):
        serializer = VehicleSerializer(data=request.data)

        if serializer.is_valid():
            vehicle = serializer.save()

            # Create a corresponding listing
            listing_type = 'rental' if vehicle.available and not vehicle.for_sale else 'sale'
            Listing.objects.create(
                listing_type=listing_type,
                created_by=request.user,
                vehicle=vehicle,
                sale_price=vehicle.sale_price,
                rental_price=vehicle.rental_price,
                title=vehicle.listing_title,
            )

            return Response({'message': 'Vehicle created and added to listing successfully'}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VehicleDetailView(RetrieveUpdateDestroyAPIView):
    allowed_methods = ['GET', 'PUT', 'DELETE']
    permission_classes = [IsAuthenticatedOrReadOnly,]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    lookup_field = 'uuid'

    def get_object(self):
        try:
            return Vehicle.objects.get(uuid=self.kwargs['uuid'])
        except Vehicle.DoesNotExist:
            raise NotFound('Vehicle not found')

    # for update
    def put(self, request, *args, **kwargs):
        vehicle = self.get_object()
        serializer = self.get_serializer(vehicle, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        try:
            listing = Listing.objects.get(vehicle=vehicle)
            
            listing_type = 'rental' if vehicle.available and not vehicle.for_sale else 'sale'
            
            listing.listing_type = listing_type
            listing.sale_price = vehicle.sale_price
            listing.rental_price = vehicle.rental_price
            listing.title = vehicle.listing_title
            
            # Save the updated listing
            listing.save()

        except Listing.DoesNotExist:
            pass 

        return Response(serializer.data)

    # for delete
    def delete(self, request, *args, **kwargs):
        vehicle = self.get_object()
        
        # Delete the corresponding listing if it exists
        try:
            listing = Listing.objects.get(vehicle=vehicle)
            listing.delete()
        except Listing.DoesNotExist:
            pass

        # Delete the vehicle
        self.perform_destroy(vehicle)

        return Response(status=status.HTTP_204_NO_CONTENT)

class ViewCarOffersView(ListAPIView):
    allowed_methods = ['GET']
    serializer_class = PurchaseOfferSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        return PurchaseOffer.objects.filter(listing__created_by=self.request.user)

# English or spanish 😂🫴