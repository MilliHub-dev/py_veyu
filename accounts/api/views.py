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
)
from ..models import (
    Mechanic,
)
from .filters import (
    MechanicFilter,
)




class LoginView(APIView):
    serializer_class = LoginSerializer
    allowed_methods = ['POST']

    def post(self, request, *args, **kwargs):
        user = authenticate(request=request, email=request.data['email'], password=request.data['password'])
        if user is not None:
            user.last_login = now()
            user.save()
            user_data = AccountSerializer(user).data
            user_data.pop('password',)
            data = {
                'user': user_data
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


@api_view(['POST'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
def verify_user_view(request):
    data = request.data
    channel = data.get('channel','email')

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


class MechanicListView(ListAPIView):
    pagination_class = OffsetPaginator
    serializer_class = MechanicSerializer
    allowed_methods = ['GET']
    permission_classes = [IsAuthenticatedOrReadOnly]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    
    # Add both the filter and ordering backends
    filter_backends = [DjangoFilterBackend,]
    filterset_class = MechanicFilter  # Use the filter class
    
    ordering = ['account__first_name']  # Default ordering if none specified by the user

    def get_queryset(self):
        return Mechanic.objects.all()

    def get(self, request, *args, **kwargs):
        queryset = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = self.serializer_class(queryset, many=True)

        data = {
            'error': False,
            'message': '',
            'data': {
                'pagination': {
                    'offset': self.paginator.offset,
                    'limit': self.paginator.limit,
                    'count': self.paginator.count,
                    'next': self.paginator.get_next_link(),
                    'previous': self.paginator.get_previous_link()
                },
                'results': serializer.data
            }
        }
        return Response(data, 200)



