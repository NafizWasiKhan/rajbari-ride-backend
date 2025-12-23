from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/rides/(?P<ride_id>\d+)/$', consumers.RideConsumer.as_asgi()),
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
]
