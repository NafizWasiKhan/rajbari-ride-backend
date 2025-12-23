import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rajbari_ride.settings")

import django
django.setup()

from rides.models import Ride
from django.contrib.auth.models import User

print("--- LATEST RIDES ---")
rides = Ride.objects.all().order_by('-id')[:5]
for r in rides:
    print(f"Ride #{r.id}: Status={r.status}, Driver={r.driver}, VehicleType={r.requested_vehicle_type}")

print("\n--- DRIVERS STATUS ---")
drivers = User.objects.filter(profile__role='DRIVER')
for d in drivers:
    print(f"Driver '{d.username}': Online={d.profile.is_online}")
