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
)
from ..models import (
    Vehicle,
    Listing,
    Order,
    CarRental,
)


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

        vehicle = Vehicle.objects.get(uuid=data['vehicle_uuid'])
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






