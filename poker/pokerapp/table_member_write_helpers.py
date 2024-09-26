from .models import Table, TableMember, TableInvite
from . import table_member_fetchers
from django.db import transaction

def join_table(user, table_id, permissions):
    table_member = TableMember.objects.filter(
        user__id=user_id
    ).filter(
        table__id=table_id
    ).first()
    if not table_member:
        table = Table.objects.get(pk=table_id)
        table_member = TableMember(
            user=user,
            table=table,
            permissions=permissions,
        )
    table_member.is_deleted = False
    table_member.save()
    return table_member

@transaction.atomic
def remove_table_member(table_member):
    table_member.is_deleted = True
    table_member.save()
    # sit them out of all games
    players = NoLimitHoldEmGamePlayer.objects.filter(
        player__table_member__id=table_member.id,
        player__is_sitting=True
    )
    for player in players:
        player.is_sitting=False
        player.save()
