from django.urls import path, include
from .table_views import TableListView, TableRetrieveView
from .table_settings_views import TableSettingsRetrieveView
from .table_member_views import MyTableMemberRetrieveView, TableMemberRetrieveView, TableMemberListView
from .table_invite_views import TableInviteListView
from .table_member_permissions import TableMemberPermissionsUpdateView
from .game_views import CurrentGameRetrieveView
from . import table_invite_views, user_views, table_views, no_limit_hold_em_views, no_limit_hold_em_action_views
from .no_limit_hold_em_views import PlayerListView, SittingPlayersListView, PlayerRetrieveView, CurrentHoldEmGameRetrieveView, CurrentHoldEmHandRetrieveView, HoldEmGameRetrieveView
from .no_limit_hold_em_adjustment_views import NoLimitHoldChipAdjustmentListView
from . import consumers

urlpatterns = [
    # user 
    path('api-auth/', include('rest_framework.urls')),
    path('account/register', user_views.register),
    path('account/api-token-auth', user_views.CustomAuthToken.as_view()),
    path('account/my_user', user_views.my_user),
    path('account/my_user/username', user_views.update_username),
    path('account/my_user/username/validate', user_views.username_is_valid),
    
    # tables
    path('tables', TableListView.as_view(), name='table-list'),
    path('tables/<uuid:pk>', TableRetrieveView.as_view(), name='table-detail'),
    path('tables/<uuid:table_pk>/settings', TableSettingsRetrieveView.as_view(), name='table-settings'),
    path('tables/<uuid:table_pk>/current_game', CurrentGameRetrieveView.as_view(), name='current-game'),
    path('tables/<uuid:table_pk>/current_game/no_limit_hold_em', CurrentHoldEmGameRetrieveView.as_view(), name='current-hold-em-game'),
    path('tables/<uuid:table_pk>/current_game/no_limit_hold_em/current_hand', CurrentHoldEmHandRetrieveView.as_view(), name='current-hold-em-hand'),

    # members
    path('tables/<uuid:table_pk>/members', TableMemberListView.as_view(), name='table-members'),
    path('tables/<uuid:table_pk>/members/me', MyTableMemberRetrieveView.as_view(), name='my-table-member'),
    path('tables/<uuid:table_pk>/members/<int:user_pk>', TableMemberRetrieveView.as_view(), name='table-member'),

    #permissions
    path('tables/<uuid:table_pk>/members/<int:user_pk>/permissions', TableMemberPermissionsUpdateView.as_view(), name='table-member-permissions'),

    # invites
    path('tables/join', table_invite_views.join_table),
    path('tables/<uuid:table_pk>/leave', table_invite_views.leave_table),
    path('tables/<uuid:table_pk>/invites', TableInviteListView.as_view(), name='table-invites'),

    # no limit hold em
    path('no_limit_hold_em_games/<uuid:game_pk>', HoldEmGameRetrieveView.as_view(), name='hold_em_game'),
    path('no_limit_hold_em_games/<uuid:game_pk>/current_hand', CurrentHoldEmHandRetrieveView.as_view(), name='current_hold_em_game'),
    path('no_limit_hold_em_games/<uuid:game_pk>/sit', no_limit_hold_em_views.sit, name='hold_em_sit'),
    path('no_limit_hold_em_games/<uuid:game_pk>/sit_out', no_limit_hold_em_views.sit_out, name='hold_em_sit_out'),
    path('no_limit_hold_em_games/<uuid:game_pk>/players', PlayerListView.as_view(), name='hold_em_player_list'),
    path('no_limit_hold_em_games/<uuid:game_pk>/sitting_players', SittingPlayersListView.as_view(), name='hold_em_sitting_players'),
    path('no_limit_hold_em_games/<uuid:game_pk>/players/<int:user_pk>', PlayerRetrieveView.as_view(), name='hold_em_player'),
    path('no_limit_hold_em_games/<uuid:game_pk>/players/<int:user_pk>/sit_out', no_limit_hold_em_views.sit_player_out, name='hold_em_sit_out_player'),
    path('no_limit_hold_em_games/<uuid:game_pk>/players/<int:user_pk>/add_chips', no_limit_hold_em_views.add_chips, name='hold_em_add_chips'),
    path('no_limit_hold_em_games/<uuid:game_pk>/chip_adjustments', NoLimitHoldChipAdjustmentListView.as_view(), name='hold_em_chip_adjustments'),
    # game actions
    path('no_limit_hold_em_games/<uuid:game_pk>/deal', no_limit_hold_em_action_views.deal, name='hold_em_deal'),
    path('no_limit_hold_em_games/<uuid:game_pk>/force', no_limit_hold_em_action_views.force_move, name='hold_em_force_move'),
    path('no_limit_hold_em_games/<uuid:game_pk>/<str:action>', no_limit_hold_em_action_views.make_move, name='hold_em_make_move'),
]
