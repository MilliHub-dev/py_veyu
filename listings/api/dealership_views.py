from django.shortcuts import redirect, resolve_url
from rest_framework.response import Response
from django.db.models import Q
import logging
from utils import (
    OffsetPaginator,
    IsAgentOrStaff,
    IsDealerOrStaff,
)
from rest_framework.parsers import (
    MultiPartParser,
    JSONParser,
    FormParser,
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
from rest_framework_simplejwt.authentication import JWTAuthentication
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
    # BookCarRentalSerializer,
    TestDriveRequestSerializer,
    TradeInRequestSerializer,
    CompleteOrderSerializer,
    PurchaseOfferSerializer,
    DealerSerializer,
)
from ..service_mapping import DealershipServiceProcessor
from ..models import (
    Vehicle,
    Car,
    Plane,
    Boat,
    Bike,
    UAV,
    Listing,
    Order,
    # CarRental,
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
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from wallet.models import Wallet
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.timezone import now, timedelta
from django.db.models import Count, Sum
from utils import (
    OffsetPaginator,
    upload_multiple_files,
)
from utils.dispatch import (on_listing_created, )

logger = logging.getLogger(__name__)
User = get_user_model()
# Dealership Views

class DealershipView(APIView):
    allowed_methods = ['GET']
    serializer_class = GetDealershipSerializer
    permission_classes = [IsAuthenticated, IsDealerOrStaff]

    def get(self, request):
        try:
            dealership = Dealership.objects.get(user=request.user)
            data = {
                'error': False,
                'data': self.serializer_class(dealership, context={'request': request}).data
            }
            return Response(data, 200)
        except Dealership.DoesNotExist:
            return Response({
                'error': True,
                'message': 'Dealership profile not found. Please complete your dealership profile setup.'
            }, status=404)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated, IsDealerOrStaff]
    allowed_methods = ['GET', 'POST']

    def get_daily_counts(self, queryset, dates):
        return [
            next(
                (item.order_item.price for item in queryset if item.date_created.date() == date), 0
            ) for date in dates
        ]
    

    def get_chart_data(self, data, period="monthly"):
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        dates = sorted(set([item.date_created.date() for item in data]))
        this_month = now().month
        span = months[:this_month]

        if period == 'daily':
            span = [date.strftime('%m-%d') for date in dates]
        elif period == 'yearly':
            span = [date.strftime('%y-%m') for date in dates]

        dataset = self.get_daily_counts(data, dates)

        if len(dataset) < 1:
            if this_month < 6:
                span = months[:6]

        if len(dataset) < len(span):
            rem = len(span) - len(dataset)
            for i in range(0, rem, 1):
                dataset.append(0)

        chart_data = {
            'labels': span,
            'datasets': [
                {
                    'label': 'Revenue',
                    'data': dataset,
                    'borderColor': '#38A169',
                    'borderWidth': 2,
                    'tension': 0.4,
                    'pointRadius': 0,
                },
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
            impressions += listing.viewers.all().count()

        for order in purchases:
            revenue += order.order_item.price

        chart_data = self.get_chart_data(data=purchases)

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



class AnalyticsView(APIView):
    allowed_methods = ["GET", "POST"]
    permission_classes = [IsAuthenticated, IsDealerOrStaff]
    dealer: Dealership = None


    def make_revenue_chart(self, data, period="monthly"):
        def get_counts(queryset, dates):
            return [
                next(
                    (item.order_item.price for item in queryset if item.date_created.date() == date), 0
                ) for date in dates
            ]
        
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        dates = sorted(set([item.date_created.date() for item in data]))
        this_month = now().month
        span = months[:this_month]

        if period == 'daily':
            span = [date.strftime('%m-%d') for date in dates]
        elif period == 'yearly':
            span = [date.strftime('%y-%m') for date in dates]

        dataset = get_counts(data, dates)

        if len(dataset) < 1:
            if this_month < 6:
                span = months[:6]

        if len(dataset) < len(span):
            rem = len(span) - len(dataset)
            for i in range(0, rem, 1):
                dataset.append(0)

        chart_data = {
            'labels': span,
            'datasets': [
                {
                    'label': 'Revenue',
                    'data': dataset,
                    'borderColor': '#3182CE',
                    'borderWidth': 2,
                    'tension': 0.4,
                    'pointRadius': 0,
                },
            ]   
        }
        return chart_data
    

    def make_sales_chart(self, data, period="monthly"):
        def get_counts(queryset, dates):
            return [
                next(
                    (1 for item in queryset if item.date_created.date() == date), 0
                ) for date in dates
            ]

        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        dates = sorted(set([item.date_created.date() for item in data]))
        print(set([item.date_created.date() for item in data]))
        this_month = now().month
        span = months[:this_month]

        if period == 'daily':
            span = [date.strftime('%m-%d') for date in dates]
        elif period == 'yearly':
            span = [date.strftime('%y-%m') for date in dates]

        dataset = get_counts(data, dates)

        if len(dataset) < 1:
            if this_month < 6:
                span = months[:6]

        if len(dataset) < len(span):
            rem = len(span) - len(dataset)
            for i in range(0, rem, 1):
                dataset.append(0)

        chart_data = {
            'labels': span,
            'datasets': [
                {
                    'label': 'Sales',
                    'data': dataset,
                    'borderColor': '#E53E3E',
                    'borderWidth': 2,
                    'tension': 0.4,
                    'pointRadius': 0,
                },
            ]   
        }
        return chart_data


    def get(self, request):
        dealer = Dealership.objects.get(user=request.user)
        purchases = dealer.orders.all()

        total_revenue = 0
        for purchase in purchases:
            total_revenue += purchase.order_item.price


        data = {
            'error': False,
            'data': {
                'revenue': {
                    'chart_data': self.make_revenue_chart(purchases),
                    'amount': total_revenue,
                    # 'change': total_revenue_change,
                },
                'sales': {
                    'chart_data': self.make_sales_chart(purchases),
                    'amount': purchases.count(),
                    # 'change': total_revenue_change,
                },
                'orders': {
                    'fulfilled': purchases.filter(order_status='completed').count(),
                    'pending': purchases.filter(
                        Q(order_status='pending') |
                        Q(order_status='awaiting-inspection') |
                        Q(order_status='inspecting')
                    ).count(),
                    'cancelled': purchases.filter(order_status='cancelled').count(),
                }
            }
        }


        return Response(data, 200)


class ListingsView(ListAPIView):
    allowed_methods = ['GET', 'POST']
    permission_classes = [IsAuthenticated, IsDealerOrStaff]
    serializer_class = ListingSerializer

    @swagger_auto_schema(
        operation_summary="List dealer listings",
        operation_description="Return all listings that belong to the authenticated dealer.",
        responses={
            200: openapi.Response(
                description='List of listings',
                examples={
                    'application/json': {
                        'error': False,
                        'data': [
                            {
                                'uuid': '550e8400-e29b-41d4-a716-446655440000',
                                'title': '2020 Toyota Camry',
                                'price': '5000000.00',
                                'listing_type': 'sale',
                                'verified': False
                            }
                        ]
                    }
                }
            )
        },
        tags=['Listings']
    )
    def get(self, request, *args, **kwargs):
        dealer = Dealership.objects.get(user=request.user)
        listings = Listing.objects.filter(vehicle__dealer=dealer)
        data = {
            'error': False,
            'data': self.serializer_class(listings, context={'request': request}, many=True).data
        }
        return Response(data, 200)

    @swagger_auto_schema(
        operation_summary="Modify a listing (delete/unpublish/publish)",
        operation_description=(
            "Provide an action and the listing UUID to modify a listing.\n\n"
            "- delete: Permanently delete the listing\n"
            "- unpublish: Mark listing as not verified (unpublished)\n"
            "- publish: Mark listing as verified (published)"
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['action', 'listing'],
            properties={
                'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['delete', 'unpublish', 'publish'], example='publish'),
                'listing': openapi.Schema(type=openapi.TYPE_STRING, format='uuid', description='Listing UUID')
            }
        ),
        responses={
            200: openapi.Response(
                description='Operation successful',
                examples={
                    'application/json': {'error': False, 'message': 'Successfully Published Listing'}
                }
            ),
            404: openapi.Response(description='Listing not found')
        },
        tags=['Listings']
    )
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
    parser_classes = [MultiPartParser, JSONParser, FormParser]
    permission_classes = [IsAuthenticated, IsDealerOrStaff]
    authentication_classes = [JWTAuthentication, TokenAuthentication, SessionAuthentication]
    serializer_class = CreateListingSerializer

    @swagger_auto_schema(
        operation_summary="Create, upload images, or publish a listing",
        operation_description=(
            "Perform listing actions based on the 'action' field.\n\n"
            "- create-listing: Create a new listing (required fields below)\n"
            "- upload-images: Upload one or more images for a listing (multipart/form-data)\n"
            "- publish-listing: Publish an existing listing\n\n"
            "Required fields for create-listing:\n"
            "title, brand, model, condition, listing_type, price.\n"
            "Optional but recommended: transmission, fuel_system, vehicle_type (defaults to 'car').\n"
            "For cars: drivetrain, seats, doors, vin are optional.\n"
            "For planes: registration_number, aircraft_type, engine_type, max_altitude, wing_span, range.\n"
            "For boats: hull_material, engine_count, propeller_type, length, beam_width, draft.\n"
            "For bikes: engine_capacity, bike_type, saddle_height.\n"
            "For UAVs: registration_number, uav_type, purpose, max_flight_time, max_range, max_altitude, camera_resolution, payload_capacity, weight, rotor_count.\n"
            "For rental listings, payment_cycle is required."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[
                'action'
            ],
            properties={
                'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['create-listing','upload-images','publish-listing'], example='create-listing'),
                'vehicle_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['car','plane','boat','bike','uav'], example='car', description='Type of vehicle'),
                'title': openapi.Schema(type=openapi.TYPE_STRING, example='2020 Toyota Camry XLE'),
                'brand': openapi.Schema(type=openapi.TYPE_STRING, example='Toyota'),
                'model': openapi.Schema(type=openapi.TYPE_STRING, example='Camry'),
                'condition': openapi.Schema(type=openapi.TYPE_STRING, enum=['new','used-foreign','used-local'], example='used-foreign'),
                'transmission': openapi.Schema(type=openapi.TYPE_STRING, enum=['auto','manual'], example='auto'),
                'fuel_system': openapi.Schema(type=openapi.TYPE_STRING, enum=['diesel','electric','petrol','hybrid'], example='petrol'),
                'drivetrain': openapi.Schema(type=openapi.TYPE_STRING, enum=['4WD','AWD','FWD','RWD'], example='FWD', description='Required for cars only'),
                'seats': openapi.Schema(type=openapi.TYPE_INTEGER, example=5, description='Required for cars only'),
                'doors': openapi.Schema(type=openapi.TYPE_INTEGER, example=4, description='Required for cars only'),
                'vin': openapi.Schema(type=openapi.TYPE_STRING, example='1HGBH41JXMN109186', description='Required for cars only'),
                'registration_number': openapi.Schema(type=openapi.TYPE_STRING, description='For planes'),
                'aircraft_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['jet','propeller','glider','helicopter'], description='For planes'),
                'engine_type': openapi.Schema(type=openapi.TYPE_STRING, description='For planes'),
                'max_altitude': openapi.Schema(type=openapi.TYPE_INTEGER, description='For planes (in feet)'),
                'wing_span': openapi.Schema(type=openapi.TYPE_NUMBER, description='For planes'),
                'range': openapi.Schema(type=openapi.TYPE_INTEGER, description='For planes (in km)'),
                'hull_material': openapi.Schema(type=openapi.TYPE_STRING, description='For boats'),
                'engine_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='For boats'),
                'propeller_type': openapi.Schema(type=openapi.TYPE_STRING, description='For boats'),
                'length': openapi.Schema(type=openapi.TYPE_NUMBER, description='For boats (in feet/meters)'),
                'beam_width': openapi.Schema(type=openapi.TYPE_NUMBER, description='For boats'),
                'draft': openapi.Schema(type=openapi.TYPE_NUMBER, description='For boats'),
                'engine_capacity': openapi.Schema(type=openapi.TYPE_INTEGER, description='For bikes (in cc)'),
                'bike_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['cruiser','sport','touring','offroad'], description='For bikes'),
                'saddle_height': openapi.Schema(type=openapi.TYPE_NUMBER, description='For bikes'),
                'uav_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['quadcopter','hexacopter','octocopter','fixed-wing','hybrid'], description='For UAVs'),
                'purpose': openapi.Schema(type=openapi.TYPE_STRING, enum=['recreational','photography','surveying','agriculture','delivery','inspection','racing','military'], description='For UAVs'),
                'max_flight_time': openapi.Schema(type=openapi.TYPE_INTEGER, description='For UAVs (in minutes)'),
                'camera_resolution': openapi.Schema(type=openapi.TYPE_STRING, description='For UAVs (e.g., 4K, 8K)'),
                'payload_capacity': openapi.Schema(type=openapi.TYPE_NUMBER, description='For UAVs (in kg)'),
                'weight': openapi.Schema(type=openapi.TYPE_NUMBER, description='For UAVs (in kg)'),
                'rotor_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='For UAVs'),
                'has_obstacle_avoidance': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='For UAVs'),
                'has_gps': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='For UAVs'),
                'has_return_to_home': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='For UAVs'),
                'listing_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['sale','rental'], example='sale'),
                'price': openapi.Schema(type=openapi.TYPE_NUMBER, example=5000000),
                'color': openapi.Schema(type=openapi.TYPE_STRING, example='Black'),
                'mileage': openapi.Schema(type=openapi.TYPE_INTEGER, example=25000),
                'notes': openapi.Schema(type=openapi.TYPE_STRING, example='Well maintained with full service history'),
                'features': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), example=['AC','Bluetooth']),
                'payment_cycle': openapi.Schema(type=openapi.TYPE_STRING, enum=['daily','weekly','monthly'], example='daily'),
                'image': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_FILE), description='Used with action=upload-images')
            }
        ),
        responses={
            200: openapi.Response(
                description='Operation successful',
                examples={
                    'application/json': {
                        'error': False,
                        'message': 'Successfully published your listing',
                        'data': {
                            'id': '550e8400-e29b-41d4-a716-446655440000',
                            'title': '2020 Toyota Camry XLE'
                        }
                    }
                }
            ),
            400: openapi.Response(
                description='Validation error',
                examples={
                    'application/json': {
                        'error': True,
                        'message': 'Missing required fields: drivetrain, seats'
                    }
                }
            ),
            404: openapi.Response(
                description='Dealership not found',
                examples={
                    'application/json': {
                        'error': True,
                        'message': 'Dealership profile not found for this user'
                    }
                }
            ),
            500: openapi.Response(
                description='Server error',
                examples={
                    'application/json': {
                        'error': True,
                        'message': 'An error occurred: ...'
                    }
                }
            )
        },
        tags=['Listings']
    )
    def post(self, request, **kwargs):
        try:
            dealer = Dealership.objects.get(user=request.user)
            data = request.data
            action = data.get('action', 'create-listing')
            message = 'Successfully created new listing'
            listing = None

            if action == 'create-listing':
                # Get vehicle type (default to 'car' for backward compatibility)
                vehicle_type = data.get('vehicle_type', 'car').lower()
                
                # Log vehicle type for debugging
                logger.info(f"Creating listing with vehicle_type='{vehicle_type}' for brand='{data.get('brand')}'")
                
                # Validate vehicle type
                valid_types = ['car', 'plane', 'boat', 'bike', 'uav', 'drone']
                if vehicle_type not in valid_types:
                    return Response({
                        'error': True,
                        'message': f'Invalid vehicle_type: {vehicle_type}. Must be one of: {", ".join(valid_types)}'
                    }, status=400)
                
                # Validate common required fields
                required_fields = ['title', 'brand', 'model', 'condition',
                                   'listing_type', 'price']
                
                # transmission and fuel_system are optional for some vehicle types
                # drivetrain, seats, doors, vin are optional (car-specific but not required)
                
                missing_fields = [field for field in required_fields if field not in data or not data.get(field)]
                
                if missing_fields:
                    return Response({
                        'error': True,
                        'message': f'Missing required fields: {", ".join(missing_fields)}'
                    }, status=400)
                
                # Validate listing_type specific fields
                if data.get('listing_type') == 'rental' and 'payment_cycle' not in data:
                    return Response({
                        'error': True,
                        'message': 'payment_cycle is required for rental listings'
                    }, status=400)
                
                # Common vehicle fields
                common_fields = {
                    'name': data['title'],
                    'dealer': dealer,
                    'color': data.get('color', 'None'),
                    'brand': data['brand'],
                    'model': data['model'],
                    'condition': data['condition'],
                    'mileage': data.get('mileage', 0),
                    'transmission': data.get('transmission'),
                    'fuel_system': data.get('fuel_system'),
                }
                
                # Create vehicle based on type
                if vehicle_type == 'car':
                    vehicle = Car(
                        **common_fields,
                        drivetrain=data.get('drivetrain'),
                        seats=data.get('seats', 5),
                        doors=data.get('doors', 4),
                        vin=data.get('vin'),
                    )
                elif vehicle_type == 'plane':
                    vehicle = Plane(
                        **common_fields,
                        registration_number=data.get('registration_number'),
                        engine_type=data.get('engine_type'),
                        aircraft_type=data.get('aircraft_type'),
                        max_altitude=data.get('max_altitude'),
                        wing_span=data.get('wing_span'),
                        range=data.get('range'),
                    )
                elif vehicle_type == 'boat':
                    vehicle = Boat(
                        **common_fields,
                        hull_material=data.get('hull_material'),
                        engine_count=data.get('engine_count'),
                        propeller_type=data.get('propeller_type'),
                        length=data.get('length'),
                        beam_width=data.get('beam_width'),
                        draft=data.get('draft'),
                    )
                elif vehicle_type == 'bike':
                    vehicle = Bike(
                        **common_fields,
                        engine_capacity=data.get('engine_capacity'),
                        bike_type=data.get('bike_type'),
                        saddle_height=data.get('saddle_height'),
                    )
                elif vehicle_type == 'uav' or vehicle_type == 'drone':
                    vehicle = UAV(
                        **common_fields,
                        registration_number=data.get('registration_number'),
                        uav_type=data.get('uav_type'),
                        purpose=data.get('purpose'),
                        max_flight_time=data.get('max_flight_time'),
                        max_range=data.get('max_range'),
                        max_altitude=data.get('max_altitude'),
                        max_speed=data.get('max_speed'),
                        camera_resolution=data.get('camera_resolution'),
                        payload_capacity=data.get('payload_capacity'),
                        weight=data.get('weight'),
                        rotor_count=data.get('rotor_count'),
                        has_obstacle_avoidance=data.get('has_obstacle_avoidance', False),
                        has_gps=data.get('has_gps', True),
                        has_return_to_home=data.get('has_return_to_home', True),
                    )
                else:
                    return Response({
                        'error': True,
                        'message': f'Invalid vehicle_type: {vehicle_type}. Must be one of: car, plane, boat, bike, uav'
                    }, status=400)
                if data['listing_type'] == 'sale':
                    vehicle.for_sale = True
                elif data['listing_type'] == 'rental':
                    # Convert features to list if it's a string
                    features = data.get('features', [])
                    if isinstance(features, str):
                        features = [f.strip() for f in features.split(',') if f.strip()]
                    elif not isinstance(features, list):
                        features = []
                    vehicle.features = features
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
                
                # Log successful creation with vehicle type
                logger.info(f"Successfully created {vehicle_type} listing: {listing.title} (Vehicle ID: {vehicle.id}, Class: {vehicle.__class__.__name__})")
            elif action == 'upload-images':
                listing = dealer.listings.get(uuid=data['listing'])
                images = data.getlist('image')
                # paths = upload_multiple_files(images)
                for img in images:
                    image = VehicleImage(
                        image=img,
                        vehicle=listing.vehicle
                    )
                    image.save()
                    listing.vehicle.images.add(image,)
                listing.vehicle.save() # save to db
                message = "Image added"
                # return Response({'error': False, 'message': })
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
        except Dealership.DoesNotExist:
            return Response({
                'error': True,
                'message': 'Dealership profile not found for this user'
            }, status=404)
        except KeyError as e:
            return Response({
                'error': True,
                'message': f'Missing required field: {str(e)}'
            }, status=400)
        except Exception as error:
            # Log the error for debugging
            import traceback
            traceback.print_exc()
            return Response({
                'error': True,
                'message': f'An error occurred: {str(error)}'
            }, status=500)


