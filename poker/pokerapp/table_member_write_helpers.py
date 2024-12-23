from .models import Table, TableMember, NoLimitHoldEmGamePlayer, TableNotificationSettings, TablePermissions
from . import table_member_fetchers
from django.db import transaction
from django.shortcuts import get_object_or_404
from . import push_categories, push_notifications, push_notifications_fetchers

def join_table(user, table_id, permissions):
    table_member = TableMember.objects.filter(
        user__id=user.id
    ).filter(
        table__id=table_id
    ).first()
    if not table_member:
        table = get_object_or_404(
            Table,
            pk=table_id,
        )
        notification_settings = TableNotificationSettings.objects.create()
        table_member = TableMember(
            user=user,
            table=table,
            permissions=permissions,
            notification_settings=notification_settings,
        )
    table_member.is_deleted = False
    table_member.save()
    subscribed_users = push_notifications_fetchers.users_subscribed_to_new_member_joined(
        table_id=table_id,
    )
    push_notifications.send_push_to_users(
        users=subscribed_users,
        text="Give them a welcome.",
        title=table_member.user.username + " joined the table",
        subtitle=table_member.table.name,
        category=push_categories.NEW_MEMBER_JOINED,
        extra_data={
            "table_id": table_id,
            "user_id": str(table_member.user.id),
        },
        thread_id=push_categories.chat_room_id(table_id),
    )
    return table_member

@transaction.atomic
def remove_table_member(table_member, removed_by):
    table_member.is_deleted = True
    table_member.save()
    # sit them out of all games
    players = NoLimitHoldEmGamePlayer.objects.filter(
        table_member__id=table_member.id,
        is_sitting=True
    )
    for player in players:
        player.is_sitting=False
        player.save()
    if table_member.notification_settings.i_was_removed_from_table:
        push_notifications.send_push(
            to_user=table_member.user,
            text=removed_by.username + " removed you.",
            title="You've been removed from the table.",
            subtitle=table_member.table.name,
            category=push_categories.I_WAS_REMOVED_FROM_TABLE,
            extra_data={
                "table_id": str(table_member.table.id),
            },
            thread_id=push_categories.chat_room_id(table_member.table.id),
        )

def join_table_on_sign_up(user):
    table_member = TableMember.objects.filter(
        user__id=user.id
    ).first()
    if not table_member:
        table = Table.objects.filter(
            join_on_account_sign_up=True
        ).first()
        if not table:
            return None
        member_permissions = TablePermissions.objects.create()
        table_member = join_table(
            user=user, 
            table_id=table.id, 
            permissions=member_permissions,
        )
    return table_member