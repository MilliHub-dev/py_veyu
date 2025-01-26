import json
<<<<<<< HEAD
from urllib.parse import parse_qs
from channels.generic.websocket import (
    WebsocketConsumer,
    JsonWebsocketConsumer,
)
=======
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
>>>>>>> f16084d (update: Implemented API documentation with Swagger and Redoc, fix: Chat app included and resolved dependency with other Installed apps)
from asgiref.sync import async_to_sync
from .models import (
    ChatMessage,
    ChatAttachment,
    ChatRoom,
)

<<<<<<< HEAD
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
=======

class LiveEventRelayConsumer(WebsocketConsumer):
    def connect(self):pass
>>>>>>> f16084d (update: Implemented API documentation with Swagger and Redoc, fix: Chat app included and resolved dependency with other Installed apps)



class SupportLiveChatConsumer(WebsocketConsumer):
    def connect(self):
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


<<<<<<< HEAD

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


=======
class SalesLiveChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_name}"

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )
        self.accept()
>>>>>>> f16084d (update: Implemented API documentation with Swagger and Redoc, fix: Chat app included and resolved dependency with other Installed apps)

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
<<<<<<< HEAD
    def receive_json(self, content):
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
            self.room_group_name, {"type": "chat.message", "data": data}
=======
    def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "chat.message", "message": message}
>>>>>>> f16084d (update: Implemented API documentation with Swagger and Redoc, fix: Chat app included and resolved dependency with other Installed apps)
        )

    # Receive message from room group
    def chat_message(self, event):
<<<<<<< HEAD
        data = event["data"]
        self.send_json(data)
    


=======
        message = event["message"]
        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message}))
    


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message", "")
        await self.send(text_data=json.dumps({"message": f"You said: {message}"}))

>>>>>>> f16084d (update: Implemented API documentation with Swagger and Redoc, fix: Chat app included and resolved dependency with other Installed apps)