class ListingDetailView(RetrieveUpdateDestroyAPIView):
    allowed_methods = ['GET', 'PUT', 'DELETE']
    permission_classes = [IsAuthenticated, IsDealerOrStaff]
    authentication_classes = [JWTAuthentication, TokenAuthentication, SessionAuthentication]
    parser_classes = [MultiPartParser, JSONParser, FormParser]
    serializer_class = ListingSerializer
    
    def get_object(self):
        return Listing.objects.get(uuid=self.kwargs['listing_id'])

    @swagger_auto_schema(
        operation_summary="Get listing detail",
        operation_description="Retrieve a single listing by its UUID (path parameter: listing_id).",
        responses={
            200: openapi.Response(description='Listing detail'),
            404: openapi.Response(description='Listing not found')
        },
        tags=['Listings']
    )
    def get(self, request, listing_id):
        try:
            data = {
                'error': False,
                'data': ListingSerializer(self.get_object(), context={'request': request}).data
            }
            return Response(data, 200)
        except Exception as error:
            return Response({'error': True, 'message': str(error)}, 500)

    @swagger_auto_schema(
        operation_summary="Edit listing / upload or remove images / publish listing",
        operation_description=(
            "This endpoint performs multiple actions based on 'action':\n\n"
            "- edit-listing: Update listing and vehicle fields (see request schema)\n"
            "- upload-images: Upload images array under 'image' (multipart/form-data)\n"
            "- remove-image: Remove a vehicle image by 'image_id' (UUID)\n"
            "- publish-listing: Publish a listing by passing 'listing' UUID (note: uses body UUID)"
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['action'],
            properties={
                'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['edit-listing','upload-images','remove-image','publish-listing'], example='edit-listing'),
                'title': openapi.Schema(type=openapi.TYPE_STRING, description='Listing title'),
                'price': openapi.Schema(type=openapi.TYPE_NUMBER, description='Listing price'),
                'notes': openapi.Schema(type=openapi.TYPE_STRING, description='Additional notes'),
                'listing_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['sale','rental']),
                'payment_cycle': openapi.Schema(type=openapi.TYPE_STRING, enum=['daily','weekly','monthly'], description='Required when listing_type=rental'),
                'vehicle': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'brand': openapi.Schema(type=openapi.TYPE_STRING),
                        'model': openapi.Schema(type=openapi.TYPE_STRING),
                        'condition': openapi.Schema(type=openapi.TYPE_STRING, enum=['new','used-foreign','used-local']),
                        'transmission': openapi.Schema(type=openapi.TYPE_STRING, enum=['auto','manual']),
                        'fuel_system': openapi.Schema(type=openapi.TYPE_STRING, enum=['diesel','electric','petrol','hybrid']),
                        'color': openapi.Schema(type=openapi.TYPE_STRING),
                        'mileage': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'drivetrain': openapi.Schema(type=openapi.TYPE_STRING, enum=['4WD','AWD','FWD','RWD'], description='For cars only'),
                        'seats': openapi.Schema(type=openapi.TYPE_INTEGER, description='For cars only'),
                        'doors': openapi.Schema(type=openapi.TYPE_INTEGER, description='For cars only'),
                        'vin': openapi.Schema(type=openapi.TYPE_STRING, description='For cars only'),
                        'registration_number': openapi.Schema(type=openapi.TYPE_STRING, description='For planes'),
                        'aircraft_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['jet','propeller','glider','helicopter'], description='For planes'),
                        'engine_type': openapi.Schema(type=openapi.TYPE_STRING, description='For planes'),
                        'max_altitude': openapi.Schema(type=openapi.TYPE_INTEGER, description='For planes'),
                        'wing_span': openapi.Schema(type=openapi.TYPE_NUMBER, description='For planes'),
                        'range': openapi.Schema(type=openapi.TYPE_INTEGER, description='For planes'),
                        'hull_material': openapi.Schema(type=openapi.TYPE_STRING, description='For boats'),
                        'engine_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='For boats'),
                        'propeller_type': openapi.Schema(type=openapi.TYPE_STRING, description='For boats'),
                        'length': openapi.Schema(type=openapi.TYPE_NUMBER, description='For boats'),
                        'beam_width': openapi.Schema(type=openapi.TYPE_NUMBER, description='For boats'),
                        'draft': openapi.Schema(type=openapi.TYPE_NUMBER, description='For boats'),
                        'engine_capacity': openapi.Schema(type=openapi.TYPE_INTEGER, description='For bikes'),
                        'bike_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['cruiser','sport','touring','offroad'], description='For bikes'),
                        'saddle_height': openapi.Schema(type=openapi.TYPE_NUMBER, description='For bikes'),
                        'features': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                    }
                ),
                'image': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_FILE), description='Used with action=upload-images'),
                'image_id': openapi.Schema(type=openapi.TYPE_STRING, format='uuid', description='Used with action=remove-image'),
                'listing': openapi.Schema(type=openapi.TYPE_STRING, format='uuid', description='Used with action=publish-listing')
            }
        ),
        responses={
            200: openapi.Response(description='Operation successful'),
            400: openapi.Response(description='Validation error'),
            404: openapi.Response(description='Not found')
        },
        tags=['Listings']
    )
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

                # Update common vehicle fields
                vehicle.name = data['title']
                vehicle.model = data['vehicle']['model']
                vehicle.color = data['vehicle'].get('color', 'None')
                vehicle.brand = data['vehicle']['brand']
                vehicle.condition = data['vehicle']['condition']
                vehicle.transmission = data['vehicle']['transmission']
                vehicle.mileage = data['vehicle']['mileage']
                vehicle.fuel_system = data['vehicle']['fuel_system']
                
                # Update vehicle-type specific fields
                # Check if vehicle is a Car (has drivetrain attribute)
                if hasattr(vehicle, 'drivetrain'):
                    vehicle.drivetrain = data['vehicle'].get('drivetrain')
                    vehicle.seats = data['vehicle'].get('seats')
                    vehicle.doors = data['vehicle'].get('doors')
                    vehicle.vin = data['vehicle'].get('vin')
                
                # Check if vehicle is a Plane
                if hasattr(vehicle, 'registration_number'):
                    vehicle.registration_number = data['vehicle'].get('registration_number')
                    vehicle.engine_type = data['vehicle'].get('engine_type')
                    vehicle.aircraft_type = data['vehicle'].get('aircraft_type')
                    vehicle.max_altitude = data['vehicle'].get('max_altitude')
                    vehicle.wing_span = data['vehicle'].get('wing_span')
                    vehicle.range = data['vehicle'].get('range')
                
                # Check if vehicle is a Boat
                if hasattr(vehicle, 'hull_material'):
                    vehicle.hull_material = data['vehicle'].get('hull_material')
                    vehicle.engine_count = data['vehicle'].get('engine_count')
                    vehicle.propeller_type = data['vehicle'].get('propeller_type')
                    vehicle.length = data['vehicle'].get('length')
                    vehicle.beam_width = data['vehicle'].get('beam_width')
                    vehicle.draft = data['vehicle'].get('draft')
                
                # Check if vehicle is a Bike
                if hasattr(vehicle, 'engine_capacity') and hasattr(vehicle, 'bike_type'):
                    vehicle.engine_capacity = data['vehicle'].get('engine_capacity')
                    vehicle.bike_type = data['vehicle'].get('bike_type')
                    vehicle.saddle_height = data['vehicle'].get('saddle_height')
                
                # Check if vehicle is a UAV
                if hasattr(vehicle, 'uav_type'):
                    vehicle.registration_number = data['vehicle'].get('registration_number')
                    vehicle.uav_type = data['vehicle'].get('uav_type')
                    vehicle.purpose = data['vehicle'].get('purpose')
                    vehicle.max_flight_time = data['vehicle'].get('max_flight_time')
                    vehicle.max_range = data['vehicle'].get('max_range')
                    vehicle.max_altitude = data['vehicle'].get('max_altitude')
                    vehicle.max_speed = data['vehicle'].get('max_speed')
                    vehicle.camera_resolution = data['vehicle'].get('camera_resolution')
                    vehicle.payload_capacity = data['vehicle'].get('payload_capacity')
                    vehicle.weight = data['vehicle'].get('weight')
                    vehicle.rotor_count = data['vehicle'].get('rotor_count')
                    vehicle.has_obstacle_avoidance = data['vehicle'].get('has_obstacle_avoidance', False)
                    vehicle.has_gps = data['vehicle'].get('has_gps', True)
                    vehicle.has_return_to_home = data['vehicle'].get('has_return_to_home', True)

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
                # paths = upload_multiple_files(images)
                # print("Images", paths)
                for img in images:
                    image = VehicleImage(
                        image=img,
                        vehicle=vehicle
                    )
                    image.save()
                    vehicle.images.add(image,)
                vehicle.save() # save to db
                message = "Image added"
                # return Response({'error': False, 'message': })
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
    @swagger_auto_schema(
        operation_summary="Delete a listing",
        operation_description="Delete the listing identified by the path parameter listing_id.",
        responses={200: openapi.Response(description='Deleted successfully'), 404: openapi.Response(description='Not found')},
        tags=['Listings']
    )
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

    @swagger_auto_schema(
        operation_summary="List dealer orders",
        operation_description="Return all orders for the authenticated dealer.",
        responses={
            200: openapi.Response(description='List of orders')
        },
        tags=['Orders']
    )
    def get(self, request):
        # Handle schema generation when user is AnonymousUser
        if getattr(self, 'swagger_fake_view', False):
            return Response({'error': False, 'data': []}, status=200)
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return Response({'error': True, 'message': 'Authentication required'}, status=401)
            
        try:
            dealer = Dealership.objects.get(user=request.user)
            orders = dealer.orders.all()
            data = {
                'error': False,
                'data': OrderSerializer(orders, many=True, context={'request': request}).data
            }
            return Response(data, status=200)
        except Dealership.DoesNotExist:
            return Response({'error': True, 'message': 'Dealer profile not found'}, status=404)

    def post(self, request):
        return Response()



