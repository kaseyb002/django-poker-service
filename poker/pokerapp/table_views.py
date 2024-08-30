from django.shortcuts import render
from django.contrib.auth.models import User
from .models import *
from .serializers import *
from pokerapp import models
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import generics, viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

class TablePagination(PageNumberPagination):
    page_size = 20

class TableListView(generics.ListAPIView):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    pagination_class = TablePagination
    permission_classes = [IsAuthenticated]

    def list(self, request):
        tables = Table.objects.filter(
            players__user__id=request.user.id
        )
        serializer = TableSerializer(tables, many=True, context={'request': request})
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
