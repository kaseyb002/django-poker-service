from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('no_limit_hold_em_games/<uuid:game_pk>', consumers.NoLimitHoldEmGameConsumer.as_asgi()),
]
