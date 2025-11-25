import json
import os
import logging
from datetime import timedelta
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
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
from utils.async_email import (
    send_verification_email_async,
    send_welcome_email_async,
    send_otp_email_async,
)
from accounts.utils.email_notifications import (
    send_verification_email, 
    send_welcome_email,
    send_otp_email,
    send_business_verification_status,
    send_booking_confirmation,
    send_inspection_scheduled,
    send_order_confirmation
)
from accounts.utils.welcome_email import send_welcome_email_on_first_login
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
from rest_framework import viewsets
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
    LocationSerializer,
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

# Set up logging
logger = logging.getLogger(__name__)


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
                    Customer.objects.create(user=user, phone_number=data.get('phone_number', ''))
                
                # Generate and save email verification OTP with consistent parameters
                otp = OTP.objects.create(
                    valid_for=user,
                    channel='email',
                    purpose='verification',
                    expires_at=timezone.now() + timedelta(minutes=10)
                )
                verification_code = otp.code

                # Send only verification email asynchronously (non-blocking)
                send_verification_email_async(user, verification_code)
                
                # Emails are sent in background, so we assume success for response
                verification_sent = True
                welcome_sent = True  # Set to True for backward compatibility, but no welcome email sent
                
                # Create OTP for phone verification if phone number exists (but don't send duplicate email)
                phone_number = data.get('phone_number', '')
                if phone_number:
                    otp_code = make_random_otp()
                    # Note: Removed send_otp_email_async call to prevent duplicate emails
                    # Phone verification should use SMS or be handled via separate endpoint
                    otp_sent = True  # Assume success for OTP creation
                    if otp_sent:
                        # Save OTP to database for phone verification
                        OTP.objects.create(
                            valid_for=user,
                            code=otp_code,
                            channel='sms',
                            purpose='phone_verification',
                            expires_at=timezone.now() + timedelta(minutes=10),
                            used=False
                        )
                
                # Prepare response data
                user_data = {
                    "token": str(user.api_token),
                    "email_verified": user.verified_email,
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
        
        # Send welcome email on first login (non-blocking)
        welcome_email_sent = send_welcome_email_on_first_login(user)
        
        data = {
            "id": user.id,
            "email": user.email,
            "token": str(user.api_token),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "user_type": user.user_type,
            "provider": user.provider,
            "is_active": user.is_active,
            "welcome_email_sent": welcome_email_sent,
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
        
        # Log the incoming request for debugging
        logger.info(f"Cart POST - Action: '{action}', Data: {request.data}, Content-Type: {request.content_type}")
        
        customer = Customer.objects.get(user=request.user)
        cart = customer.cart

        if action == "add-to-cart":
            listing_id = request.data.get('listing_id')
            if not listing_id:
                return Response({'error': True, 'message': 'listing_id is required'}, status=400)
            
            try:
                from listings.models import Listing
                listing = Listing.objects.get(uuid=listing_id)
                
                # Check if already in cart
                if cart.filter(uuid=listing_id).exists():
                    return Response({'error': False, 'message': 'Item already in cart'}, status=200)
                
                # Add to cart
                cart.add(listing)
                customer.save()
                return Response({'error': False, 'message': 'Successfully added to cart'}, status=200)
            
            except Listing.DoesNotExist:
                return Response({'error': True, 'message': 'Listing not found'}, status=404)
            except Exception as e:
                return Response({'error': True, 'message': str(e)}, status=400)

        elif action == "remove-from-cart":
            item_id = request.data.get('item')
            if not item_id:
                return Response({'error': True, 'message': 'item is required'}, status=400)
            
            try:
                item = cart.get(uuid=item_id)
                cart.remove(item)
                customer.save()
                return Response({'error': False, 'message': 'Successfully removed from your cart'}, status=200)
            except Exception as e:
                return Response({'error': True, 'message': 'Item not found in cart'}, status=404)
        
        else:
            return Response({'error': True, 'message': 'Invalid action parameter! Use "add-to-cart" or "remove-from-cart"'}, status=400)


class UpdateProfileView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get_user_profile(self,request):
        user = request.user
        user_type = user.user_type
        user_model = {'customer': Customer, 'mechanic': Mechanic, 'dealer': Dealer}.get(user_type)
        if not user_model:
            return None
        return get_object_or_404(user_model, user=user)

    @swagger_auto_schema(
        operation_summary="Update User Profile",
        operation_description=(
            "Update the authenticated user's profile information.\n\n"
            "**Partial Updates Supported:** All fields are optional. Only include fields you want to update.\n\n"
            "**Dealer-Specific Fields:**\n"
            "- `business_name` (optional): Official business name\n"
            "- `cac_number` (optional): Corporate Affairs Commission registration number\n"
            "- `tin_number` (optional): Tax Identification Number\n"
            "- `contact_email` (optional): Business contact email\n"
            "- `contact_phone` (optional): Business contact phone\n"
            "- `about` (optional): Business description\n"
            "- `headline` (optional): Short business tagline\n"
            "- `logo` (optional): Business logo image\n"
            "- `phone_number` (optional): Primary phone number\n"
            "- `location` (optional): Business location ID\n"
            "- `offers_rental` (optional): Boolean - offers rental services\n"
            "- `offers_purchase` (optional): Boolean - offers purchase services\n"
            "- `offers_drivers` (optional): Boolean - offers driver services\n"
            "- `offers_trade_in` (optional): Boolean - offers trade-in services\n"
            "- `extended_services` (optional): Additional services offered\n\n"
            "**Mechanic-Specific Fields:**\n"
            "- `business_name` (optional): Business or workshop name\n"
            "- `contact_email` (optional): Business contact email\n"
            "- `contact_phone` (optional): Business contact phone\n"
            "- `about` (optional): Business description\n"
            "- `headline` (optional): Short business tagline\n"
            "- `logo` (optional): Business logo image\n"
            "- `phone_number` (optional): Primary phone number\n"
            "- `location` (optional): Business location ID\n"
            "- `available` (optional): Boolean - currently accepting jobs\n"
            "- `business_type` (optional): Type of mechanic business\n\n"
            "**Note:** Fields like `cac_number`, `tin_number`, and `business_name` can be left blank "
            "if business verification has not been completed. These fields are automatically populated "
            "when business verification is approved by an admin.\n\n"
            "**Authentication Required:** Yes (Token or JWT)\n"
            "**User Types:** customer, dealer, mechanic"
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                # Common fields
                'about': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Profile description or bio',
                    example='We are a leading car dealership with over 10 years of experience.'
                ),
                'headline': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Short tagline or headline',
                    example='Your Trusted Auto Partner'
                ),
                'logo': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_BINARY,
                    description='Profile logo/image'
                ),
                'phone_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Primary contact phone number',
                    example='+2348012345678'
                ),
                'location': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Location ID reference',
                    example=1
                ),
                # Business verification fields (optional)
                'business_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Official business name (optional - auto-populated on verification approval)',
                    example='ABC Motors Limited'
                ),
                'cac_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='CAC registration number (optional - auto-populated on verification approval)',
                    example='RC123456'
                ),
                'tin_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Tax Identification Number (optional - auto-populated on verification approval)',
                    example='12345678-0001'
                ),
                'contact_email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description='Business contact email (optional)',
                    example='info@abcmotors.com'
                ),
                'contact_phone': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Business contact phone (optional)',
                    example='+2348098765432'
                ),
                # Dealer-specific fields
                'offers_rental': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Dealer only: Offers rental services',
                    example=True
                ),
                'offers_purchase': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Dealer only: Offers purchase services',
                    example=True
                ),
                'offers_drivers': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Dealer only: Offers driver services',
                    example=False
                ),
                'offers_trade_in': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Dealer only: Offers trade-in services',
                    example=True
                ),
                'extended_services': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Dealer only: Additional services offered',
                    example='Vehicle inspection, warranty, financing'
                ),
                # Mechanic-specific fields
                'available': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Mechanic only: Currently accepting jobs',
                    example=True
                ),
                'business_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Mechanic only: Type of mechanic business',
                    example='auto_repair'
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="Profile updated successfully",
                examples={
                    "application/json": {
                        "dealer_partial_update": {
                            "id": 1,
                            "business_name": "ABC Motors Limited",
                            "headline": "Your Trusted Auto Partner",
                            "about": "We are a leading car dealership with over 10 years of experience.",
                            "cac_number": None,
                            "tin_number": None,
                            "contact_email": "info@abcmotors.com",
                            "contact_phone": "+2348098765432",
                            "phone_number": "+2348012345678",
                            "location": 1,
                            "offers_rental": True,
                            "offers_purchase": True,
                            "offers_drivers": False,
                            "offers_trade_in": True,
                            "extended_services": "Vehicle inspection, warranty, financing",
                            "logo": "https://res.cloudinary.com/veyu/image/upload/v1234567890/logos/dealer1.jpg"
                        },
                        "mechanic_partial_update": {
                            "id": 2,
                            "business_name": "Quick Fix Auto Services",
                            "headline": "Fast and Reliable Repairs",
                            "about": "Professional auto repair services with certified mechanics.",
                            "contact_email": "contact@quickfix.com",
                            "contact_phone": "+2347012345678",
                            "phone_number": "+2347012345678",
                            "location": 2,
                            "available": True,
                            "business_type": "auto_repair",
                            "logo": None
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
                            "contact_email": ["Enter a valid email address."],
                            "phone_number": ["This field must be a valid phone number."]
                        }
                    }
                }
            )
        },
        tags=['User Profile']
    )
    def put(self, request:Request):
        from accounts.api.serializers import DealershipUpdateSerializer, MechanicUpdateSerializer
        
        user_type = request.user.user_type
        profile = self.get_user_profile(request)
        
        if not profile:
            return Response({
                'error': True,
                'message': f'Invalid user type: {user_type}'
            }, status=400)
        
        # Use specific update serializers with partial=True for optional fields
        if user_type == 'dealer':
            serializer = DealershipUpdateSerializer(profile, data=request.data, partial=True)
        elif user_type == 'mechanic':
            serializer = MechanicUpdateSerializer(profile, data=request.data, partial=True)
        else:
            # Fall back to generic serializer for customer
            serializer = get_user_serializer(user_type=user_type)
            serializer = serializer(profile, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response({
            'error': True,
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=400)


class BusinessVerificationView(views.APIView):
    """
    Submit business verification details for manual admin approval.
    Supports both POST (create/update) and GET (check status).
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, JWTAuthentication]
    parser_classes = [MultiPartParser, JSONParser]
    
    @swagger_auto_schema(
        operation_summary="Get Business Verification Status",
        operation_description=(
            "Check the current business verification status for the authenticated dealer or mechanic.\n\n"
            "Returns complete business verification information including:\n"
            "- Verification status and submission date\n"
            "- All business details (name, CAC number, TIN number, address, contact info)\n"
            "- Secure Cloudinary URLs for all uploaded documents\n\n"
            "**Statuses:**\n"
            "- `not_submitted`: No verification has been submitted yet\n"
            "- `pending`: Verification submitted and awaiting admin review\n"
            "- `verified`: Verification approved by admin (profile automatically updated)\n"
            "- `rejected`: Verification rejected by admin (check rejection_reason)\n\n"
            "**Authentication Required:** Yes (Token or JWT)\n"
            "**User Types:** dealer, mechanic only"
        ),
        responses={
            200: openapi.Response(
                description="Verification status retrieved successfully",
                examples={
                    "application/json": {
                        "verified_submission": {
                            "status": "verified",
                            "status_display": "Verified",
                            "date_created": "2025-10-20T14:30:00Z",
                            "rejection_reason": None,
                            "business_name": "ABC Motors Limited",
                            "cac_number": "RC123456",
                            "tin_number": "12345678-0001",
                            "business_address": "123 Main Street, Victoria Island, Lagos",
                            "business_email": "info@abcmotors.com",
                            "business_phone": "+2348012345678",
                            "cac_document_url": "https://res.cloudinary.com/veyu/image/upload/v1234567890/verification/cac/doc123.pdf",
                            "tin_document_url": "https://res.cloudinary.com/veyu/image/upload/v1234567890/verification/tin/doc456.pdf",
                            "proof_of_address_url": "https://res.cloudinary.com/veyu/image/upload/v1234567890/verification/address/doc789.pdf",
                            "business_license_url": "https://res.cloudinary.com/veyu/image/upload/v1234567890/verification/license/doc012.pdf"
                        },
                        "pending_submission": {
                            "status": "pending",
                            "status_display": "Pending Review",
                            "date_created": "2025-10-20T14:30:00Z",
                            "rejection_reason": None,
                            "business_name": "XYZ Auto Services",
                            "cac_number": "RC789012",
                            "tin_number": "87654321-0002",
                            "business_address": "456 Commerce Road, Ikeja, Lagos",
                            "business_email": "contact@xyzauto.com",
                            "business_phone": "+2348098765432",
                            "cac_document_url": "https://res.cloudinary.com/veyu/image/upload/v1234567890/verification/cac/doc345.pdf",
                            "tin_document_url": "https://res.cloudinary.com/veyu/image/upload/v1234567890/verification/tin/doc678.pdf",
                            "proof_of_address_url": "https://res.cloudinary.com/veyu/image/upload/v1234567890/verification/address/doc901.pdf",
                            "business_license_url": None
                        },
                        "not_submitted": {
                            "status": "not_submitted",
                            "status_display": "Not Submitted",
                            "date_created": None,
                            "rejection_reason": None,
                            "business_name": None,
                            "cac_number": None,
                            "tin_number": None,
                            "business_address": None,
                            "business_email": None,
                            "business_phone": None,
                            "cac_document_url": None,
                            "tin_document_url": None,
                            "proof_of_address_url": None,
                            "business_license_url": None
                        },
                        "rejected_submission": {
                            "status": "rejected",
                            "status_display": "Rejected",
                            "date_created": "2025-10-15T10:00:00Z",
                            "rejection_reason": "CAC document is not clear. Please resubmit with a higher quality scan.",
                            "business_name": "Quick Fix Mechanics",
                            "cac_number": None,
                            "tin_number": None,
                            "business_address": "789 Industrial Avenue, Apapa, Lagos",
                            "business_email": "info@quickfix.com",
                            "business_phone": "+2347012345678",
                            "cac_document_url": "https://res.cloudinary.com/veyu/image/upload/v1234567890/verification/cac/doc111.pdf",
                            "tin_document_url": None,
                            "proof_of_address_url": None,
                            "business_license_url": None
                        }
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
        """Get complete verification status with business details"""
        from accounts.api.serializers import EnhancedBusinessVerificationStatusSerializer
        from accounts.models import BusinessVerificationSubmission
        
        user = request.user
        
        # Find the user's business profile
        try:
            if user.user_type == 'dealer':
                # Use select_related for query optimization
                dealership = Dealership.objects.select_related('verification_submission').get(user=user)
                try:
                    submission = dealership.verification_submission
                    serializer = EnhancedBusinessVerificationStatusSerializer(submission)
                    return Response(serializer.data, status=200)
                except BusinessVerificationSubmission.DoesNotExist:
                    # Return comprehensive null response when status is 'not_submitted'
                    return Response({
                        'status': 'not_submitted',
                        'status_display': 'Not Submitted',
                        'date_created': None,
                        'rejection_reason': None,
                        'business_name': None,
                        'cac_number': None,
                        'tin_number': None,
                        'business_address': None,
                        'business_email': None,
                        'business_phone': None,
                        'cac_document_url': None,
                        'tin_document_url': None,
                        'proof_of_address_url': None,
                        'business_license_url': None
                    }, status=200)
            elif user.user_type == 'mechanic':
                # Use select_related for query optimization
                mechanic = Mechanic.objects.select_related('verification_submission').get(user=user)
                try:
                    submission = mechanic.verification_submission
                    serializer = EnhancedBusinessVerificationStatusSerializer(submission)
                    return Response(serializer.data, status=200)
                except BusinessVerificationSubmission.DoesNotExist:
                    # Return comprehensive null response when status is 'not_submitted'
                    return Response({
                        'status': 'not_submitted',
                        'status_display': 'Not Submitted',
                        'date_created': None,
                        'rejection_reason': None,
                        'business_name': None,
                        'cac_number': None,
                        'tin_number': None,
                        'business_address': None,
                        'business_email': None,
                        'business_phone': None,
                        'cac_document_url': None,
                        'tin_document_url': None,
                        'proof_of_address_url': None,
                        'business_license_url': None
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
        """Submit or update business verification details with Cloudinary document handling"""
        from accounts.api.serializers import BusinessVerificationSubmissionSerializer
        from accounts.models import BusinessVerificationSubmission, Dealership, Mechanic
        from accounts.utils.document_storage import CloudinaryDocumentStorage
        from accounts.utils.document_validation import (
            CloudinaryConnectionError,
            DocumentUploadError
        )
        from cloudinary.exceptions import Error as CloudinaryError
        
        # Validate user type
        if request.user.user_type not in ['dealer', 'mechanic']:
            return Response({
                'error': True,
                'message': 'Only dealers and mechanics can submit business verification'
            }, status=400)
        
        # Validate business profile exists
        try:
            if request.user.user_type == 'dealer':
                business_profile = Dealership.objects.get(user=request.user)
                business_type = 'dealership'
            else:
                business_profile = Mechanic.objects.get(user=request.user)
                business_type = 'mechanic'
        except (Dealership.DoesNotExist, Mechanic.DoesNotExist):
            return Response({
                'error': True,
                'message': f'Please complete your {request.user.user_type} profile before submitting verification'
            }, status=400)
        
        # Check if submission already exists
        existing_submission = None
        try:
            existing_submission = business_profile.verification_submission
            submission_id = existing_submission.id
        except BusinessVerificationSubmission.DoesNotExist:
            # For new submissions, we'll use a temporary ID that gets updated after creation
            submission_id = 0
        
        # Prepare data for serializer (excluding files)
        data = request.data.copy()
        if 'business_type' not in data:
            data['business_type'] = business_type
        
        # Remove any document fields from data to avoid conflicts with Cloudinary uploads
        document_fields = ['cac_document', 'tin_document', 'proof_of_address', 'business_license']
        for field_name in document_fields:
            if field_name in data:
                logger.info(f"Removing {field_name} from request data to avoid conflicts")
                del data[field_name]
        
        # Validate file uploads using the new validation system
        from accounts.utils.document_validation import (
            validate_business_documents, 
            DocumentValidationError,
            FileSizeExceededError,
            InvalidFileFormatError,
            MaliciousFileError
        )
        
        try:
            file_validation_errors = validate_business_documents(request.FILES)
            if file_validation_errors:
                return Response({
                    'error': True,
                    'message': 'Document validation failed',
                    'code': 'DOCUMENT_VALIDATION_ERROR',
                    'errors': file_validation_errors
                }, status=400)
        except FileSizeExceededError as e:
            return Response({
                'error': True,
                'message': 'File size limit exceeded',
                'code': 'FILE_SIZE_EXCEEDED',
                'details': str(e)
            }, status=400)
        except InvalidFileFormatError as e:
            return Response({
                'error': True,
                'message': 'Invalid file format',
                'code': 'INVALID_FILE_FORMAT',
                'details': str(e)
            }, status=400)
        except MaliciousFileError as e:
            return Response({
                'error': True,
                'message': 'File contains potentially malicious content',
                'code': 'MALICIOUS_FILE_DETECTED',
                'details': str(e)
            }, status=400)
        except DocumentValidationError as e:
            return Response({
                'error': True,
                'message': 'Document validation failed',
                'code': 'DOCUMENT_VALIDATION_ERROR',
                'details': str(e)
            }, status=400)
        
        # Handle document uploads to Cloudinary
        document_upload_results = {}
        document_upload_errors = {}
        
        try:
            storage = CloudinaryDocumentStorage()
            
            for field_name in document_fields:
                if field_name in request.FILES:
                    file = request.FILES[field_name]
                    
                    try:
                        # Upload to Cloudinary
                        logger.info(f"Uploading {field_name} for user {request.user.id}, file: {file.name}, size: {file.size} bytes")
                        
                        upload_result = storage.upload_document(
                            file=file,
                            user_id=request.user.id,
                            submission_id=submission_id or 999999,  # Temporary ID for new submissions
                            document_type=field_name
                        )
                        
                        # Validate upload result contains required fields
                        if not upload_result.get('public_id'):
                            raise ValueError(f"Upload result missing public_id for {field_name}")
                        
                        if not upload_result.get('secure_url'):
                            raise ValueError(f"Upload result missing secure_url for {field_name}")
                        
                        # Verify URL format is correct Cloudinary format
                        secure_url = upload_result['secure_url']
                        if not secure_url.startswith('https://res.cloudinary.com/'):
                            logger.warning(f"Unexpected URL format for {field_name}: {secure_url}")
                        
                        # Store the Cloudinary resource info for the serializer
                        # CloudinaryField expects the public_id as a string
                        data[field_name] = upload_result['public_id']
                        document_upload_results[field_name] = upload_result
                        
                        logger.debug(f"Stored {field_name} public_id in data: {data[field_name]}")
                        
                        # Store metadata
                        data[f'{field_name}_uploaded_at'] = timezone.now()
                        data[f'{field_name}_original_name'] = file.name
                        
                        # Log successful upload with full details
                        logger.info(
                            f"Successfully uploaded {field_name}: "
                            f"public_id={upload_result['public_id']}, "
                            f"url={secure_url}, "
                            f"format={upload_result.get('format')}, "
                            f"size={upload_result.get('bytes')} bytes"
                        )
                        
                    except CloudinaryError as e:
                        error_msg = f"Cloudinary upload failed for {field_name}: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        document_upload_errors[field_name] = {
                            'message': error_msg,
                            'code': 'CLOUDINARY_UPLOAD_ERROR',
                            'field': field_name
                        }
                    except ValueError as e:
                        error_msg = f"Upload validation failed for {field_name}: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        document_upload_errors[field_name] = {
                            'message': error_msg,
                            'code': 'UPLOAD_VALIDATION_ERROR',
                            'field': field_name
                        }
                    except Exception as e:
                        error_msg = f"Unexpected error uploading {field_name}: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        document_upload_errors[field_name] = {
                            'message': error_msg,
                            'code': 'UPLOAD_ERROR',
                            'field': field_name
                        }
        
        except CloudinaryError as e:
            logger.error(f"Cloudinary service unavailable: {str(e)}")
            return Response({
                'error': True,
                'message': 'Document upload service unavailable',
                'code': 'CLOUDINARY_SERVICE_ERROR',
                'details': str(e)
            }, status=503)
        except Exception as e:
            logger.error(f"Document upload initialization failed: {str(e)}")
            return Response({
                'error': True,
                'message': 'Document upload service initialization failed',
                'code': 'UPLOAD_SERVICE_ERROR',
                'details': str(e)
            }, status=503)
        
        # If there were upload errors, return them
        if document_upload_errors:
            # Clean up any successful uploads
            for field_name, result in document_upload_results.items():
                try:
                    storage.delete_document(result['public_id'])
                    logger.info(f"Cleaned up uploaded document: {result['public_id']}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup document {result['public_id']}: {str(cleanup_error)}")
            
            return Response({
                'error': True,
                'message': 'Document upload failed',
                'code': 'DOCUMENT_UPLOAD_FAILED',
                'errors': document_upload_errors
            }, status=400)
        
        # Create or update submission with Cloudinary URLs
        # Debug logging to see what data we're passing to the serializer
        logger.info(f"Data being passed to serializer: {list(data.keys())}")
        for field_name in document_fields:
            if field_name in data:
                logger.info(f"Serializer data[{field_name}] = {data[field_name]} (type: {type(data[field_name])})")
            else:
                logger.info(f"Field {field_name} not in serializer data")
        
        if existing_submission:
            # Update existing submission
            serializer = BusinessVerificationSubmissionSerializer(
                existing_submission,
                data=data,
                context={'request': request},
                partial=True
            )
        else:
            # Create new submission
            serializer = BusinessVerificationSubmissionSerializer(
                data=data,
                context={'request': request}
            )
        
        if serializer.is_valid():
            try:
                submission = serializer.save()
                
                # Validate that document URLs are properly stored in the database
                validation_errors = []
                for field_name in document_fields:
                    if field_name in document_upload_results:
                        # Get the field value from the saved submission
                        field_value = getattr(submission, field_name, None)
                        
                        # Check if the field is null or empty
                        if not field_value:
                            error_msg = f"Document {field_name} was uploaded but not saved to database (null value)"
                            logger.error(error_msg)
                            validation_errors.append({
                                'field': field_name,
                                'error': 'Document not saved to database',
                                'public_id': document_upload_results[field_name]['public_id']
                            })
                            continue
                        
                        # Verify the field has a URL property
                        try:
                            if hasattr(field_value, 'url'):
                                document_url = field_value.url
                                
                                # Verify URL format
                                if not document_url or not document_url.startswith('https://res.cloudinary.com/'):
                                    error_msg = f"Document {field_name} has invalid URL format: {document_url}"
                                    logger.error(error_msg)
                                    validation_errors.append({
                                        'field': field_name,
                                        'error': 'Invalid URL format',
                                        'url': document_url
                                    })
                                else:
                                    logger.info(f"Validated {field_name} URL: {document_url}")
                            else:
                                error_msg = f"Document {field_name} field does not have URL property"
                                logger.error(error_msg)
                                validation_errors.append({
                                    'field': field_name,
                                    'error': 'Field missing URL property'
                                })
                        except Exception as e:
                            error_msg = f"Error validating {field_name} URL: {str(e)}"
                            logger.error(error_msg, exc_info=True)
                            validation_errors.append({
                                'field': field_name,
                                'error': str(e)
                            })
                
                # If validation errors occurred, log them but don't fail the request
                # (documents were uploaded successfully, this is a storage issue)
                if validation_errors:
                    logger.error(f"Document URL validation errors: {validation_errors}")
                    # Note: We don't return an error here because the documents are in Cloudinary
                    # The admin can still access them via the public_id
                
                # Update Cloudinary folder structure for new submissions
                if not existing_submission and document_upload_results:
                    self._update_cloudinary_folders(
                        storage, 
                        document_upload_results, 
                        request.user.id, 
                        submission.id
                    )
                
                # Send notification email about submission
                try:
                    from accounts.utils.email_notifications import send_business_verification_status
                    send_business_verification_status(
                        request.user, 
                        'submitted', 
                        'Your business verification has been submitted and is pending review.'
                    )
                except Exception as e:
                    logger.error(f"Failed to send verification submission email: {str(e)}")
                
                # Prepare response with upload progress information
                response_data = serializer.data.copy()
                
                # Add upload progress information
                if document_upload_results:
                    response_data['upload_summary'] = {
                        'total_files': len(document_upload_results),
                        'uploaded_files': list(document_upload_results.keys()),
                        'upload_details': {
                            field: {
                                'public_id': result['public_id'],
                                'secure_url': result['secure_url'],
                                'file_size': result['bytes'],
                                'format': result['format'],
                                'uploaded_at': data.get(f'{field}_uploaded_at')
                            }
                            for field, result in document_upload_results.items()
                        }
                    }
                
                # Add validation warnings if any
                if validation_errors:
                    response_data['validation_warnings'] = validation_errors
                
                return Response({
                    'error': False,
                    'message': 'Business verification submitted successfully. Admin will review your submission.',
                    'data': response_data
                }, status=201 if not existing_submission else 200)
                
            except Exception as e:
                # Clean up uploaded documents if submission creation fails
                for field_name, result in document_upload_results.items():
                    try:
                        storage.delete_document(result['public_id'])
                    except Exception:
                        pass
                
                logger.error(f"Failed to save submission: {str(e)}")
                return Response({
                    'error': True,
                    'message': 'Failed to save verification submission',
                    'details': str(e)
                }, status=500)
        
        # Clean up uploaded documents if validation fails
        for field_name, result in document_upload_results.items():
            try:
                storage.delete_document(result['public_id'])
            except Exception:
                pass
        
        logger.error(f"Serializer validation failed: {serializer.errors}")
        return Response({
            'error': True,
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=400)
    
    def _update_cloudinary_folders(self, storage, upload_results, user_id, submission_id):
        """
        Update Cloudinary folder structure for new submissions
        This re-uploads documents with the correct submission ID
        """
        try:
            for field_name, result in upload_results.items():
                old_public_id = result['public_id']
                
                # Generate new public ID with correct submission ID
                new_public_id = storage._generate_public_id(
                    result.get('original_filename', 'document'),
                    user_id,
                    submission_id,
                    field_name
                )
                
                # Rename the resource in Cloudinary
                try:
                    import cloudinary.uploader
                    cloudinary.uploader.rename(old_public_id, new_public_id)
                    logger.info(f"Updated Cloudinary folder for {field_name}: {old_public_id} -> {new_public_id}")
                except Exception as e:
                    logger.warning(f"Failed to rename Cloudinary resource {old_public_id}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Failed to update Cloudinary folders: {str(e)}")


class DocumentViewingView(APIView):
    """
    Generate secure URLs for document viewing
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, JWTAuthentication]
    
    @swagger_auto_schema(
        operation_summary="Get Secure Document URL",
        operation_description=(
            "Generate a secure, time-limited URL for viewing a business verification document.\n\n"
            "**Authentication Required:** Yes (Token or JWT)\n"
            "**Access Control:** Users can only access their own documents, admins can access all documents"
        ),
        manual_parameters=[
            openapi.Parameter(
                'submission_id', 
                openapi.IN_PATH, 
                description='Business verification submission ID', 
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'document_type', 
                openapi.IN_PATH, 
                description='Type of document (cac_document, tin_document, proof_of_address, business_license)', 
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'expires_in', 
                openapi.IN_QUERY, 
                description='URL expiration time in seconds (default: 3600)', 
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: openapi.Response(
                description="Secure URL generated successfully",
                examples={
                    "application/json": {
                        "error": False,
                        "secure_url": "https://res.cloudinary.com/...",
                        "expires_in": 3600,
                        "document_type": "cac_document"
                    }
                }
            ),
            403: "Access denied - not authorized to view this document",
            404: "Document or submission not found"
        },
        tags=['Business Verification']
    )
    def get(self, request, submission_id, document_type):
        """Generate secure URL for document viewing with access control"""
        from accounts.models import BusinessVerificationSubmission, DocumentAccessLog
        from accounts.utils.document_storage import CloudinaryDocumentStorage
        
        # Validate document type
        valid_document_types = ['cac_document', 'tin_document', 'proof_of_address', 'business_license']
        if document_type not in valid_document_types:
            return Response({
                'error': True,
                'message': f'Invalid document type. Must be one of: {", ".join(valid_document_types)}'
            }, status=400)
        
        # Get expiration time from query params
        expires_in = int(request.GET.get('expires_in', 3600))  # Default 1 hour
        
        try:
            # Get the submission
            submission = BusinessVerificationSubmission.objects.get(id=submission_id)
            
            # Check access permissions
            user = request.user
            has_access = False
            
            # Users can access their own documents
            if submission.dealership and submission.dealership.user == user:
                has_access = True
            elif submission.mechanic and submission.mechanic.user == user:
                has_access = True
            # Admins and staff can access all documents
            elif user.is_staff or user.is_superuser:
                has_access = True
            
            if not has_access:
                return Response({
                    'error': True,
                    'message': 'Access denied - you are not authorized to view this document'
                }, status=403)
            
            # Get the document field
            document = getattr(submission, document_type, None)
            if not document or not hasattr(document, 'public_id'):
                return Response({
                    'error': True,
                    'message': f'Document {document_type} not found for this submission'
                }, status=404)
            
            # Generate secure URL
            try:
                storage = CloudinaryDocumentStorage()
                secure_url = storage.get_secure_url(document.public_id, expires_in)
                
                # Log the access attempt
                try:
                    DocumentAccessLog.objects.create(
                        submission=submission,
                        document_type=document_type,
                        accessed_by=user,
                        access_type='view',
                        ip_address=self._get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
                    )
                except Exception as log_error:
                    logger.warning(f"Failed to log document access: {str(log_error)}")
                
                return Response({
                    'error': False,
                    'secure_url': secure_url,
                    'expires_in': expires_in,
                    'document_type': document_type,
                    'submission_id': submission_id
                }, status=200)
                
            except Exception as e:
                logger.error(f"Failed to generate secure URL for {document_type}: {str(e)}")
                return Response({
                    'error': True,
                    'message': 'Failed to generate secure document URL',
                    'details': str(e)
                }, status=500)
                
        except BusinessVerificationSubmission.DoesNotExist:
            return Response({
                'error': True,
                'message': 'Business verification submission not found'
            }, status=404)
        except Exception as e:
            logger.error(f"Unexpected error in document viewing: {str(e)}")
            return Response({
                'error': True,
                'message': 'An unexpected error occurred',
                'details': str(e)
            }, status=500)
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class VerifyEmailView(APIView):
    allowed_methods = ['POST']
    serializer_class = VerifyEmailSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, JWTAuthentication]

    def post(self, request: Request):
        data = request.data
        serializer = VerifyEmailSerializer(data=data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        
        if validated_data['action'] == 'request-code':
            return self._handle_request_code(request, is_resend=False)
        elif validated_data['action'] == 'resend-code':
            return self._handle_request_code(request, is_resend=True)
        elif validated_data['action'] == 'confirm-code':
            return self._handle_confirm_code(request)
        
        return Response({
            'error': True,
            'message': 'Invalid action'
        }, status=status.HTTP_400_BAD_REQUEST)

    def _handle_request_code(self, request: Request, is_resend: bool = False):
        """Handle both initial code requests and resend requests with proper rate limiting and logging."""
        try:
            from utils.otp_manager import otp_manager
            
            # Get client information for security logging
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            action_type = "resend" if is_resend else "initial request"
            
            # Log the attempt
            logger.info(f"Email verification {action_type} attempt for user {request.user.email} from IP {ip_address}")
            
            # Check if email is already verified
            if request.user.verified_email:
                logger.warning(f"Email verification {action_type} attempted for already verified user {request.user.email}")
                return Response({
                    'error': True,
                    'message': 'Email address is already verified',
                    'error_code': 'already_verified'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # For resend requests, check additional rate limiting
            if is_resend:
                resend_check = otp_manager.check_resend_cooldown(request.user.id, 'email')
                if not resend_check['allowed']:
                    logger.warning(f"Resend cooldown active for user {request.user.email}: {resend_check.get('remaining_seconds', 0)} seconds remaining")
                    return Response({
                        'error': True,
                        'message': resend_check['message'],
                        'error_code': 'resend_cooldown',
                        'retry_after_seconds': resend_check.get('remaining_seconds', 0)
                    }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Request OTP using enhanced manager
            otp_request = otp_manager.request_otp(
                user=request.user,
                channel='email',
                purpose='verification',
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            if not otp_request['success']:
                error_message = otp_request['message']
                logger.warning(f"Email verification {action_type} failed for user {request.user.email}: {error_message}")
                
                # Determine appropriate status code based on error type
                status_code = status.HTTP_429_TOO_MANY_REQUESTS if 'limit' in error_message.lower() else status.HTTP_400_BAD_REQUEST
                
                return Response({
                    'error': True,
                    'message': error_message,
                    'error_code': 'rate_limited' if 'limit' in error_message.lower() else 'request_failed',
                    'rate_limit': otp_request.get('rate_limit'),
                    'cooldown': otp_request.get('cooldown')
                }, status=status_code)
            
            # Send OTP email using enhanced manager
            send_result = otp_manager.send_otp_email(request.user, otp_request['otp'])
            
            if send_result['success']:
                expires_in = int((otp_request['otp'].expires_at - timezone.now()).total_seconds() / 60)
                
                # Update resend cooldown for successful sends
                if is_resend:
                    otp_manager.set_resend_cooldown(request.user.id, 'email')
                
                logger.info(f"Email verification {action_type} successful for user {request.user.email}, expires in {expires_in} minutes")
                
                return Response({
                    'error': False,
                    'message': f'Verification code {"resent" if is_resend else "sent"} successfully',
                    'expires_in_minutes': expires_in,
                    'delivery_tracking': send_result.get('tracking', {}),
                    'next_resend_allowed_in': otp_manager.RESEND_COOLDOWN_MINUTES * 60 if is_resend else None
                }, status=status.HTTP_200_OK)
            else:
                # Mark OTP as used if sending failed
                otp_request['otp'].mark_as_used()
                
                logger.error(f"Email verification {action_type} send failed for user {request.user.email}: {send_result['message']}")
                
                return Response({
                    'error': True,
                    'message': f'Failed to {"resend" if is_resend else "send"} verification code. Please try again.',
                    'error_code': 'send_failed',
                    'delivery_tracking': send_result.get('tracking', {})
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as error:
            logger.error(f"Error during email verification {action_type} for user {request.user.email}: {str(error)}", exc_info=True)
            return Response({
                'error': True,
                'message': f'An error occurred while {"resending" if is_resend else "sending"} verification code. Please try again.',
                'error_code': 'system_error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _handle_confirm_code(self, request: Request):
        """Handle email verification code confirmation."""
        try:
            from utils.otp_manager import otp_manager
            
            data = request.data
            otp_code = data.get('code', '').strip()
            
            if not otp_code:
                return Response({
                    'error': True,
                    'message': 'OTP code is required',
                    'error_code': 'missing_code'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get client information for security logging
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            logger.info(f"Email verification confirmation attempt for user {request.user.email} from IP {ip_address}")
            
            # Verify OTP using enhanced manager
            verify_result = otp_manager.verify_otp(
                user=request.user,
                otp_code=otp_code,
                channel='email',
                purpose='verification',
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            if verify_result['success']:
                logger.info(f"Email verification successful for user {request.user.email}")
                return Response({
                    'error': False,
                    'message': verify_result['message']
                }, status=status.HTTP_200_OK)
            else:
                logger.warning(f"Email verification failed for user {request.user.email}: {verify_result['message']}")
                return Response({
                    'error': True,
                    'message': verify_result['message'],
                    'error_code': 'verification_failed'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as error:
            logger.error(f"Error verifying email OTP for user {request.user.email}: {str(error)}", exc_info=True)
            return Response({
                'error': True,
                'message': 'An error occurred during verification. Please try again.',
                'error_code': 'system_error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class VerifyPhoneNumberView(APIView):
    allowed_methods = ['POST']
    permission_classes = [IsAuthenticated]
    serializer_class = VerifyPhoneNumberSerializer

    def post(self, request: Request):
        data = request.data
        serializer = VerifyPhoneNumberSerializer(data=data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        
        if validated_data['action'] == 'request-code':
            try:
                from utils.otp_manager import otp_manager
                
                phone_number = data.get('phone_number', '').strip()
                
                if not phone_number:
                    return Response({
                        'error': True,
                        'message': 'Phone number is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Get client information for security logging
                ip_address = request.META.get('REMOTE_ADDR')
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                
                # Request OTP using enhanced manager
                otp_request = otp_manager.request_otp(
                    user=request.user,
                    channel='sms',
                    purpose='phone_verification',
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                if not otp_request['success']:
                    return Response({
                        'error': True,
                        'message': otp_request['message'],
                        'rate_limit': otp_request.get('rate_limit'),
                        'cooldown': otp_request.get('cooldown')
                    }, status=status.HTTP_429_TOO_MANY_REQUESTS if 'limit' in otp_request['message'] else status.HTTP_400_BAD_REQUEST)
                
                # Send OTP SMS using enhanced manager
                send_result = otp_manager.send_otp_sms(request.user, otp_request['otp'], phone_number)
                
                if send_result['success']:
                    expires_in = int((otp_request['otp'].expires_at - timezone.now()).total_seconds() / 60)
                    return Response({
                        'error': False,
                        'message': send_result['message'],
                        'expires_in_minutes': expires_in,
                        'delivery_tracking': send_result.get('tracking', {})
                    }, status=status.HTTP_200_OK)
                else:
                    # Mark OTP as used if sending failed
                    otp_request['otp'].mark_as_used()
                    return Response({
                        'error': True,
                        'message': send_result['message'],
                        'delivery_tracking': send_result.get('tracking', {})
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            except Exception as error:
                logger.error(f"Error requesting SMS OTP for user {request.user.email}: {str(error)}")
                return Response({
                    'error': True,
                    'message': 'An error occurred while sending OTP. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif validated_data['action'] == 'confirm-code':
            try:
                from utils.otp_manager import otp_manager
                
                otp_code = data.get('code', '').strip()
                
                if not otp_code:
                    return Response({
                        'error': True,
                        'message': 'OTP code is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Get client information for security logging
                ip_address = request.META.get('REMOTE_ADDR')
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                
                # Verify OTP using enhanced manager
                verify_result = otp_manager.verify_otp(
                    user=request.user,
                    otp_code=otp_code,
                    channel='sms',
                    purpose='phone_verification',
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                if verify_result['success']:
                    return Response({
                        'error': False,
                        'message': verify_result['message']
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'error': True,
                        'message': verify_result['message']
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Exception as error:
                logger.error(f"Error verifying SMS OTP for user {request.user.email}: {str(error)}")
                return Response({
                    'error': True,
                    'message': 'An error occurred during verification. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'error': True,
            'message': 'Invalid action'
        }, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailUnauthenticatedView(APIView):
    """
    Unauthenticated email verification endpoint that allows users to verify their email
    without requiring authentication. This addresses the 401 error issue during verification.
    """
    permission_classes = [AllowAny]
    allowed_methods = ['POST']

    @swagger_auto_schema(
        operation_summary="Verify email without authentication",
        operation_description=(
            "Verify email address using verification code without requiring user authentication.\n\n"
            "This endpoint allows users to verify their email after signup even if they are not logged in.\n"
            "It accepts email and verification code, validates the code, and marks the email as verified.\n\n"
            "**Required Fields:**\n"
            "- email: The email address to verify\n"
            "- code: The verification code sent to the email\n\n"
            "**Error Handling:**\n"
            "- Returns specific error messages for invalid codes, expired codes, or missing accounts\n"
            "- Includes security logging for verification attempts\n"
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'code'],
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description='Email address to verify',
                    example='user@example.com'
                ),
                'code': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Verification code sent to email',
                    example='123456'
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="Email verified successfully",
                examples={
                    "application/json": {
                        "error": False,
                        "message": "Email verified successfully"
                    }
                }
            ),
            400: openapi.Response(
                description="Validation error or invalid code",
                examples={
                    "application/json": {
                        "error": True,
                        "message": "Invalid or expired verification code"
                    }
                }
            ),
            404: openapi.Response(
                description="Account not found",
                examples={
                    "application/json": {
                        "error": True,
                        "message": "Account not found"
                    }
                }
            )
        },
        tags=['Authentication']
    )
    def post(self, request: Request):
        try:
            email = request.data.get('email', '').strip().lower()
            code = request.data.get('code', '').strip()
            
            # Validate required fields
            if not email:
                return Response({
                    'error': True,
                    'message': 'Email is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not code:
                return Response({
                    'error': True,
                    'message': 'Verification code is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Find the user account
            try:
                user = Account.objects.get(email=email)
            except Account.DoesNotExist:
                logger.warning(f"Email verification attempted for non-existent account: {email}")
                return Response({
                    'error': True,
                    'message': 'Account not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if email is already verified
            if user.verified_email:
                return Response({
                    'error': False,
                    'message': 'Email is already verified'
                }, status=status.HTTP_200_OK)
            
            # Find the most recent unused verification OTP for this user
            otp = OTP.objects.filter(
                valid_for=user,
                code=code,
                channel='email',
                purpose='verification',
                used=False
            ).order_by('-date_created').first()
            
            if not otp:
                logger.warning(f"Invalid verification code attempted for user {email}")
                return Response({
                    'error': True,
                    'message': 'Invalid or expired verification code'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify the OTP using the model's verify method
            if otp.verify(code, user):
                logger.info(f"Email successfully verified for user {email}")
                return Response({
                    'error': False,
                    'message': 'Email verified successfully'
                }, status=status.HTTP_200_OK)
            else:
                # The verify method handles logging internally
                return Response({
                    'error': True,
                    'message': 'Invalid or expired verification code'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as error:
            logger.error(f"Error during unauthenticated email verification: {str(error)}")
            return Response({
                'error': True,
                'message': 'An error occurred during verification. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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



class LocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user locations.
    
    Supports:
    - POST /api/v1/locations/ - Create new location
    - GET /api/v1/locations/ - List user's locations
    - GET /api/v1/locations/{id}/ - Retrieve specific location
    - PUT /api/v1/locations/{id}/ - Update location
    - PATCH /api/v1/locations/{id}/ - Partial update location
    - DELETE /api/v1/locations/{id}/ - Delete location
    """
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, JWTAuthentication]
    
    def get_queryset(self):
        """Return only locations belonging to the authenticated user"""
        return Location.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Automatically associate location with authenticated user"""
        serializer.save(user=self.request.user)
    
    @swagger_auto_schema(
        operation_summary="Create a new location",
        operation_description=(
            "Create a new location for the authenticated user.\n\n"
            "**Required Fields:**\n"
            "- `state`: State/province (min 2 characters)\n"
            "- `address`: Street address (min 5 characters)\n\n"
            "**Optional Fields:**\n"
            "- `country`: Country code (default: 'NG')\n"
            "- `city`: City name\n"
            "- `zip_code`: Postal code\n"
            "- `lat`: Latitude (-90 to 90)\n"
            "- `lng`: Longitude (-180 to 180)\n"
            "- `google_place_id`: Google Places ID\n\n"
            "**Authentication Required:** Yes"
        ),
        responses={
            201: openapi.Response(
                description="Location created successfully",
                schema=LocationSerializer
            ),
            400: "Validation error"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="List user's locations",
        operation_description="Retrieve all locations belonging to the authenticated user.",
        responses={200: LocationSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Retrieve a location",
        operation_description="Get details of a specific location.",
        responses={
            200: LocationSerializer,
            404: "Location not found"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Update a location",
        operation_description="Update all fields of a location.",
        responses={
            200: LocationSerializer,
            400: "Validation error",
            404: "Location not found"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Partially update a location",
        operation_description="Update specific fields of a location.",
        responses={
            200: LocationSerializer,
            400: "Validation error",
            404: "Location not found"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Delete a location",
        operation_description="Delete a location.",
        responses={
            204: "Location deleted successfully",
            404: "Location not found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
