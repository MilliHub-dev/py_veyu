import os, json, base64
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

def django_date(date_str: str) -> str:
    """
    Converts a date string from 'DD/MM/YYYY' to 'YYYY-MM-DD'
    """
    try:
        dt = datetime.strptime(date_str, '%d/%m/%Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        raise ValueError('Invalid date format. Expected DD/MM/YYYY.')



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
            print("Inspection Data:", data)
            listing = Listing.objects.get(uuid=request.data['listing_id'])
            order = Order.objects.get(customer=request.user.customer, order_item=listing)
            order.order_status = 'awaiting-inspection'
            order.save()
            date = django_date(data['date'])
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



LETTERHEAD_PATH = os.path.join(settings.BASE_DIR, 'static', 'motaa/letterhead.pdf')
MEDIA_SIGNED_DIR = os.path.join(settings.MEDIA_ROOT, 'docs')

class CheckoutDocumentView(APIView):
    parser_classes = [JSONParser, MultiPartParser]

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
            f"This agreement is made between Motaa and {order.customer.user.name}.",
            f"Vehicle: {order.order_item.vehicle.name}",
            f"Amount: {order.sub_total}",
            f"Vehicle ID: {order.order_item.vehicle.uuid}",
            f"Dealership: {order.order_item.vehicle.dealer.business_name}",
            "",
            "1. The seller agrees to supply the goods as outlined in the order summary.",
            "2. The buyer agrees to remit payment as agreed upon.",
            "3. This contract is binding and subject to Motaa's terms of service.",
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
