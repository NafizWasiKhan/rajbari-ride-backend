import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rajbari_ride.settings")

import django
django.setup()

from vehicles.models import VehicleType

def seed_vehicle_types():
    types = [
        {'name': 'Car', 'base_fare': 50.0, 'per_km_rate': 25.0, 'per_minute_rate': 2.0},
        {'name': 'Bike', 'base_fare': 30.0, 'per_km_rate': 15.0, 'per_minute_rate': 1.0},
    ]

    print("Seeding Vehicle Types...")
    for t in types:
        vt, created = VehicleType.objects.get_or_create(name=t['name'], defaults=t)
        if created:
            print(f"Created: {vt.name} (ID: {vt.id})")
        else:
            print(f"Exists: {vt.name} (ID: {vt.id})")

if __name__ == "__main__":
    seed_vehicle_types()
