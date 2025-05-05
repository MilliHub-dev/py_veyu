import hashlib, hmac, json, os, uuid, base64
from django.shortcuts import render
from django.conf import settings
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from io import BytesIO
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.core.mail import EmailMessage
from django.views.decorators.csrf import csrf_exempt


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
def email_webhook_receiver(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    signature = request.headers.get('X-Motaa-Signature')
    if not signature:
        return JsonResponse({'error': 'Missing signature'}, status=400)

    raw_body = request.body
    expected_signature = hmac.new(
        os.environ.get("MOTAA_EMAIL_HMAC_SECRET", None).encode(),
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
    return Response(status=200)


LETTERHEAD_PATH = os.path.join(settings.BASE_DIR, 'static', 'motaa/letterhead.pdf')
MEDIA_SIGNED_DIR = os.path.join(settings.MEDIA_ROOT, 'signed_docs')

def draw_overlay(data: dict, include_signature: bool) -> BytesIO:
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=letter)
    # Draw your fields (tweak coordinates as needed)
    c.drawString(65, 700, f"Client Name: {data.get('client_name','')}")
    c.drawString(65, 680, f"Date: {data.get('date','')}")
    if 'vehicle_id' in data:
        c.drawString(65, 660, f"Vehicle ID: {data['vehicle_id']}")
        c.drawString(65, 640, f"Inspector: {data.get('inspector','')}")
    if 'order_ref' in data:
        c.drawString(65, 660, f"Order Ref: {data['order_ref']}")
        c.drawString(65, 640, f"Amount: {data.get('amount','')}")
    
    # signature
    if include_signature and data.get('signature'):
        sig_b64 = data['signature'].split(',',1)[1]
        sig_img = base64.b64decode(sig_b64)
        sig_buf = BytesIO(sig_img)
        c.drawImage(sig_buf, 100, 200, width=200, height=100, mask='auto')
    c.showPage()
    c.save()
    packet.seek(0)
    return packet

def merge_letterhead(overlay_buf: BytesIO) -> BytesIO:
    overlay = PdfReader(overlay_buf)
    base = PdfReader(open(LETTERHEAD_PATH, 'rb'))
    writer = PdfWriter()
    page = base.pages[0]
    page.merge_page(overlay.pages[0])
    writer.add_page(page)
    out = BytesIO()
    writer.write(out)
    out.seek(0)
    return out


@api_view(['GET','POST'])
def inspection_slip(request):
    """
    GET:  /api/inspection-slip/?client_name=…&date=…&vehicle_id=…&inspector=…
      → returns unsigned PDF
    POST: JSON body + optional "signature" (data-URL)
      → returns PDF, saves signed copy if signature provided
    """
    # pick up data from GET or JSON POST
    if request.method == 'GET':
        data = request.GET.dict()
        include_sig = False
    else:
        data = json.loads(request.body)
        include_sig = bool(data.get('signature'))

    overlay = draw_overlay(data, include_sig)
    final_pdf = merge_letterhead(overlay)

    # save signed
    if include_sig:
        os.makedirs(MEDIA_SIGNED_DIR, exist_ok=True)
        fn = f"inspection_{uuid.uuid4().hex}.pdf"
        with open(os.path.join(MEDIA_SIGNED_DIR, fn), 'wb') as f:
            f.write(final_pdf.getvalue())

    resp = HttpResponse(final_pdf.getvalue(), content_type='application/pdf')
    resp['Content-Disposition'] = 'attachment; filename="inspection_slip.pdf"'
    return resp


@api_view(['GET','POST'])
def order_agreement(request):
    """
    GET:  /api/order-agreement/?client_name=…&date=…&order_ref=…&amount=…
    POST: JSON body + optional "signature"
    """
    if request.method == 'GET':
        data = request.GET.dict()
        include_sig = False
    else:
        data = json.loads(request.body)
        include_sig = bool(data.get('signature'))

    overlay = draw_overlay(data, include_sig)
    final_pdf = merge_letterhead(overlay)

    if include_sig:
        os.makedirs(MEDIA_SIGNED_DIR, exist_ok=True)
        fn = f"order_{uuid.uuid4().hex}.pdf"
        with open(os.path.join(MEDIA_SIGNED_DIR, fn), 'wb') as f:
            f.write(final_pdf.getvalue())

    resp = HttpResponse(final_pdf.getvalue(), content_type='application/pdf')
    resp['Content-Disposition'] = 'attachment; filename="order_agreement.pdf"'
    return resp



