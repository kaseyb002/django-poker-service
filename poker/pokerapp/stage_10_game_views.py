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
from . import hand_json_helpers
from django.db.models import Subquery, OuterRef, Prefetch
from django.db.models.functions import Coalesce

STAGE_10_MAX_SITTING_PLAYERS = 6

class Stage10GameRetrieveView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        game_pk = self.kwargs.get('game_pk')
        game = get_object_or_404(
            Stage10Game,
            pk=game_pk,
        )
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=game.table.id,
        )
        if not my_table_member:
            return responses.user_not_in_table()
        serializer = Stage10GameSerializer(game, context={'request': request})
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        game_pk = self.kwargs.get('game_pk')
        game = get_object_or_404(
            Stage10Game,
            pk=game_pk,
        )
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=game.table.id,
        )
        if not my_table_member.permissions.can_edit_settings:
            return responses.unauthorized("User cannot edit settings")
        serializer = Stage10Game(
            game, 
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class Stage10GameListView(generics.ListAPIView):
    pagination_class = NumberOnlyPagination
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_member:
            return responses.user_not_in_table()
        games = Stage10Game.objects.filter(
            table__members__user__id=request.user.id,
            table__id=table_pk,
            table__members__is_deleted=False, # does this target request.user?
        )
        page = self.paginate_queryset(games)
        serializer = Stage10GameSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

class CurrentStage10GameRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_member:
            return responses.user_not_in_table()
        game = get_object_or_404(
            CurrentGame,
            table__pk=table_pk,
        ).stage_10_game
        if not game:
            return responses.not_found("Game not found.")
        serializer = Stage10GameSerializer(game, context={'request': request})
        return Response(serializer.data)

class SelectStage10GameUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        game_pk = self.kwargs.get('game_pk')
        game = get_object_or_404(
            Stage10Game,
            pk=game_pk,
        )
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=game.table.id,
        )
        if not my_table_member:
            return responses.unauthorized("User is not a member of this table.")
        if not my_table_member.permissions.can_edit_settings:
            return responses.unauthorized("User cannot change games")
        current_game = get_object_or_404(
            CurrentGame,
            table__id=game.table.id,
        )
        current_game.stage_10_game = game
        current_game.last_move = timezone.now()
        current_game.selected_game = GameType.STAGE_10
        # TODO: need to set the current player
        """
        hand = Stage10Hand.objects.filter(
            game__pk=game.id
        ).first()
        if hand:
            current_player_id = hand_json_helpers.current_player_user_id(hand_json=hand.hand_json)
            if current_player_id:
                current_player = get_object_or_404(
                    Stage10GamePlayer,
                    game__pk=game.id,
                    table_member__user__id=current_player_id,
                )
                current_game.members_turn = current_player.table_member
            else:
                current_game.members_turn = None
        else:
            current_game.members_turn = None

        """
        current_game.save()
        serializer = CurrentGameSerializer(current_game, context={'request': request})
        return Response(serializer.data) 

class Stage10PlayerRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        game_pk = self.kwargs.get('game_pk')
        user_pk = self.kwargs.get('user_pk')
        player = stage_10_game_fetchers.get_or_make_game_player(
            user_id=user_pk,
            game_id=game_pk,
        )
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=player.game.table.id,
        )
        if not my_table_member:
            return responses.user_not_in_table()
        serializer = Stage10GamePlayerSerializer(player, context={'request': request})
        return Response(serializer.data)

class Stage10PlayerListView(generics.ListAPIView):
    pagination_class = NumberOnlyPagination
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        game_pk = self.kwargs.get('game_pk')
        game = get_object_or_404(
            Stage10Game,
            pk=game_pk,
        )
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=game.table.id,
        )
        if not my_table_member:
            return responses.user_not_in_table()
        players = Stage10GamePlayer.objects.filter(
            game__id=game_pk,
        ).prefetch_related(
            'table_member', 
            'table_member__user', 
            'table_member__user__account',
        )
        page = self.paginate_queryset(players)
        serializer = Stage10GamePlayerSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

