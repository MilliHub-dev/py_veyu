from django.shortcuts import redirect, resolve_url
from utils import (
    OffsetPaginator,
    IsAgentOrStaff,
)
from rest_framework.response import Response
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
    CarRental,
    PurchaseOffer,
)
from accounts.models import (
    Customer,
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



User = get_user_model()

class ListingsView(ListAPIView):
    """Show all listings created

    Args:
        filters (key:values): Key-Value pair of filters and their match cases
        per_page (int): Number of results for pagination
        offset (int): Pagination Offset
    """
    allowed_methods = ['GET']
    permission_classes = [IsAuthenticatedOrReadOnly,]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    serializer_class = ListingSerializer
    pagination_class = OffsetPaginator
    queryset = Listing.objects.all()
    
    def get(self, request, **kwargs):
        qs = self.get_queryset()
        filters = request.GET.get('filter', None)
        if filters:
            # filter qs based on match cases
            pass
        listings = self.serializer_class(self.paginate_queryset(qs), many=True).data
        data = {
            'error': False,
            'message': '',
            'data':{
                'pagination': {
                    'offset': self.paginator.offset,
                    'limit': self.paginator.limit,
                    'count': self.paginator.count,
                    'next': self.paginator.get_next_link(),
                    'previous': self.paginator.get_previous_link()
                },
                'results': listings         
            }
        }
        return Response(data, 200)

    def handle_exception(self, exc):
        return super().handle_exception(exc)

class ListingsDetailsView(RetrieveUpdateDestroyAPIView):
    allowed_methods = ['GET', 'PUT', 'DELETE']
    permission_classes = [IsAuthenticated, IsAgentOrStaff]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    serializer_class = CreateListingSerializer
    queryset = Listing.objects.all()

    lookup_field = 'uuid'
    

class CreateListingView(CreateAPIView):
    allowed_methods = ['POST']
    permission_classes = [IsAuthenticated, IsAgentOrStaff]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    serializer_class = CreateListingSerializer

    def post(self, request, **kwargs):
        data = request.data

        vehicle = Vehicle.objects.get(uuid=data['uuid'])
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
            'data': self.serializer_class(listing).data

        }
        return Response()


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

class AvailableForRentView(ListAPIView):
    allowed_methods = ['GET']
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    
    queryset = Vehicle.objects.filter(available=True, for_sale=False, current_rental=None)
# {
#   "order_items": [1],
#   "customer":2,
#   "order_type": "rental"
# }
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


class AvailableForRentDetailView(RetrieveUpdateDestroyAPIView):
    allowed_methods = ['GET', 'PUT', 'DELETE']
    permission_classes = [IsAuthenticatedOrReadOnly]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    queryset = Vehicle.objects.filter(available=True, for_sale=False, current_rental=None)
    serializer_class = VehicleSerializer
    lookup_field = 'uuid'

    # Remove the for_sale option when in the rental page
    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        
        if 'for_sale' in serializer.fields:
            serializer.fields.pop('for_sale')
        
        return serializer

class AvailableForBuyingView(ListAPIView):
    allowed_methods = ['GET']
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    
    queryset = Vehicle.objects.filter(available=True, for_sale=True, current_rental=None,  listing__listing_type='sale').distinct()

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
# English or spanish 😂🫴

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

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Endpoint to complete order")
    def post(self, request):
        serializer = CompleteOrderSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            order_id = validated_data['order_id']
            recipient_email = validated_data['recipient']
            

            order = get_object_or_404(Order, id=order_id)
            
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

class ViewCarOffersView(ListAPIView):
    allowed_methods = ['GET']
    serializer_class = PurchaseOfferSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        return PurchaseOffer.objects.filter(listing__created_by=self.request.user)