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
    PurchaseOfferSerializer,
    DealerSerializer,
)
from ..models import (
    Vehicle,
    Listing,
    Order,
    CarRental,
    PurchaseOffer,
    VehicleImage,
)
from accounts.api.serializers import (
    GetDealershipSerializer,
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
from utils import (
    OffsetPaginator,
    upload_multiple_files,
)
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

    def get_chart_data(self, period="monthly"):
        labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        chart_data = {
            'labels': labels,
            'datasets': [
                {
                    'key': 'revenue',
                    'data': []
                }
            ]
        }

        return chart_data

    def get(self, request):
        dealer = Dealership.objects.get(user=request.user)
        purchases = dealer.orders.all()
        listings = dealer.listings.all()

        revenue = 0
        impressions = 0
        orders = dealer.orders.order_by('-id')[:10]

        for listing in listings:
            print("Impressions:", listing.viewers.all().count())
            impressions += listing.viewers.all().count()

        for order in purchases:
            revenue += order.total

        chart_data = self.get_chart_data()

        data = {
            'error': False,
            'data': {
                'total_deals' : dealer.orders.filter(paid=True).count(),
                'impressions' : impressions,
                'total_revenue' : revenue,
                'recent_orders': OrderSerializer(orders, many=True, context={'request': request}).data,
                'chart_data': chart_data
            }
        }
        return Response(data, 200)


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
        dealer = Dealership.objects.get(user=request.user)
        listing = dealer.listings.get(uuid=request.data['listing'])
        data = {
            'error': False,
            'message': '',
        }
        if action == 'delete':
            listing.delete()
            data['message'] = "Successfully Deleted Listing"
        elif action == 'unpublish':
            listing.verified = False
            listing.save()
            data['message'] = "Successfully Unpublished Listing"
        elif action == 'publish':
            listing.verified = True
            listing.save()
            data['message'] = "Successfully Published Listing"
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
            action = data.get('action', 'create-listing')
            message = 'Successfully created new listing'
            listing = None

            if action == 'create-listing':
                vehicle = Vehicle(
                    name = data['title'],
                    dealer=dealer,
                    color = data.get('color', 'None'),
                    brand = data['brand'],
                    model = data['model'],
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
                    vehicle.features=data['features']
                    vehicle.for_rent = True
                vehicle.save()

                listing = Listing(
                    vehicle=vehicle,
                    created_by=request.user,
                    listing_type=data['listing_type'],
                    price=data['price'],
                    title=data['title'],
                    notes=data.get('notes', ''),
                )
                if data['listing_type'] == 'rental':
                    listing.payment_cycle = data['payment_cycle']
                listing.save()

                dealer.vehicles.add(vehicle,)
                dealer.listings.add(listing,)
                dealer.save()
            elif action == 'upload-images':
                listing = dealer.listings.get(uuid=data['listing'])
                images = data.getlist('image')
                paths = upload_multiple_files(images)
                for img in paths:
                    image = VehicleImage(
                        image=img,
                        vehicle=vehicle
                    )
                    image.save()
                    vehicle.images.add(image,)
                vehicle.save() # save to db
            elif action == 'publish-listing':
                listing = dealer.listings.get(uuid=data['listing'])
                listing.publish()
                message = 'Successfully published your listing'

            data = {
                'error': False,
                'message': message,
                'data': self.serializer_class(listing, context={'request': request}).data
            }
            on_listing_created.send(dealer, listing=listing)
            return Response(data, 200)
        except Exception as error:
            raise error
            return Response({'error': True, 'message': str(error)}, 500)


class ListingDetailView(RetrieveUpdateDestroyAPIView):
    allowed_methods = ['GET', 'PUT', 'DELETE']
    permission_classes = [IsAuthenticated, IsDealerOrStaff]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    serializer_class = ListingSerializer
    
    def get_object(self):
        return Listing.objects.get(uuid=self.kwargs['listing_id'])

    def get(self, request, listing_id):
        try:
            data = {
                'error': False,
                'data': ListingSerializer(self.get_object(), context={'request': request}).data
            }
            return Response(data, 200)
        except Exception as error:
            return Response({'error': True, 'message': str(error)}, 500)

    def post(self, request, listing_id):
        try:
            dealer = Dealership.objects.get(user=request.user)
            data = request.data
            action = data.get('action', 'edit-listing')
            message = 'Successfully changed listing'
            listing = self.get_object()
            vehicle = listing.vehicle

            if action == 'edit-listing':
                listing.title = data['title']
                listing.price=data['price']
                listing.notes=data['notes']

                vehicle.name = data['title']
                vehicle.model = data['vehicle']['model']
                vehicle.color = data['vehicle'].get('color', 'None')
                vehicle.brand = data['vehicle']['brand']
                vehicle.condition = data['vehicle']['condition']
                vehicle.type = data['vehicle']['type']
                vehicle.transmission = data['vehicle']['transmission']
                vehicle.mileage = data['vehicle']['mileage']
                vehicle.fuel_system = data['vehicle']['fuel_system']
                vehicle.drivetrain = data['vehicle']['drivetrain']
                vehicle.seats = data['vehicle']['seats']
                vehicle.doors = data['vehicle']['doors']
                vehicle.vin = data['vehicle']['vin']

                if data['listing_type'] == 'sale':
                    vehicle.for_sale = True
                    vehicle.for_rent = False
                elif data['listing_type'] == 'rental':
                    vehicle.features=data['vehicle']['features']
                    vehicle.for_sale = False
                    vehicle.for_rent = True
                if data['listing_type'] == 'rental':
                    listing.payment_cycle = data['payment_cycle']
                listing.save()
                vehicle.save()
            elif action == 'upload-images':
                images = data.getlist('image')
                paths = upload_multiple_files(images)
                print("Images", paths)
                for img in paths:
                    image = VehicleImage(
                        image=img,
                        vehicle=vehicle
                    )
                    image.save()
                    vehicle.images.add(image,)
                vehicle.save() # save to db
            elif action == 'remove-image':
                image = vehicle.images.get(uuid=data['image_id'])
                image.delete()
            elif action == 'publish-listing':
                listing = dealer.listings.get(uuid=data['listing'])
                listing.publish()
                message = 'Successfully published your listing'

            data = {
                'error': False,
                'message': message,
                'data': self.serializer_class(listing, context={'request': request}).data
            }
            return Response(data, 200)
        except Exception as error:
            raise error
            return Response({'error': True, 'message': str(error)}, 500)

    # for delete
    def delete(self, request, *args, **kwargs):
        try:
            listing = self.get_object()
            listing.delete()
        except Exception as error:
            return Response({'error': True, 'message': str(error)})



class OrderListView(ListAPIView):
    allowed_methods = ['GET']
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get(self, request):
        dealer = Dealership.objects.get(user=request.user)
        orders = dealer.orders.all()
        data = {
            'error': False,
            'data': OrderSerializer(orders, many=True, context={'request': request}).data
        }
        return Response(data, status=200)

    def post(self, request):
        return Response()



class SettingsView(APIView):
    allowed_methods = ['POST', 'GET']
    permission_classes = [IsAuthenticated, IsDealerOrStaff]
    parser_classes = [MultiPartParser, JSONParser]

    def get(self, request):
        dealer = Dealership.objects.get(user=request.user)
        data = {
            'error': False,
            'data': DealerSerializer(dealer, context={'request': request}).data
        }
        return Response(data, status=200)

    def post(self, request):
        data = request.data
        dealer = Dealership.objects.get(user=request.user)
        
        if data.get('new-logo', None):
            dealer.logo = data['new-logo']
        dealer.business_name = data['business_name']
        dealer.about = data['about']
        dealer.slug = data.get('slug', None)
        dealer.headline = data['headline']
        dealer.offers_purchase = 'Car Sale' in data['services']
        dealer.offers_rental = 'Car Leasing' in data['services']
        dealer.offers_drivers = 'Drivers' in data['services']
        dealer.save()
        
        data = {
            'error': False,
            'data': DealerSerializer(dealer, context={'request': request}).data
        }
        return Response(data, 200)


