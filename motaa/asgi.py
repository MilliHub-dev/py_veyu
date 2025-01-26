"""
ASGI config for motaa project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

<<<<<<< HEAD
import os
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

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'motaa.settings')

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
=======
# import os
# from channels.auth import AuthMiddlewareStack
# from django.core.asgi import get_asgi_application
# from chat.routing import websocket_urlpatterns
# from channels.routing import (
#     ProtocolTypeRouter,
#     URLRouter
# )
# from channels.security.websocket import AllowedHostsOriginValidator
# from chat.middleware import (
#     ApiTokenAuthMiddleware,
# )


# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'motaa.settings')

# # django's default application instance
# django_asgi_app = get_asgi_application()

# # django-channels wrapped application instance

# application = ProtocolTypeRouter({
#     "http": django_asgi_app,
#     "websocket": AllowedHostsOriginValidator(
#         AuthMiddlewareStack(
#             ApiTokenAuthMiddleware(
#                 URLRouter(websocket_urlpatterns)
#             )
#         )
#     )
# })


# import os

# from django.core.asgi import get_asgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'motaa.settings')

# application = get_asgi_application()

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from chat.consumers import ChatConsumer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "motaa.settings")
>>>>>>> f16084d (update: Implemented API documentation with Swagger and Redoc, fix: Chat app included and resolved dependency with other Installed apps)

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            [
                path("sales/livechat/", ChatConsumer.as_asgi()),
            ]
        )
    ),
})


