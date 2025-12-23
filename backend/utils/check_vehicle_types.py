import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rajbari_ride.settings")

import django
django.setup()

from vehicles.models import VehicleType

print("Existing Vehicle Types:")
for vt in VehicleType.objects.all():
    print(f"ID: {vt.id}, Name: {vt.name}, Base Fare: {vt.base_fare}")
