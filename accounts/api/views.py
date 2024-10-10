from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now
from rest_framework.response import Response
from django.db.models import QuerySet
from django.contrib.auth import authenticate, login, logout
from utils.sms import send_sms
from utils.mail import send_email
from django_filters.rest_framework import DjangoFilterBackend
from utils import OffsetPaginator
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly
)
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
)
from .serializers import (
    AccountSerializer,
    LoginSerializer,
    CustomerSerializer,
    MechanicSerializer,
    VerificationSerializer,
)
from utils.dispatch import (
    user_just_registered,
    handle_new_signup,
)
from rest_framework.authentication import (
    TokenAuthentication,
    SessionAuthentication
)
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    APIView
)
from ..models import (
    Account,
    OTP,
    Mechanic,
    Customer,
)




class LoginView(APIView):
    serializer_class = LoginSerializer
    allowed_methods = ['POST']

    def post(self, request, *args, **kwargs):
        print("Request:", request.data)
        user = authenticate(email=request.data['email'], password=request.data['password'])
        if user is not None:
            user.last_login = now()
            user.save()
            user_data = LoginSerializer(user).data
            # login(request=request, user=user)

            # send_email()
            code = OTP.objects.create(valid_for=user, channel='email')
            # send_email(
            #     template='utils/templates/email-confirmation.html',
            #     recipients=request.data['email'],
            #     context={'code': code.code, 'user': user},
            #     subject="Motaa Verification",
            # )

            send_sms(
                message=f"Hi {user.first_name}, here's your OTP: {code.code}",
                recipient='+2349160374200'
            )

            data = {
                'error': False,
                'message': 'Successfully authenticated',
                'data': user_data
            }
            return Response(data)
        return Response({'error': True, 'message': 'invalid credentials'}, 404)


class SignUpView(CreateAPIView):
    allowed_methods = ['POST']
    serializer_class = AccountSerializer

    def post(self, request, *args, **kwargs):
        data = request.data
        account = Account(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            user_type=data['user_type'],
        )
        account.set_password(data['password'])
        account.save()
        otp = OTP.objects.create(valid_for=account)
        
        user_just_registered.connect(handle_new_signup, sender=account)
        user_just_registered.send(sender=account, otp=otp)
        return Response({
            'error': False,
            'message': "Successfully created your account"
        }, status=201)


class VerificationView(APIView):
    allowed_methods = ['POST']
    serializer_class = VerificationSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def post(self, request, *args, **kwargs):
        data = request.data
        channel = data.get('channel','email')

        print("Confirming OTP:", data)

        if data['action'] == 'request-code':
            code = OTP.objects.create(valid_for=request.user, channel=channel)
            if channel == 'email':
                send_email(
                    template='utils/templates/email-confirmation.html',
                    recipient=data['email'],
                    context={'code': code.code, 'user': request.user},
                    subject="Motaa Verification",
                )
            elif channel == 'sms':
                send_sms(
                    message=f"Hi {request.user.first_name}, here's your OTP: {code.code}",
                    recipient=data['phone_number']
                )
            return Response({
                'error': False,
                'message': 'OTP sent to your inbox'
            }, status=200)
    
        elif data['action'] == 'confirm-code':
            try:
                otp = OTP.objects.get(code=data['code'])
                valid = otp.verify(data['code'], channel)
                request.user.verified_email = True
                request.user.save()
                if valid:
                    return Response({
                        'error': False,
                        'message': f'Successfully verified your {"email" if channel == "email" else "phone number"}'
                    }, status=200)
                raise Exception('Invalid OTP')
            except Exception as error:
                return Response({
                    'error': True,
                    'message': 'Invalid OTP'
                }, status=404)



