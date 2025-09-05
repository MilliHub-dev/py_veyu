"""
Veyu API Documentation Configuration
==================================

This module contains comprehensive API documentation schemas, examples, and configurations
for the Veyu platform API endpoints.
"""

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

# Common response schemas
success_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Request success status'),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Response message'),
        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='Response data')
    }
)

error_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Request success status'),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message'),
        'errors': openapi.Schema(type=openapi.TYPE_OBJECT, description='Detailed error information')
    }
)

# User schemas
user_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
        'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email'),
        'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name'),
        'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name'),
        'user_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['customer', 'mechanic', 'dealer']),
        'verified_email': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Email verification status'),
        'provider': openapi.Schema(type=openapi.TYPE_STRING, enum=['veyu', 'google', 'apple', 'facebook']),
        'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number'),
        'date_joined': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
    }
)

# Vehicle schemas
vehicle_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Vehicle ID'),
        'title': openapi.Schema(type=openapi.TYPE_STRING, description='Vehicle title'),
        'make': openapi.Schema(type=openapi.TYPE_STRING, description='Vehicle make'),
        'model': openapi.Schema(type=openapi.TYPE_STRING, description='Vehicle model'),
        'year': openapi.Schema(type=openapi.TYPE_INTEGER, description='Manufacturing year'),
        'price': openapi.Schema(type=openapi.TYPE_STRING, description='Vehicle price'),
        'condition': openapi.Schema(type=openapi.TYPE_STRING, enum=['new', 'used-foreign', 'used-local']),
        'mileage': openapi.Schema(type=openapi.TYPE_INTEGER, description='Vehicle mileage'),
        'fuel_type': openapi.Schema(type=openapi.TYPE_STRING, description='Fuel type'),
        'transmission': openapi.Schema(type=openapi.TYPE_STRING, description='Transmission type'),
        'features': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
        'images': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
        'dealer': openapi.Schema(type=openapi.TYPE_OBJECT, description='Dealer information'),
        'available_for_rent': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Rental availability'),
        'available_for_sale': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Sale availability')
    }
)

# Service booking schemas
service_booking_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Booking ID'),
        'type': openapi.Schema(type=openapi.TYPE_STRING, enum=['emergency', 'routine']),
        'customer': openapi.Schema(type=openapi.TYPE_OBJECT, description='Customer information'),
        'mechanic': openapi.Schema(type=openapi.TYPE_OBJECT, description='Mechanic information'),
        'services': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
        'problem_description': openapi.Schema(type=openapi.TYPE_STRING, description='Problem description'),
        'booking_status': openapi.Schema(
            type=openapi.TYPE_STRING, 
            enum=['accepted', 'canceled', 'completed', 'declined', 'expired', 'requested', 'working']
        ),
        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
        'started_on': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
        'ended_on': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
        'total_cost': openapi.Schema(type=openapi.TYPE_STRING, description='Total service cost')
    }
)

# Wallet schemas
wallet_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Wallet ID'),
        'user': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
        'ledger_balance': openapi.Schema(type=openapi.TYPE_STRING, description='Total wallet balance'),
        'available_balance': openapi.Schema(type=openapi.TYPE_STRING, description='Available balance for withdrawal'),
        'currency': openapi.Schema(type=openapi.TYPE_STRING, description='Currency code', default='NGN'),
        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
    }
)

transaction_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Transaction ID'),
        'amount': openapi.Schema(type=openapi.TYPE_STRING, description='Transaction amount'),
        'type': openapi.Schema(
            type=openapi.TYPE_STRING, 
            enum=['payment', 'charge', 'transfer_out', 'transfer_in', 'deposit', 'withdraw']
        ),
        'status': openapi.Schema(type=openapi.TYPE_STRING, enum=['pending', 'completed', 'failed', 'locked']),
        'narration': openapi.Schema(type=openapi.TYPE_STRING, description='Transaction description'),
        'sender': openapi.Schema(type=openapi.TYPE_STRING, description='Sender name'),
        'recipient': openapi.Schema(type=openapi.TYPE_STRING, description='Recipient name'),
        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
    }
)

# API Documentation Examples
API_EXAMPLES = {
    'auth_register': {
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password": "SecurePass123!",
        "confirm_password": "SecurePass123!",
        "user_type": "customer",
        "provider": "veyu",
        "phone_number": "+2348123456789"
    },
    'auth_login': {
        "email": "john.doe@example.com",
        "password": "SecurePass123!",
        "provider": "veyu"
    },
    'vehicle_create': {
        "title": "2023 Toyota Camry LE",
        "make": "Toyota",
        "model": "Camry",
        "year": 2023,
        "price": "25000000",
        "condition": "new",
        "mileage": 0,
        "fuel_type": "Petrol",
        "transmission": "Automatic",
        "features": ["Air Conditioning", "Android Auto", "Keyless Entry"],
        "available_for_sale": True,
        "available_for_rent": False,
        "description": "Brand new Toyota Camry with all modern features"
    },
    'service_booking': {
        "type": "routine",
        "mechanic_id": 1,
        "services": [1, 2, 3],
        "problem_description": "Car needs regular maintenance service",
        "preferred_date": "2024-01-15T10:00:00Z",
        "location": {
            "address": "123 Main Street, Lagos",
            "latitude": 6.5244,
            "longitude": 3.3792
        }
    },
    'wallet_transfer': {
        "recipient_wallet_id": 2,
        "amount": "5000.00",
        "narration": "Payment for vehicle rental"
    }
}

# Common API decorators
def api_response_schema(success_schema=None, error_schema=None):
    """Generate common API response schema decorator."""
    responses = {
        400: openapi.Response(description="Bad Request", schema=error_response_schema),
        401: openapi.Response(description="Unauthorized", schema=error_response_schema),
        403: openapi.Response(description="Forbidden", schema=error_response_schema),
        404: openapi.Response(description="Not Found", schema=error_response_schema),
        500: openapi.Response(description="Internal Server Error", schema=error_response_schema)
    }
    
    if success_schema:
        responses[200] = openapi.Response(description="Success", schema=success_schema)
    
    return responses

# Swagger parameter definitions
COMMON_PARAMETERS = {
    'page': openapi.Parameter(
        'page',
        openapi.IN_QUERY,
        description="Page number for pagination",
        type=openapi.TYPE_INTEGER,
        default=1
    ),
    'page_size': openapi.Parameter(
        'page_size',
        openapi.IN_QUERY,
        description="Number of items per page",
        type=openapi.TYPE_INTEGER,
        default=20
    ),
    'search': openapi.Parameter(
        'search',
        openapi.IN_QUERY,
        description="Search query",
        type=openapi.TYPE_STRING
    ),
    'ordering': openapi.Parameter(
        'ordering',
        openapi.IN_QUERY,
        description="Field to order by (prefix with - for descending)",
        type=openapi.TYPE_STRING
    )
}