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
from . import table_member_fetchers 
from . import responses

class NoLimitHoldChipAdjustmentListView(generics.ListAPIView):
    page_size = 100
    pagination_class = NumberOnlyPagination
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        game_pk = self.kwargs.get('game_pk')
        game = NoLimitHoldEmGame.objects.get(
            pk=game_pk
        )

        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=game.table.id,
        )
        if not my_table_member:
            return responses.user_not_in_table()

        adjustments = NoLimitHoldEmChipAdjusment.objects.filter(
            player__game__pk=game_pk
        )

        # Apply pagination
        page = self.paginate_queryset(adjustments)
        if page is not None:
            serializer = NoLimitHoldEmChipAdjustmentSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        # If no pagination is applied, return all data
        serializer = NoLimitHoldEmChipAdjustmentSerializer(adjustments, many=True, context={'request': request})
        return Response(serializer.data)
