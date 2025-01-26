from django.urls import re_path

from .consumers import (
<<<<<<< HEAD
    LiveChatConsumer,
    SupportLiveChatConsumer,
)

urlpatterns = [
    re_path(r"support/(?P<ticket_id>\w+)/$", SupportLiveChatConsumer.as_asgi()),
    re_path(r"chat/(?P<room_id>[\w-]+)/$", LiveChatConsumer.as_asgi()),
=======
    SalesLiveChatConsumer,
    SupportLiveChatConsumer,
)

websocket_urlpatterns = [
    re_path(r"support/livechat/(?P<ticket_id>\w+)/$", SupportLiveChatConsumer.as_asgi()),
    re_path(r"sales/livechat/(?P<room_id>\w+)/$", SalesLiveChatConsumer.as_asgi()),
>>>>>>> f16084d (update: Implemented API documentation with Swagger and Redoc, fix: Chat app included and resolved dependency with other Installed apps)
]


