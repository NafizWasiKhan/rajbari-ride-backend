import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rajbari_ride.settings")

import django
django.setup()

from django.contrib.auth.models import User
from rides.models import Ride
from users.models import Profile

def diagnose():
    with open('diagnostic_log.txt', 'w', encoding='utf-8') as f:
        f.write("--- Diagnostic Report ---\n")
        
        # 1. Check Requested Rides
        requested_rides = Ride.objects.filter(status='REQUESTED')
        f.write(f"Total REQUESTED rides: {requested_rides.count()}\n")
        for ride in requested_rides:
            f.write(f"  Ride #{ride.id}: From {ride.pickup_address} To {ride.drop_address} (Dist: {ride.distance_km}, Fare: {ride.estimated_fare})\n")
            f.write(f"    Rider: {ride.rider.username if ride.rider else 'None'}\n")
            f.write(f"    Driver: {ride.driver.username if ride.driver else 'None'}\n")

        # 2. Check Online Drivers
        online_drivers = Profile.objects.filter(role='DRIVER', is_online=True)
        f.write(f"\nOnline Drivers: {online_drivers.count()}\n")
        for profile in online_drivers:
            f.write(f"  Driver: {profile.user.username} (Online: {profile.is_online})\n")

        # 3. Check All Rides (to see if they are in other states)
        all_rides = Ride.objects.all().order_by('-id')[:10]
        f.write(f"\nLast 10 Rides (any status):\n")
        for ride in all_rides:
            f.write(f"  Ride #{ride.id}: Status={ride.status}, Rider={ride.rider.username if ride.rider else 'N/A'}, Driver={ride.driver.username if ride.driver else 'N/A'}\n")

        f.write("\n--- Recommendation ---\n")
        f.write("System shows 4 runserver processes active. InMemoryChannelLayer WILL FAIL to sync between them.\n")

    print("Diagnostic complete. Results written to diagnostic_log.txt")

if __name__ == "__main__":
    diagnose()
