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
from accounts.utils.email_notifications import (
    send_verification_email, 
    send_welcome_email,
    send_otp_email,
    send_business_verification_status,
    send_booking_confirmation,
    send_inspection_scheduled,
    send_order_confirmation
)
from utils import (
    IsDealerOrStaff,
    OffsetPaginator,
)
from utils.dispatch import (
    otp_requested,
)
from utils.otp import make_random_otp

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

    @swagger_auto_schema(
        operation_summary="Check if email is available",
        operation_description="Returns whether an email is already registered. Pass ?email=...",
        manual_parameters=[
            openapi.Parameter('email', openapi.IN_QUERY, description='Email to check', type=openapi.TYPE_STRING),
        ],
        responses={200: openapi.Response('OK'), 400: openapi.Response('Missing email')}
    )
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

    @swagger_auto_schema(
        operation_summary="Create a new account",
        operation_description=(
            "Provider notes:\n"
            "- provider=veyu: password and confirm_password are required and validated.\n"
            "- provider in [google, apple, facebook]: password is not used here; third-party token verification is expected upstream.\n"
            "- user_type must be one of: customer | mechanic | dealer.\n"
            "- action defaults to 'create-account'. Use 'setup-business-profile' to create business profile after signup."
        )
    )
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
                # Generate and save email verification code
                verification_code = make_random_otp()
                user.email_verification_code = verification_code
                user.save()

                # Send verification and welcome emails
                verification_sent = send_verification_email(user, verification_code)
                welcome_sent = send_welcome_email(user)
                
                # Send OTP for phone verification if phone number exists
                if user.phone_number:
                    otp_code = make_random_otp()
                    otp_sent = send_otp_email(user, otp_code)
                    if otp_sent:
                        # Save OTP to database
                        OTP.objects.create(
                            user=user,
                            code=otp_code,
                            phone_number=user.phone_number,
                            purpose='phone_verification',
                            expires_at=timezone.now() + timezone.timedelta(minutes=30)
                        )
                
                # Prepare response data
                user_data = {
                    "token": str(user.api_token),
                    "email_verified": user.email_verified,
                    "verification_sent": verification_sent,
                    "welcome_email_sent": welcome_sent
                }
                user_data.update(AccountSerializer(user).data)
                
                return Response({
                    'error': False,
                    'message': 'Account created successfully. Please check your email to verify your account.',
                    'data': user_data
                }, status=201)
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
            # raise error
            if message == 'UNIQUE constraint failed: accounts_customer.phone_number':
                message = "User with this phone number already exists"
            return Response({'error' : True, 'message': message}, 500)


