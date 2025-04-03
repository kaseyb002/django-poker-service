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
            'tagline',
            'description',
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

class DefaultTablePermissionsSerializer(serializers.ModelSerializer):
    permissions = TablePermissionsSerializer()

    class Meta:
        model = DefaultTablePermissions
        fields = (
            'id',
            'table',
            'permissions',
        )

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
            'used_by_username',
            'used_by_image_url',
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
    hand_json = serializers.SerializerMethodField()

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
            'hand_number',
        ]

    def __init__(self, *args, **kwargs):
        # Accept and store the authenticated player ID
        self.current_player_id = kwargs.pop('current_player_id', None)
        super().__init__(*args, **kwargs)

    def get_hand_json(self, obj):
        if not obj.hand_json:
            return {}

        data = obj.hand_json.copy()

        # Step 1: Trim board by round (0: preflop, 1: flop, 2: turn, 3: river)
        round_number = data.get("round", 0)
        board_cards = data.get("board", [])
        visible_board = board_cards[: [0, 3, 4, 5][min(round_number, 3)]]
        data["board"] = visible_board

        # Step 2: Prepare for pocket card filtering
        pocket_cards = data.get("pocket_cards", {})
        player_hands = data.get("player_hands", [])
        filtered_pocket_cards = {}

        for hand in player_hands:
            player = hand.get("player", {})
            player_id = player.get("id")
            if not player_id:
                continue

            # Always show full hand to the current player
            if player_id == str(self.current_player_id):
                filtered_pocket_cards[player_id] = pocket_cards.get(player_id, {})
                continue

            # Force reveal logic
            if str(player_id) in obj.force_reveal_cards_for_player_ids:
                filtered_pocket_cards[player_id] = pocket_cards.get(player_id, {})

        data["pocket_cards"] = filtered_pocket_cards

        return data

    def is_ready_for_dramatic_reveal(self, data):
        round_number = data.get("round", 0)
        state = data.get("state", {})
        player_hands = data.get("player_hands", [])

        # 1. Must be before river (river = 3)
        if round_number >= 3:
            return False

        # 2. Must be waiting to progress
        if not isinstance(state, dict) or "waiting_to_progress_to_next_round" not in state:
            return False

        # 3. Count active players who are NOT all-in
        active_players_not_all_in = [
            hand for hand in player_hands
            if hand.get("status") == "in" and hand.get("player", {}).get("chip_count", 0) > 0
        ]

        # 4. Count all active players
        active_player_hands = [
            hand for hand in player_hands
            if hand.get("status") == "in"
        ]

        return len(active_players_not_all_in) <= 1 and len(active_player_hands) > 1

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

class Stage10GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stage10Game
        fields = [
            'id', 
            'created', 
            'updated', 
            'completed',
            'table',
        ]

class Stage10GamePlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stage10GamePlayer
        fields = [
            'id', 
            'created', 
            'game',
            'table_id',
            'user_id',
            'username',
            'image_url',
            'is_sitting',
        ]

class Stage10RoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stage10Round
        fields = [
            'id', 
            'game',
            'created', 
            'updated', 
            'round_json', 
            'completed',
            'players',
            'round_number',
        ]

class CurrentGameSerializer(serializers.ModelSerializer):
    table = TableSerializer(read_only=True)
    no_limit_hold_em_game = NoLimitHoldEmGameSerializer(read_only=True)
    stage_10_game = Stage10GameSerializer(read_only=True)

    class Meta:
        model = CurrentGame
        fields = [
            'id',
            'table',
            'selected_game',
            'no_limit_hold_em_game',
            'stage_10_game',
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
            'is_deleted',
        ]
