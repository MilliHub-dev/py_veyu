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
from django.db.models import Count, Q
from rest_framework.response import Response
from rest_framework.permissions import (
	IsAuthenticated,
)
from accounts.models import Dealership, Customer, Mechanic

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def chats_view(request):
	user = request.user
	rooms = ChatRoom.objects.filter(members__in=[user,])
	rooms = ChatRoomListSerializer(rooms, many=True, context={'request': request}).data
	data = {
		'error': False,
		'data': rooms
	}
	return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_message_view(request, room_id=None):
	data = request.data
	room = None
	other_member = None

	if data['other_member'] == 'dealer':
		other_member = Dealership.objects.get(uuid=data['dealer_id']).user
	elif data['other_member'] == 'mechanic':
		other_member = Mechanic.objects.get(uuid=data['mechanic_id']).user
	elif data['other_member'] == 'customer':
		other_member = Customer.objects.get(uuid=data['customer_id']).user

	members = [request.user, other_member]
	member_ids = [member.id for member in members]
	print("Members:", members)
	if room_id is None:
		# create a new conversation
		try:
			room = ChatRoom.objects.filter(members__in=[request.user]).get(members=other_member.id)
			print("Rooms:", rooms)
		except ChatRoom.DoesNotExist:
			room = ChatRoom.objects.create(room_type='sales-chat')
			room.members.add(*members)
			room.save()
	else:
		room = ChatRoom.objects.get(uuid=room_id)

	message = ChatMessage.objects.create(
		room=room,
		sender=request.user,
		message_type='user',
		text=data['message']
	)
	room.messages.add(message,)
	room.save()
	return Response({'error': False, 'message': 'Message sent!'}, 200)


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