class SettingsView(APIView):
    allowed_methods = ['PUT', 'POST', 'GET']
    permission_classes = [IsAuthenticated, IsDealerOrStaff]
    parser_classes = [MultiPartParser, JSONParser, FormParser]

    @swagger_auto_schema(
        operation_summary="Get dealership settings",
        operation_description="Return the authenticated dealer's profile/settings.",
        responses={200: openapi.Response(description='Dealer profile')},
        tags=['Dealership']
    )
    def get(self, request):
        try:
            dealer = Dealership.objects.get(user=request.user)
            data = {
                'error': False,
                'data': DealerSerializer(dealer, context={'request': request}).data
            }
            return Response(data, status=200)
        except Dealership.DoesNotExist:
            return Response({
                'error': True,
                'message': 'Dealership profile not found. Please complete your dealership profile setup.'
            }, status=404)

    @swagger_auto_schema(
        operation_summary="Update dealership settings",
        operation_description=(
            "Update dealership profile fields. All fields are optional - only provided fields will be updated.\n\n"
            "For logo upload, send multipart/form-data with 'logo' field.\n\n"
            "**Logo Upload**: Upload business logo using the 'logo' field.\n"
            "**Response**: Returns updated dealership profile including logo URL."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'logo': openapi.Schema(type=openapi.TYPE_FILE, description='Business logo file'),
                'business_name': openapi.Schema(type=openapi.TYPE_STRING),
                'about': openapi.Schema(type=openapi.TYPE_STRING),
                'slug': openapi.Schema(type=openapi.TYPE_STRING),
                'headline': openapi.Schema(type=openapi.TYPE_STRING),
                'services': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), example=['Car Sale','Car Leasing','Drivers']),
                'contact_phone': openapi.Schema(type=openapi.TYPE_STRING),
                'contact_email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                'location': openapi.Schema(type=openapi.TYPE_INTEGER, description='Location ID reference (optional)')
            }
        ),
        responses={
            200: openapi.Response(
                description='Updated successfully',
                examples={
                    'application/json': {
                        'error': False,
                        'data': {
                            'uuid': '550e8400-e29b-41d4-a716-446655440000',
                            'business_name': 'ABC Motors',
                            'logo': 'https://res.cloudinary.com/.../logo.png',
                            'about': 'Leading car dealership...',
                            'headline': 'Your trusted car partner'
                        }
                    }
                }
            )
        },
        tags=['Dealership']
    )
    def put(self, request):
        return self._update_dealership_settings(request)

    @swagger_auto_schema(
        operation_summary="Update dealership settings (DEPRECATED)",
        operation_description=(
            "⚠️ DEPRECATED: Use PUT method instead. This endpoint will be removed on December 1, 2025.\n\n"
            "Update dealership profile fields. All fields are optional - only provided fields will be updated.\n\n"
            "For logo upload, send multipart/form-data with 'logo' field."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'logo': openapi.Schema(type=openapi.TYPE_FILE, description='Business logo file'),
                'business_name': openapi.Schema(type=openapi.TYPE_STRING),
                'about': openapi.Schema(type=openapi.TYPE_STRING),
                'slug': openapi.Schema(type=openapi.TYPE_STRING),
                'headline': openapi.Schema(type=openapi.TYPE_STRING),
                'services': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), example=['Car Sale','Car Leasing','Drivers']),
                'contact_phone': openapi.Schema(type=openapi.TYPE_STRING),
                'contact_email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                'location': openapi.Schema(type=openapi.TYPE_INTEGER, description='Location ID reference (optional)')
            }
        ),
        responses={200: openapi.Response(description='Updated successfully')},
        tags=['Dealership'],
        deprecated=True
    )
    def post(self, request):
        # Add deprecation warning to response headers
        response = self._update_dealership_settings(request)
        response['X-Deprecation-Warning'] = 'POST method is deprecated. Use PUT instead.'
        response['X-Deprecation-Date'] = '2025-12-01'
        
        # Log deprecation usage
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"DEPRECATED: POST method used for dealership settings update by user {request.user.email}")
        
        return response

    def _update_dealership_settings(self, request):
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            data = request.data
            dealer = Dealership.objects.get(user=request.user)
            
            # Log request details for debugging
            logger.info(f"Request content type: {request.content_type}")
            logger.info(f"Request FILES: {list(request.FILES.keys())}")
            logger.info(f"Request DATA keys: {list(data.keys())}")

            # Note: All fields are optional for partial updates
            # Only validate fields that are provided

            # Parse services if it's a JSON string (from FormData)
            import json
            
            # Check if services is sent as multiple form fields (getlist) or single field (get)
            # This handles the case where FormData sends array items separately
            if hasattr(data, 'getlist'):
                services_list = data.getlist('services')
                services_single = data.get('services')
                logger.info(f"🔍 FormData detected - getlist: {services_list}, get: {services_single}")
                # Use getlist if it has multiple items, otherwise use get
                services = services_list if len(services_list) > 1 else services_single
            else:
                services = data.get('services')
            
            logger.info(f"🔍 RAW SERVICES DEBUG - Type: {type(services)}, Value: {repr(services)}")
            logger.debug(f"Raw services data: {services}, type: {type(services)}")
            
            # Handle different input formats
            # Services is optional - skip processing if not provided
            service_updates = None
            unmapped_services = []
            suggestions = []
            
            if services is not None:
                # If it's already a list, use it directly
                if isinstance(services, list):
                    logger.debug(f"Services already a list: {services}")
                # If it's a string, try to parse as JSON
                elif isinstance(services, str):
                    try:
                        services = json.loads(services)
                        logger.debug(f"Parsed services from JSON string: {services}")
                        # Verify it's actually a list after parsing
                        if not isinstance(services, list):
                            logger.error(f"JSON parsing resulted in non-list type: {type(services)}")
                            return Response({
                                'error': True,
                                'message': 'Invalid services format. Must be an array of service names.',
                            }, status=400)
                    except json.JSONDecodeError as e:
                        # If JSON parsing fails, treat as a single service name
                        logger.warning(f"Could not parse services as JSON: {e}, treating as single service: {services}")
                        services = [services]
                else:
                    # For any other type, wrap in a list (don't use list() which splits strings)
                    logger.warning(f"Unexpected services type: {type(services)}, wrapping in list")
                    services = [str(services)]
                
                # Final validation: ensure we have a list
                if not isinstance(services, list):
                    logger.error(f"Services is not a list after processing: {type(services)}")
                    return Response({
                        'error': True,
                        'message': 'Invalid services format. Must be an array of service names.',
                    }, status=400)
                
                # Ensure all items are strings and filter out empty values
                # CRITICAL: Only iterate if we have a proper list, not a string
                if services and isinstance(services, list):
                    services = [str(s).strip() for s in services if s and isinstance(s, (str, int, float))]
                else:
                    logger.error(f"Services validation failed - not a proper list: {type(services)}")
                    return Response({
                        'error': True,
                        'message': 'Invalid services format. Must be an array of service names.',
                    }, status=400)
                
                logger.debug(f"Final services list: {services}")
                
                logger.info(f"Processing dealership settings update for {dealer.business_name}")
                logger.debug(f"New Services: {services}")
                logger.debug(f"Old Services: {getattr(dealer, 'services', [])}")
                
                # Process services using DealershipServiceProcessor
                service_processor = DealershipServiceProcessor()
                
                # Validate services first to provide detailed error information
                is_valid, unmapped_services, suggestions = service_processor.validate_services(services)
                
                # Log unmapped services for debugging
                if unmapped_services:
                    logger.warning(f"Unmapped services detected for dealership {dealer.business_name}: {unmapped_services}")
                    for service in unmapped_services:
                        service_suggestions = service_processor._suggest_similar_services(service, max_suggestions=3)
                        if service_suggestions:
                            logger.info(f"Suggestions for '{service}': {service_suggestions}")
                
                try:
                    # Process the selected services
                    service_updates = service_processor.process_services(services)
                except DjangoValidationError as ve:
                    logger.error(f"Service validation failed for dealership {dealer.business_name}: {str(ve)}")
                    
                    # Enhanced error response with detailed information
                    error_details = {
                        'field_errors': {
                            'services': [str(ve)]
                        }
                    }
                    
                    if unmapped_services:
                        error_details['unmapped_services'] = unmapped_services
                        error_details['unmapped_count'] = len(unmapped_services)
                    
                    if suggestions:
                        error_details['suggestions'] = suggestions[:5]  # Provide up to 5 suggestions
                        error_details['suggestion_message'] = f"Did you mean: {', '.join(suggestions[:3])}?"
                    
                    # Add helpful context about available services
                    available_services = service_processor.get_available_services()
                    error_details['available_service_categories'] = list(available_services.keys())
                    
                    return Response({
                        'error': True,
                        'message': 'Service validation failed. Please check your service selections.',
                        'details': error_details
                    }, status=400)
            else:
                logger.debug("No services provided in request, skipping service updates")
            
            # Update dealer profile fields (only if provided)
            # Handle logo upload
            logo_file = request.FILES.get('logo') or data.get('logo')
            if logo_file:
                logger.info(f"Logo file detected for {dealer.business_name}: {logo_file}")
                logger.info(f"Logo file type: {type(logo_file)}, size: {getattr(logo_file, 'size', 'N/A')}")
                dealer.logo = logo_file
            else:
                logger.info(f"No logo file in request. FILES keys: {list(request.FILES.keys())}, DATA keys: {list(data.keys())}")
            
            # Update fields only if provided
            if 'business_name' in data:
                dealer.business_name = data['business_name']
            if 'about' in data:
                dealer.about = data['about']
            if 'slug' in data:
                dealer.slug = data.get('slug', None)
            if 'headline' in data:
                dealer.headline = data['headline']
            
            # Apply service mappings from processor (only if services were provided and processed)
            if 'services' in data and service_updates is not None:
                dealer.offers_purchase = service_updates['offers_purchase']
                dealer.offers_rental = service_updates['offers_rental']
                dealer.offers_drivers = service_updates['offers_drivers']
                dealer.offers_trade_in = service_updates['offers_trade_in']
                
                # Handle extended services if the field exists
                if hasattr(dealer, 'extended_services'):
                    dealer.extended_services = service_updates['extended_services']
            
            if 'contact_phone' in data:
                dealer.contact_phone = data['contact_phone']
            if 'contact_email' in data:
                dealer.contact_email = data['contact_email']
            
            # Handle location update if provided
            if 'location' in data and data['location']:
                from accounts.models import Location
                try:
                    location_id = int(data['location'])
                    location = Location.objects.get(id=location_id, user=request.user)
                    dealer.location = location
                    logger.info(f"Updated location for dealership {dealer.business_name} to location ID {location_id}")
                except Location.DoesNotExist:
                    logger.warning(f"Location ID {data['location']} not found for user {request.user.email}")
                    return Response({
                        'error': True,
                        'message': 'Invalid location ID. Location not found or does not belong to you.',
                        'details': {
                            'field_errors': {
                                'location': ['Location not found or access denied']
                            }
                        }
                    }, status=400)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid location ID format: {data['location']}")
                    return Response({
                        'error': True,
                        'message': 'Invalid location ID format. Must be an integer.',
                        'details': {
                            'field_errors': {
                                'location': ['Invalid location ID format']
                            }
                        }
                    }, status=400)
            
            dealer.save()
            
            # Log logo status after save
            if logo_file:
                logger.info(f"Logo saved successfully for {dealer.business_name}. New logo URL: {dealer.logo.url if dealer.logo else 'None'}")
            
            # Log successful update
            if service_updates:
                mapped_services = sum([
                    dealer.offers_purchase,
                    dealer.offers_rental, 
                    dealer.offers_drivers,
                    dealer.offers_trade_in
                ])
                extended_count = len(service_updates.get('extended_services', []))
                logger.info(f"Successfully updated dealership {dealer.business_name}: {mapped_services} core services, {extended_count} extended services")
            else:
                logger.info(f"Successfully updated dealership {dealer.business_name} (no service changes)")
            
            response_data = {
                'error': False,
                'data': DealerSerializer(dealer, context={'request': request}).data
            }
            
            # Include debug information if there were unmapped services
            if unmapped_services and suggestions:
                response_data['warnings'] = {
                    'unmapped_services': unmapped_services,
                    'suggestions': suggestions[:5]  # Provide up to 5 suggestions
                }
            
            return Response(response_data, 200)
            
        except Dealership.DoesNotExist:
            logger.error(f"Dealership profile not found for user {request.user.email}")
            return Response({
                'error': True,
                'message': 'Dealership profile not found. Please complete your dealership profile setup.',
                'details': {
                    'error_code': 'DEALERSHIP_NOT_FOUND',
                    'help_text': 'Contact support if you believe this is an error.'
                }
            }, status=404)
        except KeyError as e:
            # This should not happen since we check 'if field in data' before accessing
            # But if it does, it's a programming error, not a user error
            logger.error(f"Unexpected KeyError in dealership settings update: {str(e)}", exc_info=True)
            return Response({
                'error': True,
                'message': 'An unexpected error occurred while processing your request.',
                'details': {
                    'error_code': 'INTERNAL_ERROR',
                    'help_text': 'Please try again. If the problem persists, contact support.'
                }
            }, status=500)
        except Exception as e:
            logger.error(f"Unexpected error in dealership settings update: {str(e)}", exc_info=True)
            return Response({
                'error': True,
                'message': 'An unexpected error occurred while updating your dealership settings.',
                'details': {
                    'error_code': 'INTERNAL_ERROR',
                    'help_text': 'Please try again. If the problem persists, contact support.',
                    'debug_info': str(e) if hasattr(request, 'user') and request.user.is_staff else None
                }
            }, status=500)





