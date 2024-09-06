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

@api_view(['POST'])
def join_table(request):
    """
    Joins table using an invite code
    """
    class Serializer(serializers.Serializer):
        code = serializers.CharField()
    serializer = Serializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    code = serializer.data['code']

    invite = TableInvite.objects.get(
        code=code
    )
    if invite.used_by:
        return responses.bad_request("Invite code has already been used.")

    # set permissions
    player_permissions = TablePermissions()
    player_permissions.save()

    # join table
    table_player = table_player_fetchers.get_table_player(
        user_id=request.user.id, 
        table_id=invite.table.id,
    )
    if not table_player:
        table_player = TablePlayer(
            user=request.user,
            table=invite.table,
            permissions=player_permissions,
        )
        table_player.save()

    if invite.is_one_time:
        invite.used_by = request.user
        invite.save()

    serializer = TablePlayerSerializer(table_player, context={'request': request})
    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED,
    )

@api_view(['DELETE'])
def leave_table(request, *args, **kwargs):
    """
    Leaves the table
    """
    table_pk = kwargs.get('table_pk')
    table_player = table_player_fetchers.get_table_player(
        user_id=request.user.id, 
        table_id=table_pk,
    )
    if not table_player_fetchers.get_table_has_another_admin(
        user_id=request.user.id,
        table_id=table_pk,
    ):
        return responses.no_admins_remaining()
    table_player.delete()
    return Response(
        serializer.data,
        status=status.HTTP_204_NO_CONTENT,
    )

class TableInviteListView(generics.ListCreateAPIView):
    pagination_class = NumberOnlyPagination
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        invites = TableInvite.objects.filter(
            table__pk=table_pk
        ).filter(
            created_by__id=request.user.id
        )

        # Apply pagination
        page = self.paginate_queryset(invites)
        if page is not None:
            serializer = TableInviteSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        # If no pagination is applied, return all data
        serializer = TableInviteSerializer(tables, many=True, context={'request': request})
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')

        table_player = table_player_fetchers.get_table_player(
            user_id=request.user.id, 
            table_id=table_pk,
        )

        if not table_player.permissions.can_send_invite:
            return responses.unauthorized("User does not have invite permissions.")

        #create invite
        invite = TableInvite(
            created_by=request.user,
            table=table_player.table,
        )
        invite.save()
            
        serializer = TableInviteSerializer(invite, context={'request': request})
        return Response(serializer.data)

"""
class TablePlayerRetrieveView(generics.RetrieveAPIView):
    queryset = TablePlayer.objects.all()
    serializer_class = TablePlayerSerializer
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
