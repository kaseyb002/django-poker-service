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
from django.db import transaction

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
        game__pk=game_id,
        completed__isnull=True
    ).first()

def current_player_user_id(hand_json):
    waiting_for_player = hand_json['state'].get('waiting_for_player_to_act')
    if not waiting_for_player:
        return None
    current_player_hand_index = waiting_for_player['player_index']
    current_player_user_id = hand_json['player_hands'][current_player_hand_index]['player']['id']
    return current_player_user_id

def is_players_turn(user_id, hand_json):
    current_player_id = current_player_user_id(hand_json)
    if not current_player_id:
        return False
    return str(user_id) == current_player_id

def is_player_waiting_to_move(user_id, hand_json):
    if is_hand_complete(hand_json):
        return False
    if is_players_turn(user_id, hand_json):
        return False
    player_hands = hand_json['player_hands']
    for player_hand in player_hands:
        if player_hand['player']['id'] == str(user_id):
            if player_hand['status'] == 'in':
                return True
    return False

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
    turn_off_auto_move_for_all_players(game_id=game.id)
    current_hand = NoLimitHoldEmHand.objects.filter(
        game__pk=game_pk,
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
        game__id=game_pk,
        is_sitting=True
    )   
    for sitting_player in sitting_players:
        if sitting_player.chip_count < game.big_blind:
            sitting_player.is_sitting=False
            sitting_player.save()
    if sitting_players.count() < 2:
        return responses.bad_request("Not enough players to play.")
    sitting_players = players_for_next_hand(game_id=game_pk)
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

def players_for_next_hand(game_id):
    sitting_players = NoLimitHoldEmGamePlayer.objects.filter(
        game__id=game_id,
        is_sitting=True
    ).prefetch_related(
        'table_member', 
        'table_member__user', 
        'table_member__user__account',
    )
    previous_hand = NoLimitHoldEmHand.objects.filter(
        game__pk=game_id,
        completed__isnull=False
    ).order_by(
        '-updated',
    ).first()
    sitting_player_dict = {str(player.table_member.user.id): player for player in sitting_players}
    if previous_hand:
        # first i need to make a new list of sitting_players that is the same order as the previous list
        rotated_players = []
        new_players = []
        for player_hand in previous_hand.hand_json['player_hands']:
            player_id = player_hand['player']['id']
            if player_id in sitting_player_dict:
                rotated_players.append(sitting_player_dict[player_id])
        rotated_player_ids_set = {str(player.id) for player in rotated_players}
        for player in sitting_players:
            if str(player.id) not in rotated_player_ids_set:
                rotated_players.append(player)
        previous_small_blind_player = rotated_players.pop(0)
        rotated_players.append(previous_small_blind_player)
        return rotated_players
    else:
        return sitting_players

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
    )
    current_hand = finish_move(
        request=request,
        current_hand=current_hand,
        hand_json=hand_json,
    )
    serializer = NoLimitHoldEmHandSerializer(current_hand, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def force_move(request, *args, **kwargs):
    game_pk = kwargs.get('game_pk')
    game = NoLimitHoldEmGame.objects.get(
        pk=game_pk
    )
    my_table_member = table_member_fetchers.get_table_member(
        user_id=request.user.id, 
        table_id=game.table.id,
    )
    if not my_table_member.permissions.can_force_move:
        return responses.unauthorized("User is not permitted force a move.")
    current_hand = valid_current_hand(game_pk)
    if not current_hand:
        return responses.bad_request("No hand currently being played.")
    hand_json = act_on_hand(
        request=request, 
        action='force', 
        current_hand=current_hand,
    )
    current_hand = finish_move(
        current_hand=current_hand,
        hand_json=hand_json,
    )
    serializer = NoLimitHoldEmHandSerializer(current_hand, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def toggle_auto_move(request, *args, **kwargs):
    class Serializer(serializers.Serializer):
        is_auto_move_on = serializers.BooleanField()
    serializer = Serializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    is_auto_move_on = serializer.data['is_auto_move_on']
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
    if not is_player_waiting_to_move(request.user.id, current_hand.hand_json):
        return responses.bad_request("User is not waiting to play.")
    player = NoLimitHoldEmGamePlayer.objects.filter(
        game__pk=game_pk
    ).get(
        table_member__user__id=request.user.id
    )
    player.is_auto_move_on = is_auto_move_on
    player.save()
    serializer = NoLimitHoldEmGamePlayerSerializer(player, context={'request': request})
    return Response(serializer.data)

def act_on_hand(request, action, current_hand):
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
    elif action in ('call', 'fold', 'check', 'force'):
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
    current_hand = auto_move_if_needed(
        request=request,
        current_hand=current_hand,
    )
    return current_hand

def auto_move_if_needed(request, current_hand):
    user_id = current_player_user_id(current_hand.hand_json)
    if not user_id:
        return current_hand
    player = NoLimitHoldEmGamePlayer.objects.filter(
        game__pk=current_hand.game.id
    ).get(
        table_member__user__id=user_id
    )
    if player.is_auto_move_on:
        hand_json = act_on_hand(
            request=request, 
            action='force', 
            current_hand=current_hand,
        )
        current_hand = finish_move(
            request=request,
            current_hand=current_hand,
            hand_json=hand_json,
        )
    return current_hand

@transaction.atomic
def turn_off_auto_move_for_all_players(game_id):
    players = NoLimitHoldEmGamePlayer.objects.filter(
        game__pk=game_id
    )
    for player in players:
        player.is_auto_move_on = False
        player.save()

