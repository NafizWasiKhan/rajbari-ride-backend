import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rajbari_ride.settings")

import django
django.setup()

from django.contrib.auth.models import User
from rides.models import Ride
from django.core.exceptions import ValidationError

def test_completion_logic():
    print("\n[TEST] Setting up Environment...")
    
    # Create Users
    try:
        rider = User.objects.get(username="rider_lock")
    except User.DoesNotExist:
        rider = User.objects.create_user("rider_lock", "r@lock.com", "pass")
    
    # Create Ride
    ride = Ride.objects.create(
        rider=rider,
        pickup_lat=Decimal("23.0"), pickup_lng=Decimal("90.0"),
        drop_lat=Decimal("23.1"), drop_lng=Decimal("90.1"),
        distance_km=10.0, estimated_fare=200.0,
        status='ONGOING'
    )
    print(f"Ride created with status: {ride.status}")
    
    # 1. Test Modification while ONGOING (Should pass)
    ride.fare = 250.0
    ride.save()
    print("SUCCESS: Modified fare while ONGOING")
    
    # 2. Complete Ride
    ride.status = 'COMPLETED'
    ride.save()
    print("Ride status updated to COMPLETED")
    
    # 3. Test Modification after COMPLETED (Should fail)
    print("\n[TEST] Modification after COMPLETED")
    try:
        ride.estimated_fare = Decimal("500.00")
        ride.save()
        print(f"FAILED: Allowed modification after COMPLETION. Fare is now: {ride.estimated_fare}")
    except ValidationError as e:
        print(f"SUCCESS: Blocked modification as expected: {e}")
    except Exception as e:
        print(f"ERROR: Unexpected exception type {type(e)}: {e}")
        
    # Refresh from DB to ensure it wasn't saved
    ride.refresh_from_db()
    if ride.estimated_fare == Decimal("200.00"):
        print(f"Verified: Fare remains {ride.estimated_fare}")
    else: 
        print(f"Verification Failed: Fare is {ride.estimated_fare} (expected 200.00)")

    # Cleanup
    ride.delete()
    rider.delete()

if __name__ == "__main__":
    test_completion_logic()
