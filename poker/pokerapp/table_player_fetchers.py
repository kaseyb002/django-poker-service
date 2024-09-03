from rest_framework import permissions
from .models import TablePlayer

def get_table_player(user_id, table_id):
    return TablePlayer.objects.filter(
        user__id=user_id
    ).get(
        table__id=table_id
    )
