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
from . import no_limit_hold_em_game_fetchers
from . import responses
from . import table_member_write_helpers

NO_LIMIT_HOLD_EM_MAX_SITTING_PLAYERS = 10

class HoldEmGameRetrieveView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        game_pk = self.kwargs.get('game_pk')
        game = NoLimitHoldEmGame.objects.get(
            pk=game_pk
        )
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=game.table.id,
        )
        if not my_table_member:
            return responses.user_not_in_table()
        serializer = NoLimitHoldEmGameSerializer(game, context={'request': request})
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        game_pk = self.kwargs.get('game_pk')
        game = NoLimitHoldEmGame.objects.get(
            pk=game_pk
        )
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=game.table.id,
        )
        if not my_table_member.permissions.can_edit_settings:
            return responses.unauthorized("User cannot edit settings")
        serializer = NoLimitHoldEmGameSerializer(
            game, 
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class CurrentHoldEmGameRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_member:
            return responses.user_not_in_table()
        game = CurrentGame.objects.get(
            table__pk=table_pk
        ).no_limit_hold_em_game
        if not game:
            return responses.not_found("Game not found.")
        serializer = NoLimitHoldEmGameSerializer(game, context={'request': request})
        return Response(serializer.data)

class CurrentHoldEmHandRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        game_pk = self.kwargs.get('game_pk')
        game = NoLimitHoldEmGame.objects.get(
           pk=game_pk
        )
        if not game:
            return responses.not_found("Game not found.")
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=game.table.id,
        )
        if not my_table_member:
            return responses.user_not_in_table()
        hand = NoLimitHoldEmHand.objects.filter(
            game__pk=game.id
        ).first()
        if not hand:
            return Response({'hand': None})
        serializer = NoLimitHoldEmHandSerializer(hand, context={'request': request})
        return Response({'hand':serializer.data})

class PlayerRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        game_pk = self.kwargs.get('game_pk')
        user_pk = self.kwargs.get('user_pk')

        player = no_limit_hold_em_game_fetchers.get_or_make_game_player(
            user_id=user_pk,
            game_id=game_pk,
        )
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=player.game.table.id,
        )
        if not my_table_member:
            return responses.user_not_in_table()
        serializer = NoLimitHoldEmGamePlayerSerializer(player, context={'request': request})
        return Response(serializer.data)

class PlayerListView(generics.ListAPIView):
    pagination_class = NumberOnlyPagination
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        game_pk = self.kwargs.get('game_pk')
        game = NoLimitHoldEmGame.objects.get(
            pk=game_pk
        )
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=game.table.id,
        )
        if not my_table_member:
            return responses.user_not_in_table()
        players = NoLimitHoldEmGamePlayer.objects.filter(
            game__id=game_pk,
        ).prefetch_related(
            'table_member', 
            'table_member__user', 
            'table_member__user__account',
        )

        # Apply pagination
        page = self.paginate_queryset(players)
        if page is not None:
            serializer = NoLimitHoldEmGamePlayerSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = NoLimitHoldEmGamePlayerSerializer(players, many=True, context={'request': request})
        return Response(serializer.data)


class SittingPlayersListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        game_pk = self.kwargs.get('game_pk')
        game = NoLimitHoldEmGame.objects.get(
            pk=game_pk
        )
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=game.table.id,
        )
        if not my_table_member:
            return responses.user_not_in_table()
        sitting_players = NoLimitHoldEmGamePlayer.objects.filter(
            game__id=game_pk,
            is_sitting=True
        ).prefetch_related(
            'table_member', 
            'table_member__user', 
            'table_member__user__account',
        )

        serializer = NoLimitHoldEmGamePlayerSerializer(sitting_players, many=True, context={'request': request})
        return Response(serializer.data)

@api_view(['POST'])
def sit(request, *args, **kwargs):
    """
    Sits down to play hold em
    """
    game_pk = kwargs.get('game_pk')
    game = NoLimitHoldEmGame.objects.get(
        pk=game_pk
    )
    table_member = table_member_fetchers.get_table_member(
        user_id=request.user.id, 
        table_id=game.table.id,
    )
    if not table_member.permissions.can_play:
        return responses.unauthorized("User is not permitted to play.")

    player = no_limit_hold_em_game_fetchers.get_or_make_game_player(
        user_id=request.user.id,
        game_id=game_pk,
    )
        
    # now we need to sit them down
    current_hand = NoLimitHoldEmHand.objects.filter(
        game__id=game_pk,
        completed__isnull=True,
        players__pk=player.id,
    ).first()
    if current_hand:
        # They exist in the hand, so they can keep their seats
        player.is_sitting = True
        player.save()
        serializer = NoLimitHoldEmGamePlayerSerializer(player, context={'request': request})
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
    sitting_players = NoLimitHoldEmGamePlayer.objects.filter(
        game__id=game_pk,
        is_sitting=True,
    )
    if sitting_players.count() >= NO_LIMIT_HOLD_EM_MAX_SITTING_PLAYERS:
        return responses.bad_request("No more seats available.")

    player.is_sitting = True
    player.save()
    serializer = NoLimitHoldEmGamePlayerSerializer(player, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def sit_out(request, *args, **kwargs):
    """
    Sit out of hold em game
    """
    game_pk = kwargs.get('game_pk')
    game = NoLimitHoldEmGame.objects.get(
        pk=game_pk
    )
    table_member = table_member_fetchers.get_table_member(
        user_id=request.user.id, 
        table_id=game.table.id,
    )
    player = no_limit_hold_em_game_fetchers.get_or_make_game_player(
        user_id=request.user.id,
        game_id=game_pk,
    )
    player.is_sitting = False
    player.save()
    serializer = NoLimitHoldEmGamePlayerSerializer(player, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def sit_player_out(request, *args, **kwargs):
    """
    Sit another player out of hold em game
    """
    game_pk = kwargs.get('game_pk')
    user_pk = kwargs.get('user_pk')
    player = no_limit_hold_em_game_fetchers.get_or_make_game_player(
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
    serializer = NoLimitHoldEmGamePlayerSerializer(player, context={'request': request})
    return Response(serializer.data)

@api_view(['PUT'])
def add_chips(request, *args, **kwargs):
    """
    Sit another player out of hold em game
    """
    class Serializer(serializers.Serializer):
        amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    serializer = Serializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    amount = Decimal(serializer.data['amount'])

    game_pk = kwargs.get('game_pk')
    user_pk = kwargs.get('user_pk')

    player = no_limit_hold_em_game_fetchers.get_or_make_game_player(
        user_id=user_pk,
        game_id=game_pk,
    )
    my_table_member = table_member_fetchers.get_table_member(
        user_id=request.user.id, 
        table_id=player.game.table.id,
    )
    if not my_table_member:
        return responses.user_not_in_table()
    if not my_table_member.permissions.can_adjust_chips:
        return responses.unauthorized("User does not have permission to adjust chips.")

    current_hand = NoLimitHoldEmHand.objects.filter(
        game__id=game_pk,
        completed__isnull=True,
        players__pk=player.id,
    ).first()
    if current_hand:
        return responses.bad_request("Player chips cannot be adjusted while they're playing a hand.")

    player.chip_count += amount
    if player.chip_count < 0:
        player.chip_count = 0
    player.save()

    # record adjustment
    adjustment = NoLimitHoldEmChipAdjusment(
        player=player,
        adjusted_by=my_table_member,
        amount=amount,
    )
    adjustment.save()

    serializer = NoLimitHoldEmGamePlayerSerializer(player, context={'request': request})
    return Response(serializer.data)
