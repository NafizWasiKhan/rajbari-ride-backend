import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rajbari_ride.settings")

import django
django.setup()

except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)

from payments.models import Wallet, Transaction
from payments.views import WalletStatsView

User = get_user_model()

def verify_wallet_stats():
    print("--- Verifying Wallet Stats ---")
    
    # 1. Setup User
    username = 'test_driver_wallet'
    email = 'test_driver_wallet@example.com'
    password = 'password123'
    
    user, created = User.objects.get_or_create(username=username, email=email)
    if created:
        user.set_password(password)
        user.save()
        print(f"Created test user: {username}")
    else:
        print(f"Using existing test user: {username}")
        
    # Ensure Wallet exists
    wallet, _ = Wallet.objects.get_or_create(user=user)
    print(f"Initial Balance: {wallet.balance}")
    
    # 2. Create Dummy Transactions
    # Clear old ones for clean test
    Transaction.objects.filter(wallet=wallet).delete()
    
    Transaction.objects.create(
        wallet=wallet,
        amount=500.00,
        transaction_type='EARNING',
        description="Test Earning 1"
    )
    Transaction.objects.create(
        wallet=wallet,
        amount=100.00,
        transaction_type='EARNING',
        description="Test Earning 2"
    )
    Transaction.objects.create(
        wallet=wallet,
        amount=-50.00,
        transaction_type='COMMISSION',
        description="Test Commission"
    )
    
    # Update wallet balance manually for the test
    wallet.balance = 550.00 # 500 + 100 - 50
    wallet.save()
    
    print("Created 3 mock transactions.")
    
    # 3. Test API View
    client = APIClient()
    client.force_authenticate(user=user)
    
    response = client.get('/api/payments/wallet/stats/')
    
    if response.status_code == 200:
        data = response.json()
        print("\nAPI Response Success:")
        print(f"Balance: {data['balance']}")
        print(f"Total Earnings: {data['total_earnings']}") # Should be 600
        print(f"History Items: {len(data['history'])}") # Should be 3
        
        if data['balance'] == 550.0 and data['total_earnings'] == 600.0 and len(data['history']) == 3:
             print("\n✅ VERIFICATION PASSED")
             with open('verification_result.txt', 'w') as f:
                 f.write('PASS')
        else:
             print("\n❌ VERIFICATION FAILED: Data mismatch")
             with open('verification_result.txt', 'w') as f:
                 f.write('FAIL')
    else:
        print(f"\n❌ API Failed: {response.status_code} - {response.content}")
        with open('verification_result.txt', 'w') as f:
                 f.write('FAIL_API')

if __name__ == '__main__':
    verify_wallet_stats()
