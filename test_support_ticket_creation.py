"""
Test script to verify support ticket creation fix
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from accounts.models import Account, Customer
from feedback.models import SupportTicket
from django.test import RequestFactory
from feedback.api.views import SupportTicketViewSet
from rest_framework.test import force_authenticate

def test_ticket_creation():
    """Test that users without customer profiles can create tickets"""
    
    # Get a test user (or create one)
    user = Account.objects.filter(email='boomcash4@gmail.com').first()
    
    if not user:
        print("User not found. Please use an existing user email.")
        return
    
    print(f"Testing with user: {user.email}")
    print(f"User type: {user.user_type}")
    print(f"Has customer profile: {hasattr(user, 'customer')}")
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.post('/api/v1/support/tickets/', {
        'subject': 'Test ticket',
        'severity_level': 'low'
    }, content_type='application/json')
    
    force_authenticate(request, user=user)
    
    # Test the view
    view = SupportTicketViewSet.as_view({'post': 'create'})
    
    try:
        response = view(request)
        print(f"\nResponse status: {response.status_code}")
        print(f"Response data: {response.data}")
        
        if response.status_code == 201:
            print("\n✓ SUCCESS: Ticket created successfully!")
            
            # Check if customer profile was created
            if hasattr(user, 'customer'):
                print(f"✓ Customer profile exists for user")
            else:
                # Refresh from DB
                user.refresh_from_db()
                if hasattr(user, 'customer'):
                    print(f"✓ Customer profile was created")
                else:
                    print(f"✗ WARNING: Customer profile not found")
        else:
            print(f"\n✗ FAILED: {response.data}")
            
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_ticket_creation()
