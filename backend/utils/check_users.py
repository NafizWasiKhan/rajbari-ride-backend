import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rajbari_ride.settings")

import django
django.setup()

from django.contrib.auth.models import User

print("--- USER STATUS CHECK ---")
for u in User.objects.all():
    role = u.profile.role if hasattr(u, 'profile') else 'No Profile'
    online = u.profile.is_online if hasattr(u, 'profile') else 'N/A'
    print(f"User: {u.username} | Role: {role} | Online: {online}")
