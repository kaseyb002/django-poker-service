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

class MyTablePlayerRetrieveView(generics.RetrieveAPIView):
    queryset = TablePlayer.objects.all()
    serializer_class = TablePlayerSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        my_table_player = table_player_fetchers.get_table_player(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        serializer = TablePlayerSerializer(my_table_player, context={'request': request})
        return Response(serializer.data)

class TablePlayerRetrieveView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        user_pk = self.kwargs.get('user_pk')
        table_player = table_player_fetchers.get_table_player(
            user_id=user_pk, 
            table_id=table_pk,
        )
        serializer = TablePlayerSerializer(table_player, context={'request': request})
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        user_pk = self.kwargs.get('user_pk')
        table_player = table_player_fetchers.get_table_player(
            user_id=user_pk, 
            table_id=table_pk,
        )
        my_table_player = table_player_fetchers.get_table_player(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_player.permissions.can_remove_player:
            return responses.unauthorized("User cannot remove players")
        if not table_player_fetchers.get_table_has_another_admin(
            user_id=user_pk,
            table_id=table_pk,
        ):
            return responses.no_admins_remaining()
        table_player.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class TablePlayerListView(generics.ListAPIView):
    queryset = Table.objects.all()
    pagination_class = NumberOnlyPagination
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        my_table_player = table_player_fetchers.get_table_player(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_player:
            return responses.user_not_in_table()
        table_players = TablePlayer.objects.filter(
            table__id=table_pk
        ).prefetch_related('permissions', 'user', 'user__account')

        # Apply pagination
        page = self.paginate_queryset(table_players)
        if page is not None:
            serializer = TablePlayerSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        # If no pagination is applied, return all data
        serializer = TablePlayerSerializer(tables, many=True, context={'request': request})
        return Response(serializer.data)

"""
    def create(self, request, *args, **kwargs):
        class Serializer(serializers.Serializer):
            name = serializers.CharField()
        serializer = Serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        name = serializer.data['name']
        
        # create table
        table = Table(name=name)
        table.save()

        # create settings
        table_settings = TableSettings(table=table)
        table_settings.save()

        # join table
        table_player = TablePlayer(
            user=request.user,
            table=table,
        )
        table_player.save()

        # set permissions
        table_permissions = TablePermissions(
            table_player=table_player,
            can_edit_permissions=True,
        )
        table_permissions.save()

        serializer = TableSerializer(table, context={'request': request})
        return Response(serializer.data)

class TableSettingsView(generics.RetrieveAPIView):
    queryset = TableSettings.objects.all()
    serializer_class = TableSettingsSerializer

@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def create_table(request):
    class Serializer(serializers.Serializer):
        name = serializers.CharField()
    serializer = Serializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    name = serializer.data['name']
    
    # create table
    table = Table(name=name)
    table.save()

    # create settings
    table_settings = TableSettings(table=table)
    table_settings.save()

    # join table
    table_player = TablePlayer(
        user=request.user,
        table=table,
    )
    table_player.save()

    # set permissions
    table_permissions = TablePermissions(
        table_player=table_player,
        can_edit_permissions=True,
    )
    table_permissions.save()

    serializer = TableSerializer(table, context={'request': request})
    return Response(serializer.data)
"""
