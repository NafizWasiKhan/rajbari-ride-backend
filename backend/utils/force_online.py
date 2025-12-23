import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rajbari_ride.settings")

import django
django.setup()

from django.contrib.auth.models import User

print("Forcing 'hasib' to Online...")
try:
    u = User.objects.get(username='hasib')
    u.profile.is_online = True
    u.profile.save()
    print("Success: hasib is now ONLINE in DB.")
except User.DoesNotExist:
    print("User 'hasib' not found?")
