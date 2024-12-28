from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import NoLimitHoldEmGamePlayer, NoLimitHoldEmHand, NoLimitHoldEmGame, Table, TableMember, TableSettings, ChatMessage, CurrentGame
from .serializers import NoLimitHoldEmGamePlayerSerializer, NoLimitHoldEmHandSerializer, NoLimitHoldEmGameSerializer, TableSerializer, TableMemberSerializer, TableSettingsSerializer, ChatMessageSerializer, CurrentGameSerializer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .utils import UUIDEncoder
import json

"""
Table Messages
"""
@receiver(post_save, sender=Table)
def notify_table_saved(sender, instance, created, **kwargs):
    channel_layer = get_channel_layer()
    serializer = TableSerializer(instance)
    data = {
        "update_type": "table",
        "table": serializer.data,
    }
    send_table_message(instance.id, data)

@receiver(post_save, sender=TableMember)
def notify_table_member_saved(sender, instance, created, **kwargs):
    serializer = TableMemberSerializer(instance)
    data = {
        "update_type": "member",
        "member": serializer.data,
    }
    send_table_message(instance.table.id, data)

@receiver(post_save, sender=TableSettings)
def notify_table_settings_saved(sender, instance, created, **kwargs):
    serializer = TableSettingsSerializer(instance)
    data = {
        "update_type": "settings",
        "settings": serializer.data,
    }
    send_table_message(instance.table.id, data)

@receiver(post_save, sender=CurrentGame)
def notify_table_current_game_saved(sender, instance, created, **kwargs):
    serializer = CurrentGameSerializer(instance)
    data = {
        "update_type": "current_game",
        "game": serializer.data,
    }
    send_table_message(instance.table.id, data)

def send_table_message(table_id, data):
    json_data = json.dumps(data, cls=UUIDEncoder)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "table_" + str(table_id),
        {
            "type": "table.message",
            "message": json_data,
        }
    )

"""
No Limit Hold Em Game Messages
"""
@receiver(post_save, sender=NoLimitHoldEmGamePlayer)
def notify_no_limit_hold_em_game_player_saved(sender, instance, created, **kwargs):
    channel_layer = get_channel_layer()
    serializer = NoLimitHoldEmGamePlayerSerializer(instance)
    data = {
        "update_type": "player",
        "player": serializer.data,
    }
    send_no_limit_hold_em_game_message(instance.game.id, data)

@receiver(post_save, sender=NoLimitHoldEmHand)
def notify_no_limit_hold_em_game_hand_saved(sender, instance, created, **kwargs):
    serializer = NoLimitHoldEmHandSerializer(instance)
    data = {
        "update_type": "hand",
        "hand": serializer.data,
    }
    send_no_limit_hold_em_game_message(instance.game.id, data)

@receiver(post_save, sender=NoLimitHoldEmGame)
def notify_no_limit_hold_em_game_saved(sender, instance, created, **kwargs):
    serializer = NoLimitHoldEmGameSerializer(instance)
    data = {
        "update_type": "currentGame",
        "game": serializer.data,
    }
    send_no_limit_hold_em_game_message(instance.id, data)

def send_no_limit_hold_em_game_message(game_id, data):
    json_data = json.dumps(data, cls=UUIDEncoder)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "no_limit_hold_em_game_" + str(game_id),
        {
            "type": "game.message",
            "message": json_data,
        }
    )

"""
Chat message
"""
@receiver(post_save, sender=ChatMessage)
def notify_chat_message_saved(sender, instance, created, **kwargs):
    channel_layer = get_channel_layer()
    serializer = ChatMessageSerializer(instance)
    data = {
        "update_type": "message",
        "chat_message": serializer.data,
    }
    send_chat_message(instance.room.id, data)

def send_chat_message(room_id, data):
    json_data = json.dumps(data, cls=UUIDEncoder)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "room_" + str(room_id),
        {
            "type": "chat.message",
            "message": json_data,
        }
    )