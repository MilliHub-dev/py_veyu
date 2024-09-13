from django.urls import re_path

from .consumers import (
    SalesLiveChatConsumer,
    SupportLiveChatConsumer,
)

websocket_urlpatterns = [
    re_path(r"support/livechat/(?P<ticket_id>\w+)/$", SupportLiveChatConsumer.as_asgi()),
    re_path(r"sales/livechat/(?P<room_id>\w+)/$", SalesLiveChatConsumer.as_asgi()),
]


