from rest_framework import serializers
from django.contrib.auth.models import User
from datetime import timedelta
from .models import *

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = (
            'id',
            'image_url',
            'bio',
        )

class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email',
            'password',
        )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        user = User.objects.create(
            username=email,
            email=email,
        )
        user.set_password(password)
        user.save()
        user.account = Account.objects.create(user=user)
        return user

    # Validate email uniqueness
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email address is already in use.")
        return value

class UserSerializer(serializers.ModelSerializer):
    account = AccountSerializer(required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'account',
        )
        extra_kwargs = {'password': {'write_only': True}}

    def update(self, instance, validated_data):
        account = instance.account
        if 'account' in validated_data:
            account_data = validated_data.pop('account')
            account.bio = account_data.get('bio', account.bio)
            account.image_id = account_data.get('image_id', account.image_id)
        account.save()

        # instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        # instance.first_name = validated_data.get('first_name', instance.first_name)
        # instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()

        return instance

    # Validate email uniqueness
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email address is already in use.")
        return value

class PushNotificationRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushNotificationRegistration
        fields = (
            'id',
            'user',
            'push_id',
        )

class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = [
            'id', 
            'created', 
            'name', 
            'image_url',
        ]

class TableSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TableSettings
        fields = [
            'id', 
            'created', 
            'table',
            'turn_time_limit',
        ]

class TablePermissionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TablePermissions
        fields = [
            'can_edit_permissions',
            'can_edit_settings',
            'can_send_invite',
            'can_remove_member',
            'can_sit_player_out',
            'can_force_move',
            'can_play',
            'can_chat',
            'can_deal',
            'can_adjust_chips',
        ]

class TableNotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TableNotificationSettings
        fields = [
            'is_my_turn',
            'new_member_joined',
            'new_chat_message',
            'i_was_sat_out',
            'i_was_forced_moved',
            'i_was_removed_from_table',
            'big_pot',
            'my_chips_adjusted',
            'i_won_hand',
            'i_lost_hand',
        ]

class TableInviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TableInvite
        fields = [
            'id',
            'table',
            'created', 
            'created_by',
            'code',
            'is_one_time',
            'used_by',
        ]

class TableMemberSerializer(serializers.ModelSerializer):
    permissions = TablePermissionsSerializer(read_only=True)

    class Meta:
        model = TableMember
        fields = [
            'id',
            'created',
            'table',
            'user',
            'username',
            'image_url',
            'is_deleted',
            'permissions',
        ]

class NoLimitHoldEmGameSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoLimitHoldEmGame
        fields = [
            'id', 
            'created', 
            'table',
            'auto_deal', 
            'big_blind',
            'small_blind',
            'starting_chip_count',
        ]

class NoLimitHoldEmGamePlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoLimitHoldEmGamePlayer
        fields = [
            'id', 
            'created', 
            'game',
            'table_id',
            'user_id',
            'username',
            'image_url',
            'chip_count',
            'is_sitting',
            'is_auto_move_on',
        ]

class NoLimitHoldEmHandSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoLimitHoldEmHand
        fields = [
            'id', 
            'game',
            'created', 
            'updated', 
            'hand_json', 
            'completed',
            'players',
        ]

class NoLimitHoldEmChipAdjustmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoLimitHoldEmChipAdjustment
        fields = [
            'id', 
            'created', 
            'player',
            'amount', 
            'summary_statement', 
            'notes', 
        ]

class CurrentGameSerializer(serializers.ModelSerializer):
    table = TableSerializer(read_only=True)
    no_limit_hold_em_game = NoLimitHoldEmGameSerializer(read_only=True)

    class Meta:
        model = CurrentGame
        fields = [
            'id',
            'table',
            'selected_game',
            'no_limit_hold_em_game',
            'users_turn',
            'last_move',
        ]

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            'id', 
            'created',
            'updated',
            'room', 
            'user', 
            'text',
            'username',
            'image_url',
        ]
