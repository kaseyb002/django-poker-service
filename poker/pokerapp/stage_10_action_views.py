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
from . import stage_10_game_fetchers
from . import responses
from . import table_member_write_helpers
from . import push_notifications, push_categories
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Subquery, OuterRef, Prefetch
from django.db.models.functions import Coalesce
import json
import requests

def send_request(path, data):
    json_body = json.loads(json.dumps(data))
    url = 'http://127.0.0.1:8080/stage10/' + path
    response = requests.post(url, json=json_body)
    if response.status_code != 200:
        return responses.bad_request(response.json().get('reason', "Unknown error."))
    return response.json()

@api_view(['POST'])
def start(request, *args, **kwargs):
    """
    Start Stage 10 game or return current game
    """
    game_pk = kwargs.get('game_pk')
    game = get_object_or_404(
        Stage10Game,
        pk=game_pk,
    )
    my_table_member = table_member_fetchers.get_table_member(
        user_id=request.user.id, 
        table_id=game.table.id,
    )
    if not my_table_member.permissions.can_play:
        return responses.unauthorized("User is not permitted to play.")
    game_json = start_new_game(game=game)
    if type(game_json) == Response:
        response = game_json
        return response
    serializer = Stage10GameSerializer(game, context={'request': request})
    return Response(serializer.data)

def start_new_game(game):
    def make_player_json(player):
        return {
            'id':str(player.user_id()),
            'name':player.username(),
            'image_url':player.image_url(),
        }
    sitting_players = Stage10GamePlayer.objects.filter(
        game__id=game.id,
        is_sitting=True,
    )
    # check player count is in bounds
    #if sitting_players.count() < 2:
    #    return responses.bad_request("Not enough players to play.")
    if sitting_players.count() > 6:
        return responses.bad_request("Too many players. " + str(sitting_players.count()) + " sitting. Max is 6." )
    # make players
    # sitting_players = players_for_next_hand(game_id=game.id)
    sitting_players_json = []
    for sitting_player in sitting_players:
        sitting_players_json.append(make_player_json(sitting_player))
    # send request to vapor service
    data = {
        'players': sitting_players_json,
    }
    game_json = send_request('start', data)
    if type(game_json) == Response:
        response = game_json
        return response
    game.game_json = game_json
    game.players.set(sitting_players)
    game.save()
    return game

@api_view(['POST'])
def pickup_card(request, *args, **kwargs):
    """
    Pick up a card from the discard pile or deck
    """
    class Serializer(serializers.Serializer):
        from_discard_pile = serializers.BooleanField()
    serializer = Serializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    from_discard_pile = serializer.data['from_discard_pile']
    game_pk = kwargs.get('game_pk')
    game = get_object_or_404(
        Stage10Game,
        pk=game_pk,
    )
    my_table_member = table_member_fetchers.get_table_member(
        user_id=request.user.id, 
        table_id=game.table.id,
    )
    if not my_table_member.permissions.can_play:
        return responses.unauthorized("User is not permitted to play.")
    if not game.game_json:
        return responses.bad_request("Game has not started.")
    data = {
        'fromDiscardPile':from_discard_pile,
        'game': game.game_json,
    }
    game_json = send_request('pickupCard', data)
    if type(game_json) == Response:
        response = game_json
        return response
    game.game_json = game_json
    game.save()
    serializer = Stage10GameSerializer(game, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def discard(request, *args, **kwargs):
    """
    Discard a card from player's deck
    """
    class Serializer(serializers.Serializer):
        card = serializers.JSONField()
    serializer = Serializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    card_json = serializer.data['card']
    game_pk = kwargs.get('game_pk')
    game = get_object_or_404(
        Stage10Game,
        pk=game_pk,
    )
    my_table_member = table_member_fetchers.get_table_member(
        user_id=request.user.id, 
        table_id=game.table.id,
    )
    if not my_table_member.permissions.can_play:
        return responses.unauthorized("User is not permitted to play.")
    if not game.game_json:
        return responses.bad_request("Game has not started.")
    data = {
        'card': card_json,
        'game': game.game_json,
    }
    game_json = send_request('discard', data)
    if type(game_json) == Response:
        response = game_json
        return response
    game.game_json = game_json
    game.save()
    serializer = Stage10GameSerializer(game, context={'request': request})
    return Response(serializer.data)