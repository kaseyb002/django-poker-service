import asyncio
import threading
from asgiref.sync import async_to_sync, sync_to_async
from decimal import Decimal
from .models import *
from .serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from . import table_member_fetchers 
from . import responses
from . import hand_json_helpers
from . import delayed_task
from . import push_notifications, push_notifications_fetchers, push_categories
import json
import requests
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404
import locale
from django.db.models import Max
from . import errors

def send_request(path, data):
    json_body = json.loads(json.dumps(data))
    url = 'http://127.0.0.1:8080/nolimitholdem/' + path
    response = requests.post(url, json=json_body)
    if response.status_code != 200:
        raise errors.PokerServiceError(response.json().get('reason', "Unknown error."))
    return response.json()

def valid_current_hand(game_id):
    return NoLimitHoldEmHand.objects.filter(
        game__pk=game_id,
        completed__isnull=True
    ).first()

@api_view(['POST'])
def deal(request, *args, **kwargs):
    """
    Deal hold em hand or return current hand
    """
    game_pk = kwargs.get('game_pk')
    game = get_object_or_404(
        NoLimitHoldEmGame,
        pk=game_pk,
    )
    my_table_member = table_member_fetchers.get_table_member(
        user_id=request.user.id, 
        table_id=game.table.id,
    )
    if not my_table_member.permissions.can_deal:
        return responses.forbidden("User is not permitted to deal.")
    hand = deal_new_hand(game=game)
    serializer = NoLimitHoldEmHandSerializer(
        hand, 
        context={'request': request},
        current_player_id=request.user.id,
    )
    return Response(serializer.data)

def deal_new_hand(game):
    current_hand = NoLimitHoldEmHand.objects.filter(
        game__pk=game.id,
        completed__isnull=True,
    ).first()
    if current_hand:
        return current_hand
    def make_player_json(player):
        return {
            'id':str(player.user_id()),
            'name':player.username(),
            'image_url':player.image_url(),
            'chip_count':float(player.chip_count),
        }
    turn_off_auto_move_for_all_players(game_id=game.id)
    sit_out_players_with_insufficient_stack(game.id)
    sitting_players = NoLimitHoldEmGamePlayer.objects.filter(
        game__id=game.id,
        is_sitting=True,
    )
    # check player count is in bounds
    if sitting_players.count() < 2:
        raise errors.PokerServiceError("Not enough players to play.")
    if sitting_players.count() > 10:
        raise errors.PokerServiceError("Too many players. " + str(sitting_players.count()) + " sitting. Max is 10.")
    # make players
    sitting_players = players_for_next_hand(game_id=game.id)
    sitting_players_json = []
    for sitting_player in sitting_players:
        sitting_players_json.append(make_player_json(sitting_player))
    # send request to vapor service
    data = {
        'smallBlind':float(game.small_blind),
        'bigBlind':float(game.big_blind),
        'players': sitting_players_json,
    }
    response_json = send_request('deal', data)
    hand_json = response_json['hand']
    max_hand_number = (
        NoLimitHoldEmHand.objects.filter(game_id=game.id)
        .aggregate(Max('hand_number'))['hand_number__max'] or 0
    )
    # save hand
    hand = NoLimitHoldEmHand.objects.create(
        game=game,
        hand_json=hand_json,
        hand_number=max_hand_number + 1,
    )
    hand.players.set(sitting_players)
    hand.force_reveal_cards_for_player_ids = response_json.get('force_reveal_cards_for_player_ids', [])
    # if some players cannot cover the blind, an auto-completed hand may result
    hand = finish_move(
        current_hand=hand,
        hand_json=hand_json,
    )
    hand.save()
    return hand

