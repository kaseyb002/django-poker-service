from .models import Table, TableMember, TableInvite
from . import table_member_fetchers

def join_table(user, table_id, permissions):
    table_member = table_member_fetchers.get_table_member(
        user_id=user.id, 
        table_id=table_id,
    )
    if not table_member:
        table = Table.objects.get(pk=table_id)
        table_member = TableMember(
            user=user,
            table=table,
            permissions=permissions,
        )
        table_member.save()
    return table_member
