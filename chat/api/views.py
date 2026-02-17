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
from accounts.models import Dealership, Customer, Mechanic, Account
from feedback.models import Notification

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def chats_view(request):
	user = request.user
	# Filter for rooms where user is a member AND there are at least 2 members
	# Fix: Annotate BEFORE filtering by members to ensure count includes all members
	rooms = ChatRoom.objects.annotate(
		member_count=Count('members')
	).filter(members__in=[user]).filter(member_count__gte=2)
	
	rooms = ChatRoomListSerializer(rooms, many=True, context={'request': request}).data
	data = {
		'error': False,
		'data': rooms
	}
	return Response(data, 200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_message_view(request, room_id=None):
	data = request.data
	room = None
	other_member = None

	# Try to get room_id from payload if not in URL
	if room_id is None:
		room_id = data.get('room_id')

	# Handle case where room_id is provided (existing chat)
	if room_id is not None:
		try:
			room = ChatRoom.objects.get(uuid=room_id)
		except ChatRoom.DoesNotExist:
			return Response({'error': True, 'message': 'Chat room not found'}, 404)
	else:
		# For new chats, we need other_member info
		other_member_type = data.get('other_member')
		
		if not other_member_type:
			return Response({'error': True, 'message': 'other_member field is required for new chats'}, 400)
		
		try:
			if other_member_type == 'dealer':
				dealer_id = data.get('dealer_id')
				if not dealer_id:
					return Response({'error': True, 'message': 'dealer_id is required'}, 400)
				other_member = Dealership.objects.get(uuid=dealer_id).user
			elif other_member_type == 'mechanic':
				mechanic_id = data.get('mechanic_id')
				if not mechanic_id:
					return Response({'error': True, 'message': 'mechanic_id is required'}, 400)
				other_member = Mechanic.objects.get(uuid=mechanic_id).user
			elif other_member_type == 'customer':
				customer_id = data.get('customer_id')
				if not customer_id:
					return Response({'error': True, 'message': 'customer_id is required'}, 400)
				other_member = Customer.objects.get(uuid=customer_id).user
			else:
				return Response({'error': True, 'message': 'Invalid other_member type'}, 400)
		except (Dealership.DoesNotExist, Mechanic.DoesNotExist, Customer.DoesNotExist):
			return Response({'error': True, 'message': 'Recipient not found'}, 404)

		members = [request.user, other_member]
		
		# Try to find existing room
		try:
			room = ChatRoom.objects.filter(members__in=[request.user]).get(members=other_member.id)
		except ChatRoom.DoesNotExist:
			room = ChatRoom.objects.create(room_type='sales-chat')
			room.members.add(*members)
			room.save()

	# Validate message content
	message_text = data.get('message')
	if not message_text:
		return Response({'error': True, 'message': 'message field is required'}, 400)

	# Create and save message
	message = ChatMessage.objects.create(
		room=room,
		sender=request.user,
		message_type='user',
		text=message_text
	)
	room.messages.add(message,)
	room.save()

	recipients = room.members.exclude(id=request.user.id)
	for recipient in recipients:
		notif = Notification.objects.create(
			user=recipient,
			subject="New message",
			message=f"{request.user.name or request.user.email}: {message_text}",
			channel="push",
			level="info",
		)
		notif.send()
	
	return Response({'error': False, 'message': 'Message sent!', 'data': {'room_id': str(room.uuid)}}, 200)


@permission_classes([IsAuthenticated])
@api_view(["POST"])
def new_chat_view(request):
	sender = request.user
	data = request.data
	recipient_id = data.get('recipient') or data.get('recipient_id') or data.get('account_id')
	if not recipient_id:
		return Response({'error': True, 'message': 'recipient is required'}, 400)
	try:
		recipient = Account.objects.get(uuid=recipient_id)
	except Account.DoesNotExist:
		return Response({'error': True, 'message': 'Recipient not found'}, 404)
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
	text = data.get('message') or data.get('content') or data.get('initial_message') or data.get('text')
	if not text:
		return Response({'error': True, 'message': 'message is required'}, 400)
	message = ChatMessage(
		message_type="user",
		text=text,
		room=room,
		sender=sender
	)
	message.save()

	# add message to room
	room.messages.add(message,)
	room.save()

	recipients = room.members.exclude(id=sender.id)
	for recipient in recipients:
		notif = Notification.objects.create(
			user=recipient,
			subject="New message",
			message=f"{sender.name or sender.email}: {text}",
			channel="push",
			level="info",
		)
		notif.send()

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




