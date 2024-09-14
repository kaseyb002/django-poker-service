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

class PlayerRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        player_pk = self.kwargs.get('player_pk')
        player = NoLimitHoldEmGamePlayer.objects.get(
            pk=player_pk
        )
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=player.game.table.id,
        )
        if not my_table_member:
            return responses.user_not_in_table()
        serializer = NoLimitHoldEmGamePlayerSerializer(player, context={'request': request})
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
            game__id=game_pk
        ).filter(
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

    # make player if needed
    player = NoLimitHoldEmGamePlayer.objects.filter(
        table_member__user__id=request.user.id
    ).filter(
        game__id=game_pk
    ).first()
    if not player:
        player = NoLimitHoldEmGamePlayer(
            game=game,
            table_member=table_member,
            chip_count=game.starting_chip_count,
        )
        player.save()
        
    # now we need to sit them down

    # if you are in the current hand, you can always sit down
    # TODO: EDGE CASE
    # at max players
    # player in hand sits out
    # new player sits in
    # previous player sits back down
    current_hand = NoLimitHoldEmHand.objects.filter(
        completed__isnull=True
    ).filter(
        players__pk=player.id
    ).first()
    if current_hand:
        player.is_sitting = True
        player.save()
        serializer = NoLimitHoldEmGamePlayerSerializer(player, context={'request': request})
        return Response(serializer.data)

    # if you're not in the current hand, then we need to check your stack
    if player.chip_count < game.big_blind:
        return responses.bad_request("User doesn't have enough money to play.")

    """
    if current_hand.players.all().count() >= 10:
        return responses.bad_request("No more seats available.")
    """

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
    player = NoLimitHoldEmGamePlayer.objects.filter(
        table_member__user__id=request.user.id
    ).filter(
        game__id=game_pk
    ).first()
    if not player:
        return responses.not_found("Player not found.")
    player.is_sitting = False
    player.save()
    serializer = NoLimitHoldEmGamePlayerSerializer(player, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def sit_player_out(request, *args, **kwargs):
    """
    Sit another player out of hold em game
    """
    player_pk = kwargs.get('player_pk')
    player = NoLimitHoldEmGamePlayer.objects.get(
        pk=player_pk
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
    
    player_pk = kwargs.get('player_pk')
    player = NoLimitHoldEmGamePlayer.objects.get(
        pk=player_pk
    )
    my_table_member = table_member_fetchers.get_table_member(
        user_id=request.user.id, 
        table_id=player.game.table.id,
    )
    if not my_table_member:
        return responses.user_not_in_table()
    if not my_table_member.permissions.can_adjust_chips:
        return responses.unauthorized("User does not have permission to adjust chips.")
    # TODO: check if player is in current hand
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
