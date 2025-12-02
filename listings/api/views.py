import os, json, base64
import requests
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
    # TestDriveRequestSerializer,
    # TradeInRequestSerializer,
    CompleteOrderSerializer,
    # OrderInspectionSerializer,
    # PurchaseOfferSerializer,
)
from ..models import (
    Vehicle,
    Listing,
    Order,
    RentalOrder,
    OrderInspection,
    PurchaseOffer,
    ListingBoost,
)
from accounts.api.serializers import (
    DealershipSerializer,
)
from accounts.models import (
    File,
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
from drf_yasg import openapi
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from wallet.models import Wallet
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from utils import OffsetPaginator
from utils.dispatch import (on_checkout_success, on_inspection_created)
from datetime import datetime
from django.conf import settings
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from django.views.decorators.csrf import csrf_exempt
from django.core.files import File as DjangoFile
from django.http import Http404
from django.core.files.storage import default_storage

# ===== OpenAPI Schemas for Listings =====

CarSchema = openapi.Schema(
    title='Car',
    type=openapi.TYPE_OBJECT,
    properties={
        'kind': openapi.Schema(type=openapi.TYPE_STRING, enum=['car']),
        'doors': openapi.Schema(type=openapi.TYPE_INTEGER),
        'seats': openapi.Schema(type=openapi.TYPE_INTEGER),
        'drivetrain': openapi.Schema(type=openapi.TYPE_STRING),
        'vin': openapi.Schema(type=openapi.TYPE_STRING),
    }
)

BoatSchema = openapi.Schema(
    title='Boat',
    type=openapi.TYPE_OBJECT,
    properties={
        'kind': openapi.Schema(type=openapi.TYPE_STRING, enum=['boat']),
        'hull_material': openapi.Schema(type=openapi.TYPE_STRING),
        'engine_count': openapi.Schema(type=openapi.TYPE_INTEGER),
        'propeller_type': openapi.Schema(type=openapi.TYPE_STRING),
        'length': openapi.Schema(type=openapi.TYPE_NUMBER),
        'beam_width': openapi.Schema(type=openapi.TYPE_NUMBER),
        'draft': openapi.Schema(type=openapi.TYPE_NUMBER),
    }
)

PlaneSchema = openapi.Schema(
    title='Plane',
    type=openapi.TYPE_OBJECT,
    properties={
        'kind': openapi.Schema(type=openapi.TYPE_STRING, enum=['plane']),
        'registration_number': openapi.Schema(type=openapi.TYPE_STRING),
        'engine_type': openapi.Schema(type=openapi.TYPE_STRING),
        'aircraft_type': openapi.Schema(type=openapi.TYPE_STRING),
        'max_altitude': openapi.Schema(type=openapi.TYPE_INTEGER),
        'wing_span': openapi.Schema(type=openapi.TYPE_NUMBER),
        'range': openapi.Schema(type=openapi.TYPE_INTEGER),
    }
)

BikeSchema = openapi.Schema(
    title='Bike',
    type=openapi.TYPE_OBJECT,
    properties={
        'kind': openapi.Schema(type=openapi.TYPE_STRING, enum=['bike']),
        'engine_capacity': openapi.Schema(type=openapi.TYPE_INTEGER),
        'bike_type': openapi.Schema(type=openapi.TYPE_STRING, description='cruiser|sport|touring|offroad'),
        'saddle_height': openapi.Schema(type=openapi.TYPE_NUMBER),
    }
)

VehicleOneOf = openapi.Schema(
    title='Vehicle',
    type=openapi.TYPE_OBJECT,
    oneOf=[CarSchema, BoatSchema, PlaneSchema, BikeSchema],
)

ListingSchema = openapi.Schema(
    title='Listing',
    type=openapi.TYPE_OBJECT,
    properties={
        'uuid': openapi.Schema(type=openapi.TYPE_STRING),
        'listing_type': openapi.Schema(type=openapi.TYPE_STRING),
        'price': openapi.Schema(type=openapi.TYPE_NUMBER),
        'vehicle': VehicleOneOf,
    }
)

PaginationSchema = openapi.Schema(
    title='Pagination',
    type=openapi.TYPE_OBJECT,
    properties={
        'offset': openapi.Schema(type=openapi.TYPE_INTEGER),
        'limit': openapi.Schema(type=openapi.TYPE_INTEGER),
        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
        'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
        'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
    }
)

EnvelopeListSchema = openapi.Schema(
    title='EnvelopeList',
    type=openapi.TYPE_OBJECT,
    properties={
        'error': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        'message': openapi.Schema(type=openapi.TYPE_STRING),
        'data': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'pagination': PaginationSchema,
                'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=ListingSchema),
            }
        )
    }
)

