"""
ASGI config for rajbari_ride project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from .middleware import TokenAuthMiddleware
import tracking.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rajbari_ride.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TokenAuthMiddleware(
        URLRouter(
            tracking.routing.websocket_urlpatterns
        )
    ),
})
