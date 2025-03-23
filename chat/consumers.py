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
        print(f"connecting {self.scope['user']}")
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
        created = False
        user = self.scope['user']
        query_string = self.scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)

        # Extract the value of arg_1 (it will be a list, so you may need to access the first item)
        arg_1 = query_params.get("arg_1", [None])[0]

        try:
            room = ChatRoom.objects.get(uuid=self.room_name)
            self.room = room
            self.scope['chat_room'] = self.room
            print("Got Rooms", room)
        except ChatRoom.DoesNotExist:
            pass

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    def receive_json(self, content):
        user = self.scope['user']
        print("Request User:", self.scope['user'])

        if user in self.room.members.all():
            message = ChatMessage(
                message_type='user',
                text=content['message'],
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

    # Receive message from room group
    def chat_message(self, event):
        data = event["data"]
        self.send_json(data)