class LoginView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    @swagger_auto_schema(
        operation_summary="Authenticate user",
        operation_description=(
            "Provider notes:\n"
            "- The account's provider must match the provided provider.\n"
            "- provider=veyu: email/password are validated locally.\n"
            "- provider in [google, apple, facebook]: current implementation does not validate third-party tokens (should be added).\n\n"
            "**Response includes:**\n"
            "- For dealers: dealerId, verified_id, verified_business, business_verification_status\n"
            "- For mechanics: mechanicId, verified_id, verified_business, business_verification_status\n"
            "- business_verification_status values: 'not_submitted', 'pending', 'verified', 'rejected'"
        ),
        responses={
            200: openapi.Response(
                description="Login successful",
                examples={
                    "application/json": {
                        "id": 123,
                        "email": "dealer@example.com",
                        "token": "abc123token",
                        "refresh": "refresh_token_here",
                        "first_name": "John",
                        "last_name": "Doe",
                        "user_type": "dealer",
                        "provider": "veyu",
                        "is_active": True,
                        "dealerId": "550e8400-e29b-41d4-a716-446655440000",
                        "verified_id": True,
                        "verified_business": False,
                        "business_verification_status": "pending"
                    }
                }
            ),
            401: "Invalid credentials or provider mismatch",
            404: "Account does not exist"
        },
        tags=['Authentication']
    )
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
            try:
                data.update({
                 "dealerId": str(user.dealership.uuid),
                 "verified_id": user.dealership.verified_id,
                 "verified_business": user.dealership.verified_business,
                 "business_verification_status": user.dealership.business_verification_status,
                })
            except Account.dealership.RelatedObjectDoesNotExist:
                pass
        elif user.user_type == 'mechanic':
            try:
                data.update({
                 "mechanicId": str(user.mechanic.uuid),
                 "verified_id": user.mechanic.verified_id,
                 "verified_business": user.mechanic.verified_business,
                 "business_verification_status": user.mechanic.business_verification_status,
                })
            except Account.mechanic.RelatedObjectDoesNotExist:
                pass
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
    """
    Submit business verification details for manual admin approval.
    Supports both POST (create/update) and GET (check status).
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, JWTAuthentication]
    
    @swagger_auto_schema(
        operation_summary="Get Business Verification Status",
        operation_description=(
            "Check the current business verification status for the authenticated dealer or mechanic.\n\n"
            "**Statuses:**\n"
            "- `not_submitted`: No verification has been submitted yet\n"
            "- `pending`: Verification submitted and awaiting admin review\n"
            "- `verified`: Verification approved by admin\n"
            "- `rejected`: Verification rejected by admin (check rejection_reason)\n\n"
            "**Authentication Required:** Yes (Token or JWT)\n"
            "**User Types:** dealer, mechanic only"
        ),
        responses={
            200: openapi.Response(
                description="Verification status retrieved successfully",
                examples={
                    "application/json": {
                        "status": "pending",
                        "status_display": "Pending Review",
                        "submission_date": "2025-10-20T14:30:00Z",
                        "rejection_reason": None
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid user type",
                examples={
                    "application/json": {
                        "error": True,
                        "message": "Only dealers and mechanics can submit business verification"
                    }
                }
            ),
            404: openapi.Response(
                description="Business profile not found",
                examples={
                    "application/json": {
                        "error": True,
                        "message": "Business profile not found"
                    }
                }
            )
        },
        tags=['Business Verification']
    )
    def get(self, request):
        """Get the current verification status"""
        from accounts.api.serializers import BusinessVerificationStatusSerializer
        from accounts.models import BusinessVerificationSubmission
        
        user = request.user
        
        # Find the user's business profile
        try:
            if user.user_type == 'dealer':
                dealership = Dealership.objects.get(user=user)
                try:
                    submission = dealership.verification_submission
                    serializer = BusinessVerificationStatusSerializer({
                        'status': submission.status,
                        'status_display': submission.get_status_display(),
                        'date_created': submission.date_created,
                        'rejection_reason': submission.rejection_reason
                    })
                    return Response(serializer.data, status=200)
                except BusinessVerificationSubmission.DoesNotExist:
                    return Response({
                        'status': 'not_submitted',
                        'status_display': 'Not Submitted',
                        'submission_date': None,
                        'rejection_reason': None
                    }, status=200)
            elif user.user_type == 'mechanic':
                mechanic = Mechanic.objects.get(user=user)
                try:
                    submission = mechanic.verification_submission
                    serializer = BusinessVerificationStatusSerializer({
                        'status': submission.status,
                        'status_display': submission.get_status_display(),
                        'date_created': submission.date_created,
                        'rejection_reason': submission.rejection_reason
                    })
                    return Response(serializer.data, status=200)
                except BusinessVerificationSubmission.DoesNotExist:
                    return Response({
                        'status': 'not_submitted',
                        'status_display': 'Not Submitted',
                        'submission_date': None,
                        'rejection_reason': None
                    }, status=200)
            else:
                return Response({
                    'error': True,
                    'message': 'Only dealers and mechanics can submit business verification'
                }, status=400)
        except (Dealership.DoesNotExist, Mechanic.DoesNotExist):
            return Response({
                'error': True,
                'message': 'Business profile not found'
            }, status=404)

    @swagger_auto_schema(
        operation_summary="Submit Business Verification",
        operation_description=(
            "Submit business verification details for manual admin approval.\n\n"
            "**Process:**\n"
            "1. Submit this form with all required business details and documents\n"
            "2. Status will be set to `pending`\n"
            "3. Admin reviews the submission in the admin panel\n"
            "4. Admin approves or rejects the verification\n"
            "5. Use GET endpoint to check current status\n\n"
            "**Required Fields:**\n"
            "- business_type: 'dealership' or 'mechanic'\n"
            "- business_name: Official business name\n"
            "- business_address: Full business address\n"
            "- business_email: Business contact email\n"
            "- business_phone: Business contact phone\n\n"
            "**Optional Fields:**\n"
            "- cac_number: Corporate Affairs Commission number\n"
            "- tin_number: Tax Identification Number\n"
            "- cac_document: CAC registration document (file)\n"
            "- tin_document: TIN certificate (file)\n"
            "- proof_of_address: Utility bill or lease agreement (file)\n"
            "- business_license: Business license document (file)\n\n"
            "**Note:** If a submission already exists, it will be updated and status reset to `pending`.\n\n"
            "**Authentication Required:** Yes (Token or JWT)\n"
            "**User Types:** dealer, mechanic only"
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['business_type', 'business_name', 'business_address', 'business_email', 'business_phone'],
            properties={
                'business_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['dealership', 'mechanic'],
                    description='Type of business'
                ),
                'business_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Official business name',
                    example='ABC Motors Limited'
                ),
                'cac_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Corporate Affairs Commission registration number',
                    example='RC123456'
                ),
                'tin_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Tax Identification Number',
                    example='12345678-0001'
                ),
                'business_address': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Full business address',
                    example='123 Main Street, Victoria Island, Lagos'
                ),
                'business_email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description='Business contact email',
                    example='info@abcmotors.com'
                ),
                'business_phone': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Business contact phone number',
                    example='+2348012345678'
                ),
                'cac_document': openapi.Schema(
                    type=openapi.TYPE_FILE,
                    description='CAC registration certificate (PDF, JPG, PNG)'
                ),
                'tin_document': openapi.Schema(
                    type=openapi.TYPE_FILE,
                    description='TIN certificate (PDF, JPG, PNG)'
                ),
                'proof_of_address': openapi.Schema(
                    type=openapi.TYPE_FILE,
                    description='Proof of business address - utility bill or lease (PDF, JPG, PNG)'
                ),
                'business_license': openapi.Schema(
                    type=openapi.TYPE_FILE,
                    description='Business operating license (PDF, JPG, PNG)'
                ),
            }
        ),
        responses={
            201: openapi.Response(
                description="Verification submitted successfully",
                examples={
                    "application/json": {
                        "error": False,
                        "message": "Business verification submitted successfully. Admin will review your submission.",
                        "data": {
                            "id": 1,
                            "uuid": "550e8400-e29b-41d4-a716-446655440000",
                            "business_type": "dealership",
                            "status": "pending",
                            "business_name": "ABC Motors Limited",
                            "cac_number": "RC123456",
                            "tin_number": "12345678-0001",
                            "business_address": "123 Main Street, Victoria Island, Lagos",
                            "business_email": "info@abcmotors.com",
                            "business_phone": "+2348012345678",
                            "rejection_reason": None,
                            "date_created": "2025-10-20T14:30:00Z",
                            "business_verification_status": "Pending Review"
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Validation error or invalid user type",
                examples={
                    "application/json": {
                        "error": True,
                        "message": "Validation failed",
                        "errors": {
                            "business_name": ["This field is required."],
                            "business_email": ["Enter a valid email address."]
                        }
                    }
                }
            )
        },
        tags=['Business Verification']
    )
    def post(self, request):
        """Submit or update business verification details"""
        from accounts.api.serializers import BusinessVerificationSubmissionSerializer
        
        # Validate user type
        if request.user.user_type not in ['dealer', 'mechanic']:
            return Response({
                'error': True,
                'message': 'Only dealers and mechanics can submit business verification'
            }, status=400)
        
        serializer = BusinessVerificationSubmissionSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            submission = serializer.save()
            return Response({
                'error': False,
                'message': 'Business verification submitted successfully. Admin will review your submission.',
                'data': serializer.data
            }, status=201)
        
        return Response({
            'error': True,
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=400)



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
    serializer_class = VerifyPhoneNumberSerializer

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

