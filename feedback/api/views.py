from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404

from ..models import SupportTicket, Tag, TicketCategory
from .serializers import (
    SupportTicketSerializer,
    SupportTicketCreateSerializer,
    SupportTicketUpdateSerializer,
    TagSerializer,
    TicketCategorySerializer,
)
from chat.models import ChatRoom


class TicketPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class SupportTicketViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = TicketPagination
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_staff:
            # Staff can see all tickets or tickets assigned to them
            queryset = SupportTicket.objects.all()
            
            # Filter by assigned tickets
            if self.request.query_params.get('assigned_to_me') == 'true':
                queryset = queryset.filter(correspondents=user)
            
        else:
            # All authenticated users can see their own tickets
            if hasattr(user, 'customer'):
                queryset = SupportTicket.objects.filter(customer=user.customer)
            else:
                # For users without customer profile yet, show empty queryset
                # (they'll get one created when they create their first ticket)
                queryset = SupportTicket.objects.none()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by severity
        severity_filter = self.request.query_params.get('severity')
        if severity_filter:
            queryset = queryset.filter(severity_level=severity_filter)
        
        # Filter by category
        category_filter = self.request.query_params.get('category')
        if category_filter:
            queryset = queryset.filter(category__uuid=category_filter)
        
        # Filter overdue tickets
        if self.request.query_params.get('overdue') == 'true':
            queryset = [t for t in queryset if t.is_overdue]
        
        return queryset.select_related('customer', 'category', 'chat_room').prefetch_related('tags', 'correspondents')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SupportTicketCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SupportTicketUpdateSerializer
        return SupportTicketSerializer
    
    def create(self, request, *args, **kwargs):
        # Ensure user has a customer profile (create one if needed for dealers/other users)
        from accounts.models import Customer
        from django.db import IntegrityError
        import logging
        
        logger = logging.getLogger(__name__)
        
        if not hasattr(request.user, 'customer'):
            # Create a customer profile for non-customer users (dealers, mechanics, etc.)
            try:
                # Get phone number from dealership profile if exists, otherwise None
                phone_number = None
                if hasattr(request.user, 'dealership_profile'):
                    phone_number = request.user.dealership_profile.phone_number
                
                # Use get_or_create to avoid duplicate customer profiles
                customer, created = Customer.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'phone_number': phone_number,
                    }
                )
                if created:
                    logger.info(f"Created customer profile for user {request.user.email}")
            except IntegrityError as e:
                logger.warning(f"IntegrityError creating customer for {request.user.email}: {str(e)}")
                # If phone number is already taken, create without phone number
                customer, created = Customer.objects.get_or_create(
                    user=request.user,
                    defaults={'phone_number': None}
                )
            except Exception as e:
                logger.error(f"Error creating customer profile for {request.user.email}: {str(e)}")
                return Response(
                    {'error': 'Failed to create customer profile', 'detail': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            customer = request.user.customer
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()
        
        # Create a chat room for this ticket
        chat_room = ChatRoom.objects.create(room_type='staff-chat')
        chat_room.members.add(request.user)
        ticket.chat_room = chat_room
        ticket.save()
        
        return Response(
            SupportTicketSerializer(ticket).data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        # Only staff can update tickets
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can update support tickets'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        # Only staff can update tickets
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can update support tickets'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        # Only staff can delete tickets
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can delete support tickets'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def assign_staff(self, request, pk=None):
        """Assign staff members to a ticket"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can assign correspondents'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        ticket = self.get_object()
        staff_ids = request.data.get('staff_ids', [])
        
        from accounts.models import Account
        staff_members = Account.objects.filter(id__in=staff_ids, is_staff=True)
        
        ticket.correspondents.add(*staff_members)
        
        # Add staff to chat room
        if ticket.chat_room:
            ticket.chat_room.members.add(*staff_members)
        
        return Response(
            SupportTicketSerializer(ticket).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def remove_staff(self, request, pk=None):
        """Remove staff members from a ticket"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can remove correspondents'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        ticket = self.get_object()
        staff_ids = request.data.get('staff_ids', [])
        
        from accounts.models import Account
        staff_members = Account.objects.filter(id__in=staff_ids, is_staff=True)
        
        ticket.correspondents.remove(*staff_members)
        
        # Remove staff from chat room
        if ticket.chat_room:
            ticket.chat_room.members.remove(*staff_members)
        
        return Response(
            SupportTicketSerializer(ticket).data,
            status=status.HTTP_200_OK
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_tags(request):
    """List all available tags"""
    tags = Tag.objects.all()
    serializer = TagSerializer(tags, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_tag(request):
    """Create a new tag (staff only)"""
    if not request.user.is_staff:
        return Response(
            {'error': 'Only staff can create tags'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = TagSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_categories(request):
    """List all ticket categories"""
    categories = TicketCategory.objects.all()
    serializer = TicketCategorySerializer(categories, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_category(request):
    """Create a new category (staff only)"""
    if not request.user.is_staff:
        return Response(
            {'error': 'Only staff can create categories'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = TicketCategorySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ticket_stats(request):
    """Get ticket statistics (staff only)"""
    if not request.user.is_staff:
        return Response(
            {'error': 'Only staff can view ticket statistics'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    tickets = SupportTicket.objects.all()
    
    stats = {
        'total': tickets.count(),
        'open': tickets.filter(status='open').count(),
        'in_progress': tickets.filter(status='in-progress').count(),
        'awaiting_user': tickets.filter(status='awaiting-user').count(),
        'resolved': tickets.filter(status='resolved').count(),
        'high_severity': tickets.filter(severity_level='high').count(),
        'moderate_severity': tickets.filter(severity_level='moderate').count(),
        'low_severity': tickets.filter(severity_level='low').count(),
        'overdue': len([t for t in tickets if t.is_overdue]),
    }
    
    return Response(stats)
