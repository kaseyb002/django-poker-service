from rest_framework import permissions
from .models import TableMember, NoLimitHoldEmGamePlayer
from django.shortcuts import get_object_or_404

def get_table_member(user_id, table_id, check_deleted=True):
    if check_deleted:
        return TableMember.objects.filter(
            user__id=user_id,
            table__id=table_id,
            is_deleted=False,
        ).first()
    else:
        return TableMember.objects.filter(
            user__id=user_id,
            table__id=table_id,
        ).first()

def get_table_member_or_404(user_id, table_id, check_deleted=True):
    if check_deleted:
        return get_object_or_404(
            TableMember,
            user__id=user_id,
            table__id=table_id,
            is_deleted=False,
        )
    else:
        return get_object_or_404(
            TableMember,
            user__id=user_id,
            table__id=table_id,
        )

def get_table_has_another_admin(user_id, table_id):
    return TableMember.objects.filter(
        table__id=table_id,
        permissions__can_edit_permissions=True,
    ).exclude(
        user__id=user_id,
    ).exists()

def table_member_count(table_id):
    return TableMember.objects.filter(
        table__id=table_id,
        is_deleted=False,
    ).count()