class BoostPricingView(APIView):
    """View for getting boost pricing (public endpoint)"""
    allowed_methods = ['GET']
    permission_classes = []  # Public endpoint
    
    @swagger_auto_schema(
        operation_summary="Get boost pricing",
        operation_description="Retrieve current pricing for listing boosts (daily, weekly, monthly)",
        responses={
            200: openapi.Response(
                description='Boost pricing list',
                examples={
                    'application/json': {
                        'error': False,
                        'data': [
                            {
                                'duration_type': 'daily',
                                'duration_display': 'Daily',
                                'price': '1000.00',
                                'formatted_price': '₦1,000.00'
                            }
                        ]
                    }
                }
            )
        },
        tags=['Boost']
    )
    def get(self, request):
        from .serializers import BoostPricingSerializer
        from ..models import BoostPricing
        
        pricing = BoostPricing.objects.filter(is_active=True)
        data = {
            'error': False,
            'data': BoostPricingSerializer(pricing, many=True).data
        }
        return Response(data, 200)


class ListingBoostView(APIView):
    """View for managing listing boosts"""
    allowed_methods = ['GET', 'POST', 'DELETE']
    permission_classes = [IsAuthenticated, IsDealerOrStaff]
    authentication_classes = [JWTAuthentication, TokenAuthentication, SessionAuthentication]
    
    @swagger_auto_schema(
        operation_summary="Get boost status for a listing",
        operation_description="Retrieve the current boost status for a specific listing",
        responses={
            200: openapi.Response(
                description='Boost details',
                examples={
                    'application/json': {
                        'error': False,
                        'data': {
                            'listing_uuid': '550e8400-e29b-41d4-a716-446655440000',
                            'active': True,
                            'days_remaining': 5,
                            'amount_paid': '5000.00'
                        }
                    }
                }
            ),
            404: openapi.Response(description='No active boost found')
        },
        tags=['Boost']
    )
    def get(self, request, listing_id):
        from .serializers import ListingBoostSerializer
        from ..models import ListingBoost
        
        try:
            dealer = Dealership.objects.get(user=request.user)
            listing = dealer.listings.get(uuid=listing_id)
            
            if not hasattr(listing, 'listing_boost'):
                return Response({
                    'error': False,
                    'message': 'No boost found for this listing',
                    'data': None
                }, 200)
            
            boost = listing.listing_boost
            data = {
                'error': False,
                'data': ListingBoostSerializer(boost).data
            }
            return Response(data, 200)
            
        except Dealership.DoesNotExist:
            return Response({
                'error': True,
                'message': 'Dealership profile not found'
            }, 404)
        except Listing.DoesNotExist:
            return Response({
                'error': True,
                'message': 'Listing not found or does not belong to you'
            }, 404)
    
    @swagger_auto_schema(
        operation_summary="Create a boost for a listing",
        operation_description=(
            "Create a boost for a listing. This will calculate the cost and create a pending boost.\n\n"
            "**Payment Flow:**\n"
            "1. Create boost (returns total cost and boost ID)\n"
            "2. Process payment using your payment gateway\n"
            "3. Confirm payment using the confirm-payment endpoint\n\n"
            "**Duration Types:**\n"
            "- daily: Boost per day\n"
            "- weekly: Boost per week\n"
            "- monthly: Boost per month\n\n"
            "**Duration Count:**\n"
            "Number of duration units (e.g., duration_count=2 with duration_type=weekly means 2 weeks)"
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['duration_type', 'duration_count'],
            properties={
                'duration_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['daily', 'weekly', 'monthly'],
                    example='weekly'
                ),
                'duration_count': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    minimum=1,
                    maximum=12,
                    example=2,
                    description='Number of duration units'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description='Boost created successfully',
                examples={
                    'application/json': {
                        'error': False,
                        'message': 'Boost created successfully. Please proceed with payment.',
                        'data': {
                            'boost_id': 123,
                            'total_cost': '10000.00',
                            'duration_type': 'weekly',
                            'duration_count': 2,
                            'start_date': '2025-11-24',
                            'end_date': '2025-12-08'
                        }
                    }
                }
            ),
            400: openapi.Response(description='Validation error')
        },
        tags=['Boost']
    )
    def post(self, request, listing_id):
        from .serializers import CreateListingBoostSerializer, ListingBoostSerializer
        from ..models import ListingBoost, BoostPricing
        from datetime import timedelta
        
        try:
            dealer = Dealership.objects.get(user=request.user)
            
            # Add listing UUID to request data
            data = request.data.copy()
            data['listing'] = listing_id
            
            serializer = CreateListingBoostSerializer(data=data, context={'request': request})
            
            if not serializer.is_valid():
                return Response({
                    'error': True,
                    'message': 'Validation failed',
                    'errors': serializer.errors
                }, 400)
            
            validated_data = serializer.validated_data
            listing = Listing.objects.get(uuid=validated_data['listing'])
            
            # Calculate dates
            start_date = now().date()
            duration_type = validated_data['duration_type']
            duration_count = validated_data['duration_count']
            
            if duration_type == 'daily':
                end_date = start_date + timedelta(days=duration_count)
            elif duration_type == 'weekly':
                end_date = start_date + timedelta(weeks=duration_count)
            elif duration_type == 'monthly':
                end_date = start_date + timedelta(days=30 * duration_count)
            
            # Delete existing boost if any (replace with new one)
            if hasattr(listing, 'listing_boost'):
                listing.listing_boost.delete()
            
            # Create boost
            boost = ListingBoost.objects.create(
                listing=listing,
                dealer=dealer,
                start_date=start_date,
                end_date=end_date,
                duration_type=duration_type,
                duration_count=duration_count,
                amount_paid=validated_data['total_cost'],
                payment_status='pending'
            )
            
            response_data = {
                'error': False,
                'message': 'Boost created successfully. Please proceed with payment.',
                'data': {
                    'boost_id': boost.id,
                    'boost_uuid': str(boost.uuid),
                    'total_cost': str(boost.amount_paid),
                    'formatted_cost': boost.formatted_amount,
                    'duration_type': duration_type,
                    'duration_count': duration_count,
                    'start_date': str(start_date),
                    'end_date': str(end_date),
                    'payment_status': 'pending',
                    'listing': ListingSerializer(listing, context={'request': request}).data
                }
            }
            
            return Response(response_data, 200)
            
        except Dealership.DoesNotExist:
            return Response({
                'error': True,
                'message': 'Dealership profile not found'
            }, 404)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'error': True,
                'message': f'An error occurred: {str(e)}'
            }, 500)
    
    @swagger_auto_schema(
        operation_summary="Cancel/Delete a boost",
        operation_description=(
            "Cancel or delete a boost for a listing.\n\n"
            "**Note:** Only pending or inactive boosts can be deleted. "
            "Active paid boosts cannot be deleted (contact support for refunds)."
        ),
        responses={
            200: openapi.Response(
                description='Boost deleted successfully',
                examples={
                    'application/json': {
                        'error': False,
                        'message': 'Boost cancelled successfully'
                    }
                }
            ),
            400: openapi.Response(description='Cannot delete active boost'),
            404: openapi.Response(description='Boost not found')
        },
        tags=['Boost']
    )
    def delete(self, request, listing_id):
        from ..models import ListingBoost
        
        try:
            dealer = Dealership.objects.get(user=request.user)
            listing = dealer.listings.get(uuid=listing_id)
            
            if not hasattr(listing, 'listing_boost'):
                return Response({
                    'error': True,
                    'message': 'No boost found for this listing'
                }, 404)
            
            boost = listing.listing_boost
            
            # Don't allow deletion of active paid boosts
            if boost.payment_status == 'paid' and boost.is_active():
                return Response({
                    'error': True,
                    'message': 'Cannot delete an active paid boost. Please contact support for refunds.'
                }, 400)
            
            boost.delete()
            
            return Response({
                'error': False,
                'message': 'Boost cancelled successfully'
            }, 200)
            
        except Dealership.DoesNotExist:
            return Response({
                'error': True,
                'message': 'Dealership profile not found'
            }, 404)
        except Listing.DoesNotExist:
            return Response({
                'error': True,
                'message': 'Listing not found or does not belong to you'
            }, 404)