DetailEnvelopeSchema = openapi.Schema(
    title='EnvelopeDetail',
    type=openapi.TYPE_OBJECT,
    properties={
        'error': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        'message': openapi.Schema(type=openapi.TYPE_STRING),
        'data': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'listing': ListingSchema,
                'recommended': openapi.Schema(type=openapi.TYPE_ARRAY, items=ListingSchema),
            }
        )
    }
)

def django_date(date_str: str) -> str:
    """
    Converts a date string from 'DD/MM/YYYY' to 'YYYY-MM-DD'
    """
    try:
        dt = datetime.strptime(date_str, '%d/%m/%Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        raise ValueError('Invalid date format. Expected DD/MM/YYYY.')

# ... rest of your code ...

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

    @swagger_auto_schema(
        operation_summary="Search listings (sale and rental)",
        tags=["Listings"],
        manual_parameters=[
            openapi.Parameter('find', openapi.IN_QUERY, description='Search term for name/brand/model', type=openapi.TYPE_STRING),
            openapi.Parameter('brands', openapi.IN_QUERY, description='Comma-separated brands', type=openapi.TYPE_STRING),
            openapi.Parameter('transmission', openapi.IN_QUERY, description='Comma-separated transmission', type=openapi.TYPE_STRING),
            openapi.Parameter('fuel_system', openapi.IN_QUERY, description='Comma-separated fuel system', type=openapi.TYPE_STRING),
            openapi.Parameter('price', openapi.IN_QUERY, description='Price range min-max', type=openapi.TYPE_STRING),
        ],
        responses={200: EnvelopeListSchema}
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
                    'count': self.paginator.count,
                    'next': self.paginator.get_next_link(),
                    'previous': self.paginator.get_previous_link(),
                },
                'results': serializer.data
            }
        }
        return Response(data, 200)

class AllListingsView(ListAPIView):
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
    ).distinct()
    filter_backends = [DjangoFilterBackend,]
    filterset_class = CarRentalFilter
    pagination_class = OffsetPaginator

    @swagger_auto_schema(
        operation_summary="Get all active listings",
        tags=["Listings"],
        manual_parameters=[
            openapi.Parameter('ordering', openapi.IN_QUERY, description='Ordering field (e.g. -created_at)', type=openapi.TYPE_STRING),
        ],
        responses={200: EnvelopeListSchema}
    )
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        ordering = request.GET.get('ordering')
        if ordering:
            try:
                queryset = queryset.order_by(ordering)
            except Exception:
                pass
        queryset = self.paginate_queryset(queryset)
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

class FeaturedListingsView(ListAPIView):
    allowed_methods = ['GET']
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    queryset = Listing.objects.filter(
        approved=True,
        verified=True,
        vehicle__available=True,
        listing_boost__active=True,
        vehicle__dealer__verified_business=True,
        vehicle__dealer__verified_id=True,
    ).distinct()
    pagination_class = OffsetPaginator

    @swagger_auto_schema(
        operation_summary="Get featured listings",
        tags=["Listings"],
        responses={200: EnvelopeListSchema}
    )
    def get(self, request, *args, **kwargs):
        queryset = self.paginate_queryset(self.get_queryset())
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

    @swagger_auto_schema(
        operation_summary="Get car listings for rent",
        tags=["Listings"],
        manual_parameters=[
            openapi.Parameter('make', openapi.IN_QUERY, description='Comma-separated brands', type=openapi.TYPE_STRING),
            openapi.Parameter('transmission', openapi.IN_QUERY, description='Comma-separated transmission', type=openapi.TYPE_STRING),
            openapi.Parameter('fuel_system', openapi.IN_QUERY, description='Comma-separated fuel system', type=openapi.TYPE_STRING),
            openapi.Parameter('price', openapi.IN_QUERY, description='Price range min-max', type=openapi.TYPE_STRING),
        ],
        responses={200: EnvelopeListSchema}
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
                    'count': self.paginator.count,
                    'next': self.paginator.get_next_link(),
                    'previous': self.paginator.get_previous_link(),
                },
                'results': serializer.data
            }
        }
        return Response(data, 200)

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
        operation_summary="Get car listings for sale",
        tags=["Listings"],
        manual_parameters=[
            openapi.Parameter('brands', openapi.IN_QUERY, description='Comma-separated brands', type=openapi.TYPE_STRING),
            openapi.Parameter('transmission', openapi.IN_QUERY, description='Comma-separated transmission', type=openapi.TYPE_STRING),
            openapi.Parameter('fuel_system', openapi.IN_QUERY, description='Comma-separated fuel system', type=openapi.TYPE_STRING),
            openapi.Parameter('price', openapi.IN_QUERY, description='Price range min-max', type=openapi.TYPE_STRING),
        ],
        responses={200: EnvelopeListSchema}
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

