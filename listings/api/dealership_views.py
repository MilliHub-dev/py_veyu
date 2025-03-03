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
    CarRental,
    PurchaseOffer,
    VehicleImage,
)
from accounts.api.serializers import GetDealershipSerializer
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
from utils.dispatch import (on_listing_created, )
User = get_user_model()

# Dealership Views

class DealershipView(APIView):
    allowed_methods = ['GET']
    serializer_class = GetDealershipSerializer
    permission_classes = [IsAuthenticated, IsDealerOrStaff]

    def get(self, request):
        dealership = Dealership.objects.get(user=request.user)
        data = {
            'error': False,
            'data': self.serializer_class(dealership, context={'request': request}).data
        }
        return Response(data, 200)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated, IsDealerOrStaff]
    allowed_methods = ['GET']

    def get(self, request):
        data = {
            'error': False,
            'data': {
                'total_deals' : 0,
                'impressions' : '200',
                'total_revenue' : 0,
            }
        }
        return Response(data, 200)


class CreateListingView(CreateAPIView):
    allowed_methods = ['POST']
    parser_classes = [MultiPartParser, JSONParser]
    permission_classes = [IsAuthenticated, IsDealerOrStaff]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    serializer_class = CreateListingSerializer

    def post(self, request, **kwargs):
        try:
            dealer = Dealership.objects.get(user=request.user)
            data = request.data
            images = data.getlist('image')

            vehicle = Vehicle(
                name = data['title'],
                dealer=dealer,
                color = data.get('color', 'None'),
                brand = data['brand'],
                condition = data['condition'],
                type = data['vehicle_type'],
                mileage = data.get('mileage', 0),
                transmission = data['transmission'],
                fuel_system = data['fuel_system'],
                drivetrain = data['drivetrain'],
                seats = data['seats'],
                doors = data['doors'],
                vin = data['vin'],
            )
            if data['listing_type'] == 'sale':
                vehicle.for_sale = True
            elif data['listing_type'] == 'rental':
                vehicle.for_rent = True
            # just create an ID, don't write to db just yet
            vehicle.save(using=None)

            for img in images:
                image = VehicleImage(
                    image=img,
                    vehicle=vehicle
                )
                image.save()
                vehicle.images.add(image,)
            vehicle.save() # save to db

            listing = Listing(
                vehicle=vehicle,
                created_by=request.user,
                listing_type=data['listing_type'],
                price=data['price'],
                title=data['title'],
            )
            listing.save()

            dealer.vehicles.add(vehicle,)
            dealer.listings.add(listing,)
            dealer.save()

            data = {
                'error': False,
                'message': 'Successfully created new listing',
                'data': self.serializer_class(listing, context={'request': request}).data
            }
            on_listing_created.send(dealer, listing=listing)
            return Response(data, 200)
        except Exception as error:
            return Response({'error': True, 'message': str(error)}, 500)

class ListingsView(ListAPIView):
    allowed_methods = ['GET', 'POST']
    permission_classes = [IsAuthenticated, IsDealerOrStaff]
    serializer_class = ListingSerializer

    def get(self, request, *args, **kwargs):
        dealer = Dealership.objects.get(user=request.user)
        listings = Listing.objects.filter(vehicle__dealer=dealer)
        data = {
            'error': False,
            'data': self.serializer_class(listings, context={'request': request}, many=True).data
        }
        return Response(data, 200)

    def post(self, request, *args, **kwargs):
        action = request.data['action']

        if action == 'delete':
            pass
        elif action == 'boost':
            pass
        elif action == 'make-available':pass
        return


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