import logging
from typing import Dict, Any
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authentication import TokenAuthentication
from dj_rest_auth.jwt_auth import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth import get_user_model
from utils.otp_security import otp_security_manager
from utils.otp_manager import otp_manager

logger = logging.getLogger(__name__)
User = get_user_model()

class OTPSecurityStatusView(APIView):
    """
    Get OTP security status for a user or system-wide statistics.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, JWTAuthentication]
    
    @swagger_auto_schema(
        operation_summary="Get OTP Security Status",
        operation_description=(
            "Get comprehensive OTP security status including:\n"
            "- Failed attempt counts\n"
            "- Lockout status\n"
            "- Audit log entries\n"
            "- Suspicious activity flags\n\n"
            "**Admin users** can check status for any user by providing user_id.\n"
            "**Regular users** can only check their own status."
        ),
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_QUERY,
                description='User ID to check (admin only)',
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'channel',
                openapi.IN_QUERY,
                description='OTP channel to check (email/sms)',
                type=openapi.TYPE_STRING,
                enum=['email', 'sms'],
                required=False
            ),
            openapi.Parameter(
                'include_audit_log',
                openapi.IN_QUERY,
                description='Include recent audit log entries',
                type=openapi.TYPE_BOOLEAN,
                default=False
            )
        ],
        responses={
            200: openapi.Response(
                description="Security status retrieved successfully",
                examples={
                    "application/json": {
                        "user_id": 123,
                        "channels": {
                            "email": {
                                "locked_out": False,
                                "failed_attempts": {
                                    "hour_count": 2,
                                    "day_count": 5,
                                    "hour_limit": 10,
                                    "day_limit": 50
                                },
                                "suspicious_activity": False,
                                "recent_audit_entries": 3
                            },
                            "sms": {
                                "locked_out": True,
                                "lockout_details": {
                                    "reason": "hourly_limit_exceeded",
                                    "expires_at": "2025-11-07T15:30:00Z",
                                    "remaining_seconds": 1800
                                },
                                "failed_attempts": {
                                    "hour_count": 10,
                                    "day_count": 15,
                                    "hour_limit": 10,
                                    "day_limit": 50
                                },
                                "suspicious_activity": False,
                                "recent_audit_entries": 8
                            }
                        },
                        "overall_status": "locked_out",
                        "alerts": ["SMS channel is locked out until 2025-11-07T15:30:00Z"]
                    }
                }
            ),
            403: "Permission denied",
            404: "User not found"
        },
        tags=['OTP Security']
    )
    def get(self, request):
        """Get OTP security status."""
        try:
            # Get parameters
            user_id = request.GET.get('user_id')
            channel = request.GET.get('channel')
            include_audit_log = request.GET.get('include_audit_log', 'false').lower() == 'true'
            
            # Determine target user
            if user_id:
                # Admin check
                if not request.user.is_staff and not request.user.is_superuser:
                    return Response({
                        'error': True,
                        'message': 'Permission denied. Only administrators can check other users.'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                try:
                    target_user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    return Response({
                        'error': True,
                        'message': 'User not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                target_user = request.user
            
            # Get security summary
            security_summary = otp_security_manager.get_security_summary(target_user.id)
            
            # Filter by channel if specified
            if channel and channel in security_summary['channels']:
                filtered_summary = {
                    'user_id': target_user.id,
                    'channel': channel,
                    'status': security_summary['channels'][channel],
                    'overall_status': security_summary['overall_status']
                }
                
                # Add audit log if requested
                if include_audit_log:
                    audit_log = otp_security_manager.get_audit_log(target_user.id, channel, limit=20)
                    filtered_summary['audit_log'] = audit_log
                
                return Response(filtered_summary, status=status.HTTP_200_OK)
            
            # Add audit log if requested
            if include_audit_log:
                if channel:
                    security_summary['audit_log'] = otp_security_manager.get_audit_log(target_user.id, channel, limit=20)
                else:
                    security_summary['audit_log'] = {
                        'email': otp_security_manager.get_audit_log(target_user.id, 'email', limit=10),
                        'sms': otp_security_manager.get_audit_log(target_user.id, 'sms', limit=10)
                    }
            
            return Response(security_summary, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting OTP security status: {str(e)}", exc_info=True)
            return Response({
                'error': True,
                'message': 'An error occurred while retrieving security status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OTPSecurityActionsView(APIView):
    """
    Perform OTP security actions (admin only).
    """
    permission_classes = [IsAdminUser]
    authentication_classes = [TokenAuthentication, JWTAuthentication]
    
    @swagger_auto_schema(
        operation_summary="Reset OTP Security Status",
        operation_description=(
            "Reset OTP security status for a user. Available actions:\n"
            "- `reset_failed_attempts`: Reset failed attempt counters\n"
            "- `remove_lockout`: Remove current lockout\n"
            "- `clear_suspicious_flag`: Clear suspicious activity flag\n"
            "- `reset_all`: Reset all security status\n\n"
            "**Admin access required.**"
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['user_id', 'action'],
            properties={
                'user_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='User ID to reset'
                ),
                'action': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['reset_failed_attempts', 'remove_lockout', 'clear_suspicious_flag', 'reset_all'],
                    description='Action to perform'
                ),
                'channel': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['email', 'sms', 'all'],
                    description='Channel to reset (default: all)',
                    default='all'
                ),
                'reason': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Reason for the action (for audit log)'
                )
            }
        ),
        responses={
            200: "Action completed successfully",
            400: "Invalid request",
            403: "Permission denied",
            404: "User not found"
        },
        tags=['OTP Security']
    )
    def post(self, request):
        """Perform OTP security actions."""
        try:
            data = request.data
            user_id = data.get('user_id')
            action = data.get('action')
            channel = data.get('channel', 'all')
            reason = data.get('reason', f'Admin action by {request.user.email}')
            
            if not user_id or not action:
                return Response({
                    'error': True,
                    'message': 'user_id and action are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate user exists
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({
                    'error': True,
                    'message': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Determine channels to process
            channels_to_process = ['email', 'sms'] if channel == 'all' else [channel]
            
            results = {}
            
            for ch in channels_to_process:
                if action == 'reset_failed_attempts':
                    otp_security_manager.reset_failed_attempts(user_id, ch)
                    results[ch] = 'Failed attempts reset'
                    
                elif action == 'remove_lockout':
                    lockout_key = otp_security_manager._get_cache_key(
                        otp_security_manager.LOCKOUT_PREFIX, user_id, ch
                    )
                    from django.core.cache import cache
                    cache.delete(lockout_key)
                    results[ch] = 'Lockout removed'
                    
                elif action == 'clear_suspicious_flag':
                    suspicious_key = otp_security_manager._get_cache_key(
                        otp_security_manager.SUSPICIOUS_PREFIX, user_id, ch
                    )
                    from django.core.cache import cache
                    cache.delete(suspicious_key)
                    results[ch] = 'Suspicious flag cleared'
                    
                elif action == 'reset_all':
                    # Reset everything
                    otp_security_manager.reset_failed_attempts(user_id, ch)
                    
                    lockout_key = otp_security_manager._get_cache_key(
                        otp_security_manager.LOCKOUT_PREFIX, user_id, ch
                    )
                    suspicious_key = otp_security_manager._get_cache_key(
                        otp_security_manager.SUSPICIOUS_PREFIX, user_id, ch
                    )
                    
                    from django.core.cache import cache
                    cache.delete(lockout_key)
                    cache.delete(suspicious_key)
                    
                    results[ch] = 'All security status reset'
                    
                else:
                    return Response({
                        'error': True,
                        'message': f'Invalid action: {action}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Log the admin action
                otp_security_manager.log_otp_attempt(
                    user_id=user_id,
                    channel=ch,
                    action='admin_reset',
                    success=True,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    error_message=f'Admin action: {action} - {reason}'
                )
            
            logger.info(f"Admin {request.user.email} performed OTP security action '{action}' for user {user_id}")
            
            return Response({
                'error': False,
                'message': f'Action "{action}" completed successfully',
                'results': results,
                'user_id': user_id,
                'performed_by': request.user.email
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error performing OTP security action: {str(e)}", exc_info=True)
            return Response({
                'error': True,
                'message': 'An error occurred while performing the action'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OTPSystemStatusView(APIView):
    """
    Get system-wide OTP statistics and health status.
    """
    permission_classes = [IsAdminUser]
    authentication_classes = [TokenAuthentication, JWTAuthentication]
    
    @swagger_auto_schema(
        operation_summary="Get OTP System Status",
        operation_description=(
            "Get system-wide OTP statistics and health information including:\n"
            "- SMS provider status\n"
            "- Email configuration status\n"
            "- Recent system activity\n"
            "- Performance metrics\n\n"
            "**Admin access required.**"
        ),
        responses={
            200: "System status retrieved successfully",
            403: "Permission denied"
        },
        tags=['OTP Security']
    )
    def get(self, request):
        """Get system-wide OTP status."""
        try:
            from utils.sms_providers import sms_provider_manager
            from utils.mail import get_email_backend_health
            
            # Get SMS provider status
            sms_status = sms_provider_manager.get_provider_status()
            
            # Get email backend health
            email_status = get_email_backend_health()
            
            # Get basic system statistics (you could expand this)
            system_stats = {
                'sms_providers': sms_status,
                'email_backend': email_status,
                'security_features': {
                    'rate_limiting_enabled': True,
                    'lockout_protection_enabled': True,
                    'audit_logging_enabled': True,
                    'suspicious_activity_detection_enabled': True
                },
                'configuration': {
                    'max_failed_attempts_per_hour': otp_security_manager.MAX_FAILED_ATTEMPTS_PER_HOUR,
                    'max_failed_attempts_per_day': otp_security_manager.MAX_FAILED_ATTEMPTS_PER_DAY,
                    'lockout_duration_minutes': otp_security_manager.LOCKOUT_DURATION_MINUTES,
                    'suspicious_activity_threshold': otp_security_manager.SUSPICIOUS_ACTIVITY_THRESHOLD
                }
            }
            
            return Response(system_stats, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting OTP system status: {str(e)}", exc_info=True)
            return Response({
                'error': True,
                'message': 'An error occurred while retrieving system status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)