class RentListingDetailView(RetrieveUpdateDestroyAPIView):
    allowed_methods = ['GET', 'PUT', 'DELETE']
    permission_classes = [IsAuthenticatedOrReadOnly]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    queryset = Listing.objects.filter(
        verified=True,
        approved=True,
        listing_type='rental',
        vehicle__available=True
    ).distinct()
    serializer_class = ListingSerializer
    lookup_field = 'uuid'

    @swagger_auto_schema(
        operation_summary="Get rental listing details",
        tags=["Listings"],
        responses={200: DetailEnvelopeSchema}
    )
    def get(self, request, *args, **kwargs):
        listing = Listing.objects.get(uuid=self.kwargs['uuid'])

        if not request.user in listing.viewers.all():
            listing.viewers.add(request.user,)
            listing.save()

        small_change = (decimal.Decimal(25/100) * listing.price)

        recommended = self.queryset.filter(
            Q(price__gte=(listing.price - small_change)) |
            Q(price__lte=(listing.price + small_change)) |
            Q(vehicle__brand__iexact=listing.vehicle.brand) |
            Q(payment_cycle__iexact=listing.payment_cycle)
            # Q(vehicle__dealer=listing.vehicle.dealer)
            # Q(price=listing.price) |
        ).exclude(uuid=listing.uuid).distinct()

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

class BuyListingDetailView(RetrieveAPIView):
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticated,]
    authentication_classes = [JWTAuthentication, TokenAuthentication, SessionAuthentication]
    allowed_methods = ['GET', 'POST']
    lookup_field = 'uuid'
    queryset = Listing.objects.filter(verified=True, approved=True, listing_type='sale').distinct()

    @swagger_auto_schema(
        operation_summary="Get sale listing details",
        tags=["Listings"],
        responses={200: DetailEnvelopeSchema}
    )
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


