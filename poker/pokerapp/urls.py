from django.urls import path, include
from rest_framework.authtoken import views as authtoken_views
from rest_framework.routers import DefaultRouter
from pokerapp import views
from .table_views import TableListView
from . import user_views, table_views

urlpatterns = [
    # user 
    path('api-auth/', include('rest_framework.urls')),
    path('account/register', user_views.register),
    path('account/api-token-auth', user_views.CustomAuthToken.as_view()),
    path('account/my_user', user_views.my_user),
    path('account/my_user/username', user_views.update_username),
    path('account/my_user/username/validate', user_views.username_is_valid),
    
    path('tables/', TableListView.as_view(), name='table-list'),
    # path('tables/settings/<uuid:pk>/', TableSettingsView.as_view(), name='table-settings'),
    path('tables', table_views.create_table),
]
