from django.urls import path, include
from .table_views import TableListView, TableRetrieveView
from .table_settings_views import TableSettingsRetrieveView
from .table_player_views import MyTablePlayerRetrieveView, TablePlayerRetrieveView, TablePlayerListView
from .table_invite_views import TableInviteListView
from .table_player_permissions import TablePlayerPermissionsUpdateView
from . import table_invite_views
from . import user_views, table_views

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
    path('tables/<uuid:pk>/settings', TableSettingsRetrieveView.as_view(), name='table-settings'),

    # players
    path('tables/<uuid:table_pk>/players', TablePlayerListView.as_view(), name='table-players'),
    path('tables/<uuid:table_pk>/players/me', MyTablePlayerRetrieveView.as_view(), name='my-table-player'),
    path('tables/<uuid:table_pk>/players/<int:user_pk>', TablePlayerRetrieveView.as_view(), name='table-player'),

    #permissions
    path('tables/<uuid:table_pk>/players/<int:user_pk>/permissions', TablePlayerPermissionsUpdateView.as_view(), name='table-player-permissions'),

    # invites
    path('tables/join', table_invite_views.join_table),
    path('tables/<uuid:table_pk>/invites', TableInviteListView.as_view(), name='table-invites'),
]
