from django.shortcuts import render
from django.contrib.auth.models import User
from .models import *
from .serializers import *
from pokerapp import models
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import generics, viewsets, status
from rest_framework.permissions import IsAuthenticated
from . import table_player_fetchers 
from . import responses

class TableSettingsRetrieveView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('table_pk')
        table_settings = TableSettings.objects.filter(
            table__players__user__id=request.user.id
        ).get(
            table__pk=pk
        )
        serializer = TableSettingsSerializer(table_settings, context={'request': request})
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        my_table_player = table_player_fetchers.get_table_player(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_player.permissions.can_edit_settings:
            return responses.unauthorized("User cannot edit settings")
        table_settings = TableSettings.objects.get(
            table__pk=table_pk
        )
        settings_serializer = TableSettingsSerializer(
            table_settings,
            data=request.data, 
            partial=True,
            context={'request': request},
        )
        settings_serializer.is_valid(raise_exception=True)
        settings_serializer.save()
        return Response(settings_serializer.data)
