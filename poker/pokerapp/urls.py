from django.urls import path, include
from .table_views import TableListView, TableRetrieveView
from .table_settings_views import TableSettingsRetrieveView
from .table_member_views import MyTableMemberRetrieveView, TableMemberRetrieveView, TableMemberListView, SittingTableMemberListView
from .table_invite_views import TableInviteListView
from .table_member_permissions import TableMemberPermissionsUpdateView
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
    path('tables/<uuid:table_pk>/settings', TableSettingsRetrieveView.as_view(), name='table-settings'),

    # members
    path('tables/<uuid:table_pk>/members', TableMemberListView.as_view(), name='table-members'),
    path('tables/<uuid:table_pk>/members/me', MyTableMemberRetrieveView.as_view(), name='my-table-member'),
    # path('tables/<uuid:table_pk>/members/sitting', SittingTableMemberListView.as_view(), name='sitting-table-members'),
    path('tables/<uuid:table_pk>/members/<int:user_pk>', TableMemberRetrieveView.as_view(), name='table-member'),

    #permissions
    path('tables/<uuid:table_pk>/members/<int:user_pk>/permissions', TableMemberPermissionsUpdateView.as_view(), name='table-member-permissions'),

    # invites
    path('tables/join', table_invite_views.join_table),
    path('tables/<uuid:table_pk>/leave', table_invite_views.leave_table),
    path('tables/<uuid:table_pk>/invites', TableInviteListView.as_view(), name='table-invites'),
]
