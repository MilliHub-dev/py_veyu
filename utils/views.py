import hashlib, hmac, json, os, uuid, base64
from django.shortcuts import render
from django.conf import settings
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.mail import EmailMessage
from django.views.generic import TemplateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.html import escape
from django.utils import timezone
from django.db.models import Q
import re
import logging
from utils.mail import send_email, validate_email_configuration, test_smtp_connection, get_email_backend_health, process_email_queue
from utils.database_utils import DatabaseHealthChecker
from utils.error_handlers import handle_api_exception
from utils.auth_decorators import admin_required
from utils.log_service import LogFileService, LogParser
from utils.exceptions import VeyuException, APIError, ErrorCodes
from utils.log_security import security_logger, get_request_metadata


@csrf_exempt
@api_view(['POST'])
def email_relay(request):
    data = request.data
    template_name = data['template_name']
    recepients = data['recipients']
    context=data['context']
    subject=data['subject']


    try:
        send_email(
            subject=subject,
            recipients=recipients,
            template=template_name,
            context=context
        )
    except Exception as error:
        print("Error Sending email", error)
        # send an email delivery error report log
        # to the main server



    return Response(200)


def index_view(request, **kwargs):
    try:
        temp = kwargs.get('template', 'welcome_email')
        print("template", temp)
        template = settings.BASE_DIR / f'utils/templates/{temp}.html'
        return render(request, template, {'user': request.user})
    except Exception as error:
        print("Error", error)
        raise error


def chat_view(request, room_name):
    template = settings.BASE_DIR / 'feedback/templates/chat.html'
    return render(request, template, {'user': request.user, 'room_name': room_name})


