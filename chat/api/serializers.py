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
		fields = '__all__'


class ChatRoomSerializer(ModelSerializer):
	messages = ChatMessageSerializer(many=True)
	members = StringRelatedField(many=True)

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
		return {
			'message': message.text,
			'date': message.date_created
		}

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
			data['image'] = request.build_absolute_uri(other_person.customer.image.url) or None
		elif other_person.user_type == 'dealer':
			data['name'] = other_person.dealer.business_name
			data['image'] = request.build_absolute_uri(other_person.dealer.logo.url) or None
		elif other_person.user_type == 'mechanic':
			data['name'] = other_person.mechanic.business_name
			data['image'] = request.build_absolute_uri(other_person.mechanic.logo.url) or None
		return data


# 
