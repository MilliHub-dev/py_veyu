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
    parser_classes = [MultiPartParser, JSONParser]
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
            "title, brand, model, condition, transmission, fuel_system, drivetrain, seats, doors, vin, listing_type, price.\n"
            "For rental listings, payment_cycle is required."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[
                'action'
            ],
            properties={
                'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['create-listing','upload-images','publish-listing'], example='create-listing'),
                'title': openapi.Schema(type=openapi.TYPE_STRING, example='2020 Toyota Camry XLE'),
                'brand': openapi.Schema(type=openapi.TYPE_STRING, example='Toyota'),
                'model': openapi.Schema(type=openapi.TYPE_STRING, example='Camry'),
                'condition': openapi.Schema(type=openapi.TYPE_STRING, enum=['new','used-foreign','used-local'], example='used-foreign'),
                'transmission': openapi.Schema(type=openapi.TYPE_STRING, enum=['auto','manual'], example='auto'),
                'fuel_system': openapi.Schema(type=openapi.TYPE_STRING, enum=['diesel','electric','petrol','hybrid'], example='petrol'),
                'drivetrain': openapi.Schema(type=openapi.TYPE_STRING, enum=['4WD','AWD','FWD','RWD'], example='FWD'),
                'seats': openapi.Schema(type=openapi.TYPE_INTEGER, example=5),
                'doors': openapi.Schema(type=openapi.TYPE_INTEGER, example=4),
                'vin': openapi.Schema(type=openapi.TYPE_STRING, example='1HGBH41JXMN109186'),
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
                # Validate required fields
                required_fields = ['title', 'brand', 'model', 'condition',
                                   'transmission', 'fuel_system', 'drivetrain', 'seats', 'doors', 
                                   'vin', 'listing_type', 'price']
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
                
                # Create Car instance (not Vehicle) since it has the additional fields
                vehicle = Car(
                    name = data['title'],
                    dealer=dealer,
                    color = data.get('color', 'None'),
                    brand = data['brand'],
                    model = data['model'],
                    condition = data['condition'],
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
                        'drivetrain': openapi.Schema(type=openapi.TYPE_STRING, enum=['4WD','AWD','FWD','RWD']),
                        'seats': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'doors': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'vin': openapi.Schema(type=openapi.TYPE_STRING),
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

                vehicle.name = data['title']
                vehicle.model = data['vehicle']['model']
                vehicle.color = data['vehicle'].get('color', 'None')
                vehicle.brand = data['vehicle']['brand']
                vehicle.condition = data['vehicle']['condition']
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
    allowed_methods = ['PUT', 'POST', 'GET']
    permission_classes = [IsAuthenticated, IsDealerOrStaff]
    parser_classes = [MultiPartParser, JSONParser]

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
            "Update dealership profile fields. For logo upload, send multipart/form-data with 'logo' field.\n\n"
            "**Logo Upload**: Upload business logo using the 'logo' field.\n"
            "**Response**: Returns updated dealership profile including logo URL."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['business_name','about','headline','services','contact_phone','contact_email'],
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
            "Update dealership profile fields. For logo upload, send multipart/form-data with 'logo' field."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['business_name','about','headline','services','contact_phone','contact_email'],
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

            # Validate required fields first
            required_fields = ['business_name', 'about', 'headline', 'services', 'contact_phone', 'contact_email']
            missing_fields = [field for field in required_fields if field not in data or not data.get(field)]
            
            if missing_fields:
                return Response({
                    'error': True,
                    'message': 'Missing required fields',
                    'details': {
                        'field_errors': {
                            field: [f'{field.replace("_", " ").title()} is required'] for field in missing_fields
                        }
                    }
                }, status=400)

            # Parse services if it's a JSON string (from FormData)
            import json
            services = data['services']
            if isinstance(services, str):
                try:
                    services = json.loads(services)
                    logger.debug(f"Parsed services from JSON string: {services}")
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse services JSON: {services}")
                    return Response({
                        'error': True,
                        'message': 'Invalid services format. Must be a valid JSON array.',
                    }, status=400)
            
            # Ensure services is always a list
            if not isinstance(services, list):
                # If it's a single string, wrap it in a list
                services = [services] if services else []
                logger.debug(f"Converted single service to list: {services}")
            
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
                
                # Update dealer profile fields
                # Handle logo upload
                logo_file = request.FILES.get('logo') or data.get('logo')
                if logo_file:
                    logger.info(f"Logo file detected for {dealer.business_name}: {logo_file}")
                    logger.info(f"Logo file type: {type(logo_file)}, size: {getattr(logo_file, 'size', 'N/A')}")
                    dealer.logo = logo_file
                else:
                    logger.info(f"No logo file in request. FILES keys: {list(request.FILES.keys())}, DATA keys: {list(data.keys())}")
                
                dealer.business_name = data['business_name']
                dealer.about = data['about']
                dealer.slug = data.get('slug', None)
                dealer.headline = data['headline']
                
                # Apply service mappings from processor
                dealer.offers_purchase = service_updates['offers_purchase']
                dealer.offers_rental = service_updates['offers_rental']
                dealer.offers_drivers = service_updates['offers_drivers']
                dealer.offers_trade_in = service_updates['offers_trade_in']
                
                # Handle extended services if the field exists
                if hasattr(dealer, 'extended_services'):
                    dealer.extended_services = service_updates['extended_services']
                
                dealer.contact_phone = data['contact_phone']
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
                mapped_services = sum([
                    dealer.offers_purchase,
                    dealer.offers_rental, 
                    dealer.offers_drivers,
                    dealer.offers_trade_in
                ])
                extended_count = len(service_updates.get('extended_services', []))
                logger.info(f"Successfully updated dealership {dealer.business_name}: {mapped_services} core services, {extended_count} extended services")
                
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
            logger.error(f"Missing required field in dealership settings update: {str(e)}")
            field_name = str(e).strip("'\"")
            return Response({
                'error': True,
                'message': f'Missing required field: {field_name}',
                'details': {
                    'field_errors': {
                        field_name: [f'{field_name.replace("_", " ").title()} is required']
                    },
                    'error_code': 'MISSING_FIELD'
                }
            }, status=400)
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


