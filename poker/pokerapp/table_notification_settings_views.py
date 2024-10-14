from django.shortcuts import render
from django.contrib.auth.models import User
from .models import *
from .serializers import *
from pokerapp import models
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import generics, viewsets, status
from rest_framework.permissions import IsAuthenticated
from . import table_member_fetchers 
from . import responses
from django.shortcuts import get_object_or_404

class TableNotificationSettingsRetrieveView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        serializer = TableNotificationSettingsSerializer(my_table_member.notification_settings, context={'request': request})
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        settings_serializer = TableNotificationSettingsSerializer(
            my_table_member.notification_settings,
            data=request.data, 
            partial=True,
            context={'request': request},
        )
        settings_serializer.is_valid(raise_exception=True)
        settings_serializer.save()
        return Response(settings_serializer.data)
