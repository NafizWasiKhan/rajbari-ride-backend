import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rajbari_ride.settings")

import django
django.setup()

from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rides.models import Ride
from rides.utils import is_within_rajbari, calculate_distance
from payments.models import Payment

def test_security():
    client = APIClient()
    
    # Cleanup any leftovers
    print("\n[TEST] Cleaning up test data...")
    Payment.objects.filter(ride__rider__username="sec_tester").delete()
    Ride.objects.filter(rider__username="sec_tester").delete()
    User.objects.filter(username="sec_tester").delete()

    # Setup Authenticated User
    user = User.objects.create_user("sec_tester", "test@sec.com", "pass")
    client.force_authenticate(user=user)

    # 1. Test Auth Enforcement (Implicitly tested by next steps, but let's do a quick one)
    print("\n[TEST] API Authentication Enforcement")
    anon_client = APIClient()
    resp = anon_client.post('/api/rides/create/', {})
    if resp.status_code == 401:
        print("SUCCESS: Anonymous request rejected (401)")
    else:
        print(f"FAILED: Anonymous request allowed ({resp.status_code})")

    # 2. Test Boundary Validation
    print("\n[TEST] Boundary Validation (Out of Rajbari)")
    # Coordinates for Dhaka (Invalid for this app)
    data = {
        "pickup_lat": 23.81, "pickup_lng": 90.41,
        "drop_lat": 23.82, "drop_lng": 90.42
    }
    resp = client.post('/api/rides/create/', data)
    if resp.status_code == 400 and "within Rajbari district" in str(resp.content):
        print("SUCCESS: Out-of-bounds request rejected")
    else:
        print(f"FAILED: Out-of-bounds request allowed or wrong error: {resp.content}")

    # 3. Test Speed Check Helper
    print("\n[TEST] Speed Calculation for Spoofing Detection")
    # Rajbari coordinates
    p1 = (23.75, 89.65)
    p2 = (23.90, 89.80) # Far away point relative to time
    dist = calculate_distance(p1[0], p1[1], p2[0], p2[1])
    time_diff = 1 # 1 second
    speed_kmh = (dist / time_diff) * 3600
    print(f"Calculated Speed: {speed_kmh:.2f} km/h for 1s jump")
    if speed_kmh > 150:
        print("Verified: Jump distance correctly identifies as high-speed (Spoofing)")

    # 4. Test Duplicate Payment Check
    ride = Ride.objects.create(
        rider=user,
        pickup_lat=Decimal("23.70"), pickup_lng=Decimal("89.60"),
        drop_lat=Decimal("23.71"), drop_lng=Decimal("89.61"),
        distance_km=Decimal("1.5"), estimated_fare=Decimal("80.0"),
        status='COMPLETED'
    )
    
    print("\n[TEST] Duplicate Payment Session")
    # Mark as COMPLETED (Paid)
    Payment.objects.create(ride=ride, transaction_id="TX-FIXED-123", amount=Decimal("80.0"), status='COMPLETED')
    resp2 = client.post('/api/payments/initiate/', {"ride_id": ride.id})
    if resp2.status_code == 400 and "already paid" in str(resp2.content):
        print("SUCCESS: Duplicate payment initiation for paid ride blocked")
    else:
         print(f"FAILED: Duplicate payment for paid ride allowed: {resp2.content}")

    # Cleanup
    ride.delete()
    user.delete()

if __name__ == "__main__":
    test_security()
