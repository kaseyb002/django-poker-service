from rest_framework import permissions
from .models import TableMember

def get_table_member(user_id, table_id):
    return TableMember.objects.filter(
        user__id=user_id
    ).filter(
        table__id=table_id
    ).first()

def get_table_has_another_admin(user_id, table_id):
    return TableMember.objects.filter(
        table__id=table_id
    ).filter(
        permissions__can_edit_permissions=True
    ).exclude(
        user__id=user_id
    ).exists()