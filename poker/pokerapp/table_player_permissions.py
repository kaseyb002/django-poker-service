from django.shortcuts import render
from django.contrib.auth.models import User
from .models import *
from .serializers import *
from .pagination import NumberOnlyPagination
from pokerapp import models
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import generics, viewsets, status
from rest_framework.permissions import IsAuthenticated
from . import table_player_fetchers 
from . import responses

class TablePlayerPermissionsUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        user_id = self.kwargs.get('user_pk')
        my_table_player = table_player_fetchers.get_table_player(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_player.permissions.can_edit_permissions:
            return responses.unauthorized("User cannot edit permissions")

        table_player = table_player_fetchers.get_table_player(
            user_id=user_id, 
            table_id=table_pk,
        )
        if not table_player:
            return responses.not_found("Player not found in table")

        permissions_serializer = TablePermissionsSerializer(
            table_player.permissions,
            data=request.data, 
            partial=True,
            context={'request': request},
        )
        permissions_serializer.is_valid(raise_exception=True)
        permissions_serializer.save()
        serializer = TablePlayerSerializer(table_player, context={'request': request})
        return Response(serializer.data)
