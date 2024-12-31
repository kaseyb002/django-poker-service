from .models import Stage10GamePlayer, Stage10Game
from . import table_member_fetchers 
from django.shortcuts import get_object_or_404

def get_or_make_game_player(user_id, game_id):
    player = Stage10GamePlayer.objects.filter(
        game__pk=game_id,   
        table_member__user__pk=user_id
    ).first()
    if not player:
        game = get_object_or_404(
            Stage10Game,
            pk=game_id,
        )
        table_member = table_member_fetchers.get_table_member(
            user_id=user_id, 
            table_id=game.table.id,
        )
        player = Stage10GamePlayer.objects.create(
            game=game,
            table_member=table_member,
        )
    return player