from django.urls import path, include
from rest_framework.authtoken import views as authtoken_views
from rest_framework.routers import DefaultRouter
from pokerapp import views
from .views import TableListView, TableSettingsView
from . import user_views

urlpatterns = [
    # user 
    path('api-auth/', include('rest_framework.urls')),
    path('account/register', user_views.register),
    path('account/api-token-auth', user_views.CustomAuthToken.as_view()),
    path('account/my_user', user_views.my_user),
    
    path('tables/', TableListView.as_view(), name='table-list'),
    path('tables/settings/<uuid:pk>/', TableSettingsView.as_view(), name='table-settings'),
]
