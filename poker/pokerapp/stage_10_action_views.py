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
from . import stage_10_round_json_helper
from . import push_notifications, push_categories
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Subquery, OuterRef, Prefetch
from django.db.models.functions import Coalesce
import json
import requests
from . import errors
from django.db.models import Max

def send_request(path, data):
    json_body = json.loads(json.dumps(data))
    url = 'http://127.0.0.1:8080/stage10/' + path
    response = requests.post(url, json=json_body)
    if response.status_code != 200:
        raise errors.PokerServiceError(response.json().get('reason', "Unknown error."))
    return response.json()

def valid_current_round(game_id):
    return get_object_or_404(
        Stage10Round,
        game_id=game_id,
        completed__isnull=True,
    )

@api_view(['POST'])
def start(request, *args, **kwargs):
    """
    Start Stage 10 round or return current round
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
    if not my_table_member.permissions.can_deal:
        return responses.forbidden("User is not permitted to deal.")
    round = start_new_round(game=game)
    serializer = Stage10RoundSerializer(round, context={'request': request})
    return Response(serializer.data)

def start_new_round(game):
    current_round = Stage10Round.objects.filter(
        game_id=game.id,
        completed__isnull=True,
    ).first()
    if current_round:
        return current_round
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
    if sitting_players.count() < 2:
       return responses.bad_request("Not enough players to play.")
    if sitting_players.count() > 6:
        return responses.bad_request("Too many players. " + str(sitting_players.count()) + " sitting. Max is 6." )
    # TODO: ROTATE make players
    # sitting_players = players_for_next_hand(game_id=game.id)
    sitting_players_json = []
    for sitting_player in sitting_players:
        sitting_players_json.append(make_player_json(sitting_player))
    # send request to vapor service
    data = {
        'players': sitting_players_json,
    }
    round_json = send_request('start', data)
    max_round_number = (
        Stage10Round.objects.filter(game_id=game.id)
        .aggregate(Max('round_number'))['round_number__max'] or 0
    )
    round = Stage10Round.objects.create(
        game=game,
        round_json=round_json,
        round_number=max_round_number + 1,
    )
    round.players.set(sitting_players)
    round.save()
    return round

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
        return responses.forbidden("User is not permitted to play.")
    current_round = valid_current_round(game_id=game.id)
    if not stage_10_round_json_helper.is_players_turn(
        user_id=request.user.id,
        round_json=current_round.round_json,
    ):
        return responses.bad_request("Not player's turn.")
    data = {
        'fromDiscardPile':from_discard_pile,
        'round': current_round.round_json,
    }
    round_json = send_request('pickupCard', data)
    current_round = finish_move(
        current_round=current_round, 
        round_json=round_json,
    )
    serializer = Stage10RoundSerializer(current_round, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def discard(request, *args, **kwargs):
    """
    Discard a card from player's deck
    """
    class Serializer(serializers.Serializer):
        card_id = serializers.IntegerField()
    serializer = Serializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    card_id = serializer.data['card_id']
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
        return responses.forbidden("User is not permitted to play.")
    current_round = valid_current_round(game_id=game.id)
    if not stage_10_round_json_helper.is_players_turn(
        user_id=request.user.id,
        round_json=current_round.round_json,
    ):
        return responses.bad_request("Not player's turn.")
    current_round = valid_current_round(game_id=game.id)
    data = {
        'cardID': card_id,
        'round': current_round.round_json,
    }
    round_json = send_request('discard', data)
    current_round = finish_move(
        current_round=current_round, 
        round_json=round_json,
    )
    serializer = Stage10RoundSerializer(current_round, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def complete_stage(request, *args, **kwargs):
    """
    Complete a stage's requirements
    """
    class Serializer(serializers.Serializer):
        form = serializers.JSONField()
    serializer = Serializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    form = serializer.data['form']
    game_pk = kwargs.get('game_pk')
    game = get_object_or_404(
        Stage10Game,
        pk=game_pk,
    )
    my_table_member = table_member_fetchers.get_table_member(
        user_id=request.user.id, 
        table_id=game.table.id,
    )
    current_round = valid_current_round(game_id=game.id)
    if not stage_10_round_json_helper.is_players_turn(
        user_id=request.user.id,
        round_json=current_round.round_json,
    ):
        return responses.bad_request("Not player's turn.")
    data = {
        'form': form,
        'round': current_round.round_json,
    }
    round_json = send_request('completeStage', data)
    current_round = finish_move(
        current_round=current_round, 
        round_json=round_json,
    )
    serializer = Stage10RoundSerializer(current_round, context={'request': request})
    return Response(serializer.data)

def finish_move(current_round, round_json):
    current_round.round_json = round_json
    # check if game is complete

    # else if check if round is complete

    # else just save the round_json
    if stage_10_round_json_helper.is_round_complete(round_json):
        current_round.completed = timezone.now()
        # also need to update player points and current stage
        for player_json in round_json['players']:
            player = Stage10GamePlayer.objects.get(
                game_id=current_round.game_id,
                user_id=player_json['id'],
            )
            player.points = player_json['points']
            player.save()
    current_round.save()
    return current_round