class MyListingsView(ListAPIView):
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticated]
    queryset = Listing.objects.filter(
        approved=True,
        verified=True,
        vehicle__available=True,
        vehicle__dealer__verified_business=True,
        vehicle__dealer__verified_id=True,
    ).distinct()

    def get(self, request, *args, **kwargs):
        scope = request.GET.get('scope', '')
        scope = scope.split(';') if scope else []
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
    serializer_class = DealershipSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid=None, slug=None):
        dealer = None
        if uuid:
            dealer = Dealership.objects.get(uuid=uuid)
        elif slug:
            dealer = Dealership.objects.get(slug=slug)
        else:
            raise Http404("Dealer not found")
        data = {
            'error': False,
            'data': DealershipSerializer(dealer, context={'request': request}).data
        }
        return Response(data, 200)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    queryset = Listing.objects.all()
    lookup_field = 'uuid'

    @swagger_auto_schema(
        operation_summary="Get checkout summary for a listing",
        tags=["Listings"],
    )
    def get(self, request, *args, **kwargs):
        from listings.models import PlatformFeeSettings
        from inspections.models import VehicleInspection
        
        listing = Listing.objects.get(uuid=kwargs['listingId'])
        
        # Get active fee settings
        fee_settings = PlatformFeeSettings.get_active_settings()
        
        # Calculate fees
        listing_price = float(listing.price) if listing.price else 0
        tax = fee_settings.calculate_tax(listing_price) if listing_price else 0
        inspection_fee = fee_settings.calculate_inspection_fee(listing_price) if listing_price else 0
        service_fee = fee_settings.calculate_service_fee(listing_price) if listing_price else 0
        
        # Calculate total
        total = listing_price + tax + inspection_fee + service_fee
        
        # Check inspection payment status for sale listings
        inspection_status = None
        if listing.listing_type == 'sale':
            try:
                customer = request.user.customer_profile
                paid_inspection = VehicleInspection.objects.filter(
                    vehicle=listing.vehicle,
                    customer=customer,
                    payment_status='paid'
                ).first()
                
                if paid_inspection:
                    inspection_status = {
                        'paid': True,
                        'inspection_id': paid_inspection.id,
                        'status': paid_inspection.status,
                        'can_proceed': True
                    }
                else:
                    inspection_status = {
                        'paid': False,
                        'inspection_id': None,
                        'status': None,
                        'can_proceed': False,
                        'message': 'Inspection payment required before checkout'
                    }
            except AttributeError:
                inspection_status = {
                    'paid': False,
                    'inspection_id': None,
                    'status': None,
                    'can_proceed': False,
                    'message': 'Customer profile required'
                }
        
        data = {
            'error': False,
            'listing_price': listing_price,
            'fees': {
                'tax': round(tax, 2),
                'inspection_fee': round(inspection_fee, 2),
                'service_fee': round(service_fee, 2),
            },
            'total': round(total, 2),
            'listing': ListingSerializer(listing, context={'request': request}).data,
            'inspection_status': inspection_status,
        }
        return Response(data)

    @swagger_auto_schema(
        operation_summary="Create order for a listing",
        tags=["Listings"],
    )
    def post(self, request, *args, **kwargs):
        data = request.data
        listing = Listing.objects.get(uuid=kwargs['listingId'])
        
        # Get customer profile - handle case where profile doesn't exist
        try:
            customer = request.user.customer_profile
        except AttributeError:
            return Response(
                {'error': 'Customer profile not found. Please complete your profile first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get payment_option with a sensible default
        payment_option = data.get('payment_option', 'pay-after-inspection')
        payment_reference = data.get('payment_reference')  # Paystack reference
        
        # CHECK IF INSPECTION FEE HAS BEEN PAID
        # For sale listings with pay-after-inspection option
        if listing.listing_type == 'sale' and payment_option == 'pay-after-inspection':
            from inspections.models import VehicleInspection
            import requests
            
            # If payment reference is provided, verify and create inspection payment
            if payment_reference:
                # Verify payment with Paystack
                paystack_secret = settings.PAYSTACK_SECRET_KEY
                headers = {
                    'Authorization': f'Bearer {paystack_secret}',
                    'Content-Type': 'application/json'
                }
                
                try:
                    verify_url = f'https://api.paystack.co/transaction/verify/{payment_reference}'
                    response = requests.get(verify_url, headers=headers)
                    response_data = response.json()
                    
                    if response_data.get('status') and response_data.get('data', {}).get('status') == 'success':
                        # Payment verified, create or update inspection
                        amount = response_data['data']['amount'] / 100  # Convert from kobo
                        
                        # Create transaction record first
                        from wallet.models import Transaction
                        
                        # Truncate fields to fit database constraints
                        sender_name = (request.user.name or request.user.email)[:50]
                        tx_reference = payment_reference[:40]
                        narration = f'Inspection payment for vehicle {listing.vehicle.name}'[:200]
                        
                        transaction, tx_created = Transaction.objects.get_or_create(
                            tx_ref=tx_reference,
                            defaults={
                                'sender': sender_name,
                                'recipient': 'Veyu',
                                'type': 'payment',
                                'source': 'bank',
                                'amount': amount,
                                'status': 'completed',
                                'narration': narration,
                            }
                        )
                        
                        # Get dealer and inspector
                        dealer = listing.vehicle.dealer
                        inspector = dealer.user if hasattr(dealer, 'user') else request.user
                        
                        # Get or create inspection
                        inspection, created = VehicleInspection.objects.get_or_create(
                            vehicle=listing.vehicle,
                            customer=customer,
                            defaults={
                                'dealer': dealer,
                                'inspector': inspector,
                                'inspection_type': 'pre_purchase',
                                'status': 'draft',
                                'payment_status': 'paid',
                                'payment_method': 'bank',
                                'payment_transaction': transaction,
                                'paid_at': transaction.date_created
                            }
                        )
                        
                        if not created and inspection.payment_status != 'paid':
                            inspection.payment_status = 'paid'
                            inspection.payment_method = 'bank'
                            inspection.payment_transaction = transaction
                            inspection.paid_at = transaction.date_created
                            inspection.save()
                        
                    else:
                        return Response({
                            'error': 'Payment verification failed',
                            'message': 'Could not verify your payment. Please try again or contact support.',
                        }, status=status.HTTP_402_PAYMENT_REQUIRED)
                        
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Payment verification error: {str(e)}", exc_info=True)
                    return Response({
                        'error': 'Payment verification error',
                        'message': f'Error verifying payment: {str(e)}',
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                # No payment reference provided, check if inspection was already paid
                import logging
                logger = logging.getLogger(__name__)
                
                # First check if there's a paid inspection
                paid_inspection = VehicleInspection.objects.filter(
                    vehicle=listing.vehicle,
                    customer=customer,
                    payment_status='paid'
                ).first()
                
                logger.info(f"Checking for paid inspection - Vehicle: {listing.vehicle.id}, Customer: {customer.id}")
                logger.info(f"Found paid inspection: {paid_inspection.id if paid_inspection else 'None'}")
                
                if not paid_inspection:
                    # Check if there's a recent successful transaction that might be for this inspection
                    from wallet.models import Transaction
                    from datetime import timedelta
                    from django.utils import timezone
                    
                    # Look for recent payments by email or name
                    recent_payment = Transaction.objects.filter(
                        Q(sender__icontains=request.user.email) | Q(sender__icontains=request.user.name),
                        type='payment',
                        status='completed',
                        date_created__gte=timezone.now() - timedelta(minutes=5)
                    ).order_by('-date_created').first()
                    
                    logger.info(f"Looking for recent payment for user: {request.user.email} / {request.user.name}")
                    logger.info(f"Found recent payment: {recent_payment.tx_ref if recent_payment else 'None'}")
                    
                    if recent_payment:
                        # Found a recent payment, create inspection record
                        logger.info(f"Found recent payment {recent_payment.tx_ref}, creating inspection record")
                        
                        # Get dealer from vehicle
                        dealer = listing.vehicle.dealer
                        
                        # Use a system account as inspector (or the dealer's account)
                        inspector = dealer.user if hasattr(dealer, 'user') else request.user
                        
                        paid_inspection = VehicleInspection.objects.create(
                            vehicle=listing.vehicle,
                            customer=customer,
                            dealer=dealer,
                            inspector=inspector,
                            inspection_type='pre_purchase',
                            status='draft',
                            payment_status='paid',
                            payment_method='bank',
                            payment_transaction=recent_payment,
                            paid_at=recent_payment.date_created
                        )
                        logger.info(f"Created inspection {paid_inspection.id} from recent payment")
                    else:
                        # No recent payment found, require payment
                        all_inspections = VehicleInspection.objects.filter(
                            vehicle=listing.vehicle,
                            customer=customer
                        )
                        logger.warning(f"No paid inspection found. Total inspections: {all_inspections.count()}")
                        for insp in all_inspections:
                            logger.warning(f"  - Inspection {insp.id}: status={insp.status}, payment_status={insp.payment_status}")
                        
                        return Response({
                            'error': 'Inspection payment required',
                            'message': 'You must pay for and complete a vehicle inspection before placing an order for this vehicle.',
                            'required_action': 'pay_inspection',
                            'vehicle_id': listing.vehicle.id,
                            'listing_id': str(listing.uuid)
                        }, status=status.HTTP_402_PAYMENT_REQUIRED)
                else:
                    logger.info(f"Paid inspection found: {paid_inspection.id}, proceeding with order creation")
        
        order = Order(
            payment_option=payment_option,
            customer=customer,
            order_type=listing.listing_type,
            order_item=listing,
            paid=True if payment_option == 'card' else False
        )
        order.save()
        listing.vehicle.available = False
        listing.vehicle.save()
        customer.orders.add(order,)
        listing.vehicle.dealer.orders.add(order,)
        customer.save()
        listing.vehicle.dealer.save()

        on_checkout_success.send(order, listing=listing, customer=customer,)
        # Send order confirmation email using the new template
        try:
            from accounts.utils.email_notifications import send_order_confirmation
            from decimal import Decimal
            
            order_details = {
                'order_number': f"ORD-{order.uuid}",
                'order_date': order.date_created.strftime("%B %d, %Y"),
                'customer_name': request.user.name or request.user.email,
                'order_status': 'confirmed',
                'order_items': [{
                    'name': listing.title,
                    'description': listing.vehicle.name,
                    'quantity': 1,
                    'price': str(order.sub_total)
                }],
                'subtotal': str(order.sub_total),
                'tax': str(Decimal('0.075') * order.sub_total) if order.sub_total else '0.00',
                'shipping': '0.00',
                'total': str(order.sub_total * Decimal('1.075')) if order.sub_total else '0.00',
                'shipping_address': order.shipping_address or 'Not specified',
                'billing_address': order.billing_address or 'Same as shipping',
                'tracking_number': order.tracking_number or 'Not available yet',
                'tracking_link': f"{settings.FRONTEND_URL}/orders/{order.uuid}/tracking" if hasattr(settings, 'FRONTEND_URL') else '#',
                'support_email': settings.DEFAULT_FROM_EMAIL,
                'order_details_link': f"{settings.FRONTEND_URL}/orders/{order.uuid}" if hasattr(settings, 'FRONTEND_URL') else '#'
            }
            
            send_order_confirmation(request.user, order_details)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send order confirmation email: {str(e)}", exc_info=True)
        return Response({'error': False, 'message': 'Your order was created', 'data': OrderSerializer(order).data}, 200)


class BookInspectionView(APIView):
    allowed_methods = ['POST']
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Book vehicle inspection",
        tags=["Listings"],
    )
    def post(self, request):
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # Get customer profile - handle case where profile doesn't exist
            try:
                customer = request.user.customer_profile
            except AttributeError:
                return Response(
                    {'error': 'Customer profile not found. Please complete your profile first.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            data = request.data
            logger.info(f"Received inspection booking data: {data}")
            
            # Validate required fields
            if 'listing_id' not in data:
                return Response(
                    {'error': 'listing_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Accept multiple field name variations for date
            date_value = data.get('date') or data.get('inspection_date') or data.get('scheduled_date')
            if not date_value:
                return Response(
                    {'error': 'date, inspection_date, or scheduled_date is required', 'received_fields': list(data.keys())},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Accept multiple field name variations for time
            time_value = data.get('time') or data.get('inspection_time') or data.get('scheduled_time')
            if not time_value:
                return Response(
                    {'error': 'time, inspection_time, or scheduled_time is required', 'received_fields': list(data.keys())},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            listing = Listing.objects.get(uuid=data['listing_id'])
            
            # Get the most recent order for this customer and listing
            order = Order.objects.filter(
                customer=customer, 
                order_item=listing
            ).order_by('-date_created').first()
            
            if not order:
                return Response(
                    {'error': 'No order found for this listing. Please create an order first.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            order.order_status = 'awaiting-inspection'
            order.save()
            date_str = django_date(date_value)
            time = time_value

            inspection = OrderInspection(
                order=order,
                customer=customer,
                inspection_date=date_str,
                inspection_time=time,
            )
            inspection.save()
            
            # Trigger inspection created signal for notification
            on_inspection_created.send(customer, date=date_str, time=time)
            
            # Send inspection scheduled email using the new template
            try:
                from accounts.utils.email_notifications import send_inspection_scheduled
                from datetime import datetime, time as dt_time
                
                # Parse the date string to a datetime object for formatting
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                except (ValueError, TypeError):
                    date_obj = datetime.now()
                
                # Parse the time string to a time object
                try:
                    inspection_time = datetime.strptime(time, "%H:%M").time()
                except (ValueError, TypeError):
                    inspection_time = dt_time(10, 0)  # Default to 10:00 AM if parsing fails
                
                inspection_details = {
                    'inspection_reference': f"INSP-{inspection.id}",
                    'inspection_date': date_obj.strftime("%A, %B %d, %Y"),
                    'inspection_time': inspection_time.strftime("%I:%M %p"),
                    'vehicle_name': inspection.order.order_item.vehicle.name,
                    'vehicle_year': getattr(inspection.order.order_item.vehicle, 'year', 'N/A'),
                    'vehicle_make': inspection.order.order_item.vehicle.brand,
                    'vehicle_model': inspection.order.order_item.vehicle.model or 'N/A',
                    'listing_title': inspection.order.order_item.title,
                    'location': inspection.order.order_item.vehicle.dealer.location.address if (hasattr(inspection.order.order_item.vehicle.dealer, 'location') and inspection.order.order_item.vehicle.dealer.location) else 'To be determined',
                    'contact_person': inspection.order.order_item.vehicle.dealer.contact_name if hasattr(inspection.order.order_item.vehicle.dealer, 'contact_name') else 'Dealership Representative',
                    'contact_phone': inspection.order.order_item.vehicle.dealer.phone_number if hasattr(inspection.order.order_item.vehicle.dealer, 'phone_number') else 'N/A',
                    'support_email': settings.DEFAULT_FROM_EMAIL,
                    'inspection_checklist': [
                        'Exterior condition and paint',
                        'Engine and mechanical components',
                        'Interior condition and electronics',
                        'Test drive (if applicable)',
                        'Document verification'
                    ],
                    'what_to_bring': [
                        'Valid driver\'s license',
                        'Proof of insurance (if test driving)',
                        'List of any specific concerns'
                    ]
                }
                
                send_inspection_scheduled(request.user, inspection_details)
                
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send inspection scheduled email: {str(e)}", exc_info=True)
                
            # Original email sending code (kept as fallback)
            try:
                from utils.mail import send_email
                send_email(
                    subject="Inspection Scheduled",
                    recipients=[request.user.email],
                    template="utils/templates/inspection_scheduled.html",
                    context={
                        "customer_name": request.user.first_name or request.user.email,
                        "listing_title": listing.title,
                        "vehicle_name": listing.vehicle.name,
                        "date": date_str,
                        "time": time,
                    }
                )
            except Exception:
                pass
            
            # Build inspection slip response
            slip_reference = f"INSP-{inspection.id}"
            inspection_slip = {
                'id': inspection.id,
                'slip_reference': slip_reference,
                'inspection_date': date_str,
                'inspection_time': time,
                'status': 'scheduled' if not inspection.completed else 'completed',
                'order_id': order.id,
                'customer': {
                    'id': customer.id,
                    'name': request.user.name or request.user.email,
                    'email': request.user.email,
                },
                'vehicle': {
                    'id': listing.vehicle.id,
                    'name': listing.vehicle.name,
                    'make': listing.vehicle.brand,
                    'model': listing.vehicle.model or 'N/A',
                    'year': getattr(listing.vehicle, 'year', 'N/A'),
                },
                'listing': {
                    'id': listing.id,
                    'uuid': str(listing.uuid),
                    'title': listing.title,
                },
                'dealer': {
                    'id': listing.vehicle.dealer.id,
                    'name': listing.vehicle.dealer.business_name or listing.vehicle.dealer.user.name,
                    'location': listing.vehicle.dealer.location.address if (hasattr(listing.vehicle.dealer, 'location') and listing.vehicle.dealer.location) else 'To be determined',
                    'contact_person': listing.vehicle.dealer.contact_name if hasattr(listing.vehicle.dealer, 'contact_name') else 'Dealership Representative',
                    'contact_phone': listing.vehicle.dealer.phone_number if hasattr(listing.vehicle.dealer, 'phone_number') else 'N/A',
                },
                'created_at': inspection.date_created.isoformat() if hasattr(inspection, 'date_created') else None,
            }
            
            return Response({
                'success': True,
                'message': 'Inspection Scheduled',
                'slip_reference': slip_reference,
                'inspection_slip': inspection_slip
            }, status=status.HTTP_200_OK)
        except KeyError as error:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Missing required field in inspection booking: {str(error)}", exc_info=True)
            logger.error(f"Received data: {request.data}")
            return Response({
                'error': True, 
                'message': f'Missing required field: {str(error)}',
                'received_fields': list(request.data.keys())
            }, 400)
        except Exception as error:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error booking inspection: {str(error)}", exc_info=True)
            return Response({'error': True, 'message': str(error)}, 500)

class CompleteOrderView(APIView):
    allowed_methods = ['POST']
    permission_classes = [IsAuthenticatedOrReadOnly,]
    serializer_class = CompleteOrderSerializer

    # @swagger_auto_schema(operation_summary="Endpoint to complete order")
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



LETTERHEAD_PATH = os.path.join(settings.BASE_DIR, 'static', 'veyu/letterhead.pdf')
MEDIA_SIGNED_DIR = os.path.join(settings.MEDIA_ROOT, 'docs')

class CheckoutDocumentView(APIView):
    parser_classes = [JSONParser, MultiPartParser]

    @swagger_auto_schema(
        operation_summary="Generate and fetch checkout document",
        tags=["Listings"],
    )
    def get(self, request):
        doc_type = request.GET.get('doc_type', 'order-slip')
        params = request.GET.dict()

        # Check if file exists already
        fname = f"{doc_type}_{params.get('order_id')}.pdf"
        file_path = os.path.join(MEDIA_SIGNED_DIR, fname)
        file_obj = None

        order = Order.objects.filter(order_item__uuid=params['order_id'])[0]
        if not os.path.exists(file_path):
            print("Creating new file...")
            text_lines = self.write_contract(doc_type=doc_type, order=order)
            final_pdf = self.build_document(text_lines)
            # os.makedirs(MEDIA_SIGNED_DIR, exist_ok=True)
            with open(file_path, 'wb') as file:
                file.write(final_pdf.getvalue())

            file_obj = File(name=fname, file=DjangoFile(default_storage.open(file_path)))
            file_obj.save()
        else:
            file_obj = File.objects.filter(file=f"docs/{fname}").first()
            print("Found Existing file...", file_obj.name)

        # if not file_obj:
        #     raise Http404("File record not found")

        return Response({
            'error': False,
            'message': 'Successfully generated your document',
            'data': {
                'file_id': str(file_obj.uuid),
                'url': request.build_absolute_uri(file_obj.file.url)
            }
        }, 200)

    def post(self, request):
        data = request.data
        file_id = data.get('file_id')
        signature = data.get('signature')

        try:
            pdf_file = File.objects.get(uuid=file_id)
        except File.DoesNotExist:
            raise Http404("Document not found")

        existing_path = pdf_file.file.path
        overlay = self.build_signature_overlay(signature)
        signed_pdf = self.append_signature(existing_path, overlay)

        with open(existing_path, 'wb') as f:
            f.write(signed_pdf.getvalue())

        return Response({
            'error': False,
            'message': 'Document signed successfully!',
            'data': {
                'file_id': str(pdf_file.uuid),
                'url': request.build_absolute_uri(pdf_file.file.url)
            }
        }, 200)

    def build_document(self, text_lines: list) -> BytesIO:
        content = BytesIO()
        pdf_canvas = canvas.Canvas(content, pagesize=letter)
        x_coord, y_coord = 65, 700

        for line in text_lines:
            pdf_canvas.drawString(x_coord, y_coord, line)
            y_coord -= 20

        pdf_canvas.showPage()
        pdf_canvas.save()
        content.seek(0)
        return self.append_signature(LETTERHEAD_PATH, content)

    def build_signature_overlay(self, signature_data: str) -> BytesIO:
        overlay = BytesIO()
        c = canvas.Canvas(overlay, pagesize=letter)
        if signature_data:
            sig_b64 = signature_data.split('data:image/png;base64,')[1]
            sig_img = base64.b64decode(sig_b64)
            sig_buf = BytesIO(sig_img)
            sig_reader = ImageReader(sig_buf)
            c.drawImage(sig_reader, 100, 200, width=200, height=100, mask='auto')
        c.showPage()
        c.save()
        overlay.seek(0)
        return overlay

    def append_signature(self, base_pdf_path: str, overlay_buf: BytesIO) -> BytesIO:
        base_pdf = PdfReader(open(base_pdf_path, 'rb'))
        overlay_pdf = PdfReader(overlay_buf)
        writer = PdfWriter()

        base_page = base_pdf.pages[0]
        overlay_page = overlay_pdf.pages[0]
        base_page.merge_page(overlay_page)
        writer.add_page(base_page)

        result = BytesIO()
        writer.write(result)
        result.seek(0)
        return result

    def write_contract(self, doc_type, order) -> list:
        if doc_type == 'order-slip':
            return self.write_order_contract(order)
        elif doc_type == 'inspection-slip':
            return self.write_inspection_contract(order)
        else:
            return ["Invalid document type"]

    def write_order_contract(self, order) -> list:
        return [
            f"ORDER AGREEMENT",
            "",
            f"This agreement is made between veyu and {order.customer.user.name}.",
            f"Vehicle: {order.order_item.vehicle.name}",
            f"Amount: {order.sub_total}",
            f"Vehicle ID: {order.order_item.vehicle.uuid}",
            f"Dealership: {order.order_item.vehicle.dealer.business_name}",
            "",
            "1. The seller agrees to supply the goods as outlined in the order summary.",
            "2. The buyer agrees to remit payment as agreed upon.",
            "3. This contract is binding and subject to veyu's terms of service.",
            "4. All disputes will be resolved under applicable local laws.",
            "",
            "Signed and agreed by both parties on the date above."
        ]

    def write_inspection_contract(self, order) -> list:
        return [
            f"VEHICLE INSPECTION AGREEMENT",
            "",
            f"This agreement confirms that {order.customer.user.name} has requested a vehicle inspection on {order.date_created}.",
            f"Vehicle: {order.order_item.vehicle.name}",
            f"Vehicle ID: {order.order_item.vehicle.uuid}",
            f"Dealership: {order.order_item.vehicle.dealer.business_name}",
            "",
            "1. The inspector will perform a comprehensive assessment of the vehicle.",
            "2. The client understands the inspection is non-invasive and based on visible/mechanical checks.",
            "3. This document does not constitute a warranty or certification of the vehicle's future condition.",
            "4. The client accepts the findings as-is at the date of inspection.",
            "",
            "Signed and agreed by both parties on the date above."
        ]


class UserOrdersView(ListAPIView):
    """
    Get all orders for the authenticated user
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = OffsetPaginator
    
    @swagger_auto_schema(
        operation_summary="Get user's orders",
        operation_description="Retrieve all orders placed by the authenticated user",
        tags=["Orders"],
    )
    def get(self, request):
        user = request.user
        
        # Get orders for the user based on their role
        if hasattr(user, 'customer'):
            orders = Order.objects.filter(customer=user.customer).order_by('-date_created')
        else:
            orders = Order.objects.filter(customer__user=user).order_by('-date_created')
        
        # Paginate results
        paginator = self.pagination_class()
        paginated_orders = paginator.paginate_queryset(orders, request)
        
        serializer = self.serializer_class(paginated_orders, many=True)
        
        return Response({
            'error': False,
            'message': 'Orders retrieved successfully',
            'data': serializer.data,
            'pagination': {
                'count': orders.count(),
                'next': paginator.get_next_link(),
                'previous': paginator.get_previous_link()
            }
        }, 200)



class CancelOrderView(APIView):
    """
    Cancel or delete an unpaid order
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Cancel an unpaid order",
        operation_description="Allows customers to cancel/delete their unpaid orders",
        tags=["Orders"],
    )
    def delete(self, request, order_id):
        try:
            # Get the order
            order = Order.objects.get(uuid=order_id)
            
            # Verify the order belongs to the requesting user
            if hasattr(request.user, 'customer'):
                if order.customer != request.user.customer:
                    return Response({
                        'error': True,
                        'message': 'You do not have permission to cancel this order'
                    }, 403)
            else:
                if order.customer.user != request.user:
                    return Response({
                        'error': True,
                        'message': 'You do not have permission to cancel this order'
                    }, 403)
            
            # Check if order is already paid
            if order.paid:
                return Response({
                    'error': True,
                    'message': 'Cannot cancel a paid order. Please contact support for refunds.'
                }, 400)
            
            # Check if order status allows cancellation
            if order.order_status in ['completed', 'expired']:
                return Response({
                    'error': True,
                    'message': f'Cannot cancel an order with status: {order.get_order_status_display()}'
                }, 400)
            
            # Delete the order
            order_number = f"ORD-{order.uuid}"
            order.delete()
            
            return Response({
                'error': False,
                'message': f'Order {order_number} has been cancelled successfully'
            }, 200)
            
        except Order.DoesNotExist:
            return Response({
                'error': True,
                'message': 'Order not found'
            }, 404)
        except Exception as e:
            return Response({
                'error': True,
                'message': f'Failed to cancel order: {str(e)}'
            }, 500)
