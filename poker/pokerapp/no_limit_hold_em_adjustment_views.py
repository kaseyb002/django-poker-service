from django.shortcuts import render
from .models import *
from .serializers import *
from .pagination import NumberOnlyPagination
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import generics
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

        my_table_member = table_member_fetchers.get_table_member_or_404(
            user_id=request.user.id, 
            table_id=game.table.id,
        )
        if not my_table_member:
            return responses.user_not_in_table()

        adjustments = NoLimitHoldEmChipAdjustment.objects.filter(
            player__game__pk=game_pk
        )
        page = self.paginate_queryset(adjustments)
        serializer = NoLimitHoldEmChipAdjustmentSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)