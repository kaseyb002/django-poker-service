from django.contrib.auth.models import User
from decimal import Decimal
from .models import *
from .serializers import *
from .pagination import NumberOnlyPagination
from pokerapp import models
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import generics, viewsets, status
from rest_framework.permissions import IsAuthenticated
from . import table_member_fetchers 
from . import responses
from . import table_member_write_helpers
import json
import requests
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .utils import UUIDEncoder

def send_request(path, data):
    json_body = json.loads(json.dumps(data))
    url = 'http://127.0.0.1:8080/nolimitholdem/' + path
    # TODO: add error handling
    response = requests.post(url, json=json_body)
    return response.json()

def is_hand_complete(hand_json):
    return hand_json['state'].get('hand_complete') is not None

def valid_current_hand(game_id):
    return NoLimitHoldEmHand.objects.filter(
        game__pk=game_id
    ).filter(
        completed__isnull=True
    ).first()

def is_players_turn(user_id, hand_json):
    current_player_hand_index = hand_json['state']['waiting_for_player_to_act']['player_index']
    current_player_hand_id = hand_json['player_hands'][current_player_hand_index]['player']['id']
    return str(user_id) == current_player_hand_id

@api_view(['POST'])
def deal(request, *args, **kwargs):
    """
    Deal hold em hand or return current hand
    """
    game_pk = kwargs.get('game_pk')
    game = NoLimitHoldEmGame.objects.get(
        pk=game_pk
    )
    my_table_member = table_member_fetchers.get_table_member(
        user_id=request.user.id, 
        table_id=game.table.id,
    )
    if not my_table_member.permissions.can_deal:
        return responses.unauthorized("User is not permitted to deal.")
    current_hand = NoLimitHoldEmHand.objects.filter(
        game__pk=game_pk
    ).filter(
        completed__isnull=True
    ).first()
    if current_hand:
        serializer = NoLimitHoldEmHandSerializer(current_hand, context={'request': request})
        return Response(serializer.data)

    def make_player_json(player):
        return {
            'id':str(player.user_id()),
            'name':player.username(),
            'image_url':player.image_url(),
            'chip_count':float(player.chip_count),
        }

    sitting_players = NoLimitHoldEmGamePlayer.objects.filter(
        game__id=game_pk
    ).filter(
        is_sitting=True
    )   
    for sitting_player in sitting_players:
        if sitting_player.chip_count < game.big_blind:
            sitting_player.is_sitting=False
            sitting_player.save()
    sitting_players = NoLimitHoldEmGamePlayer.objects.filter(
        game__id=game_pk
    ).filter(
        is_sitting=True
    ).prefetch_related(
        'table_member', 
        'table_member__user', 
        'table_member__user__account',
    )
    sitting_players_json = []
    for sitting_player in sitting_players:
        sitting_players_json.append(make_player_json(sitting_player))
    data = {
        'smallBlind':float(game.small_blind),
        'bigBlind':float(game.big_blind),
        'players': sitting_players_json,
    }
    hand_json = send_request('deal', data)
    hand = NoLimitHoldEmHand(
        game=game,
        hand_json=hand_json,
    )
    hand.save()
    hand.players.set(sitting_players)
    if is_hand_complete(hand_json):
        hand.completed = timezone.now()
    hand.save()
    serializer = NoLimitHoldEmHandSerializer(hand, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def make_move(request, *args, **kwargs):
    game_pk = kwargs.get('game_pk')
    game = NoLimitHoldEmGame.objects.get(
        pk=game_pk
    )
    my_table_member = table_member_fetchers.get_table_member(
        user_id=request.user.id, 
        table_id=game.table.id,
    )
    if not my_table_member.permissions.can_play:
        return responses.unauthorized("User is not permitted to play.")
    current_hand = valid_current_hand(game_pk)
    if not current_hand:
        return responses.bad_request("No hand currently being played.")
    if not is_players_turn(request.user.id, current_hand.hand_json):
        return responses.bad_request("Not the user's turn.")
    action = kwargs.get('action')
    hand_json = act_on_hand(
        request=request, 
        action=action, 
        current_hand=current_hand,
        my_table_member=my_table_member,
    )
    return finish_move(
        request=request,
        current_hand=current_hand,
        hand_json=hand_json,
    )

def act_on_hand(request, action, current_hand, my_table_member):
    if action == 'bet':
        class Serializer(serializers.Serializer):
            amount = serializers.DecimalField(max_digits=10, decimal_places=2)
        serializer = Serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        amount = Decimal(serializer.data['amount'])
        data = {
            'amount':float(amount),
            'hand': current_hand.hand_json,
        }
        return send_request('bet', data)
    elif action in ('call', 'fold', 'check'):
        data = {
            'hand': current_hand.hand_json,
        }
        return send_request(action, data)
    else:
        return responses.bad_request("Invalid move name.")

def finish_move(request, current_hand, hand_json):
    current_hand.hand_json = hand_json
    if is_hand_complete(hand_json):
        current_hand.completed = timezone.now()
    player_chip_counts = {
        player['player']['id']: player['player']['chip_count']
        for player in hand_json['player_hands']
    }
    for player in current_hand.players.all():
        if str(player.user_id()) in player_chip_counts:
            player.chip_count = player_chip_counts[str(player.user_id())]
            player.save()
    current_hand.save()

    channel_layer = get_channel_layer()

    serializer = NoLimitHoldEmHandSerializer(current_hand, context={'request': request})
    data = {
        "update_type": "handUpdated",
        "hand": serializer.data,
    }
    json_data = json.dumps(data, cls=UUIDEncoder)
    async_to_sync(channel_layer.group_send)(
        "no_limit_hold_em_game_" + str(current_hand.game.id),
        {
            "type": "chat.message",
            "message": json_data,
        }
    )
    return Response(serializer.data)
