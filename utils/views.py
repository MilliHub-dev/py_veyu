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
from utils.mail import send_email


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



