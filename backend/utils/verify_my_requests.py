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

def run_test():
    print("--- Verifying My Requests Feature ---")
    
    # 1. Setup User
    username = "test_passenger_req"
    password = "password123"
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(username=username, password=password)
        from users.models import Profile
        if not hasattr(user, 'profile'):
            Profile.objects.create(user=user, role='RIDER')
        print(f"Created user: {username}")
    else:
        user = User.objects.get(username=username)
        print(f"Using existing user: {username}")

    client = APIClient()
    client.force_authenticate(user=user)

    # 2. Create Request
    print("\n[1] Creating Ride Request...")
    create_data = {
        "pickup_lat": 23.8103,
        "pickup_lng": 90.4125,
        "drop_lat": 23.8203,
        "drop_lng": 90.4225,
        "pickup_address": "Test Pickup",
        "drop_address": "Test Drop"
    }
    response = client.post('/api/rides/create/', create_data, format='json')
    if response.status_code != 201:
        print(f"FAILED to create ride: {response.data}")
        return
    ride_id = response.data['id']
    print(f"SUCCESS: Created Ride #{ride_id}")

    # 3. List My Requests
    print("\n[2] Fetching My Requests...")
    response = client.get('/api/rides/my-requests/')
    if response.status_code == 200:
        rides = response.data
        found = any(r['id'] == ride_id for r in rides)
        if found:
            print(f"SUCCESS: Found Ride #{ride_id} in list.")
        else:
            print("FAILED: Ride NOT found in list.")
            print("List:", [r['id'] for r in rides])
    else:
        print(f"FAILED to fetch requests: {response.data}")

    # 4. Edit Request
    print("\n[3] Editing Request...")
    update_data = {
        "pickup_lat": 23.9999,
        "pickup_lng": 90.9999,
        # Other fields optional in PATCH, or required? 
        # Serializer is RideCreateSerializer, requires lat/lngs.
        # But for UpdateAPIView with partial=True (PATCH) or full (PUT)?
        # Let's try PUT with full data + change
        "drop_lat": 23.8203,
        "drop_lng": 90.4225,
        "pickup_address": "Updated Pickup",
    }
    # We used UpdateAPIView, so PUT/PATCH.
    response = client.patch(f'/api/rides/{ride_id}/update/', update_data, format='json')
    if response.status_code == 200:
        print(f"SUCCESS: Updated Ride #{ride_id}")
        print(f"New Pickup: {response.data['pickup_lat']}")
        if float(response.data['pickup_lat']) == 23.9999:
            print("Verification: Data matches.")
        else:
            print("Verification: Data mismatch!")
    else:
        print(f"FAILED to update: {response.data}")

    # 5. Cancel Request
    print("\n[4] Cancelling (Deleting) Request...")
    response = client.post(f'/api/rides/{ride_id}/cancel/')
    if response.status_code == 200:
        print(f"SUCCESS: Cancelled Ride #{ride_id}")
        # Verify Deletion
        if not Ride.objects.filter(pk=ride_id).exists():
             print("Verification: Ride deleted from DB.")
        else:
             print("Verification: Ride STILL EXISTS in DB (Expected Deletion)")
    else:
        print(f"FAILED to cancel: {response.data}")

    print("\n--- Test Complete ---")

if __name__ == "__main__":
    run_test()
