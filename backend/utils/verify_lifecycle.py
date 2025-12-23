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

def test_ride_lifecycle():
    client = APIClient()
    
    print("\n[TEST] Setting up Users...")
    # Cleanup
    User.objects.filter(username__in=["rider_test", "driver_test"]).delete()
    
    # Create Rider
    rider = User.objects.create_user(username="rider_test", password="password123")
    rider.profile.role = "RIDER"
    rider.save()
    
    # Create Driver
    driver = User.objects.create_user(username="driver_test", password="password123")
    driver.profile.role = "DRIVER"
    driver.save()
    
    # Login Rider
    resp = client.post('/api/users/login/', {"username": "rider_test", "password": "password123"})
    rider_token = resp.data['token']
    print(f"Rider Token: {rider_token[:10]}...")

    # Login Driver
    resp = client.post('/api/users/login/', {"username": "driver_test", "password": "password123"})
    driver_token = resp.data['token']
    print(f"Driver Token: {driver_token[:10]}...")
    
    # 1. Create Ride (Rider)
    print("\n[TEST] 1. Create Ride (Rider)")
    client.credentials(HTTP_AUTHORIZATION='Token ' + rider_token)
    data = {
        "pickup_lat": 23.76, "pickup_lng": 89.65,
        "drop_lat": 23.80, "drop_lng": 89.70
    }
    response = client.post('/api/rides/create/', data, format='json')
    if response.status_code == 201:
        ride_id = response.data['id']
        print(f"SUCCESS: Ride {ride_id} created. Status: {response.data['status']}")
    else:
        print(f"FAILED: {response.data}")
        return

    # 2. Try Illegal Transition (REQUESTED -> COMPLETED)
    print("\n[TEST] 2. Illegal Transition (REQUESTED -> COMPLETED)")
    # Using Driver to update (or Rider, strictly speaking permission logic might vary but let's test transition logic first)
    client.credentials(HTTP_AUTHORIZATION='Token ' + driver_token)
    response = client.patch(f'/api/rides/{ride_id}/status/', {"status": "COMPLETED"})
    if response.status_code == 400:
        print(f"SUCCESS: Blocked invalid transition. Error: {response.data.get('error')}")
    else:
        print(f"FAILED: Allowed invalid transition? Code: {response.status_code}")

    # 3. Assign Driver (REQUESTED -> ASSIGNED)
    print("\n[TEST] 3. Assign Driver (REQUESTED -> ASSIGNED)")
    # Must provide driver_id if assigning? Or just current user?
    # Serializer expects 'driver' field or we might need to handle it.
    # Let's say the driver accepts it.
    
    # NOTE: The RideStatusSerializer allows driver field. 
    # If a driver accepts, they should update status to ASSIGNED and set driver=self.
    
    response = client.patch(f'/api/rides/{ride_id}/status/', {
        "status": "ASSIGNED",
        "driver": driver.id
    })
    
    if response.status_code == 200:
         print(f"SUCCESS: Assigned. Status: {response.data['status']}, Driver: {response.data['driver']}")
    else:
         print(f"FAILED: {response.data}")

    # 4. Start Ride (ASSIGNED -> ONGOING)
    print("\n[TEST] 4. Start Ride (ASSIGNED -> ONGOING)")
    response = client.patch(f'/api/rides/{ride_id}/status/', {"status": "ONGOING"})
    if response.status_code == 200:
         print(f"SUCCESS: Started. Status: {response.data['status']}")
    else:
         print(f"FAILED: {response.data}")

    # 5. Complete Ride (ONGOING -> COMPLETED)
    print("\n[TEST] 5. Complete Ride (ONGOING -> COMPLETED)")
    response = client.patch(f'/api/rides/{ride_id}/status/', {"status": "COMPLETED"})
    if response.status_code == 200:
         print(f"SUCCESS: Completed. Status: {response.data['status']}")
    else:
         print(f"FAILED: {response.data}")
         
    # Cleanup
    # User.objects.filter(username__in=["rider_test", "driver_test"]).delete()

if __name__ == "__main__":
    test_ride_lifecycle()
