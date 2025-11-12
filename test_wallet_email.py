#!/usr/bin/env python
"""
Test the new wallet transaction email template.
"""
import os
import sys
import django
from pathlib import Path
from datetime import datetime

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.utils.email_notifications import send_wallet_transaction

User = get_user_model()

def create_test_user():
    """Create or get a test user."""
    try:
        user = User.objects.get(email='ekeminieffiong22@gmail.com')
    except User.DoesNotExist:
        user = User(
            email='ekeminieffiong22@gmail.com',
            first_name='Test',
            last_name='User'
        )
    return user

def main():
    print("💰 WALLET TRANSACTION EMAIL TEST")
    print("=" * 60)
    
    user = create_test_user()
    
    # Test 1: Credit Transaction
    print("\n1. Testing credit transaction email...")
    result = send_wallet_transaction(user, {
        'transaction_type': 'Credit',
        'amount': '₦50,000.00',
        'balance': '₦125,000.00',
        'reference': 'TXN-2025-001234',
        'description': 'Wallet funding via bank transfer',
        'timestamp': datetime.now().strftime('%B %d, %Y at %I:%M %p'),
        'payment_method': 'Bank Transfer',
        'status': 'Completed',
        'wallet_url': 'https://veyu.cc/wallet'
    })
    print("✅ Credit email sent" if result else "❌ Credit email failed")
    
    # Test 2: Debit Transaction
    print("\n2. Testing debit transaction email...")
    result = send_wallet_transaction(user, {
        'transaction_type': 'Debit',
        'amount': '₦25,000.00',
        'balance': '₦100,000.00',
        'reference': 'TXN-2025-001235',
        'description': 'Payment for Toyota Camry 2020',
        'timestamp': datetime.now().strftime('%B %d, %Y at %I:%M %p'),
        'payment_method': 'Wallet Balance',
        'status': 'Completed',
        'wallet_url': 'https://veyu.cc/wallet'
    })
    print("✅ Debit email sent" if result else "❌ Debit email failed")
    
    # Test 3: Transfer Transaction
    print("\n3. Testing transfer transaction email...")
    result = send_wallet_transaction(user, {
        'transaction_type': 'Transfer',
        'amount': '₦10,000.00',
        'balance': '₦90,000.00',
        'reference': 'TXN-2025-001236',
        'description': 'Transfer to John Doe',
        'timestamp': datetime.now().strftime('%B %d, %Y at %I:%M %p'),
        'payment_method': 'Wallet Transfer',
        'status': 'Completed',
        'wallet_url': 'https://veyu.cc/wallet'
    })
    print("✅ Transfer email sent" if result else "❌ Transfer email failed")
    
    print("\n" + "=" * 60)
    print("📬 Check your inbox at ekeminieffiong22@gmail.com")
    print("You should see beautiful wallet transaction emails!")

if __name__ == "__main__":
    main()
