
from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from rest_framework.response import Response
from rest_framework import generics, status, views
from rest_framework.request import Request
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes
)
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.authentication import (
    TokenAuthentication,
    SessionAuthentication
)

from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
)
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import QuerySet

# Utility imports
from utils.sms import send_sms
from utils.mail import send_email
from utils import OffsetPaginator
from utils.dispatch import (
    user_just_registered,
    handle_new_signup,
)

# Local app imports
from ..models import (
    Account,
    OTP,
    Mechanic,
    # Agent,
    Customer,
    Dealer,
    UserProfile
)
from .serializers import (
    AccountSerializer,
    LoginSerializer,
    CustomerSerializer,
    MechanicSerializer,
    VerifyEmailSerializer,
    GetAccountSerializer,
    UserProfileSerializer,
    get_user_serializer,
    ChangePasswordSerializer,
    VerifyAccountSerializer,
    VerifyPhoneNumberSerializer,
)
from .filters import (
    MechanicFilter,

) 


class SignUpView(generics.CreateAPIView):
    permission_classes = [AllowAny]
   
    def post(self, request:Request):
        with transaction.atomic():
            data = request.data
            serializer = GetAccountSerializer(data=data)
            if serializer.is_valid():
                validated_data  = serializer.validated_data
                validated_data.pop('password2', None) 
                user = Account.objects.create_user(**validated_data)
                user.save()

                user_type = validated_data['user_type']

                # can't use Agent in profile model, because Agents are basically ordinary users with is_staff=True
                profile_model = {'customer': Customer, 'mechanic': Mechanic, 'dealer': Dealer}.get(user_type)
                if profile_model:
                    profile_model.objects.create(user=user)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                else:
                    raise ValueError('invalid user type')
            else:
                return Response(serializer.errors)



class LoginView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request:Request):
    
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            email = validated_data['email']
            password = validated_data['password']

            user = Account.objects.get(email=email)
            try:
                if user and user.check_password(raw_password=password):
                    access_token = AccessToken.for_user(user)
                    refresh_token = RefreshToken.for_user(user)

                    return Response(
                        {
                            "access_token": str(access_token),
                            "refresh_token": str(refresh_token),
                            "user_id": user.id,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "email": user.email,
                            "is_active": user.is_active
                        }
                    )
                else:
                    return Response(
                        {
                            "message": "Unable to log in with provided credentials.",
                        },
                        status=status.HTTP_401_UNAUTHORIZED,
                    )

            except Account.DoesNotExist:
                return Response(
                    {
                        "message": "Account does not exist"
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        else:
            return Response(serializer.errors)
        



class UpdateProfileView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get_user_profile(self,request):
        user = request.user
        user_type = user.user_type
        user_model = {'customer': Customer, 'mechanic': Mechanic, 'dealer': Dealer, 'agent': Agent}.get(user_type)
        return get_object_or_404(user_model, user=user)
    
    def put(self, request:Request):
        user_type = request.user.user_type
        profile = self.get_user_profile(request)
        serializer = get_user_serializer(user_type=user_type)
        serializer = serializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)


class VerifyEmailView(APIView):
    allowed_methods = ['POST']
    permission_classes = [IsAuthenticated]

    def post(self, request:Request):
        data = request.data
        serializer = VerifyEmailSerializer(data=data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            if validated_data['action'] == 'request-code':
                code = OTP.objects.create(valid_for=request.user)
        
                send_email(
                    template='utils/templates/email-confirmation.html',
                    recipient=data['email'],
                    context={'code': code.code, 'user': request.user},
                    subject="Motaa Verification",
                )

                return Response({
                    'error': False,
                    'message': 'OTP sent to your inbox'
                }, status=status.HTTP_200_OK)
    
            elif validated_data['action'] == 'confirm-code':
                try:
                    otp = OTP.objects.get(code=data['code'])
                    if otp.valid_for == request.user:
                        valid = otp.verify(data['code'], 'email')
                        if valid:
                            return Response({
                                'error': False,
                                'message': f'Successfully verified your email'
                            }, status=status.HTTP_200_OK)
                        raise Exception('Invalid OTP')
                except Exception as error:
                    return Response({
                        'error': True,
                        'message': 'Invalid OTP'
                    }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return(Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST))
        

class VerifyPhoneNumberView(APIView):
    allowed_methods = ['POST']
    permission_classes = [IsAuthenticated]

    def post(self, request:Request):
        data = request.data
        serializer = VerifyPhoneNumberSerializer(data=data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            if validated_data['action'] == 'request-code':
                code = OTP.objects.create(valid_for=request.user)
                send_sms(
                    message=f"Hi {request.user.first_name}, here's your OTP: {code.code}",
                    recipient=data['phone_number']
                )
                return Response({
                    'error': False,
                    'message': 'OTP sent to your inbox'
                }, status=status.HTTP_200_OK)
    
            elif validated_data['action'] == 'confirm-code':
                try:
                    otp = OTP.objects.get(code=data['code'])
                    valid = otp.verify(data['code'], 'sms')
                    if valid:
                        return Response({
                            'error': False,
                            'message': f'Successfully verified your phone number'
                        }, status=status.HTTP_200_OK)
                    raise Exception('Invalid OTP')
                except Exception as error:
                    print(error)
                    return Response({
                        'error': True,
                        'message': 'Invalid OTP'
                    }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return(Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST))


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
        queryset = self.paginate_queryset(
            self.filter_queryset(
                self.get_queryset()
            )
        )
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
                    'previous': self.paginator.get_previous_link(),
                },
                'results': serializer.data
            }
        }
        return Response(data, 200)




