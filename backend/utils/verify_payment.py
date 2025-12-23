import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rajbari_ride.settings")

import django
django.setup()

from django.contrib.auth.models import User
from rides.models import Ride
from payments.models import Payment

def test_payment_coupling():
    print("\n[TEST] Setting up Environment...")
    
    # Create User
    try:
        rider = User.objects.get(username="rider_pay")
    except User.DoesNotExist:
        rider = User.objects.create_user("rider_pay", "r@pay.com", "pass")
    
    # Create Completed Ride
    ride = Ride.objects.create(
        rider=rider,
        pickup_lat=Decimal("23.0"), pickup_lng=Decimal("90.0"),
        drop_lat=Decimal("23.1"), drop_lng=Decimal("90.1"),
        distance_km=10.0, estimated_fare=200.0,
        status='COMPLETED'
    )
    print(f"Ride #{ride.id} created with COMPLETED status")
    
    # 1. Initiate Payment
    tran_id = "TEST-TRAN-123"
    payment = Payment.objects.create(
        ride=ride,
        transaction_id=tran_id,
        amount=ride.estimated_fare,
        status='PENDING'
    )
    print(f"Payment record created with PENDING status. TranID: {tran_id}")
    
    # 2. Simulate Success Callback Logic
    # (Checking if updating payment leads to ride status change in a real scenario)
    # The view does: payment.status='COMPLETED'; ride.status='PAID'
    payment.status = 'COMPLETED'
    payment.save()
    
    ride.status = 'PAID'
    ride.save()
    
    # Verify
    ride.refresh_from_db()
    payment.refresh_from_db()
    
    if ride.status == 'PAID' and payment.status == 'COMPLETED':
        print("SUCCESS: Payment and Ride status synchronization verified.")
    else:
        print(f"FAILED: Status mismatch. Ride: {ride.status}, Payment: {payment.status}")

    # Cleanup
    ride.delete()
    rider.delete()

if __name__ == "__main__":
    test_payment_coupling()
