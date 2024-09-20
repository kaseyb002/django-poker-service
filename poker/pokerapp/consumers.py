import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from .utils import UUIDEncoder

class NoLimitHoldEmGameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope["url_route"]["kwargs"]["game_pk"]
        self.game_group_name = f"no_limit_hold_em_game_{self.game_id}"

        await self.channel_layer.group_add(
            self.game_group_name, self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.game_group_name, self.channel_name
        )

    async def chat_message(self, event):
        data = event["message"]
        await self.send(text_data=data)