class ConfirmBoostPaymentView(APIView):
    """View for confirming boost payment"""
    allowed_methods = ['POST']
    permission_classes = [IsAuthenticated, IsDealerOrStaff]
    authentication_classes = [JWTAuthentication, TokenAuthentication, SessionAuthentication]
    
    @swagger_auto_schema(
        operation_summary="Confirm boost payment",
        operation_description=(
            "Confirm payment for a boost after successful payment processing.\n\n"
            "This endpoint should be called after payment is verified through your payment gateway."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['boost_id', 'payment_reference'],
            properties={
                'boost_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=123),
                'payment_reference': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example='PAY-123456789',
                    description='Payment reference from payment gateway'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description='Payment confirmed',
                examples={
                    'application/json': {
                        'error': False,
                        'message': 'Payment confirmed. Your listing is now boosted!',
                        'data': {
                            'boost_id': 123,
                            'active': True,
                            'days_remaining': 14
                        }
                    }
                }
            ),
            400: openapi.Response(description='Invalid payment or boost'),
            404: openapi.Response(description='Boost not found')
        },
        tags=['Boost']
    )
    def post(self, request):
        from .serializers import ListingBoostSerializer
        from ..models import ListingBoost
        
        try:
            dealer = Dealership.objects.get(user=request.user)
            boost_id = request.data.get('boost_id')
            payment_reference = request.data.get('payment_reference')
            
            if not boost_id or not payment_reference:
                return Response({
                    'error': True,
                    'message': 'boost_id and payment_reference are required'
                }, 400)
            
            boost = ListingBoost.objects.get(id=boost_id, dealer=dealer)
            
            if boost.payment_status == 'paid':
                return Response({
                    'error': True,
                    'message': 'Payment already confirmed for this boost'
                }, 400)
            
            # Update payment status
            boost.payment_status = 'paid'
            boost.payment_reference = payment_reference
            boost.save()  # This will auto-update active status
            
            return Response({
                'error': False,
                'message': 'Payment confirmed. Your listing is now boosted!',
                'data': ListingBoostSerializer(boost).data
            }, 200)
            
        except Dealership.DoesNotExist:
            return Response({
                'error': True,
                'message': 'Dealership profile not found'
            }, 404)
        except ListingBoost.DoesNotExist:
            return Response({
                'error': True,
                'message': 'Boost not found or does not belong to you'
            }, 404)
        except Exception as e:
            return Response({
                'error': True,
                'message': f'An error occurred: {str(e)}'
            }, 500)


