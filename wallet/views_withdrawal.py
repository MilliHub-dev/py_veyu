"""
Withdrawal request views for business accounts
"""
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from inspections.models_revenue import WithdrawalRequest
from .models import Wallet
from accounts.models import PayoutInformation
from .serializers import WithdrawalRequestSerializer, WithdrawalRequestCreateSerializer

logger = logging.getLogger(__name__)


class WithdrawalRequestListCreateView(APIView):
    """
    List withdrawal requests or create a new withdrawal request
    Only for business accounts (dealers/mechanics)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get user's withdrawal requests",
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status", type=openapi.TYPE_STRING),
            openapi.Parameter('limit', openapi.IN_QUERY, description="Number of requests to return", type=openapi.TYPE_INTEGER),
        ]
    )
    def get(self, request):
        """Get user's withdrawal requests"""
        try:
            # Check if user is a business account
            if not (hasattr(request.user, 'dealership') or hasattr(request.user, 'mechanic')):
                return Response({
                    'error': 'Only business accounts can request withdrawals'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get user's withdrawal requests
            requests_qs = WithdrawalRequest.objects.filter(
                user=request.user
            ).select_related(
                'wallet',
                'payout_info',
                'transaction',
                'reviewed_by'
            ).order_by('-date_created')
            
            # Apply filters
            status_filter = request.GET.get('status')
            if status_filter:
                requests_qs = requests_qs.filter(status=status_filter)
            
            # Pagination
            limit = int(request.GET.get('limit', 50))
            requests_qs = requests_qs[:limit]
            
            # Serialize
            serializer = WithdrawalRequestSerializer(requests_qs, many=True)
            
            # Get wallet info
            wallet = Wallet.objects.get(user=request.user)
            
            return Response({
                'success': True,
                'data': {
                    'wallet': {
                        'balance': float(wallet.balance),
                        'ledger_balance': float(wallet.ledger_balance),
                        'currency': wallet.currency
                    },
                    'withdrawal_requests': serializer.data,
                    'total_requests': requests_qs.count()
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting withdrawal requests: {str(e)}")
            return Response({
                'error': 'Failed to get withdrawal requests'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        operation_summary="Create a new withdrawal request",
        request_body=WithdrawalRequestCreateSerializer
    )
    def post(self, request):
        """Create a new withdrawal request"""
        try:
            # Check if user is a business account
            if not (hasattr(request.user, 'dealership') or hasattr(request.user, 'mechanic')):
                return Response({
                    'error': 'Only business accounts can request withdrawals'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get user's wallet
            wallet = get_object_or_404(Wallet, user=request.user)
            
            # Validate request data
            serializer = WithdrawalRequestCreateSerializer(
                data=request.data,
                context={'user': request.user, 'wallet': wallet}
            )
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Create withdrawal request
            withdrawal_request = serializer.save(
                user=request.user,
                wallet=wallet
            )
            
            # Serialize response
            response_serializer = WithdrawalRequestSerializer(withdrawal_request)
            
            return Response({
                'success': True,
                'data': response_serializer.data,
                'message': 'Withdrawal request submitted successfully. It will be reviewed by our team.'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating withdrawal request: {str(e)}")
            return Response({
                'error': 'Failed to create withdrawal request'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WithdrawalRequestDetailView(APIView):
    """
    Get details of a specific withdrawal request
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(operation_summary="Get withdrawal request details")
    def get(self, request, request_id):
        """Get withdrawal request details"""
        try:
            # Get withdrawal request
            withdrawal_request = get_object_or_404(
                WithdrawalRequest,
                id=request_id,
                user=request.user
            )
            
            # Serialize
            serializer = WithdrawalRequestSerializer(withdrawal_request)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error getting withdrawal request {request_id}: {str(e)}")
            return Response({
                'error': 'Failed to get withdrawal request'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_withdrawal_request(request, request_id):
    """
    Cancel a pending withdrawal request
    """
    try:
        # Get withdrawal request
        withdrawal_request = get_object_or_404(
            WithdrawalRequest,
            id=request_id,
            user=request.user
        )
        
        # Check if can be cancelled
        if withdrawal_request.status != 'pending':
            return Response({
                'error': f'Cannot cancel request with status: {withdrawal_request.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cancel request
        withdrawal_request.status = 'cancelled'
        withdrawal_request.save()
        
        return Response({
            'success': True,
            'message': 'Withdrawal request cancelled successfully'
        })
        
    except Exception as e:
        logger.error(f"Error cancelling withdrawal request {request_id}: {str(e)}")
        return Response({
            'error': 'Failed to cancel withdrawal request'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def withdrawal_statistics(request):
    """
    Get withdrawal statistics for the user
    """
    try:
        # Check if user is a business account
        if not (hasattr(request.user, 'dealership') or hasattr(request.user, 'mechanic')):
            return Response({
                'error': 'Only business accounts can view withdrawal statistics'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get user's withdrawal requests
        all_requests = WithdrawalRequest.objects.filter(user=request.user)
        
        # Calculate statistics
        from django.db.models import Sum, Count
        
        total_requests = all_requests.count()
        pending_requests = all_requests.filter(status='pending').count()
        approved_requests = all_requests.filter(status='approved').count()
        completed_requests = all_requests.filter(status='completed').count()
        rejected_requests = all_requests.filter(status='rejected').count()
        
        total_withdrawn = all_requests.filter(
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        pending_amount = all_requests.filter(
            status__in=['pending', 'approved', 'processing']
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Get wallet info
        wallet = Wallet.objects.get(user=request.user)
        
        # Recent requests
        recent_requests = all_requests.order_by('-date_created')[:5]
        recent_serializer = WithdrawalRequestSerializer(recent_requests, many=True)
        
        return Response({
            'success': True,
            'data': {
                'wallet': {
                    'balance': float(wallet.balance),
                    'ledger_balance': float(wallet.ledger_balance),
                    'currency': wallet.currency
                },
                'statistics': {
                    'total_requests': total_requests,
                    'pending_requests': pending_requests,
                    'approved_requests': approved_requests,
                    'completed_requests': completed_requests,
                    'rejected_requests': rejected_requests,
                    'total_withdrawn': float(total_withdrawn),
                    'pending_amount': float(pending_amount)
                },
                'recent_requests': recent_serializer.data
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting withdrawal statistics: {str(e)}")
        return Response({
            'error': 'Failed to get withdrawal statistics'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_account_number(request):
    """
    Verify bank account details with Paystack
    This should be called from frontend before submitting withdrawal request
    """
    try:
        from wallet.gateway.payment_adapter import PaystackAdapter
        
        # Check if user is a business account
        if not (hasattr(request.user, 'dealership') or hasattr(request.user, 'mechanic')):
            return Response({
                'error': 'Only business accounts can verify account details'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get account details from request
        account_number = request.data.get('account_number')
        bank_code = request.data.get('bank_code')
        
        if not account_number or not bank_code:
            return Response({
                'error': 'account_number and bank_code are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify with Paystack
        gateway = PaystackAdapter()
        
        try:
            # Call Paystack resolve account endpoint
            verification_result = gateway.resolve_account(account_number, bank_code)
            
            if verification_result.get('status'):
                return Response({
                    'success': True,
                    'verified': True,
                    'data': {
                        'account_name': verification_result.get('data', {}).get('account_name'),
                        'account_number': verification_result.get('data', {}).get('account_number'),
                        'bank_code': bank_code
                    },
                    'message': 'Account verified successfully'
                })
            else:
                return Response({
                    'success': False,
                    'verified': False,
                    'error': 'Account verification failed',
                    'message': verification_result.get('message', 'Unable to verify account')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Paystack verification error: {str(e)}")
            return Response({
                'success': False,
                'verified': False,
                'error': 'Verification service unavailable',
                'message': 'Unable to verify account at this time. Please try again later.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
    except Exception as e:
        logger.error(f"Error verifying account: {str(e)}")
        return Response({
            'error': 'Failed to verify account'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
