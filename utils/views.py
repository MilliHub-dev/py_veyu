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
from utils.mail import send_email, validate_email_configuration, test_smtp_connection, get_email_backend_health, process_email_queue
from utils.database_utils import DatabaseHealthChecker
from utils.error_handlers import handle_api_exception


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
    # Paystack webhook secret key
    secret = os.environ.get("PAYSTACK_SECRET_KEY", None).encode()

    # Get the signature from the header
    signature = request.META.get('HTTP_X_PAYSTACK_SIGNATURE')
    if not signature:
        return Response({'detail': 'Signature missing'}, status=400)

    # Get request body and verify signature
    payload = request.body
    computed_signature = hmac.new(secret, payload, hashlib.sha512).hexdigest()

    if not hmac.compare_digest(computed_signature, signature):
        return Response({'detail': 'Invalid signature'}, status=400)

    # Decode and handle event
    event = json.loads(payload)
    event_type = event.get('event')
    customer = event.get('customer')
    metadata = event.get['customer']['metadata']

    if event_type == 'charge.success':
        # Mark order as paid, notify user, send emails, update listings.
        if metadata['reason'] == 'listing.order.paid':pass
        elif metadata['reason'] == 'listing.order.paid':pass
        elif metadata['reason'] == 'listing.order.paid':pass
    pass

    # for payout
    if event_type == 'transfer.successful':pass
        

    return Response(status=200)


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



