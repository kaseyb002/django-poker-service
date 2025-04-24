from .models import NoLimitHoldEmGamePlayer, NoLimitHoldEmGame, NoLimitHoldEmChipAdjustment
from . import table_member_fetchers 
from django.shortcuts import get_object_or_404

def get_or_make_game_player(user_id, game_id):
    player = NoLimitHoldEmGamePlayer.objects.filter(
        game__pk=game_id,   
        table_member__user__pk=user_id
    ).first()
    if not player:
        game = get_object_or_404(
            NoLimitHoldEmGame,
            pk=game_id,
        )
        table_member = table_member_fetchers.get_table_member_or_404(
            user_id=user_id, 
            table_id=game.table.id,
        )
        player = NoLimitHoldEmGamePlayer.objects.create(
            game=game,
            table_member=table_member,
            chip_count=game.starting_chip_count,
        )
        if player.chip_count > 0:
            summary_statement = (
                f"{player.username()} started with ${abs(player.chip_count)}."
            )
            # record adjustment
            adjustment = NoLimitHoldEmChipAdjustment(
                player=player,
                adjusted_by=None,
                amount=player.chip_count,
                summary_statement=summary_statement,
                notes="",
            )
            adjustment.save()
                    
    return player