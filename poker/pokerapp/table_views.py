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
from rest_framework.pagination import PageNumberPagination
from . import table_member_write_helpers

class TableRetrieveView(generics.RetrieveAPIView):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        table = Table.objects.get(
            members__user__id=request.user.id,
            members__is_deleted=False,
            pk=pk
        )
        serializer = TableSerializer(table, context={'request': request})
        return Response(serializer.data)

class TableListView(generics.ListCreateAPIView):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    pagination_class = NumberOnlyPagination
    permission_classes = [IsAuthenticated]

    def list(self, request):
        tables = Table.objects.filter(
            members__user__id=request.user.id,
            members__is_deleted=False
        )

        # Apply pagination
        page = self.paginate_queryset(tables)
        if page is not None:
            serializer = TableSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        # If no pagination is applied, return all data
        serializer = TableSerializer(tables, many=True, context={'request': request})
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        class Serializer(serializers.Serializer):
            name = serializers.CharField()
        serializer = Serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        name = serializer.data['name']
        
        # create table
        table = Table(
            name=name,
            created_by=request.user,
        )
        table.save()

        # create settings
        table_settings = TableSettings(table=table)
        table_settings.save()

        # set permissions
        admin_permissions = TablePermissions(
            can_edit_permissions = True,
            can_edit_settings = True,
            can_send_invite = True,
            can_remove_member = True,
            can_sit_player_out = True,
            can_force_move = True,
            can_play = True,
            can_chat = True,
            can_adjust_chips=True,
            can_deal=True,
        )
        admin_permissions.save()

        # join table
        table_member = table_member_write_helpers.join_table(
            user=request.user, 
            table_id=table.id,
            permissions=admin_permissions,
        )

        # setup default hold em game
        hold_em_game = NoLimitHoldEmGame(
            table=table
        )
        hold_em_game.save()

        # create current game
        current_game = CurrentGame(
            table=table,
            no_limit_hold_em_game=hold_em_game,
        )
        current_game.save()

        serializer = TableSerializer(table, context={'request': request})
        return Response(serializer.data)
