import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rajbari_ride.settings")

import django
django.setup()

from rest_framework.test import APIClient

def test_fare_estimate():
    client = APIClient()
    
    print("\n[TEST] Fare Estimate")
    # Rajbari coords (approx)
    data = {
        "pickup_lat": 23.76, 
        "pickup_lng": 89.65,
        "drop_lat": 23.80, 
        "drop_lng": 89.70
    }
    
    response = client.post('/api/rides/fare-estimate/', data, format='json')
    
    print(f"Response Status: {response.status_code}")
    if response.status_code == 200:
        print(f"SUCCESS: {json.dumps(response.data, indent=2)}")
        
        # Validation
        dist = response.data.get('distance_km')
        fare = response.data.get('estimated_fare')
        
        if dist > 0 and fare > 50:
             print("Validation PASSED: Distance > 0 and Fare > Base Fare")
        else:
             print("Validation FAILED: Values seem incorrect")
             
    else:
        print(f"FAILED: {response.data}")

if __name__ == "__main__":
    test_fare_estimate()
