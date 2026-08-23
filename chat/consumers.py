import json
from urllib.parse import parse_qs
from channels.generic.websocket import (
    WebsocketConsumer,
    JsonWebsocketConsumer,
)
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
from .models import (
    ChatMessage,
    ChatAttachment,
    ChatRoom,
)
from rest_framework.authtoken.models import Token
from .api.serializers import (
    ChatMessageSerializer,
)
from feedback.models import create_and_send_user_notifications
from accounts.utils.email_notifications import send_simple_email


class LiveEventRelayConsumer(WebsocketConsumer):
    # for live notifications
    # use to update icon badges and show alert when user
    # is on page and update online status of other users
    def connect(self):
        # when a new connection is formed
        # if user.is_authenticated
        # if user.is_offline, user.online=True
        pass



class SupportLiveChatConsumer(WebsocketConsumer):
    def connect(self):
        token = self.scope["query_string"].decode().split("token=")[-1]

        if token:
            try:
                # Validate token
                token_obj = Token.objects.get(key=token)
                self.scope['user'] = token_obj.user  # Attach the user to the connection
            except Token.DoesNotExist:
                self.close()  # Reject connection if token is invalid
                return

        self.room_name = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_name}"

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "chat.message", "message": message}
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event["message"]
        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message}))


class LiveChatConsumer(JsonWebsocketConsumer):
    def connect(self):
        self.room = None
        self.room_name = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_name}"

        # Step 1: find a chat room between the customer and mech/dealer
        # Step 2: if no room is found, create one
        # Step 3: load the messages in the room
        # Step 4: send initial messages in response

        # Join room group
        self.get_chat_room()
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
        self.get_chat_room()

    def get_chat_room(self):
        user = self.scope['user']

        try:
            room = ChatRoom.objects.get(uuid=self.room_name)
            self.room = room
            self.scope['chat_room'] = self.room
        except ChatRoom.DoesNotExist:
            # Leave self.room as None so receive_json can reject cleanly instead
            # of raising AttributeError and killing the connection.
            self.room = None

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    def receive_json(self, content):
        user = self.scope['user']

        if self.room is None:
            self.send_json({"error": "Chat room not found."})
            return

        text = (content or {}).get('message')
        if not text:
            self.send_json({"error": "A 'message' field is required."})
            return

        if not user or not user.is_authenticated:
            # ApiTokenAuthMiddleware attaches AnonymousUser when the token is
            # missing or not an Account.api_token. Say so rather than dropping
            # the message on the floor.
            self.send_json({"error": "Authentication required."})
            return

        if user not in self.room.members.all():
            self.send_json({"error": "You are not a member of this chat room."})
            return

        message = ChatMessage(
            message_type='user',
            text=text,
            room=self.room,
            sender=self.scope['user']
        )
        message.save()
        self.room.messages.add(message,)
        self.room.save()

        data = ChatMessageSerializer(message).data
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {"type": "chat.message", "data": data}
        )

        # Send Push Notification to offline members
        recipients = self.room.members.exclude(id=user.id)
        for recipient in recipients:
            try:
                create_and_send_user_notifications(
                    user=recipient,
                    subject="New message",
                    message=f"{user.name or user.email}: {message.text}",
                    level="info",
                    cta_link=f"/chat/{self.room.uuid}",
                )

                if recipient.user_type == 'dealer':
                    try:
                        send_simple_email(
                            subject="New chat message on Veyu",
                            recipients=[recipient.email],
                            template_name="chat_new_message.html",
                            context={
                                "user_name": recipient.first_name or recipient.email,
                                "sender_name": user.name or user.email,
                                "message_preview": message.text[:200],
                            },
                        )
                    except Exception as e:
                        print(f"Error sending email to dealer: {e}")
            except Exception as e:
                print(f"Error sending push notification: {e}")

    # Receive message from room group
    def chat_message(self, event):
        data = event["data"]
        self.send_json(data)