def players_for_next_hand(game_id):
    sitting_players = NoLimitHoldEmGamePlayer.objects.filter(
        game__id=game_id,
        is_sitting=True,
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
    game = get_object_or_404(
        NoLimitHoldEmGame,
        pk=game_pk,
    )
    my_table_member = table_member_fetchers.get_table_member(
        user_id=request.user.id, 
        table_id=game.table.id,
    )
    if not my_table_member.permissions.can_play:
        return responses.forbidden("User is not permitted to play.")
    current_hand = valid_current_hand(game_pk)
    if not current_hand:
        return responses.bad_request("No hand currently being played.")
    if not hand_json_helpers.is_players_turn(request.user.id, current_hand.hand_json):
        return responses.bad_request("Not the user's turn.")
    action = kwargs.get('action')
    round_before_move = current_hand.hand_json['round']
    amount = None
    if action == 'bet':
        class Serializer(serializers.Serializer):
            amount = serializers.DecimalField(max_digits=10, decimal_places=2)
        serializer = Serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        amount = Decimal(serializer.data['amount'])

    response_json = act_on_hand(
        action=action, 
        amount=amount,
        current_hand=current_hand,
    )
    hand_json = response_json['hand']
    if action == 'bet':
        turn_off_auto_move_for_all_players(game_id=game_pk)
    if hand_json['round'] is not round_before_move:
        turn_off_auto_move_for_all_players(game_id=game_pk)
    current_hand = finish_move(
        current_hand=current_hand,
        hand_json=hand_json,
    )
    current_hand.force_reveal_cards_for_player_ids = response_json.get('force_reveal_cards_for_player_ids', [])
    current_hand.save()
    serializer = NoLimitHoldEmHandSerializer(
        current_hand, 
        context={'request': request},
        current_player_id=request.user.id,
    )
    return Response(serializer.data)

@api_view(['POST'])
def force_move(request, *args, **kwargs):
    game_pk = kwargs.get('game_pk')
    game = get_object_or_404(
        NoLimitHoldEmGame,
        pk=game_pk,
    )
    my_table_member = table_member_fetchers.get_table_member(
        user_id=request.user.id, 
        table_id=game.table.id,
    )
    if not my_table_member.permissions.can_force_move:
        return responses.forbidden("User is not permitted force a move.")
    current_hand = valid_current_hand(game_pk)
    if not current_hand:
        return responses.bad_request("No hand currently being played.")
    player_user_id = hand_json_helpers.current_player_user_id(current_hand.hand_json)
    response_json = act_on_hand(
        action='force', 
        amount=None,
        current_hand=current_hand,
    )
    hand_json = response_json['hand']
    current_hand.force_reveal_cards_for_player_ids = response_json.get('force_reveal_cards_for_player_ids', [])
    current_hand = finish_move(
        current_hand=current_hand,
        hand_json=hand_json,
    )

    if type(current_hand) == Response:
        response = current_hand
        return response

    if player_user_id:
        notify_i_was_forced_moved(
            current_hand=current_hand, 
            player_user_id=player_user_id, 
            request=request,
        )

    serializer = NoLimitHoldEmHandSerializer(
        current_hand, 
        context={'request': request},
        current_player_id=request.user.id,
    )
    return Response(serializer.data)

@api_view(['POST'])
def toggle_auto_move(request, *args, **kwargs):
    class Serializer(serializers.Serializer):
        is_auto_move_on = serializers.BooleanField()
    serializer = Serializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    is_auto_move_on = serializer.data['is_auto_move_on']
    game_pk = kwargs.get('game_pk')
    game = get_object_or_404(
        NoLimitHoldEmGame,
        pk=game_pk,
    )
    my_table_member = table_member_fetchers.get_table_member(
        user_id=request.user.id, 
        table_id=game.table.id,
    )
    if not my_table_member.permissions.can_play:
        return responses.forbidden("User is not permitted to play.")
    current_hand = valid_current_hand(game_pk)
    if not current_hand:
        return responses.bad_request("No hand currently being played.")
    if not hand_json_helpers.is_player_waiting_to_move(request.user.id, current_hand.hand_json):
        return responses.bad_request("User is not waiting to play.")
    player = get_object_or_404(
        NoLimitHoldEmGamePlayer,
        game__pk=game_pk,
        table_member__user__id=request.user.id,
    )
    player.is_auto_move_on = is_auto_move_on
    player.save()
    serializer = NoLimitHoldEmGamePlayerSerializer(player, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def show_cards(request, *args, **kwargs):
    class Serializer(serializers.Serializer):
        show_cards = serializers.CharField()
        player_id = serializers.CharField()
    serializer = Serializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    player_id = serializer.data['player_id']
    show_cards = serializer.data['show_cards']
    hand_pk = kwargs.get('hand_pk')
    hand = get_object_or_404(
        NoLimitHoldEmHand,
        pk=hand_pk,
    )
    my_table_member = table_member_fetchers.get_table_member(
        user_id=request.user.id, 
        table_id=hand.game.table.id,
    )
    if not request.user.id == int(player_id):
        return responses.forbidden("You can't show another player's cards.")
    if not hand:
        return responses.bad_request("No hand currently being played.")
    data = {
        'showCards':show_cards,
        'playerID':player_id,
        'hand': hand.hand_json,
    }
    response_json = send_request('show', data)
    hand_json = response_json['hand']
    hand.hand_json = hand_json
    hand.force_reveal_cards_for_player_ids = hand_json.get('force_reveal_cards_for_player_ids', [])
    hand.save()
    serializer = NoLimitHoldEmHandSerializer(
        hand, 
        context={'request': request},
        current_player_id=request.user.id,
    )
    return Response(serializer.data)

@api_view(['POST'])
def progress_round(request, *args, **kwargs):
    hand_pk = kwargs.get('hand_pk')
    hand = get_object_or_404(
        NoLimitHoldEmHand,
        pk=hand_pk,
    )
    my_table_member = table_member_fetchers.get_table_member(
        user_id=request.user.id, 
        table_id=hand.game.table.id,
    )
    if not hand:
        return responses.bad_request("No hand currently being played.")
    data = {
        'hand': hand.hand_json,
    }
    response_json = send_request('progressRound', data)
    hand_json = response_json['hand']
    hand.force_reveal_cards_for_player_ids = response_json.get('force_reveal_cards_for_player_ids', [])
    hand = finish_move(
        current_hand=hand,
        hand_json=hand_json,
    )
    serializer = NoLimitHoldEmHandSerializer(
        hand, 
        context={'request': request},
        current_player_id=request.user.id,
    )
    return Response(serializer.data) 

def act_on_hand(action, amount, current_hand):
    if action == 'bet':
        if not amount:
            return responses.bad_request("Cannot bet 0.")
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

def finish_move(current_hand, hand_json):
    current_hand.hand_json = hand_json
    player_chip_counts = {
        player['player']['id']: player['player']['chip_count']
        for player in hand_json['player_hands']
    }
    for player in current_hand.players.all():
        if str(player.user_id()) in player_chip_counts:
            player.chip_count = player_chip_counts[str(player.user_id())]
            player.save()
    current_hand.game.table.current_game.last_move = timezone.now()
    current_player_id = hand_json_helpers.current_player_user_id(hand_json=hand_json)
    if current_player_id:
        current_player = get_object_or_404(
            NoLimitHoldEmGamePlayer,
            game__pk=current_hand.game.id,
            table_member__user__id=current_player_id,
        )
        current_hand.game.table.current_game.members_turn = current_player.table_member
    else:
        current_hand.game.table.current_game.members_turn = None
    current_hand.game.table.current_game.save()
    current_hand.save()
    if hand_json_helpers.is_hand_complete(hand_json):
        current_hand.completed = timezone.now()
        current_hand.save()
        notify_winners_and_losers(current_hand=current_hand)
        notify_big_pot_subscribers(current_hand=current_hand)
        sit_out_players_with_insufficient_stack(game_id=current_hand.game.id)
        if current_hand.game.auto_deal:
            def deal_new():
                deal_new_hand(game=current_hand.game)
            delayed_task.run_delayed(
                task=deal_new,
                delay=5,
            )
        return current_hand
    else:
        current_hand = auto_move_if_needed(
            current_hand=current_hand,
        )
        notify_is_my_turn(current_hand)
        return current_hand

def auto_move_if_needed(current_hand):
    user_id = hand_json_helpers.current_player_user_id(current_hand.hand_json)
    if not user_id:
        return current_hand
    player = NoLimitHoldEmGamePlayer.objects.filter(
        game__pk=current_hand.game.id
    ).get(
        table_member__user__id=user_id
    )
    if player.is_auto_move_on or not player.is_sitting:
        response_json = act_on_hand(
            action='force', 
            amount=None,
            current_hand=current_hand,
        )
        hand_json = response_json['hand']
        current_hand = finish_move(
            current_hand=current_hand,
            hand_json=hand_json,
        )
        current_hand.force_reveal_cards_for_player_ids = response_json.get('force_reveal_cards_for_player_ids', [])
        current_hand.save()
    return current_hand

@transaction.atomic
def turn_off_auto_move_for_all_players(game_id):
    players = NoLimitHoldEmGamePlayer.objects.filter(
        game__pk=game_id,
        is_auto_move_on=True,
    )
    for player in players:
        player.is_auto_move_on = False
        player.save()

def notify_i_was_forced_moved(current_hand, player_user_id, request):
    table_member = table_member_fetchers.get_table_member(
        user_id=player_user_id,
        table_id=current_hand.game.table.id,
    )
    if table_member.notification_settings.i_was_forced_moved:
        action = "fold"
        if hand_json_helpers.is_player_in_hand(
            user_id=player_user_id,
            hand_json=current_hand.hand_json,
        ):
            action = "check"
        push_notifications.send_push(
            to_user=table_member.user, 
            text=request.user.username + " forced you to move.",
            title="You were forced to " + action + ".", 
            subtitle=table_member.table.name,
            category=push_categories.I_WAS_FORCED_MOVED,
            extra_data={
                "table_id": str(current_hand.game.table.id),
                "no_limit_hold_em_game_id": str(current_hand.game.id),
            },
            thread_id=push_categories.game_thread_id(current_hand.game.id),
            collapse_id=push_categories.game_collapse_id(current_hand.game.id),
        )

def notify_is_my_turn(current_hand):
    player_user_id = hand_json_helpers.current_player_user_id(current_hand.hand_json)
    if player_user_id:
        table_member = table_member_fetchers.get_table_member(
            user_id=player_user_id,
            table_id=current_hand.game.table.id,
        )
        if table_member.notification_settings.is_my_turn:
            board_cards = hand_json_helpers.board_cards(current_hand.hand_json)
            board_cards_str = hand_json_helpers.board_cards_to_string(
                board_cards=board_cards, 
                round=current_hand.hand_json.get('round', 0),
            )
            if board_cards_str == "":
                board_cards_str = "Preflop"
            else:
                board_cards_str = "Board: " + board_cards_str
            pocket_cards = hand_json_helpers.pocket_cards_for_user(
                user_id=player_user_id,
                hand_json=current_hand.hand_json,
            )
            if pocket_cards:
                pocket_cards_str = hand_json_helpers.pocket_cards_to_string(pocket_cards)
                push_notifications.send_push(
                    to_user=table_member.user, 
                    text=pocket_cards_str + " " + board_cards_str,
                    title="Your turn", 
                    subtitle=table_member.table.name,
                    category=push_categories.IS_MY_TURN,
                    extra_data={
                        "table_id": str(current_hand.game.table.id),
                        "no_limit_hold_em_game_id": str(current_hand.game.id),
                    },
                    thread_id=push_categories.game_thread_id(current_hand.game.id),
                    collapse_id=push_categories.game_collapse_id(current_hand.game.id),
                )

def notify_big_pot_subscribers(current_hand):
    hand_json = current_hand.hand_json
    (max_net_gain, player_user_id) = hand_json_helpers.biggest_net_gain(hand_json)
    if max_net_gain > current_hand.game.big_blind * 50:
        table_member = table_member_fetchers.get_table_member(
            user_id=player_user_id,
            table_id=current_hand.game.table.id,
            check_deleted=False,
        )
        subscribed_users = push_notifications_fetchers.users_subscribed_to_big_pot(
            table_id=current_hand.game.table.id,
        )
        if table_member.notification_settings.big_pot:
            push_notifications.send_push_to_users(
                users=subscribed_users,
                text=table_member.username() + " made " + str(max_net_gain) + ".",
                title="Big Pot", 
                subtitle=table_member.table.name,
                category=push_categories.BIG_POT,
                extra_data={
                    "table_id": str(table_member.table.id),
                    "no_limit_hold_em_game_id": str(current_hand.game.id),
                    "no_limit_hold_em_hand_id": str(current_hand.id),
                },
                thread_id=push_categories.game_thread_id(current_hand.game.id),
            ) 

def notify_winners_and_losers(current_hand):
    hand_json = current_hand.hand_json
    winners = hand_json_helpers.get_players_with_net_gain(hand_json=hand_json)
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    for winner in winners:
        table_member = table_member_fetchers.get_table_member(
            user_id=winner['player_id'],
            table_id=current_hand.game.table.id,
        )
        if table_member.notification_settings.i_won_hand:
            formatted_number = locale.currency(winner['net_gain'], grouping=True)
            push_notifications.send_push(
                to_user=table_member.user, 
                text="You made " + formatted_number + ".", 
                title="You won the hand", 
                subtitle=current_hand.game.table.name, 
                category=push_categories.I_WON_HAND, 
                extra_data={
                    "table_id": str(current_hand.game.table.id),
                    "no_limit_hold_em_game_id": str(current_hand.game.id),
                    "no_limit_hold_em_hand_id": str(current_hand.id),
                },
                thread_id=push_categories.game_thread_id(current_hand.game.id),
                collapse_id=push_categories.game_collapse_id(current_hand.game.id),
            )
    losers = hand_json_helpers.get_players_with_net_loss(hand_json=hand_json)
    for loser in losers:
        table_member = table_member_fetchers.get_table_member(
            user_id=winner['player_id'],
            table_id=current_hand.game.table.id,
        )
        if table_member.notification_settings.i_lost_hand:
            formatted_number = locale.currency(loser['net_loss'], grouping=True)
            push_notifications.send_push(
                to_user=table_member.user, 
                text="You lost " + formatted_number + ".", 
                title="You lost the hand", 
                subtitle=current_hand.game.table.name, 
                category=push_categories.I_LOST_HAND, 
                extra_data={
                    "table_id": str(current_hand.game.table.id),
                    "no_limit_hold_em_game_id": str(current_hand.game.id),
                    "no_limit_hold_em_hand_id": str(current_hand.id),
                },
                thread_id=push_categories.game_thread_id(current_hand.game.id),
                collapse_id=push_categories.game_collapse_id(current_hand.game.id),
            )

@transaction.atomic
def sit_out_players_with_insufficient_stack(game_id):
    sitting_players = NoLimitHoldEmGamePlayer.objects.filter(
        game__id=game_id,
        is_sitting=True,
    )
    for sitting_player in sitting_players:
        if sitting_player.chip_count <= 0:
            sitting_player.is_sitting=False
            sitting_player.save()
    return sitting_players