from rest_framework.serializers import (
	ModelSerializer,
	SerializerMethodField,
	StringRelatedField,
)
from ..models import (
	ChatMessage,
	ChatRoom,
	ChatAttachment
)
from accounts.models import Account


class ChatAttachmentSerializer(ModelSerializer):
	url = SerializerMethodField()
	class Meta:
		model = ChatAttachment
		fields = '__all__'

	def get_url(self, obj):
		request = self.context.get('request', None)
		if request:
			return request.build_absolute_uri(obj.file.url)
		return obj.file.url




class ChatMessageSerializer(ModelSerializer):
	sender = StringRelatedField()
	attachments = ChatAttachmentSerializer(many=True)
	room = StringRelatedField()
	class Meta:
		model = ChatMessage
		fields = ['sender', 'attachments', 'text', 'room', 'uuid', 'id', 'sent']


class ChatMemberSerializer(ModelSerializer):
	image = SerializerMethodField()
	name = SerializerMethodField()
	class Meta:
		fields = ['id', 'uuid', 'email', 'name', 'image']
		model = Account

	def get_name(self, obj):
		if obj.user_type == 'dealer':
			if hasattr(obj, 'dealership') and obj.dealership.business_name:
				return obj.dealership.business_name
		elif obj.user_type == 'mechanic':
			if hasattr(obj, 'mechanic') and obj.mechanic.business_name:
				return obj.mechanic.business_name
		return obj.name

	def get_image(self, obj):
		url = None
		request = self.context.get('request', None)
		if not request: return url
		if obj.user_type == 'customer':
			if hasattr(obj, 'customer') and obj.customer.image:
				url= request.build_absolute_uri(obj.customer.image.url)
		elif obj.user_type == 'dealer':
			if hasattr(obj, 'dealership') and obj.dealership.logo:
				url= request.build_absolute_uri(obj.dealership.logo.url)
		elif obj.user_type == 'mechanic':
			if hasattr(obj, 'mechanic') and obj.mechanic.logo:
				url= request.build_absolute_uri(obj.mechanic.logo.url)
		return url


class ChatRoomSerializer(ModelSerializer):
	messages = ChatMessageSerializer(many=True)
	members = ChatMemberSerializer(many=True)

	class Meta:
		model = ChatRoom
		fields = '__all__'


class ChatRoomListSerializer(ModelSerializer):
	last_message = SerializerMethodField()
	recipient = SerializerMethodField()

	class Meta:
		model = ChatRoom
		fields = ['uuid', 'id', 'last_message', 'recipient']

	def get_last_message(self, obj):
		message = obj.messages.all().order_by('-id').first()
		if message:
			return {
				'message': message.text,
				'date': message.sent
			}
		return None

	def get_recipient(self, obj):
		request = self.context.get('request', None)
		if not request:
			raise Exception("request context missing for <serializer: ChatRoomListSerializer>")

		user = request.user; image = None
		other_person = obj.members.all().exclude(email__iexact=user.email).first()
		data = {
			'name': user.name, 
			'image': None
		}

		if other_person.user_type == 'customer':
			if hasattr(other_person, 'customer') and other_person.customer.image:
				data['image'] = request.build_absolute_uri(other_person.customer.image.url)
		elif other_person.user_type == 'dealer':
			if hasattr(other_person, 'dealership'):
				data['name'] = other_person.dealership.business_name
				if other_person.dealership.logo:
					data['image'] = request.build_absolute_uri(other_person.dealership.logo.url)
		elif other_person.user_type == 'mechanic':
			if hasattr(other_person, 'mechanic'):
				data['name'] = other_person.mechanic.business_name
				if other_person.mechanic.logo:
					data['image'] = request.build_absolute_uri(other_person.mechanic.logo.url)
		return data


# 
