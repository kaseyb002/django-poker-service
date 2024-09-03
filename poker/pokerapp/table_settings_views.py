from django.shortcuts import render
from django.contrib.auth.models import User
from .models import *
from .serializers import *
from pokerapp import models
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import generics, viewsets, status
from rest_framework.permissions import IsAuthenticated

class TableSettingsRetrieveView(generics.RetrieveAPIView):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        table_settings = TableSettings.objects.filter(
            table__players__user__id=request.user.id
        ).get(
            table__pk=pk
        )
        serializer = TableSettingsSerializer(table_settings, context={'request': request})
        return Response(serializer.data)
