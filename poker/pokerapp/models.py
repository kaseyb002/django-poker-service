import uuid
from django.contrib.auth.models import User
from django.db import models
from enum import Enum

class Account(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image_url = models.URLField(null=True, blank=True)
    bio = models.CharField(max_length=1024, blank=True)

class PushNotificationRegistration(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('auth.User', related_name='push_registrations', on_delete=models.CASCADE)
    push_id = models.CharField(max_length=192, blank=True)

class Table(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('auth.User', related_name='created_tables', on_delete=models.SET_NULL, null=True, editable=False)
    name = models.CharField(max_length=25, blank=False)
    tagline = models.CharField(max_length=40, blank=True)
    description = models.CharField(max_length=2000, blank=True)
    image_url = models.URLField(null=True, blank=True)
    join_on_account_sign_up = models.BooleanField(default=False)

    class Meta:
        ordering = ['created']

class TableSettings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    table = models.OneToOneField(
        Table,
        on_delete=models.CASCADE,
        editable=False,
    )
    turn_time_limit = models.DurationField(null=True, blank=True)

class TablePermissions(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    can_edit_permissions = models.BooleanField(default=False)
    can_edit_settings = models.BooleanField(default=False)
    can_send_invite = models.BooleanField(default=True)
    can_remove_member = models.BooleanField(default=False)
    can_force_move = models.BooleanField(default=False)
    can_play = models.BooleanField(default=True)
    can_sit_player_out = models.BooleanField(default=False)
    can_chat = models.BooleanField(default=True)
    can_adjust_chips = models.BooleanField(default=False)
    can_deal = models.BooleanField(default=True)

class TableNotificationSettings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_my_turn = models.BooleanField(default=True)
    new_member_joined = models.BooleanField(default=False)
    new_chat_message = models.BooleanField(default=True)
    i_was_sat_out = models.BooleanField(default=True)
    i_was_forced_moved = models.BooleanField(default=True)
    i_was_removed_from_table = models.BooleanField(default=True)
    # no limit
    big_pot = models.BooleanField(default=True)
    my_chips_adjusted = models.BooleanField(default=True)
    i_won_hand = models.BooleanField(default=True)
    i_lost_hand = models.BooleanField(default=True)

class TableInvite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('auth.User', related_name='created_invites', on_delete=models.SET_NULL, null=True)
    table = models.ForeignKey(Table, related_name='invites', on_delete=models.CASCADE)
    code = models.CharField(max_length=22, unique=True, editable=False)
    is_one_time = models.BooleanField(default=True)
    used_by = models.ForeignKey('auth.User', related_name='used_invites', on_delete=models.SET_NULL, null=True)

    def used_by_username(self):
        if self.used_by:
            return self.used_by.username
        return None

    def used_by_image_url(self):
        if self.used_by:
            return self.used_by.account.image_url
        return None

    class Meta:
        ordering = ['-created']

class TableMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    user = models.ForeignKey('auth.User', related_name='memberships', on_delete=models.CASCADE)
    table = models.ForeignKey(Table, related_name='members', on_delete=models.CASCADE)
    permissions = models.OneToOneField(TablePermissions, null=True, on_delete=models.SET_NULL)
    notification_settings = models.OneToOneField(TableNotificationSettings, null=True, on_delete=models.SET_NULL)

    def username(self):
        return self.user.username

    def first_name(self):
        return self.user.first_name

    def last_name(self):
        return self.user.last_name

    def image_url(self):
        return self.user.account.image_url

    class Meta:
        ordering = ['created']

class NoLimitHoldEmGame(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    table = models.ForeignKey(Table, related_name='no_limit_hold_em_games', on_delete=models.CASCADE)
    auto_deal = models.BooleanField(default=True)
    big_blind = models.DecimalField(max_digits=10, decimal_places=2, default=0.10)
    small_blind = models.DecimalField(max_digits=10, decimal_places=2, default=0.05)
    starting_chip_count = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)

    class Meta:
        ordering = ['-created']
       
class NoLimitHoldEmGamePlayer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    game = models.ForeignKey(NoLimitHoldEmGame, related_name='players', on_delete=models.CASCADE)
    table_member = models.ForeignKey(TableMember, related_name='no_limit_hold_em_game_players', on_delete=models.CASCADE)
    chip_count = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    is_sitting = models.BooleanField(default=False)
    is_auto_move_on = models.BooleanField(default=False)

    def user_id(self):
        return self.table_member.user.id

    def table_id(self):
        return self.table_member.table.id

    def username(self):
        return self.table_member.username()

    def image_url(self):
        return self.table_member.image_url()

class NoLimitHoldEmHand(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game = models.ForeignKey(NoLimitHoldEmGame, related_name='hands', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    completed = models.DateTimeField(null=True)
    players = models.ManyToManyField(NoLimitHoldEmGamePlayer)
    hand_json = models.JSONField(null=False, blank=False)
    hand_number = models.BigIntegerField(unique=True, null=True)

    def is_completed(self):
        return not self.completed

    class Meta:
        ordering = ['-created']

class NoLimitHoldEmChipAdjustment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    player = models.ForeignKey(NoLimitHoldEmGamePlayer, related_name='chip_adjustments', on_delete=models.CASCADE)
    adjusted_by = models.ForeignKey(TableMember, related_name='chip_adjustments', on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    summary_statement = models.CharField(max_length=1024, blank=False)
    notes = models.CharField(max_length=1024, blank=True)

    class Meta:
        ordering = ['-created']

class GameType(models.TextChoices):
    NO_LIMIT_HOLD_EM = 'NO_LIMIT_HOLD_EM', 'No Limit Hold Em'
 
class CurrentGame(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    last_move = models.DateTimeField(auto_now=True)
    members_turn = models.ForeignKey(TableMember, related_name='turns', on_delete=models.CASCADE, null=True)
    selected_game = models.CharField(
        max_length=40,
        choices=GameType.choices,
    )
    table = models.OneToOneField(
        Table,
        related_name='current_game',
        on_delete=models.CASCADE,
    )
    no_limit_hold_em_game = models.OneToOneField(
        NoLimitHoldEmGame,
        on_delete=models.SET_NULL,
        null=True,
    )

    def users_turn(self):
        if self.members_turn:
            return self.members_turn.user.id
        else:
            return None

    class Meta:
        ordering = ['-last_move']

class ChatRoom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)

class TableChatRoom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    room = models.OneToOneField(
        ChatRoom,
        on_delete=models.CASCADE,
    )
    table = models.OneToOneField(
        Table,
        on_delete=models.CASCADE,
    )

class ChatMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.CharField(max_length=1024, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    room = models.ForeignKey(ChatRoom, related_name='messages', on_delete=models.CASCADE)
    user = models.ForeignKey('auth.User', related_name='chat_messages', on_delete=models.CASCADE)

    def username(self):
        return self.user.username

    def image_url(self):
        return self.user.account.image_url

    class Meta:
        ordering = ['-created']