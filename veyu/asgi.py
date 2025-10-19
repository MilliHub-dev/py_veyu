"""
ASGI config for veyu project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veyu.settings')
django.setup()

from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from chat.routing import urlpatterns
from channels.routing import (
    ProtocolTypeRouter,
    URLRouter
)
from channels.security.websocket import AllowedHostsOriginValidator
from chat.middleware import (
    ApiTokenAuthMiddleware,
)


# django's default application instance
django_asgi_app = get_asgi_application()

# django-channels wrapped application instance

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            ApiTokenAuthMiddleware(
                URLRouter(urlpatterns)
            )
        )
    )
})

