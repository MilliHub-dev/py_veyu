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
)
from ..models import (
    Vehicle,
    Listing,
    Order,
    CarRental,
)
from rest_framework.viewsets import ModelViewSet

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


# NOT DONE
class CreateVehicleView(CreateAPIView):
    allowed_methods = ['POST']
    permission_classes = [IsAuthenticatedOrReadOnly,]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

    def post(self, request, *args, **kwargs):
        serializer = VehicleSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Vehicle created successfully'}, status=status.HTTP_201_CREATED)
        
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
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        vehicle = self.get_object()
        self.perform_destroy(vehicle)
        return Response(status=status.HTTP_204_NO_CONTENT)

class AvailableForRentView(ListAPIView):
    allowed_methods = ['GET']
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    
    queryset = Vehicle.objects.filter(available=True, for_sale=False, current_rental=None)

class BookCarRentalView(CreateAPIView):
    allowed_methods = ['POST']
    permission_classes = [IsAuthenticated, IsAgentOrStaff]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    serializer_class = BookCarRentalSerializer
    queryset = Order.objects.all()

    def perform_create(self, serializer):
        order_items = serializer.validated_data.get('order_items', [])

        # Calculate the sub_total by summing the rental_price of all items
        sub_total = sum(float(item.rental_price) for item in order_items)
        serializer.save(customer=self.request.user.customer, sub_total=sub_total)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            'message': 'Car rental successfully booked',
            'order': response.data
        })

class AvailableForRentDetailView(RetrieveUpdateDestroyAPIView):
    allowed_methods = ['GET', 'PUT', 'DELETE']
    permission_classes = [IsAuthenticatedOrReadOnly,]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    queryset = Vehicle.objects.filter(available=True, for_sale=False, current_rental=None)
    serializer_class = VehicleSerializer
    lookup_field = 'uuid'

# English or spanish 😂🫴