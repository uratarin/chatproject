import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from datetime import datetime, timezone

from .models import Message, Room


class ChatConsumer(AsyncJsonWebsocketConsumer):
    groups = ['broadcast']

    async def connect(self):
        await self.accept()
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        await self.channel_layer.group_add(
            self.room_id,
            self.channel_name,
        )
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        await self.channel_layer.group_send(
            self.room_id,
            {
                "type": "chat_message",
                "message": f"{self.scope['user']}さんが入室しました",
                "user": "system",
                "timestamp": current_time,
            }
        )

    async def disconnect(self, _close_code):
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        await self.channel_layer.group_send(
            self.room_id,
            {
                "type": "chat_message",
                "message": f"{self.scope['user']}さんが退室しました",
                "user": "system",
                "timestamp": current_time,
            }
        )
        await self.channel_layer.group_discard(
            self.room_id,
            self.channel_name,
        )

    async def receive_json(self, data):
        message = data['message']
        user = self.scope['user'].username
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        await self.createMessage(data)
        await self.channel_layer.group_send(
            self.room_id,
            {
                'type': 'chat_message',
                'message': message,
                'user': user,
                'timestamp': current_time,
            }
        )

    async def chat_message(self, event):
        message = event['message']
        user = event['user']
        current_time = event['timestamp']
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message,
            'user': user,
            'timestamp': current_time,
        }))

    @database_sync_to_async
    def createMessage(self, data):
        room = Room.objects.get(id=self.room_id)
        Message.objects.create(
            room=room,
            content=data['message'],
            posted_by=self.scope['user'],
        )
