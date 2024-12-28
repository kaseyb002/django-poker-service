from django.contrib.auth.models import User
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
from django.db.models import Subquery, OuterRef, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone

class CurrentGameRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_member:
            return responses.unauthorized("User is not a member of this table.")
        current_game = get_object_or_404(
            CurrentGame,
            table__id=table_pk,
        )
        serializer = CurrentGameSerializer(current_game, context={'request': request})
        return Response(serializer.data)

class CurrentGameListView(generics.ListCreateAPIView):
    pagination_class = NumberOnlyPagination
    permission_classes = [IsAuthenticated]
    
    def list(self, request, *args, **kwargs):
        current_games = CurrentGame.objects.filter(
            table__members__user__id=request.user.id,
            table__members__is_deleted=False, # does this target request.user?
        )
        page = self.paginate_queryset(current_games)

        # find hold em hands
        no_limit_hold_em_game_ids = [current_game.no_limit_hold_em_game.id for current_game in page]
        hands = NoLimitHoldEmHand.objects.filter(
            game__id__in=no_limit_hold_em_game_ids,
            completed__isnull=True,
        )
        hands_dict = {}
        for hand in hands:
            hands_dict[hand.game.id] = hand
            
        # find sitting players
        sitting_players = NoLimitHoldEmGamePlayer.objects.filter(
            game__id__in=no_limit_hold_em_game_ids,
            is_sitting=True,
        ).prefetch_related('table_member__user')
        no_limit_hold_em_players_dict = {}
        for player in sitting_players:
            if player.game.id not in no_limit_hold_em_players_dict:
                no_limit_hold_em_players_dict[player.game.id] = []
            no_limit_hold_em_players_dict[player.game.id].append(player)
        
        # find other game types (ie, stage 10 round)


        # make full games list
        games = []
        for game in page:
            game_serializer = CurrentGameSerializer(game, context={'request': request})
            games.append({
                'game': game_serializer.data,
            })

            # add hold em hands
            if game.no_limit_hold_em_game.id in hands_dict:
                hand = hands_dict[game.no_limit_hold_em_game.id]
                hand_serializer = NoLimitHoldEmHandSerializer(hand, context={'request': request})
                games[-1]['game']['no_limit_hold_em_hand'] = hand_serializer.data

            # add hold em players
            if game.no_limit_hold_em_game.id in no_limit_hold_em_players_dict:
                players = no_limit_hold_em_players_dict[game.no_limit_hold_em_game.id]
                players_serializer = NoLimitHoldEmGamePlayerSerializer(players, many=True, context={'request': request})
                games[-1]['game']['no_limit_hold_em_players'] = players_serializer.data

            # add other game data as needed

        return self.get_paginated_response(games)

    def create(self, request, *args, **kwargs):
        class Serializer(serializers.Serializer):
            game_type = serializers.ChoiceField(choices=GameType.choices)
        serializer = Serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        table_pk = self.kwargs.get('table_pk')
        game_type = serializer.validated_data['game_type']
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_member:
            return responses.user_not_in_table()
        if not my_table_member.permissions.can_edit_settings:
            return responses.unauthorized("User cannot create games")
        game = create_game(table_pk, game_type)
        serializer = CurrentGameSerializer(game, context={'request': request})
        return Response(serializer.data)

def create_game(table_id, game_type):
    table = get_object_or_404(
        Table,
        pk=table_id,
    )
    current_game = CurrentGame.objects.filter(
        table__pk=table_id,
    ).first()
    game = None
    match game_type:
        case GameType.NO_LIMIT_HOLD_EM:
            game = NoLimitHoldEmGame.objects.create(
                table=table,
            )
            if not current_game:
                current_game = CurrentGame.objects.create(
                    table=table,
                    no_limit_hold_em_game=game,
                )
            current_game.no_limit_hold_em_game = game
        case _:
            raise Exception("Invalid game type")
    # override current game settings
    current_game.last_move = timezone.now()
    current_game.members_turn = None
    current_game.selected_game = game_type
    current_game.save()
    return current_game