@csrf_exempt
@api_view(['POST'])
def email_webhook_receiver(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    signature = request.headers.get('X-Veyu-Signature')
    if not signature:
        return JsonResponse({'error': 'Missing signature'}, status=400)

    raw_body = request.body
    expected_signature = hmac.new(
        os.environ.get("VEYU_EMAIL_HMAC_SECRET", None).encode(),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        return JsonResponse({'error': 'Invalid signature'}, status=403)

    try:
        payload = json.loads(raw_body)
        email = EmailMessage(
            subject=payload['subject'],
            body=payload['body'],
            from_email=payload['from_email'],
            to=payload.get('to', []),
            cc=payload.get('cc', []),
            bcc=payload.get('bcc', []),
        )

        # Attach files if present
        for attachment in payload.get('attachments', []):
            content = attachment['content']
            filename = attachment['filename']
            mimetype = attachment.get('mimetype', 'application/octet-stream')
            email.attach(filename, content, mimetype)

        email.send()
        return JsonResponse({'error': False, 'message': 'Email sent successfully'})

    except Exception as e:
        return JsonResponse({'error': True, 'message':str(e)}, status=500)


@csrf_exempt
@api_view(['POST'])
def payment_webhook(request, **kwargs):
    """
    Paystack webhook handler for processing payment events.
    Handles: charge.success, transfer.success, transfer.failed, transfer.reversed
    """
    from wallet.models import Wallet, Transaction
    from inspections.models import VehicleInspection
    from listings.models import Order
    from bookings.models import ServiceBooking
    from django.contrib.auth import get_user_model
    from utils.mail import send_email
    
    User = get_user_model()
    
    # Paystack webhook secret key
    secret = os.environ.get("PAYSTACK_SECRET_KEY", None)
    if not secret:
        logging.error("PAYSTACK_SECRET_KEY not configured")
        return Response({'detail': 'Webhook configuration error'}, status=500)
    
    secret = secret.encode()

    # Get the signature from the header
    signature = request.META.get('HTTP_X_PAYSTACK_SIGNATURE')
    if not signature:
        logging.warning("Webhook received without signature")
        return Response({'detail': 'Signature missing'}, status=400)

    # Get request body and verify signature
    payload = request.body
    computed_signature = hmac.new(secret, payload, hashlib.sha512).hexdigest()

    if not hmac.compare_digest(computed_signature, signature):
        logging.warning("Invalid webhook signature received")
        return Response({'detail': 'Invalid signature'}, status=400)

    # Decode and handle event
    try:
        event = json.loads(payload)
        event_type = event.get('event')
        data = event.get('data', {})
        
        logging.info(f"Processing Paystack webhook: {event_type}")
        
        # Handle successful charge/payment
        if event_type == 'charge.success':
            reference = data.get('reference')
            amount = data.get('amount', 0) / 100  # Convert from kobo to naira
            customer_email = data.get('customer', {}).get('email')
            metadata = data.get('metadata', {})
            
            # Get payment purpose from metadata
            purpose = metadata.get('purpose')  # 'wallet_deposit', 'inspection', 'order', 'booking'
            related_id = metadata.get('related_id')
            user_id = metadata.get('user_id')
            
            try:
                user = User.objects.get(id=user_id) if user_id else User.objects.get(email=customer_email)
                wallet = Wallet.objects.get(user=user)
                
                # Check if transaction already exists
                existing_tx = Transaction.objects.filter(tx_ref=reference).first()
                if existing_tx:
                    logging.info(f"Transaction {reference} already processed")
                    return Response({'status': 'already_processed'}, status=200)
                
                # Handle different payment purposes
                if purpose == 'wallet_deposit':
                    # Wallet top-up
                    transaction = Transaction.objects.create(
                        sender=user.name,
                        recipient_wallet=wallet,
                        type='deposit',
                        source='bank',
                        amount=amount,
                        tx_ref=reference,
                        status='completed',
                        narration=f'Wallet deposit via Paystack'
                    )
                    wallet.ledger_balance += amount
                    wallet.transactions.add(transaction)
                    wallet.save()
                    
                    # Send notification
                    send_email(
                        subject='Wallet Deposit Successful',
                        recipients=[user.email],
                        template='wallet_deposit_success',
                        context={
                            'user': user,
                            'amount': amount,
                            'balance': wallet.balance,
                            'reference': reference
                        }
                    )
                    
                elif purpose == 'inspection':
                    # Inspection payment
                    try:
                        inspection = VehicleInspection.objects.get(id=related_id)
                        transaction = Transaction.objects.create(
                            sender=user.get_full_name() or user.email,
                            recipient='Veyu',
                            type='payment',
                            source='bank',
                            amount=amount,
                            tx_ref=reference,
                            status='completed',
                            narration=f'Inspection payment for #{inspection.id}',
                            related_inspection=inspection
                        )
                        
                        # Update inspection payment status
                        inspection.mark_paid(transaction, payment_method='bank')
                        
                        # Send notification
                        send_email(
                            subject='Inspection Payment Confirmed',
                            recipients=[user.email],
                            template='inspection_payment_success',
                            context={
                                'user': user,
                                'inspection': inspection,
                                'amount': amount,
                                'reference': reference
                            }
                        )
                    except VehicleInspection.DoesNotExist:
                        # Inspection doesn't exist yet, create generic transaction
                        # The checkout endpoint will create the inspection later
                        logging.warning(f"Inspection {related_id} not found, creating generic transaction")
                        transaction = Transaction.objects.create(
                            sender=user.get_full_name() or user.email,
                            recipient='Veyu',
                            type='payment',
                            source='bank',
                            amount=amount,
                            tx_ref=reference,
                            status='completed',
                            narration=f'Inspection payment - {reference}'
                        )
                        logging.info(f"Created generic transaction for inspection payment: {reference}")
                    
                elif purpose == 'order':
                    # Vehicle order payment
                    order = Order.objects.get(id=related_id)
                    transaction = Transaction.objects.create(
                        sender=user.name,
                        recipient=order.listing.dealer.business_name,
                        type='payment',
                        source='bank',
                        amount=amount,
                        tx_ref=reference,
                        status='completed',
                        narration=f'Order payment for #{order.id}',
                        related_order=order
                    )
                    
                    # Update order status
                    order.payment_status = 'paid'
                    order.save()
                    
                elif purpose == 'booking':
                    # Service booking payment
                    booking = ServiceBooking.objects.get(id=related_id)
                    transaction = Transaction.objects.create(
                        sender=user.name,
                        recipient='Veyu',
                        type='payment',
                        source='bank',
                        amount=amount,
                        tx_ref=reference,
                        status='completed',
                        narration=f'Booking payment for #{booking.id}',
                        related_booking=booking
                    )
                    
                    # Update booking status
                    booking.payment_status = 'paid'
                    booking.save()
                
                else:
                    # No purpose specified - treat as generic payment/wallet deposit
                    # This handles cases where frontend doesn't send metadata
                    logging.warning(f"Payment received without purpose metadata: {reference}")
                    transaction = Transaction.objects.create(
                        sender=user.get_full_name() or user.email,
                        recipient='Veyu',
                        type='payment',
                        source='bank',
                        amount=amount,
                        tx_ref=reference,
                        status='completed',
                        narration=f'Payment via Paystack - {reference}'
                    )
                    logging.info(f"Created generic transaction for payment: {reference}")
                
                logging.info(f"Successfully processed payment: {reference}")
                
            except User.DoesNotExist:
                logging.error(f"User not found for payment: {customer_email}")
                return Response({'detail': 'User not found'}, status=404)
            except (VehicleInspection.DoesNotExist, Order.DoesNotExist, ServiceBooking.DoesNotExist) as e:
                logging.error(f"Related object not found: {str(e)}")
                return Response({'detail': 'Related object not found'}, status=404)
            except Exception as e:
                logging.error(f"Error processing payment webhook: {str(e)}")
                return Response({'detail': 'Processing error'}, status=500)
        
        # Handle successful transfer/payout
        elif event_type == 'transfer.success':
            reference = data.get('reference')
            amount = data.get('amount', 0) / 100
            recipient_code = data.get('recipient_code')
            
            # Update transaction status
            transaction = Transaction.objects.filter(tx_ref=reference).first()
            if transaction:
                transaction.status = 'completed'
                transaction.save()
                logging.info(f"Transfer completed: {reference}")
        
        # Handle failed transfer
        elif event_type == 'transfer.failed':
            reference = data.get('reference')
            
            # Update transaction status and refund wallet
            transaction = Transaction.objects.filter(tx_ref=reference).first()
            if transaction and transaction.sender_wallet:
                transaction.status = 'failed'
                transaction.save()
                
                # Refund wallet
                wallet = transaction.sender_wallet
                wallet.ledger_balance += transaction.amount
                wallet.save()
                
                logging.info(f"Transfer failed and refunded: {reference}")
        
        # Handle reversed transfer
        elif event_type == 'transfer.reversed':
            reference = data.get('reference')
            
            # Update transaction status and refund wallet
            transaction = Transaction.objects.filter(tx_ref=reference).first()
            if transaction and transaction.sender_wallet:
                transaction.status = 'reversed'
                transaction.save()
                
                # Refund wallet
                wallet = transaction.sender_wallet
                wallet.ledger_balance += transaction.amount
                wallet.save()
                
                logging.info(f"Transfer reversed and refunded: {reference}")
        
        return Response({'status': 'success'}, status=200)
        
    except json.JSONDecodeError:
        logging.error("Invalid JSON in webhook payload")
        return Response({'detail': 'Invalid payload'}, status=400)
    except Exception as e:
        logging.error(f"Unexpected error in webhook: {str(e)}")
        return Response({'detail': 'Internal error'}, status=500)


@csrf_exempt
@api_view(['POST'])
def verification_webhook(request, **kwargs):
    # webhook that receives event after verification
    # from dojah

    data = request.data
    print("Got Verification Data:", data)
    return Response(status=200)


@api_view(['GET'])
def email_health_check(request):
    """
    Comprehensive email system health check endpoint.
    """
    try:
        health_status = get_email_backend_health()
        
        # Determine HTTP status code based on health
        if health_status.get('healthy', False):
            status_code = 200
        elif health_status.get('status') == 'warning':
            status_code = 200  # Still operational
        else:
            status_code = 503  # Service unavailable
        
        return Response(health_status, status=status_code)
        
    except Exception as e:
        return Response({
            'healthy': False,
            'status': 'error',
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def email_config_validation(request):
    """
    Email configuration validation endpoint.
    """
    try:
        validation_result = validate_email_configuration()
        status_code = 200 if validation_result['valid'] else 400
        return Response(validation_result, status=status_code)
        
    except Exception as e:
        return Response({
            'valid': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
def email_connection_test(request):
    """
    Test email backend connection endpoint.
    """
    try:
        test_result = test_smtp_connection()
        status_code = 200 if test_result['success'] else 400
        return Response(test_result, status=status_code)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
def email_test_send(request):
    """
    Send a test email to verify email functionality.
    """
    try:
        recipient = request.data.get('recipient')
        if not recipient:
            return Response({
                'success': False,
                'error': 'Recipient email required'
            }, status=400)
        
        # Send test email
        success = send_email(
            subject='Test Email from Veyu',
            recipients=[recipient],
            message='This is a test email to verify email functionality.',
            fail_silently=False
        )
        
        return Response({
            'success': success,
            'message': 'Test email sent successfully' if success else 'Failed to send test email'
        }, status=200 if success else 400)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
def process_email_queue_endpoint(request):
    """
    Process queued emails endpoint.
    """
    try:
        max_retry_count = request.data.get('max_retry_count', 5)
        stats = process_email_queue(max_retry_count)
        
        return Response({
            'success': True,
            'stats': stats
        }, status=200)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@handle_api_exception
def database_health_check(request):
    """
    Database health check endpoint.
    
    Returns database connection status, performance metrics,
    and configuration information.
    """
    health_data = DatabaseHealthChecker.check_connection()
    
    # Add performance metrics if connection is healthy
    if health_data['status'] == 'healthy':
        performance_data = DatabaseHealthChecker.check_query_performance()
        health_data['performance'] = performance_data
    
    # Determine HTTP status code
    status_code = 200 if health_data['status'] == 'healthy' else 503
    
    return Response(health_data, status=status_code)


@api_view(['GET'])
@handle_api_exception
def database_info(request):
    """
    Database configuration and connection information endpoint.
    
    Returns database configuration details (without sensitive information).
    """
    db_info = DatabaseHealthChecker.get_database_info()
    
    # Remove sensitive information
    sensitive_fields = ['password', 'user']
    for field in sensitive_fields:
        if field in db_info:
            db_info[field] = '***'
    
    return Response({
        'database_info': db_info,
        'timestamp': DatabaseHealthChecker.check_connection()['timestamp']
    })


@api_view(['GET'])
@handle_api_exception
def system_health_check(request):
    """
    Comprehensive system health check endpoint.
    
    Returns health status for database, email system, and other components.
    """
    health_status = {
        'overall_status': 'healthy',
        'timestamp': DatabaseHealthChecker.check_connection()['timestamp'],
        'components': {}
    }
    
    # Check database health
    try:
        db_health = DatabaseHealthChecker.check_connection()
        health_status['components']['database'] = db_health
        
        if db_health['status'] != 'healthy':
            health_status['overall_status'] = 'degraded'
    except Exception as e:
        health_status['components']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['overall_status'] = 'unhealthy'
    
    # Check email system health
    try:
        email_health = get_email_backend_health()
        health_status['components']['email'] = email_health
        
        if not email_health.get('healthy', False):
            if health_status['overall_status'] == 'healthy':
                health_status['overall_status'] = 'degraded'
    except Exception as e:
        health_status['components']['email'] = {
            'healthy': False,
            'status': 'error',
            'error': str(e)
        }
        if health_status['overall_status'] == 'healthy':
            health_status['overall_status'] = 'degraded'
    
    # Determine HTTP status code
    status_code_map = {
        'healthy': 200,
        'degraded': 200,  # Still operational
        'unhealthy': 503
    }
    status_code = status_code_map.get(health_status['overall_status'], 503)
    
    return Response(health_status, status=status_code)





# Log Viewer Views
# Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.4, 2.5, 4.1, 4.5

class LogListView(TemplateView):
    """
    View for displaying available log files with metadata.
    
    Requirements: 1.1, 4.5
    """
    template_name = 'logs/log_list.html'
    
    @admin_required
    def dispatch(self, request, *args, **kwargs):
        """Ensure admin authentication before processing request."""
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """
        Get context data for the log list template.
        
        Returns:
            dict: Context containing available log files and metadata
        """
        context = super().get_context_data(**kwargs)
        
        # Initialize log service
        log_service = LogFileService()
        
        try:
            # Get available log files with metadata
            log_files = log_service.get_available_logs()
            
            # Log successful access attempt
            security_logger.log_access_attempt(
                user_email=self.request.user.email,
                log_file='log_list_view',
                ip_address=self.request.META.get('REMOTE_ADDR', 'unknown'),
                success=True,
                additional_data=get_request_metadata(self.request)
            )
            
            context.update({
                'log_files': log_files,
                'total_files': len(log_files),
                'error_message': None,
                'error_type': None
            })
            
        except PermissionError as e:
            # Handle permission denied scenarios
            security_logger.log_file_access_error(
                user_email=self.request.user.email,
                log_file='log_directory',
                error_type='permission_error',
                error_message=str(e),
                ip_address=self.request.META.get('REMOTE_ADDR', 'unknown'),
                additional_data=get_request_metadata(self.request)
            )
            
            context.update({
                'log_files': [],
                'total_files': 0,
                'error_message': 'Permission denied. Unable to access log directory. Please contact system administrator.',
                'error_type': 'permission_denied'
            })
            
        except FileNotFoundError as e:
            # Handle missing log directory
            security_logger.log_file_access_error(
                user_email=self.request.user.email,
                log_file='log_directory',
                error_type='directory_not_found',
                error_message=str(e),
                ip_address=self.request.META.get('REMOTE_ADDR', 'unknown'),
                additional_data=get_request_metadata(self.request)
            )
            
            context.update({
                'log_files': [],
                'total_files': 0,
                'error_message': 'Log directory not found. Please contact system administrator.',
                'error_type': 'directory_not_found'
            })
            
        except OSError as e:
            # Handle file system errors
            security_logger.log_file_access_error(
                user_email=self.request.user.email,
                log_file='log_directory',
                error_type='filesystem_error',
                error_message=str(e),
                ip_address=self.request.META.get('REMOTE_ADDR', 'unknown'),
                additional_data=get_request_metadata(self.request)
            )
            
            context.update({
                'log_files': [],
                'total_files': 0,
                'error_message': 'File system error. Unable to access log files. Please contact system administrator.',
                'error_type': 'filesystem_error'
            })
            
        except Exception as e:
            # Handle unexpected errors
            security_logger.log_file_access_error(
                user_email=self.request.user.email,
                log_file='log_directory',
                error_type='unexpected_error',
                error_message=str(e),
                ip_address=self.request.META.get('REMOTE_ADDR', 'unknown'),
                additional_data=get_request_metadata(self.request)
            )
            
            context.update({
                'log_files': [],
                'total_files': 0,
                'error_message': 'An unexpected error occurred. Please contact system administrator.',
                'error_type': 'unexpected_error'
            })
        
        return context


class LogDetailView(TemplateView):
    """
    View for displaying log file content with pagination, search, and filtering.
    
    Requirements: 1.2, 1.3, 2.1, 2.2, 2.4, 2.5
    """
    template_name = 'logs/log_detail.html'
    
    @admin_required
    def dispatch(self, request, *args, **kwargs):
        """Ensure admin authentication before processing request."""
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """
        Get context data for the log detail template.
        
        Returns:
            dict: Context containing log entries, pagination, and search results
        """
        context = super().get_context_data(**kwargs)
        
        # Get log file name from URL
        log_file = kwargs.get('log_file')
        
        # Initialize services
        log_service = LogFileService()
        
        # Validate file access
        if not log_service.validate_file_access(log_file):
            # Log security event for invalid file access
            security_logger.log_invalid_request(
                user_email=self.request.user.email,
                request_details=f"Attempted to access invalid log file: {log_file}",
                ip_address=self.request.META.get('REMOTE_ADDR', 'unknown'),
                additional_data=get_request_metadata(self.request)
            )
            
            context.update({
                'error_message': f'Access denied or file not found: {log_file}',
                'error_type': 'access_denied',
                'log_file': log_file,
                'log_entries': [],
                'page_obj': None,
                'file_info': None,
                'search_query': self.request.GET.get('search', ''),
                'level_filter': self.request.GET.get('level', ''),
                'large_file_warning': None,
                'total_entries': 0,
                'available_levels': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            })
            return context
        
        try:
            # Get file information
            file_info = log_service.get_file_info(log_file)
            if not file_info or not file_info.is_accessible:
                raise FileNotFoundError(f"File {log_file} is not accessible")
            
            # Get search and filter parameters
            search_query = self.request.GET.get('search', '').strip()
            level_filter = self.request.GET.get('level', '').strip().upper()
            page_number = self.request.GET.get('page', 1)
            
            # Handle large file warning (> 10MB or > 10000 lines)
            large_file_warning = None
            if file_info.size > 10 * 1024 * 1024:  # 10MB
                large_file_warning = f"Large file ({file_info.size // (1024*1024)}MB). Consider downloading for better performance."
            elif file_info.line_count > 10000:
                large_file_warning = f"Large file ({file_info.line_count} lines). Showing recent entries only."
            
            # Read log entries (limit to last 5000 lines for large files)
            if file_info.line_count > 5000:
                start_line = max(1, file_info.line_count - 5000)
                log_entries = log_service.read_log_file(log_file, start_line=start_line)
            else:
                log_entries = log_service.read_log_file(log_file)
            
            # Apply search and level filtering
            filtered_entries = self._filter_log_entries(log_entries, search_query, level_filter)
            
            # Reverse order to show newest entries first
            filtered_entries.reverse()
            
            # Paginate results (100 entries per page)
            paginator = Paginator(filtered_entries, 100)
            
            try:
                page_obj = paginator.page(page_number)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            
            # Highlight search terms in entries
            if search_query:
                page_obj.object_list = self._highlight_search_terms(page_obj.object_list, search_query)
            
            # Log successful access
            additional_data = get_request_metadata(self.request)
            additional_data.update({
                'search_query': search_query,
                'level_filter': level_filter
            })
            
            security_logger.log_access_attempt(
                user_email=self.request.user.email,
                log_file=log_file,
                ip_address=self.request.META.get('REMOTE_ADDR', 'unknown'),
                success=True,
                additional_data=additional_data
            )
            
            context.update({
                'log_file': log_file,
                'file_info': file_info,
                'log_entries': page_obj.object_list,
                'page_obj': page_obj,
                'search_query': search_query,
                'level_filter': level_filter,
                'large_file_warning': large_file_warning,
                'total_entries': len(filtered_entries),
                'available_levels': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                'error_message': None,
                'error_type': None
            })
            
        except FileNotFoundError as e:
            # Handle file not found (404) scenarios
            security_logger.log_file_access_error(
                user_email=self.request.user.email,
                log_file=log_file,
                error_type='file_not_found',
                error_message=str(e),
                ip_address=self.request.META.get('REMOTE_ADDR', 'unknown'),
                additional_data=get_request_metadata(self.request)
            )
            
            context.update({
                'log_file': log_file,
                'file_info': None,
                'log_entries': [],
                'page_obj': None,
                'search_query': self.request.GET.get('search', ''),
                'level_filter': self.request.GET.get('level', ''),
                'large_file_warning': None,
                'total_entries': 0,
                'available_levels': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                'error_message': f'Log file "{log_file}" not found. The file may have been moved or deleted.',
                'error_type': 'file_not_found'
            })
            
        except PermissionError as e:
            # Handle permission denied (403) scenarios
            security_logger.log_permission_denied(
                user_email=self.request.user.email,
                log_file=log_file,
                ip_address=self.request.META.get('REMOTE_ADDR', 'unknown'),
                reason='file_permission_denied',
                additional_data=get_request_metadata(self.request)
            )
            
            context.update({
                'log_file': log_file,
                'file_info': None,
                'log_entries': [],
                'page_obj': None,
                'search_query': self.request.GET.get('search', ''),
                'level_filter': self.request.GET.get('level', ''),
                'large_file_warning': None,
                'total_entries': 0,
                'available_levels': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                'error_message': f'Permission denied accessing log file "{log_file}". Please contact system administrator.',
                'error_type': 'permission_denied'
            })
            
        except UnicodeDecodeError as e:
            # Handle file encoding issues
            security_logger.log_file_access_error(
                user_email=self.request.user.email,
                log_file=log_file,
                error_type='encoding_error',
                error_message=str(e),
                ip_address=self.request.META.get('REMOTE_ADDR', 'unknown'),
                additional_data=get_request_metadata(self.request)
            )
            
            context.update({
                'log_file': log_file,
                'file_info': None,
                'log_entries': [],
                'page_obj': None,
                'search_query': self.request.GET.get('search', ''),
                'level_filter': self.request.GET.get('level', ''),
                'large_file_warning': None,
                'total_entries': 0,
                'available_levels': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                'error_message': f'Unable to read log file "{log_file}" due to encoding issues. File may be corrupted or in an unsupported format.',
                'error_type': 'encoding_error'
            })
            
        except OSError as e:
            # Handle file read errors and other OS-level issues
            security_logger.log_file_access_error(
                user_email=self.request.user.email,
                log_file=log_file,
                error_type='file_read_error',
                error_message=str(e),
                ip_address=self.request.META.get('REMOTE_ADDR', 'unknown'),
                additional_data=get_request_metadata(self.request)
            )
            
            context.update({
                'log_file': log_file,
                'file_info': None,
                'log_entries': [],
                'page_obj': None,
                'search_query': self.request.GET.get('search', ''),
                'level_filter': self.request.GET.get('level', ''),
                'large_file_warning': None,
                'total_entries': 0,
                'available_levels': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                'error_message': f'Unable to read log file "{log_file}". The file may be locked or corrupted.',
                'error_type': 'file_read_error'
            })
            
        except Exception as e:
            # Handle unexpected errors
            security_logger.log_file_access_error(
                user_email=self.request.user.email,
                log_file=log_file,
                error_type='unexpected_error',
                error_message=str(e),
                ip_address=self.request.META.get('REMOTE_ADDR', 'unknown'),
                additional_data=get_request_metadata(self.request)
            )
            
            context.update({
                'log_file': log_file,
                'file_info': None,
                'log_entries': [],
                'page_obj': None,
                'search_query': self.request.GET.get('search', ''),
                'level_filter': self.request.GET.get('level', ''),
                'large_file_warning': None,
                'total_entries': 0,
                'available_levels': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                'error_message': f'An unexpected error occurred while loading log file "{log_file}". Please contact system administrator.',
                'error_type': 'unexpected_error'
            })
        
        return context
    
    def _filter_log_entries(self, log_entries, search_query, level_filter):
        """
        Filter log entries based on search query and log level.
        
        Args:
            log_entries: List of LogEntry objects
            search_query: Search term to filter by
            level_filter: Log level to filter by
            
        Returns:
            List[LogEntry]: Filtered log entries
        """
        filtered_entries = log_entries
        
        # Apply level filter
        if level_filter and level_filter in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            filtered_entries = [entry for entry in filtered_entries if entry.level == level_filter]
        
        # Apply search filter (case-insensitive search in message and raw_line)
        if search_query:
            search_lower = search_query.lower()
            filtered_entries = [
                entry for entry in filtered_entries
                if search_lower in entry.message.lower() or search_lower in entry.raw_line.lower()
            ]
        
        return filtered_entries
    
    def _highlight_search_terms(self, log_entries, search_query):
        """
        Highlight search terms in log entry messages.
        
        Args:
            log_entries: List of LogEntry objects
            search_query: Search term to highlight
            
        Returns:
            List[LogEntry]: Log entries with highlighted search terms
        """
        if not search_query:
            return log_entries
        
        # Escape search query for safe HTML insertion
        escaped_query = escape(search_query)
        
        # Create highlight pattern (case-insensitive)
        pattern = re.compile(re.escape(search_query), re.IGNORECASE)
        
        for entry in log_entries:
            # Highlight in message
            entry.message = pattern.sub(
                f'<mark class="search-highlight">{escaped_query}</mark>',
                escape(entry.message)
            )
            
            # Highlight in raw_line for display
            entry.highlighted_raw_line = pattern.sub(
                f'<mark class="search-highlight">{escaped_query}</mark>',
                escape(entry.raw_line)
            )
        
        return log_entries


class LogDownloadView(TemplateView):
    """
    View for downloading log files securely.
    
    Requirements: 3.1, 3.2, 3.3, 3.4
    """
    
    @admin_required
    def dispatch(self, request, *args, **kwargs):
        """Ensure admin authentication before processing request."""
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request for log file download.
        
        Supports both full file download and filtered results download.
        """
        log_file = kwargs.get('log_file')
        
        # Initialize log service
        log_service = LogFileService()
        
        # Validate file access
        if not log_service.validate_file_access(log_file):
            # Log security event
            security_logger.log_invalid_request(
                user_email=request.user.email,
                request_details=f"Attempted to download invalid log file: {log_file}",
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                additional_data=get_request_metadata(request)
            )
            return HttpResponse(
                'Access denied or file not found. Please verify the file name and try again.',
                status=404,
                content_type='text/plain'
            )
        
        try:
            # Get file information
            file_info = log_service.get_file_info(log_file)
            if not file_info or not file_info.is_accessible:
                return HttpResponse(
                    f'Log file "{log_file}" is not accessible. The file may have been moved or deleted.',
                    status=404,
                    content_type='text/plain'
                )
            
            # Check for large file warning (> 100MB)
            if file_info.size > 100 * 1024 * 1024:  # 100MB
                large_file_warning = (
                    f'Warning: This is a large file ({file_info.size // (1024*1024)}MB). '
                    f'Download may take some time and consume significant bandwidth. '
                    f'Consider using filters to download only relevant entries.'
                )
                
                # Add warning header to response
                response = HttpResponse(
                    large_file_warning + '\n\nProceed with download? Add "?force=true" to URL to continue.',
                    status=413,  # Payload Too Large
                    content_type='text/plain'
                )
                
                # Only proceed if force parameter is provided
                if not request.GET.get('force') == 'true':
                    return response
            
            # Check if this is a filtered download request
            search_query = request.GET.get('search', '').strip()
            level_filter = request.GET.get('level', '').strip().upper()
            
            if search_query or level_filter:
                # Generate filtered content download
                return self._download_filtered_content(
                    log_service, log_file, file_info, search_query, level_filter, request
                )
            else:
                # Download complete file
                return self._download_complete_file(log_service, log_file, file_info, request)
                
        except FileNotFoundError as e:
            # Handle file not found
            security_logger.log_download_attempt(
                user_email=request.user.email,
                log_file=log_file,
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                success=False,
                additional_data=get_request_metadata(request)
            )
            security_logger.log_file_access_error(
                user_email=request.user.email,
                log_file=log_file,
                error_type='file_not_found',
                error_message=str(e),
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                additional_data=get_request_metadata(request)
            )
            return HttpResponse(
                f'Log file "{log_file}" not found. The file may have been moved or deleted.',
                status=404,
                content_type='text/plain'
            )
            
        except PermissionError as e:
            # Handle permission denied
            security_logger.log_download_attempt(
                user_email=request.user.email,
                log_file=log_file,
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                success=False,
                additional_data=get_request_metadata(request)
            )
            security_logger.log_permission_denied(
                user_email=request.user.email,
                log_file=log_file,
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                reason='download_permission_denied',
                additional_data=get_request_metadata(request)
            )
            return HttpResponse(
                f'Permission denied accessing log file "{log_file}". Please contact system administrator.',
                status=403,
                content_type='text/plain'
            )
            
        except OSError as e:
            # Handle file system errors
            security_logger.log_download_attempt(
                user_email=request.user.email,
                log_file=log_file,
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                success=False,
                additional_data=get_request_metadata(request)
            )
            security_logger.log_file_access_error(
                user_email=request.user.email,
                log_file=log_file,
                error_type='file_system_error',
                error_message=str(e),
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                additional_data=get_request_metadata(request)
            )
            return HttpResponse(
                f'Unable to access log file "{log_file}". The file may be locked or corrupted.',
                status=500,
                content_type='text/plain'
            )
            
        except Exception as e:
            # Handle unexpected errors
            security_logger.log_download_attempt(
                user_email=request.user.email,
                log_file=log_file,
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                success=False,
                additional_data=get_request_metadata(request)
            )
            security_logger.log_file_access_error(
                user_email=request.user.email,
                log_file=log_file,
                error_type='unexpected_error',
                error_message=str(e),
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                additional_data=get_request_metadata(request)
            )
            return HttpResponse(
                'An unexpected error occurred while processing the download request. Please contact system administrator.',
                status=500,
                content_type='text/plain'
            )
    
    def _download_complete_file(self, log_service, log_file, file_info, request):
        """
        Download the complete log file with proper headers.
        
        Args:
            log_service: LogFileService instance
            log_file: Name of the log file
            file_info: LogFileInfo object
            request: HTTP request object
            
        Returns:
            HttpResponse: File download response
        """
        try:
            # Read the complete file
            with open(file_info.full_path, 'rb') as f:
                file_content = f.read()
            
            # Create response with proper headers
            response = HttpResponse(
                file_content,
                content_type='text/plain; charset=utf-8'
            )
            
            # Set download headers to preserve original filename
            response['Content-Disposition'] = f'attachment; filename="{log_file}"'
            response['Content-Length'] = str(len(file_content))
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
            # Log successful download
            security_logger.log_download_attempt(
                user_email=request.user.email,
                log_file=log_file,
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                success=True,
                file_size=file_info.size,
                is_filtered=False,
                additional_data=get_request_metadata(request)
            )
            
            return response
            
        except FileNotFoundError as e:
            return HttpResponse(
                f'Log file "{log_file}" not found during download. The file may have been moved or deleted.',
                status=404,
                content_type='text/plain'
            )
        except PermissionError as e:
            return HttpResponse(
                f'Permission denied reading log file "{log_file}". Please contact system administrator.',
                status=403,
                content_type='text/plain'
            )
        except UnicodeDecodeError as e:
            return HttpResponse(
                f'Unable to read log file "{log_file}" due to encoding issues. File may be corrupted.',
                status=500,
                content_type='text/plain'
            )
        except OSError as e:
            return HttpResponse(
                f'File system error reading log file "{log_file}": {str(e)}',
                status=500,
                content_type='text/plain'
            )
    
    def _download_filtered_content(self, log_service, log_file, file_info, search_query, level_filter, request):
        """
        Download filtered log content as a text file.
        
        Args:
            log_service: LogFileService instance
            log_file: Name of the log file
            file_info: LogFileInfo object
            search_query: Search term filter
            level_filter: Log level filter
            request: HTTP request object
            
        Returns:
            HttpResponse: Filtered content download response
        """
        try:
            # Read all log entries
            log_entries = log_service.read_log_file(log_file)
            
            # Apply filters (reuse logic from LogDetailView)
            filtered_entries = self._filter_log_entries(log_entries, search_query, level_filter)
            
            # Generate filtered content
            filtered_lines = []
            
            # Add header with filter information
            header_lines = [
                f"# Filtered log content from {log_file}",
                f"# Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"# Original file size: {file_info.size} bytes ({file_info.line_count} lines)",
                f"# Filtered results: {len(filtered_entries)} entries"
            ]
            
            if search_query:
                header_lines.append(f"# Search filter: '{search_query}'")
            if level_filter:
                header_lines.append(f"# Level filter: {level_filter}")
                
            header_lines.extend(["", ""])  # Empty lines for separation
            
            filtered_lines.extend(header_lines)
            
            # Add filtered log entries (preserve original format)
            for entry in filtered_entries:
                filtered_lines.append(entry.raw_line)
            
            # Join lines and encode
            content = '\n'.join(filtered_lines)
            content_bytes = content.encode('utf-8')
            
            # Create response
            response = HttpResponse(
                content_bytes,
                content_type='text/plain; charset=utf-8'
            )
            
            # Generate filename for filtered content
            filter_suffix = []
            if search_query:
                # Sanitize search query for filename
                safe_query = re.sub(r'[^\w\-_.]', '_', search_query)[:20]
                filter_suffix.append(f"search_{safe_query}")
            if level_filter:
                filter_suffix.append(f"level_{level_filter}")
            
            if filter_suffix:
                base_name = log_file.rsplit('.', 1)[0]
                extension = log_file.rsplit('.', 1)[1] if '.' in log_file else 'log'
                filtered_filename = f"{base_name}_filtered_{'_'.join(filter_suffix)}.{extension}"
            else:
                filtered_filename = f"filtered_{log_file}"
            
            # Set download headers
            response['Content-Disposition'] = f'attachment; filename="{filtered_filename}"'
            response['Content-Length'] = str(len(content_bytes))
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
            # Log successful filtered download
            additional_data = get_request_metadata(request)
            additional_data.update({
                'search_query': search_query,
                'level_filter': level_filter
            })
            
            security_logger.log_download_attempt(
                user_email=request.user.email,
                log_file=log_file,
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                success=True,
                file_size=len(content_bytes),
                is_filtered=True,
                additional_data=additional_data
            )
            
            return response
            
        except FileNotFoundError as e:
            return HttpResponse(
                f'Log file "{log_file}" not found during filtered download. The file may have been moved or deleted.',
                status=404,
                content_type='text/plain'
            )
        except PermissionError as e:
            return HttpResponse(
                f'Permission denied reading log file "{log_file}" for filtered download. Please contact system administrator.',
                status=403,
                content_type='text/plain'
            )
        except UnicodeDecodeError as e:
            return HttpResponse(
                f'Unable to read log file "{log_file}" for filtered download due to encoding issues. File may be corrupted.',
                status=500,
                content_type='text/plain'
            )
        except Exception as e:
            return HttpResponse(
                f'Error generating filtered content from log file "{log_file}": {str(e)}',
                status=500,
                content_type='text/plain'
            )
    
    def _filter_log_entries(self, log_entries, search_query, level_filter):
        """
        Filter log entries based on search query and log level.
        
        Args:
            log_entries: List of LogEntry objects
            search_query: Search term to filter by
            level_filter: Log level to filter by
            
        Returns:
            List[LogEntry]: Filtered log entries
        """
        filtered_entries = log_entries
        
        # Apply level filter
        if level_filter and level_filter in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            filtered_entries = [entry for entry in filtered_entries if entry.level == level_filter]
        
        # Apply search filter (case-insensitive search in message and raw_line)
        if search_query:
            search_lower = search_query.lower()
            filtered_entries = [
                entry for entry in filtered_entries
                if search_lower in entry.message.lower() or search_lower in entry.raw_line.lower()
            ]
        
        return filtered_entries

class LogRefreshAPIView(TemplateView):
    """
    AJAX API endpoint for real-time log updates.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    
    @admin_required
    def dispatch(self, request, *args, **kwargs):
        """Ensure admin authentication before processing request."""
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request for log refresh API.
        
        Returns JSON data with latest log entries and metadata for real-time updates.
        """
        log_file = kwargs.get('log_file')
        
        # Initialize log service
        log_service = LogFileService()
        
        # Validate file access
        if not log_service.validate_file_access(log_file):
            # Log security event for invalid API access
            security_logger.log_invalid_request(
                user_email=request.user.email,
                request_details=f"Attempted to access invalid log file via API: {log_file}",
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                additional_data=get_request_metadata(request)
            )
            
            return JsonResponse({
                'success': False,
                'error': 'Access denied or file not found',
                'error_type': 'access_denied',
                'entries': [],
                'metadata': {}
            }, status=404)
        
        try:
            # Get request parameters
            last_line_number = int(request.GET.get('last_line', 0))
            search_query = request.GET.get('search', '').strip()
            level_filter = request.GET.get('level', '').strip().upper()
            page_number = int(request.GET.get('page', 1))
            
            # Get file information
            file_info = log_service.get_file_info(log_file)
            if not file_info or not file_info.is_accessible:
                return JsonResponse({
                    'success': False,
                    'error': f'Log file "{log_file}" is not accessible',
                    'error_type': 'file_not_accessible',
                    'entries': [],
                    'metadata': {}
                }, status=404)
            
            # Check if file has been modified since last request
            last_modified_timestamp = request.GET.get('last_modified')
            current_modified = file_info.last_modified.timestamp()
            
            file_changed = True
            if last_modified_timestamp:
                try:
                    last_modified = float(last_modified_timestamp)
                    file_changed = current_modified > last_modified
                except (ValueError, TypeError):
                    file_changed = True
            
            # If file hasn't changed and we're not filtering, return minimal response
            if not file_changed and not search_query and not level_filter:
                return JsonResponse({
                    'success': True,
                    'file_changed': False,
                    'entries': [],
                    'new_entries_count': 0,
                    'metadata': {
                        'filename': log_file,
                        'last_modified': current_modified,
                        'total_lines': file_info.line_count,
                        'file_size': file_info.size
                    }
                })
            
            # Read log entries
            if file_info.line_count > 5000:
                # For large files, only read recent entries
                start_line = max(1, file_info.line_count - 5000)
                log_entries = log_service.read_log_file(log_file, start_line=start_line)
            else:
                log_entries = log_service.read_log_file(log_file)
            
            # Apply filters
            filtered_entries = self._filter_log_entries_api(log_entries, search_query, level_filter)
            
            # Reverse to show newest first
            filtered_entries.reverse()
            
            # Identify new entries (entries with line numbers greater than last_line_number)
            new_entries = []
            if last_line_number > 0:
                new_entries = [
                    entry for entry in filtered_entries 
                    if entry.line_number > last_line_number
                ]
            
            # Paginate results (100 entries per page)
            paginator = Paginator(filtered_entries, 100)
            
            try:
                page_obj = paginator.page(page_number)
            except (PageNotAnInteger, EmptyPage):
                page_obj = paginator.page(1)
            
            # Format entries for JSON response
            formatted_entries = []
            for entry in page_obj.object_list:
                # Highlight search terms if present
                message = entry.message
                raw_line = entry.raw_line
                
                if search_query:
                    message, raw_line = self._highlight_search_terms_json(
                        entry.message, entry.raw_line, search_query
                    )
                
                formatted_entry = {
                    'line_number': entry.line_number,
                    'timestamp': entry.timestamp.isoformat() if entry.timestamp else None,
                    'level': entry.level,
                    'message': message,
                    'raw_line': raw_line,
                    'is_new': entry.line_number > last_line_number if last_line_number > 0 else False
                }
                formatted_entries.append(formatted_entry)
            
            # Prepare pagination metadata
            pagination_data = {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_entries': paginator.count,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
                'next_page': page_obj.next_page_number() if page_obj.has_next() else None
            }
            
            # Log API access (only for manual refresh to avoid spam)
            if request.GET.get('manual_refresh') == 'true':
                additional_data = get_request_metadata(request)
                additional_data['is_manual_refresh'] = True
                
                security_logger.log_api_access(
                    user_email=request.user.email,
                    log_file=log_file,
                    ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                    endpoint='log_refresh_api',
                    success=True,
                    additional_data=additional_data
                )
            
            return JsonResponse({
                'success': True,
                'file_changed': file_changed,
                'entries': formatted_entries,
                'new_entries_count': len(new_entries),
                'pagination': pagination_data,
                'metadata': {
                    'filename': log_file,
                    'last_modified': current_modified,
                    'total_lines': file_info.line_count,
                    'file_size': file_info.size,
                    'search_query': search_query,
                    'level_filter': level_filter,
                    'max_line_number': max([e.line_number for e in filtered_entries]) if filtered_entries else 0
                }
            })
            
        except ValueError as e:
            # Handle invalid parameters
            security_logger.log_api_access(
                user_email=request.user.email,
                log_file=log_file,
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                endpoint='log_refresh_api',
                success=False,
                additional_data=get_request_metadata(request)
            )
            security_logger.log_invalid_request(
                user_email=request.user.email,
                request_details=f"Invalid parameters in log refresh API: {str(e)}",
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                additional_data=get_request_metadata(request)
            )
            
            return JsonResponse({
                'success': False,
                'error': f'Invalid parameters: {str(e)}',
                'error_type': 'invalid_parameters',
                'entries': [],
                'metadata': {}
            }, status=400)
            
        except FileNotFoundError as e:
            # Handle file not found
            security_logger.log_api_access(
                user_email=request.user.email,
                log_file=log_file,
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                endpoint='log_refresh_api',
                success=False,
                additional_data=get_request_metadata(request)
            )
            security_logger.log_file_access_error(
                user_email=request.user.email,
                log_file=log_file,
                error_type='file_not_found',
                error_message=str(e),
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                additional_data=get_request_metadata(request)
            )
            
            return JsonResponse({
                'success': False,
                'error': f'Log file "{log_file}" not found',
                'error_type': 'file_not_found',
                'entries': [],
                'metadata': {}
            }, status=404)
            
        except PermissionError as e:
            # Handle permission denied
            security_logger.log_api_access(
                user_email=request.user.email,
                log_file=log_file,
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                endpoint='log_refresh_api',
                success=False,
                additional_data=get_request_metadata(request)
            )
            security_logger.log_permission_denied(
                user_email=request.user.email,
                log_file=log_file,
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                reason='api_permission_denied',
                additional_data=get_request_metadata(request)
            )
            
            return JsonResponse({
                'success': False,
                'error': f'Permission denied accessing log file "{log_file}"',
                'error_type': 'permission_denied',
                'entries': [],
                'metadata': {}
            }, status=403)
            
        except UnicodeDecodeError as e:
            # Handle encoding issues
            security_logger.log_api_access(
                user_email=request.user.email,
                log_file=log_file,
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                endpoint='log_refresh_api',
                success=False,
                additional_data=get_request_metadata(request)
            )
            security_logger.log_file_access_error(
                user_email=request.user.email,
                log_file=log_file,
                error_type='encoding_error',
                error_message=str(e),
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                additional_data=get_request_metadata(request)
            )
            
            return JsonResponse({
                'success': False,
                'error': f'Unable to read log file "{log_file}" due to encoding issues',
                'error_type': 'encoding_error',
                'entries': [],
                'metadata': {}
            }, status=500)
            
        except OSError as e:
            # Handle file system errors
            security_logger.log_api_access(
                user_email=request.user.email,
                log_file=log_file,
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                endpoint='log_refresh_api',
                success=False,
                additional_data=get_request_metadata(request)
            )
            security_logger.log_file_access_error(
                user_email=request.user.email,
                log_file=log_file,
                error_type='file_system_error',
                error_message=str(e),
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                additional_data=get_request_metadata(request)
            )
            
            return JsonResponse({
                'success': False,
                'error': f'Unable to access log file "{log_file}"',
                'error_type': 'file_system_error',
                'entries': [],
                'metadata': {}
            }, status=500)
            
        except Exception as e:
            # Handle unexpected errors
            security_logger.log_api_access(
                user_email=request.user.email,
                log_file=log_file,
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                endpoint='log_refresh_api',
                success=False,
                additional_data=get_request_metadata(request)
            )
            security_logger.log_file_access_error(
                user_email=request.user.email,
                log_file=log_file,
                error_type='unexpected_error',
                error_message=str(e),
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                additional_data=get_request_metadata(request)
            )
            
            return JsonResponse({
                'success': False,
                'error': 'An unexpected error occurred',
                'error_type': 'unexpected_error',
                'entries': [],
                'metadata': {}
            }, status=500)
    
    def _filter_log_entries_api(self, log_entries, search_query, level_filter):
        """
        Filter log entries based on search query and log level.
        
        Args:
            log_entries: List of LogEntry objects
            search_query: Search term to filter by
            level_filter: Log level to filter by
            
        Returns:
            List[LogEntry]: Filtered log entries
        """
        filtered_entries = log_entries
        
        # Apply level filter
        if level_filter and level_filter in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            filtered_entries = [entry for entry in filtered_entries if entry.level == level_filter]
        
        # Apply search filter (case-insensitive search in message and raw_line)
        if search_query:
            search_lower = search_query.lower()
            filtered_entries = [
                entry for entry in filtered_entries
                if search_lower in entry.message.lower() or search_lower in entry.raw_line.lower()
            ]
        
        return filtered_entries
    
    def _highlight_search_terms_json(self, message, raw_line, search_query):
        """
        Highlight search terms for JSON response (using simple markers).
        
        Args:
            message: Log entry message
            raw_line: Raw log line
            search_query: Search term to highlight
            
        Returns:
            tuple: (highlighted_message, highlighted_raw_line)
        """
        if not search_query:
            return message, raw_line
        
        # Use simple text markers for JSON (will be converted to HTML on frontend)
        pattern = re.compile(re.escape(search_query), re.IGNORECASE)
        
        highlighted_message = pattern.sub(f'**{search_query}**', message)
        highlighted_raw_line = pattern.sub(f'**{search_query}**', raw_line)
        
        return highlighted_message, highlighted_raw_line