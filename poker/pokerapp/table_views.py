from django.shortcuts import render
from django.contrib.auth.models import User
from .models import *
from .serializers import *
from pokerapp import models
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import generics, viewsets, status
from rest_framework.permissions import IsAuthenticated

@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def create_table(request):
    class Serializer(serializers.Serializer):
        name = serializers.CharField()
        description = serializers.CharField(required=False)
        is_public = serializers.BooleanField(default=False)
    serializer = Serializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    name = serializer.data['name']
    
    table = Table(name=name)
    table.save()
    # create settings
    table_settings = TableSettings(table=table)
    table_settings.save()

    serializer = TableSerializer(table, context={'request': request})
    return Response(serializer.data)
