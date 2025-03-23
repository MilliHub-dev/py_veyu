from django.urls import path
from .views import (
	chats_view,
	chat_room_view,
	new_chat_view,
	send_message_view,
)

app_name = 'chat_api'

urlpatterns = [
	path('chats/', chats_view),
	path('message/', send_message_view),
	path('new/', new_chat_view),
	path('chats/<room_id>/', chat_room_view),
]



