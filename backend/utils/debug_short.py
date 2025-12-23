import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rajbari_ride.settings")

import django
django.setup()

from rides.models import Ride
from django.contrib.auth.models import User

r = Ride.objects.last()
if r:
    print(f"LAST RIDE: {r.id}, {r.status}")
else:
    print("NO RIDES")

print("DRIVERS:")
for u in User.objects.filter(profile__role='DRIVER'):
    print(f"{u.username}: {u.profile.is_online}")
