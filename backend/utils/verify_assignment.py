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
from rides.assignment import find_nearest_driver

def test_assignment_logic():
    print("\n[TEST] Setting up Environment...")
    client = APIClient()
    
    # Cleanup
    User.objects.filter(username__in=["rider_1", "driver_A", "driver_B"]).delete()
    
    # Create Rider
    rider = User.objects.create_user("rider_1", "rider@test.com", "pass")
    rider.profile.role = "RIDER"
    rider.save()
    
    # Create Drivers
    # Driver A: Near (1km away)
    driver_a = User.objects.create_user("driver_A", "a@test.com", "pass")
    driver_a.profile.role = "DRIVER"
    driver_a.profile.is_online = True
    driver_a.profile.current_lat = Decimal("23.77") # ~1.1km from 23.76
    driver_a.profile.current_lng = Decimal("89.65")
    driver_a.profile.save()
    
    # Driver B: Far (5km away)
    driver_b = User.objects.create_user("driver_B", "b@test.com", "pass")
    driver_b.profile.role = "DRIVER"
    driver_b.profile.is_online = True
    driver_b.profile.current_lat = Decimal("23.80") # ~4.4km
    driver_b.profile.current_lng = Decimal("89.65")
    driver_b.profile.save()
    
    # Login as Drivers to get tokens
    resp_a = client.post('/api/users/login/', {"username": "driver_A", "password": "pass"})
    token_a = resp_a.data['token']
    
    resp_b = client.post('/api/users/login/', {"username": "driver_B", "password": "pass"})
    token_b = resp_b.data['token']
    
    # 1. Create Ride
    print("\n[TEST] 1. Create Ride")
    ride = Ride.objects.create(
        rider=rider,
        pickup_lat=Decimal("23.76"), pickup_lng=Decimal("89.65"),
        drop_lat=Decimal("23.78"), drop_lng=Decimal("89.65"),
        distance_km=2.0, estimated_fare=90.0
    )
    print(f"Ride {ride.id} created at 23.76, 89.65")
    
    # 2. Find Nearest Driver (Should be A)
    print("\n[TEST] 2. Find Nearest Driver")
    nearest = find_nearest_driver(ride)
    if nearest == driver_a:
        print("SUCCESS: Found Nearest Driver A")
    else:
        print(f"FAILED: Found {nearest}")
        
    # 3. Driver A Rejects
    print("\n[TEST] 3. Driver A Rejects")
    client.credentials(HTTP_AUTHORIZATION='Token ' + token_a)
    resp = client.post(f'/api/rides/{ride.id}/action/', {"action": "REJECT"})
    
    ride.refresh_from_db()
    if driver_a in ride.rejected_drivers.all():
        print("SUCCESS: Driver A added to rejected list")
    else:
        print("FAILED: Driver A NOT in rejected list")
        
    # 4. Find Nearest (Should be B now)
    print("\n[TEST] 4. Re-assignment (Should find B)")
    # The view doesn't auto-assign in strict sense of saving 'driver' field yet (as per my impl), 
    # but the logic should find the next one.
    next_driver = find_nearest_driver(ride)
    if next_driver == driver_b:
        print("SUCCESS: Found Next Driver B")
    else:
        print(f"FAILED: Found {next_driver}")
        
    # 5. Driver B Accepts
    print("\n[TEST] 5. Driver B Accepts")
    client.credentials(HTTP_AUTHORIZATION='Token ' + token_b)
    resp = client.post(f'/api/rides/{ride.id}/action/', {"action": "ACCEPT"})
    
    ride.refresh_from_db()
    if ride.driver == driver_b and ride.status == 'ASSIGNED':
        print("SUCCESS: Ride Assigned to Driver B")
    else:
        print(f"FAILED: Status {ride.status}, Driver {ride.driver}")

if __name__ == "__main__":
    test_assignment_logic()
