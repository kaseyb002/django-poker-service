from .models import *

def users_subscribed_to_big_pot(table_id):
    table_members = TableMember.objects.filter(
        table__id=table_id,
        is_deleted=False,
        notification_settings__big_pot=True,
    )
    return [member.user for member in table_members]

def users_subscribed_to_chat_message(table_id, author_user_id):
    table_members = TableMember.objects.filter(
        table__id=table_id,
        is_deleted=False,
        notification_settings__new_chat_message=True,
    ).exclude(
        user__id=author_user_id,
    )
    return [member.user for member in table_members]

def users_subscribed_to_new_member_joined(table_id):
    table_members = TableMember.objects.filter(
        table__id=table_id,
        is_deleted=False,
        notification_settings__new_member_joined=True,
    )
    return [member.user for member in table_members]