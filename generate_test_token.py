"""
Generate a fresh JWT token for testing
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from accounts.models import Account
from accounts.authentication import TokenManager

# Get the dealer user with ID 69 (from the token)
try:
    user = Account.objects.get(id=69)
    print(f"Generating tokens for user: {user.email}")
    print(f"User ID: {user.id}")
    print(f"User Type: {user.user_type}")
    
    # Generate fresh tokens
    tokens = TokenManager.create_tokens_for_user(user)
    
    print("\n=== FRESH TOKENS ===")
    print(f"\nAccess Token:")
    print(tokens['access'])
    print(f"\nRefresh Token:")
    print(tokens['refresh'])
    print(f"\nAccess Expires: {tokens['access_expires']}")
    print(f"\nRefresh Expires: {tokens['refresh_expires']}")
    
    print("\n=== USE THIS IN YOUR FRONTEND ===")
    print(f"Authorization: Bearer {tokens['access']}")
    
except Account.DoesNotExist:
    print("User with ID 69 not found. Available dealer users:")
    dealers = Account.objects.filter(user_type='dealer')
    for dealer in dealers:
        print(f"  - {dealer.email} (ID: {dealer.id})")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
