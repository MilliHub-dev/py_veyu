import json
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
from django.db.models import QuerySet, Q

# Utility imports
from utils.sms import send_sms
from utils.mail import send_email
from utils import (
    IsDealerOrStaff,
    OffsetPaginator,
)
from utils.dispatch import (
    otp_requested,
)

# Local app imports
from ..models import (
    Account,
    OTP,
    Mechanic,
    Customer,
    Dealership,
    Dealer,
    UserProfile,
    Location,
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
    SignupSerializer,
    GetDealershipSerializer,
    ListingSerializer,
)
from listings.api.serializers import OrderSerializer
from .filters import (
    MechanicFilter,
)
from feedback.models import Notification
from feedback.api.serializers import NotificationSerializer
from bookings.models import (ServiceBooking, )
from bookings.api.serializers import (BookingSerializer, )
from dj_rest_auth.jwt_auth import JWTAuthentication
from rest_framework.parsers import (
    MultiPartParser,
    JSONParser,
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class SignUpView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = SignupSerializer
    parser_classes = [MultiPartParser, JSONParser]

    def get(self, request:Request):
        # check if user with email exists only
        email = request.GET.get('email', None)

        if email:
            try:
                user = Account.objects.get(email=email)
                return Response({
                    'error': True,
                    'message': "User with this email already exists",
                }, status=400)
            except Account.DoesNotExist:
                return Response({
                    'error': False,
                    'message': "Email OK",
                }, status=200)
        return Response({
            'error': True,
            'message': "This route must be called with the 'email' param.",
        }, status=400)

    def post(self, request:Request):
        try:
            data = request.data
            print("Signup data:", data)
            action = data['action'] or 'create-account'

            if action == 'create-account':
                user_type = data['user_type']
                user = Account(
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    email=data['email'],
                    provider=data['provider'],
                    user_type=data['user_type']
                )
                user.save(using=None)
                if data['provider'] == 'veyu':
                    user.set_password(data['password'])
                else:
                    user.set_unusable_password()
                user.save()

                if user_type == 'customer':
                    Customer.objects.create(user=user, phone_number=data['phone_number'])
                # else:
                #     business = {'dealer': Dealership, 'mechanic': Mechanic}.get(user_type)
                #     business.objects.create(user=user)
                user_data = {
                    "token": str(user.api_token),
                }
                user_data.update(AccountSerializer(user).data)
                return Response({ 'error': False, 'data': user_data }, 201)
            elif action == 'setup-business-profile':
                user = request.user
                if not user:
                    return Response({'error': True, 'message': "Unauthorized access"}, 401)

                user_type = data['user_type']
                profile_model = {'mechanic': Mechanic, 'dealer': Dealership}.get(user_type)
                serializer = {'mechanic': MechanicSerializer, 'dealer': GetDealershipSerializer}.get(user_type)
                if profile_model:
                    business = profile_model(
                        user=user,
                        logo = data['logo'],
                        about=data['about'],
                        headline=data['headline'],
                        phone_number=data['contact_phone'],
                        business_name=data['business_name'],
                        contact_email = data['contact_email'],
                        contact_phone = data['contact_phone'],
                    )

                    if user_type == 'mechanic':
                        business.business_type = data['business_type']
                    elif user_type == 'dealer':
                        business.offers_purchase = ('Car Sale' in data['services'])
                        business.offers_rentals = ('Car Leasing' in data['services'])
                        business.offers_drivers = ('Drivers' in data['services'])

                    if data.get('location', None):
                        if type(data['location']) == str:
                            place = json.loads(data['location'])
                            business_location = Location(
                                user=user,
                                lat=place.get('lat', None),
                                lng=place.get('lng', None),
                                country=place['country'],
                                state=place['state'],
                                city=place['city'],
                                address=place['street_address'],
                                zip_code=place.get('zip_code', None),
                                google_place_id=place.get('place_id', None),
                            )
                            business_location.save()
                            business.location = business_location
                    business.save()


                    data = {
                        'error': False,
                        'data': serializer(business, context={'request': request}).data
                    }
                    return Response(data, status=200)
                else:
                    return Response({'error' : False, 'message': "Invalid or missing user_type param"})
        except Exception as error:
            message = str(error)
            raise error
            if message == 'UNIQUE constraint failed: accounts_customer.phone_number':
                message = "User with this phone number already exists"
            return Response({'error' : True, 'message': message}, 500)


class LoginView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer


    def post(self, request: Request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": True, "message": "Invalid data", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = serializer.validated_data
        email = validated_data.get("email")
        password = validated_data.get("password")
        provider = validated_data.get("provider")

        try:
            user = Account.objects.get(email=email)
        except Account.DoesNotExist:
            return Response(
                {"error": True, "message": "Account does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # **Strict Provider Matching Logic**
        if user.provider != provider:
            return Response(
                {"error": True, "message": "Authentication failed: Provider mismatch"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # **If provider is "veyu", validate password**
        if provider == "veyu" and not user.check_password(raw_password=password):
            return Response(
                {"error": True, "message": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # **Login the user and generate tokens**
        login(request, user)
        data = {
            "id": user.id,
            "email": user.email,
            "token": str(user.api_token),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "user_type": user.user_type,
            "provider": user.provider,
            "is_active": user.is_active,
        }


        # signing into dashboard
        if user.user_type == 'dealer':
            data.update({
             "dealerId": str(user.dealership.uuid),
             "verified_id": user.dealership.verified_id,
             "verified_business": user.dealership.verified_business,
            })
        elif user.user_type == 'mechanic':
            data.update({
             "mechanicId": str(user.mechanic.uuid),
             "verified_id": user.mechanic.verified_id,
             "verified_business": user.mechanic.verified_business,
            })
        return Response(data, 200)


class CartView(views.APIView):
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        customer = Customer.objects.get(user=request.user)
        cars = customer.cart.filter(listing_type='sale')
        rentals = customer.cart.filter(listing_type='rental')
        bookings = ServiceBooking.objects.filter(customer=customer, booking_status__in=['pending', 'requested'])
        orders = customer.orders.all()

        data = {
            'error': False,
            'message': 'Loaded your cart',
            'data': {
                'cars': ListingSerializer(cars, context={'request': request}, many=True).data,
                'orders': OrderSerializer(orders, context={'request': request}, many=True).data,
                'rentals': ListingSerializer(rentals, context={'request': request}, many=True).data,
                'bookings': BookingSerializer(bookings, context={'request': request}, many=True).data,
            }
        }
        return Response(data, 200)

    def post(self, request, *args, **kwargs):
        action = request.data.get('action', None)
        customer = Customer.objects.get(user=request.user)
        cart = customer.cart

        if action == "remove-from-cart":
            item = cart.get(uuid=request.data['item'])
            cart.remove(item)
            customer.save()
            return Response({'error': False, 'message': 'Successfully removed from your cart'})
        else:
            return Response({'error': True, 'message': 'Invalid action parameter!'}, status=400)


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


class BusinessVerificationView(views.APIView):
    allowed_methods = ['POST']

    def post(self, request):
        try:
            data = request.data
            objects = {'dealership': Dealership, 'mechanic': Mechanic}
            obj = objects.get(data['object'])

            # get dealership / mechanic
            business = obj.objects.get(uuid=data['object_id'])
            business.verification_ref = data['verification_ref']

            if 'user.verified_email' in data['scope']:
                business.user.verified_email = True
                business.user.save()
            if 'verified_id' in data['scope']:
                business.user.verified_id = True
            if 'verified_business' in data['scope']:
                business.verified_business = True
            if 'verified_tin' in data['scope']:
                business.verified_tin = True
            business.save()
            
            response = {
                'error': False,
                'message': 'Verification Successful'
            }
            return Response(response, 200)
        except Exception as error:
            raise error



class VerifyEmailView(APIView):
    allowed_methods = ['POST']
    serializer_class = VerifyEmailSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, JWTAuthentication]

    def post(self, request:Request):
        data = request.data
        serializer = VerifyEmailSerializer(data=data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            if validated_data['action'] == 'request-code':
                code = OTP.objects.create(valid_for=request.user)
                #  send a signal to the receiver
                otp_requested.send('email', user=request.user, otp=code)
                return Response({
                    'error': False,
                    'message': 'OTP sent to your inbox'
                }, status=status.HTTP_200_OK)

            elif validated_data['action'] == 'confirm-code':
                try:
                    otp = OTP.objects.get(code=data['code'])
                    if otp.valid_for == request.user:
                        valid = otp.verify(data['code'], user=request.user)
                        if valid:
                            return Response({
                                'error': False,
                                'message': f'Successfully verified your email'
                            }, status=status.HTTP_200_OK)
                        raise Exception('Invalid OTP')
                except Exception as error:
                    raise error
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
                code = OTP.objects.create(valid_for=request.user, channel='sms')
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


class NotificationView(APIView):
    permission_classes = [IsAuthenticated]
    allowed_methods = ['GET', 'POST']
    serializer_class =  NotificationSerializer

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        notifications = Notification.objects.filter(user=request.user, read=False)
        data = {
            'error': False,
            'data': NotificationSerializer(notifications, many=True).data
        }
        return Response(data, 200)

    def post(self, request):
        notifications = Notification.objects.filter(user=request.user)
        notification = notifications.get(uuid=request.data['notification_id'])
        notification.mark_as_read()
        data = {
            'error': False,
            'data': NotificationSerializer(notifications.filter(read=False), many=True).data
        }
        return Response(data, 200)

