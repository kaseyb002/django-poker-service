from rest_framework import permissions
from .models import NoLimitHoldEmGamePlayer, NoLimitHoldEmGame
from . import table_member_fetchers 

def get_or_make_game_player(user_id, game_id):
    player = NoLimitHoldEmGamePlayer.objects.filter(
        game__pk=game_id,   
        table_member__user__pk=user_id
    ).first()
    if not player:
        game = NoLimitHoldEmGame.objects.get(
            pk=game_id
        )
        table_member = table_member_fetchers.get_table_member(
            user_id=user_id, 
            table_id=game.table.id,
        )
        player = NoLimitHoldEmGamePlayer(
            game=game,
            table_member=table_member,
            chip_count=game.starting_chip_count,
        )
        player.save()
    return player

