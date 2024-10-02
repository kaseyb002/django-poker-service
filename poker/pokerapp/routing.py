from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('tables/<uuid:table_pk>', consumers.TableConsumer.as_asgi()),
    path('no_limit_hold_em_games/<uuid:game_pk>', consumers.NoLimitHoldEmGameConsumer.as_asgi()),
    path('chat_room/<uuid:room_pk>', consumers.ChatRoomConsumer.as_asgi()),
]
