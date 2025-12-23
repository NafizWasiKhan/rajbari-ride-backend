import time
import requests
from django.core.management.base import BaseCommand
from rides.models import Ride

class Command(BaseCommand):
    help = 'Fixes ride addresses by reverse geocoding "Loc:" entries'

    def handle(self, *args, **options):
        rides = Ride.objects.filter(pickup_address__startswith='Loc:') | Ride.objects.filter(drop_address__startswith='Loc:')
        self.stdout.write(f"Found {rides.count()} rides to fix.")

        for ride in rides:
            self.stdout.write(f"Fixing Ride #{ride.id}...")
            
            if ride.pickup_address.startswith('Loc:'):
                addr = self.reverse_geocode(ride.pickup_lat, ride.pickup_lng)
                if addr:
                    ride.pickup_address = addr
                    self.stdout.write(f"  Pickup set to: {addr}")
            
            if ride.drop_address.startswith('Loc:'):
                addr = self.reverse_geocode(ride.drop_lat, ride.drop_lng)
                if addr:
                    ride.drop_address = addr
                    self.stdout.write(f"  Drop set to: {addr}")
            
            ride.save()
            # Be nice to Nominatim
            time.sleep(1)

        self.stdout.write(self.style.SUCCESS('Successfully fixed addresses.'))

    def reverse_geocode(self, lat, lng):
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&zoom=18"
            headers = {'User-Agent': 'ZatraBot/1.0'}
            response = requests.get(url, headers=headers)
            data = response.json()
            if 'display_name' in data:
                return ",".join(data['display_name'].split(',')[:3])
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error geocoding {lat},{lng}: {e}"))
        return None
