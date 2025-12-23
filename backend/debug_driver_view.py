import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rajbari_ride.settings')
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rides.models import Ride

User = get_user_model()
# Get a driver
driver = User.objects.filter(profile__role='DRIVER').first()
if not driver:
    print("No driver found! Creating one...")
    user = User.objects.create_user(username='test_driver', password='password123')
    from users.models import Profile 
    # Profile might be AutoCreated or needs creation
    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user, role='DRIVER', is_online=True)
    else:
        user.profile.role = 'DRIVER'
        user.profile.is_online = True
        user.profile.save()
    driver = user
    print(f"Created/Found Driver: {driver.username}")

print(f"Driver: {driver.username}, Online: {driver.profile.is_online}")
# Force online
if not driver.profile.is_online:
    driver.profile.is_online = True
    driver.profile.save()
    print("Forced driver online.")

# Create a test ride request if none exists
if not Ride.objects.filter(status='REQUESTED', driver__isnull=True).exists():
     print("No requested rides found. Creating one...")
     rider = User.objects.filter(profile__role='RIDER').first()
     if not rider:
         rider = User.objects.create_user(username='test_rider', password='password123')
         if hasattr(rider, 'profile'):
             rider.profile.role = 'RIDER'
             rider.profile.save()
         else:
             from users.models import Profile
             Profile.objects.create(user=rider, role='RIDER')

     Ride.objects.create(
         rider=rider,
         pickup_lat=23.7, pickup_lng=90.3,
         drop_lat=23.8, drop_lng=90.4,
         status='REQUESTED',
         estimated_fare=100.0,
         distance_km=5.0
     )
     print("Created test ride request.")

client = APIClient()
client.force_authenticate(user=driver)
try:
    response = client.get('/api/rides/available/')
    print(f"Status Code: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.content}")
        print("Detailed content:", response.content.decode('utf-8'))
    else:
        print("Success. Data sample:", response.json()[0] if response.json() else "Empty List")
except Exception as e:
    import traceback
    print("Exception during request:")
    print(traceback.format_exc())