class MyBoostsView(APIView):
    """View for listing all boosts for a dealer"""
    allowed_methods = ['GET']
    permission_classes = [IsAuthenticated, IsDealerOrStaff]
    authentication_classes = [JWTAuthentication, TokenAuthentication, SessionAuthentication]
    
    @swagger_auto_schema(
        operation_summary="List all boosts",
        operation_description="Get all boosts (active and inactive) for the authenticated dealer",
        responses={
            200: openapi.Response(
                description='List of boosts',
                examples={
                    'application/json': {
                        'error': False,
                        'data': {
                            'active_boosts': [],
                            'inactive_boosts': [],
                            'total_active': 0,
                            'total_inactive': 0
                        }
                    }
                }
            )
        },
        tags=['Boost']
    )
    def get(self, request):
        from .serializers import ListingBoostSerializer
        from ..models import ListingBoost
        
        try:
            dealer = Dealership.objects.get(user=request.user)
            boosts = ListingBoost.objects.filter(dealer=dealer).order_by('-date_created')
            
            active_boosts = [b for b in boosts if b.is_active()]
            inactive_boosts = [b for b in boosts if not b.is_active()]
            
            data = {
                'error': False,
                'data': {
                    'active_boosts': ListingBoostSerializer(active_boosts, many=True).data,
                    'inactive_boosts': ListingBoostSerializer(inactive_boosts, many=True).data,
                    'total_active': len(active_boosts),
                    'total_inactive': len(inactive_boosts)
                }
            }
            return Response(data, 200)
            
        except Dealership.DoesNotExist:
            return Response({
                'error': True,
                'message': 'Dealership profile not found'
            }, 404)
