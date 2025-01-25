from django.shortcuts import render
from rest_framework.decorators import (
	api_view,
	authentication_classes,
	permission_classes,
)
from ..models import ChatRoom, ChatMessage
from .serializers import (
	ChatMessageSerializer,
	ChatRoomSerializer,
	ChatRoomListSerializer,
)
from rest_framework.response import Response
from rest_framework.permissions import (
	IsAuthenticated,
)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def chats_view(request):
	user = request.user
	rooms = ChatRoom.objects.filter(members__in=[user,]).distinct()
	rooms = ChatRoomListSerializer(rooms, many=True, context={'request': request}).data
	data = {
		'error': False,
		'data': rooms
	}
	return Response(data)



@permission_classes([IsAuthenticated])
@api_view(["POST"])
def new_chat_view(request):
	sender = request.user
	recipient = Account.objects.get(uuid=request.data['recipient'])
	room = None

	try:
		# if user has a chat history?
		# get the chat room
		room = ChatRoom.objects.get(members__in=[sender, recipient])
	except ChatRoom.DoesNotExist:
	# else? create a new room
		room = ChatRoom.objects.create(room_type='sales-chat')
		room.members.add(sender, recipient,)
		room.save()

	# create new message
	message = ChatMessage(
		message_type="user",
		text=request.data['message'],
		room=room,
		sender=sender
	)
	message.save()

	# add message to room
	room.messages.add(message,)
	room.save()

	# dispatch a signal (in a thread)
	data = {
		'error': False,
		'data': ChatMessageSerializer(message).data
	}
	return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def chat_room_view(request, room_id):
	user = request.user
	room = ChatRoom.objects.get(uuid=room_id)
	room = ChatRoomSerializer(room, context={'request': request}).data
	data = {
		'error': False,
		'data': room
	}
	return Response(data)




