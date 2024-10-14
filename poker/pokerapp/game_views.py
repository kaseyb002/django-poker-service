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
from . import table_member_write_helpers
from django.db.models import Subquery, OuterRef
from django.shortcuts import get_object_or_404

class CurrentGameRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_member:
            return responses.unauthorized("User is not a member of this table.")
        current_game = get_object_or_404(
            CurrentGame,
            table__id=table_pk,
        )
        serializer = CurrentGameSerializer(current_game, context={'request': request})
        return Response(serializer.data)

class CurrentGameListView(generics.ListAPIView):
    pagination_class = NumberOnlyPagination
    permission_classes = [IsAuthenticated]
    
    def list(self, request, *args, **kwargs):

        # Subquery to get the latest hand per table
        latest_hand_per_table = NoLimitHoldEmHand.objects.filter(
            game__table=OuterRef('game__table'),
            game__table__members__is_deleted=False,
            game__table__members__user__id=request.user.id,
        ).order_by('-updated').values('id')[:1]

        hands = NoLimitHoldEmHand.objects.filter(
            id__in=Subquery(latest_hand_per_table)
        ).prefetch_related(
            'game',
            'game__table',
        )
        # hands = NoLimitHoldEmHand.objects.filter(
        #     game__table__members__is_deleted=False,
        #     game__table__members__user__id=request.user.id,
        # ).order_by(
        #     'game__table',  # This must be included in order_by for distinct to work
        #     '-updated',
        # ).distinct(
        #     'game__table',
        # ).prefetch_related(
        #     'current_game',
        #     'current_game__no_limit_hold_em_game',
        #     'current_game__table',
        # )

        # for other games, you'd need to similarly fetch for the current 
        # game state, and then 

        class GameListSerializer(serializers.ModelSerializer):
            table = TableSerializer(source='game.table', read_only=True)
            game = NoLimitHoldEmGameSerializer(read_only=True)

            class Meta:
                model = NoLimitHoldEmHand
                fields = [
                    'id', 
                    'game',
                    'created', 
                    'updated', 
                    'hand_json', 
                    'completed',
                    'players',
                    'table', 
                ]

        page = self.paginate_queryset(hands)
        serializer = GameListSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)