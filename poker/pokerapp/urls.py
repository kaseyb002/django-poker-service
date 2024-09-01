from django.urls import path, include
from .table_views import TableListView, TableRetrieveView
from . import user_views, table_views

urlpatterns = [
    # user 
    path('api-auth/', include('rest_framework.urls')),
    path('account/register', user_views.register),
    path('account/api-token-auth', user_views.CustomAuthToken.as_view()),
    path('account/my_user', user_views.my_user),
    path('account/my_user/username', user_views.update_username),
    path('account/my_user/username/validate', user_views.username_is_valid),
    
    path('tables', TableListView.as_view(), name='table-list'),
    path('tables/<uuid:pk>', TableRetrieveView.as_view(), name='table-detail'),
]
