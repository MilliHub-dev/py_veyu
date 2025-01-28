from django.urls import re_path

from .consumers import (
    LiveChatConsumer,
    SupportLiveChatConsumer,
)



urlpatterns = [
    re_path(r"support/(?P<ticket_id>\w+)/$", SupportLiveChatConsumer.as_asgi()),
    re_path(r"chat/(?P<room_id>[\w-]+)/$", LiveChatConsumer.as_asgi()),
]