class Stage10SittingPlayersListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        game_pk = self.kwargs.get('game_pk')
        game = get_object_or_404(
            Stage10Game,
            pk=game_pk,
        )
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=game.table.id,
        )
        if not my_table_member:
            return responses.user_not_in_table()
        sitting_players = Stage10GamePlayer.objects.filter(
            game__id=game_pk,
            is_sitting=True
        ).prefetch_related(
            'table_member', 
            'table_member__user', 
            'table_member__user__account',
        )
        serializer = Stage10GamePlayerSerializer(sitting_players, many=True, context={'request': request})
        return Response(serializer.data)

@api_view(['POST'])
def sit(request, *args, **kwargs):
    """
    Sits down to play hold em
    """
    game_pk = kwargs.get('game_pk')
    game = get_object_or_404(
        Stage10Game,
        pk=game_pk,
    )
    table_member = table_member_fetchers.get_table_member(
        user_id=request.user.id, 
        table_id=game.table.id,
    )
    if not table_member.permissions.can_play:
        return responses.unauthorized("User is not permitted to play.")
    player = stage_10_game_fetchers.get_or_make_game_player(
        user_id=request.user.id,
        game_id=game_pk,
    )
    """
    current_hand = NoLimitHoldEmHand.objects.filter(
        game__id=game_pk,
        completed__isnull=True,
        players__pk=player.id,
    ).first()
    if current_hand:
        # They exist in the hand, so they can keep their seats
        player.is_sitting = True
        player.save()
        serializer = Stage10GamePlayerSerializer(player, context={'request': request})
        return Response(serializer.data)

    # if you're not in the current hand, then we need to check your stack
    if player.chip_count < game.big_blind:
        return responses.bad_request("User doesn't have enough money to play.")

    # We probably need a waitlist feature at some point
    current_hand = NoLimitHoldEmHand.objects.filter(
        game__id=game_pk,
        completed__isnull=True,
    ).first()
    if current_hand:
        # if its a full table, we dont let anyone sit, period
        if current_hand.players.all().count() >= NO_LIMIT_HOLD_EM_MAX_SITTING_PLAYERS:
            return responses.bad_request("No more seats available.")

    # if there is no current hand, then we just check the current number of sitting players
    sitting_players = Stage10GamePlayer.objects.filter(
        game__id=game_pk,
        is_sitting=True,
    )
    if sitting_players.count() >= NO_LIMIT_HOLD_EM_MAX_SITTING_PLAYERS:
        return responses.bad_request("No more seats available.")
    """
    player.is_sitting = True
    player.save()
    serializer = Stage10GamePlayerSerializer(player, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def sit_out(request, *args, **kwargs):
    """
    Sit out of hold em game
    """
    game_pk = kwargs.get('game_pk')
    game = Stage10Game.objects.get(
        pk=game_pk
    )
    table_member = table_member_fetchers.get_table_member(
        user_id=request.user.id, 
        table_id=game.table.id,
    )
    player = stage_10_game_fetchers.get_or_make_game_player(
        user_id=request.user.id,
        game_id=game_pk,
    )
    player.is_sitting = False
    player.save()
    serializer = Stage10GamePlayerSerializer(player, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def sit_player_out(request, *args, **kwargs):
    """
    Sit another player out of hold em game
    """
    game_pk = kwargs.get('game_pk')
    user_pk = kwargs.get('user_pk')
    player = stage_10_game_fetchers.get_or_make_game_player(
        user_id=user_pk,
        game_id=game_pk,
    )
    my_table_member = table_member_fetchers.get_table_member(
        user_id=request.user.id, 
        table_id=player.game.table.id,
    )
    if not my_table_member.permissions.can_sit_player_out:
        return responses.unauthorized("User does not have permission to sit players out.")
    player.is_sitting = False
    player.save()
    
    if player.table_member.notification_settings.i_was_sat_out:
        push_notifications.send_push(
            to_user=player.table_member.user,
            text=request.user.username + " sat you out of the game. Sit down again to keep playing.",
            title="You were sat out.",
            subtitle=player.game.table.name,
            extra_data={
                "stage_10_game_id": str(player.game.id),
                "table_id": str(player.game.table.id),
            },
            category=push_categories.I_WAS_SAT_OUT,
            thread_id=push_categories.game_thread_id(player.game.id),
            collapse_id=push_categories.game_collapse_id(player.game.id),
        )

    serializer = Stage10GamePlayerSerializer(player, context={'request': request})
    return Response(serializer.data)