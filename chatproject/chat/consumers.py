import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from datetime import datetime, timezone

from .models import Message, Room


class ChatConsumer(AsyncJsonWebsocketConsumer):
    groups = ['broadcast']

    async def connect(self):
        await self.accept()

        #room idを取得しインスタンス変数に格納
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        await self.channel_layer.group_add( #グループにチャンネルを追加
            self.room_id,
            self.channel_name,
        )
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        #入室しました
        await self.channel_lawyer.group_send(
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
        await self.channel_lawyer.group_send(
            self.room_id,
            {
                "type": "chat_message",
                "message": f"{self.scope['user']}さんが退室しました",
                "user": "system",
                "timestamp": current_time,
            }
        )

        await self.channel_layer.group_discard( #グループからチャンネルを削除
            self.room_id,
            self.channel_name,
        )

    async def receive_json(self, data):
        #メッセージをjson形式で受け取る
        message = data['message'] #受信データからメッセージを取り出す
        user = self.scope['user'].username
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        await self.createMessage(data) #メッセージをモデルに保存する
        await self.channel_layer.group_send( #指定グループにメッセージを送信する
            self.room_id,
            {
                'type': 'chat_message',
                'message': message,
                'user': user,
                'timestamo': current_time,
            }
        )

    async def chat_message(self, event):
        #グループメッセージを受け取る
        message = event['message']
        user = event['user']
        current_time = event['timestamp']
        #メッセージを送信する
        await self.send(text_data = json.dumps({
            'type': 'chat_message',
            'message': message,
            'user': user,
            'timestamp': current_time,
        }))

    @database_sync_to_async
    def createMessage(self, event):
        room = Room.objects.get(id=self.room_id)

        Message.objects.create(
            room=room,
            content=event['message'],
            posted_by=self.scope['user'],
        )