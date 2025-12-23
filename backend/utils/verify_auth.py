import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rajbari_ride.settings")

import django
django.setup()

from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

def test_auth():
    # Cleanup first
    User.objects.filter(username="rider_test").delete()
    print("Cleaned up existing user")

    client = APIClient()
    
    # 1. Register Rider
    print("\n[TEST] Register Rider")
    data = {
        "username": "rider_test",
        "email": "rider@example.com",
        "password": "password123",
        "profile": {"role": "RIDER"}
    }
    response = client.post('/api/users/register/', data, format='json')
    print(f"Response Type: {type(response)}")
    
    if response.status_code == 201:
        print(f"SUCCESS: {response.data}")
        token = response.data['token']
    else:
        print(f"FAILED: {response.status_code}")
        if hasattr(response, 'data'):
             print(response.data)
        else:
             with open('error_response.html', 'wb') as f:
                 f.write(response.content)
             print("Saved error response to error_response.html")
        return

    # 2. Login
    print("\n[TEST] Login")
    login_data = {"username": "rider_test", "password": "password123"}
    response = client.post('/api/users/login/', login_data, format='json')
    if response.status_code == 200:
        print(f"SUCCESS: Token: {response.data['token']}")
    else:
        print(f"FAILED: {response.data}")
        return

    # 3. Logout
    print("\n[TEST] Logout")
    client.credentials(HTTP_AUTHORIZATION='Token ' + token)
    response = client.post('/api/users/logout/')
    if response.status_code == 204:
        print("SUCCESS: Logged out")
    else:
        print(f"FAILED: {response.status_code}")

    # Cleanup
    User.objects.filter(username="rider_test").delete()

if __name__ == "__main__":
    test_auth()
