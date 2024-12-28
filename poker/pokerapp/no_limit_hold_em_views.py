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
from . import push_notifications, push_categories
from django.shortcuts import get_object_or_404
from django.utils import timezone
from . import hand_json_helpers
from django.db.models import Subquery, OuterRef, Prefetch
from django.db.models.functions import Coalesce

NO_LIMIT_HOLD_EM_MAX_SITTING_PLAYERS = 10

class HoldEmGameRetrieveView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        game_pk = self.kwargs.get('game_pk')
        game = get_object_or_404(
            NoLimitHoldEmGame,
            pk=game_pk,
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
        game = get_object_or_404(
            NoLimitHoldEmGame,
            pk=game_pk,
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

class HoldEmGameListView(generics.ListAPIView):
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
        # Annotate NoLimitHoldEmGame with the latest hand's updated timestamp
        games = NoLimitHoldEmGame.objects.filter(
            table__members__user__id=request.user.id,
            table__id=table_pk,
            table__members__is_deleted=False, # does this target request.user?
        ).annotate(
            latest_hand_time=Subquery(
                NoLimitHoldEmHand.objects.filter(
                    game=OuterRef('pk')
                ).order_by('-updated').values('updated')[:1]
            )
        ).order_by('-latest_hand_time', '-created')
        page = self.paginate_queryset(games)

        # find hold em hands
        no_limit_hold_em_game_ids = [game.id for game in page]
        hands = NoLimitHoldEmHand.objects.filter(
            game__id__in=no_limit_hold_em_game_ids,
            completed__isnull=True,
        )
        hands_dict = {}
        for hand in hands:
            hands_dict[hand.game.id] = hand
        
        game_list = []
        for game in page:
            game_serializer = NoLimitHoldEmGameSerializer(game, context={'request': request})
            game_list.append({
                'game': game_serializer.data,
            })
            if game.id in hands_dict:
                hand = hands_dict[game.id]
                hand_serializer = NoLimitHoldEmHandSerializer(hand, context={'request': request})
                game_list[-1]['hand'] = hand_serializer.data
        return self.get_paginated_response(game_list)

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
        game = get_object_or_404(
            CurrentGame,
            table__pk=table_pk,
        ).no_limit_hold_em_game
        if not game:
            return responses.not_found("Game not found.")
        serializer = NoLimitHoldEmGameSerializer(game, context={'request': request})
        return Response(serializer.data)

class SelectHoldEmGameUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        game_pk = self.kwargs.get('game_pk')
        game = get_object_or_404(
            NoLimitHoldEmGame,
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
        current_game.no_limit_hold_em_game = game
        current_game.last_move = timezone.now()
        current_game.selected_game = GameType.NO_LIMIT_HOLD_EM
        hand = NoLimitHoldEmHand.objects.filter(
            game__pk=game.id
        ).first()
        if hand:
            current_player_id = hand_json_helpers.current_player_user_id(hand_json=hand.hand_json)
            if current_player_id:
                current_player = get_object_or_404(
                    NoLimitHoldEmGamePlayer,
                    game__pk=game.id,
                    table_member__user__id=current_player_id,
                )
                current_game.members_turn = current_player.table_member
            else:
                current_game.members_turn = None
        else:
            current_game.members_turn = None
        current_game.save()
        serializer = CurrentGameSerializer(current_game, context={'request': request})
        return Response(serializer.data) 

class CurrentHoldEmHandRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        game_pk = self.kwargs.get('game_pk')
        game = get_object_or_404(
            NoLimitHoldEmGame,
            pk=game_pk,
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
            return Response({'hand':None})
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
        game = get_object_or_404(
            NoLimitHoldEmGame,
            pk=game_pk,
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
        page = self.paginate_queryset(players)
        serializer = NoLimitHoldEmGamePlayerSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

class SittingPlayersListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        game_pk = self.kwargs.get('game_pk')
        game = get_object_or_404(
            NoLimitHoldEmGame,
            pk=game_pk,
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

class NoLimitHoldEmHandRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        game_pk = self.kwargs.get('game_pk')
        hand_pk = self.kwargs.get('hand_pk')
        game = get_object_or_404(
            NoLimitHoldEmGame,
            pk=game_pk,
        )
        hand = get_object_or_404(
            NoLimitHoldEmHand,
            pk=hand_pk,
        )
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=game.table.id,
        )
        if not my_table_member:
            return responses.user_not_in_table()
        serializer = NoLimitHoldEmHandSerializer(hand, context={'request': request})
        return Response(serializer.data)

class NoLimitHoldEmHandListView(generics.ListAPIView):
    pagination_class = NumberOnlyPagination
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        game_pk = self.kwargs.get('game_pk')
        game = get_object_or_404(
            NoLimitHoldEmGame,
            pk=game_pk,
        )
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=game.table.id,
        )
        if not my_table_member:
            return responses.user_not_in_table()
        hands = NoLimitHoldEmHand.objects.filter(
            game__id=game_pk,
        )
        page = self.paginate_queryset(hands)
        serializer = NoLimitHoldEmHandSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

@api_view(['POST'])
def sit(request, *args, **kwargs):
    """
    Sits down to play hold em
    """
    game_pk = kwargs.get('game_pk')
    game = get_object_or_404(
        NoLimitHoldEmGame,
        pk=game_pk,
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
    
    if player.table_member.notification_settings.i_was_sat_out:
        push_notifications.send_push(
            to_user=player.table_member.user,
            text=request.user.username + " sat you out of the game. Sit down again to keep playing.",
            title="You were sat out.",
            subtitle=player.game.table.name,
            extra_data={
                "no_limit_hold_em_game_id": str(player.game.id),
                "table_id": str(player.game.table.id),
            },
            category=push_categories.I_WAS_SAT_OUT,
            thread_id=push_categories.game_thread_id(player.game.id),
            collapse_id=push_categories.game_collapse_id(player.game.id),
        )

    serializer = NoLimitHoldEmGamePlayerSerializer(player, context={'request': request})
    return Response(serializer.data)

@api_view(['PUT'])
def add_chips(request, *args, **kwargs):
    """
    Adjust a player's chip stack in a hold em game
    """
    class Serializer(serializers.Serializer):
        amount = serializers.DecimalField(max_digits=10, decimal_places=2)
        notes = serializers.CharField(required=False)
    serializer = Serializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    amount = Decimal(serializer.data['amount'])
    notes = serializer.data.get('notes', '')

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
        return responses.bad_request("Player's chips cannot be adjusted while they're playing a hand.")

    original_player_chip_count = player.chip_count
    player.chip_count += amount
    bounded_amount = amount
    if player.chip_count < 0:
        bounded_amount = original_player_chip_count
        player.chip_count = 0
    player.save()

    action = "added" if amount >= 0 else "removed"
    preposition = "to" if amount >= 0 else "from"

    summary_statement = (
        f"{request.user.username} {action} ${abs(bounded_amount)} {preposition} "
        f"{player.table_member.user.username}'s stack."
    )

    # record adjustment
    adjustment = NoLimitHoldEmChipAdjustment(
        player=player,
        adjusted_by=my_table_member,
        amount=bounded_amount,
        summary_statement=summary_statement,
        notes=notes,
    )
    adjustment.save()

    if player.table_member.notification_settings.my_chips_adjusted:
        title = "Chips added"
        if amount < 0:
            title = "Chips removed"
        subtitle = player.table_member.table.name
        action = "added" if amount >= 0 else "removed"
        preposition = "to" if amount >= 0 else "from"
        summary_statement = (
            f"{request.user.username} {action} ${abs(bounded_amount)} {preposition} "
            f"your stack."
        )
        push_notifications.send_push(
            to_user=player.table_member.user,
            text=summary_statement,
            title=title,
            subtitle=subtitle,
            extra_data={
                "no_limit_hold_em_game_id": str(player.game.id),
                "table_id": str(player.game.table.id),
            },
            category=push_categories.MY_CHIPS_ADJUSTED,
            thread_id=push_categories.game_thread_id(player.game.id),
        )

    serializer = NoLimitHoldEmGamePlayerSerializer(player, context={'request': request})
    return Response(serializer.data)