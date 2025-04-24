from .models import *
from .serializers import *
from .pagination import NumberOnlyPagination
from pokerapp import models
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import generics, viewsets, status
from rest_framework.permissions import IsAuthenticated
from . import table_member_fetchers, table_member_write_helpers
from . import responses
from django.shortcuts import get_object_or_404
from django.http import Http404

class MyTableMemberRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        my_table_member = table_member_fetchers.get_table_member_or_404(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_member:
            raise Http404("My table member not found.")
        serializer = TableMemberSerializer(my_table_member, context={'request': request})
        return Response(serializer.data)

class TableMemberRetrieveView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        user_pk = self.kwargs.get('user_pk')
        table_member = table_member_fetchers.get_table_member_or_404(
            user_id=user_pk, 
            table_id=table_pk,
        )
        if not table_member:
            raise Http404("Table member not found.")
        serializer = TableMemberSerializer(table_member, context={'request': request})
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        user_pk = self.kwargs.get('user_pk')
        table_member = table_member_fetchers.get_table_member_or_404(
            user_id=user_pk, 
            table_id=table_pk,
        )
        if not table_member:
            raise Http404("Table member not found.")
        my_table_member = table_member_fetchers.get_table_member_or_404(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_member.permissions.can_remove_member:
            return responses.forbidden("User cannot remove members")
        if not table_member_fetchers.get_table_has_another_admin(
            user_id=user_pk,
            table_id=table_pk,
        ):
            return responses.no_admins_remaining()
        table_member_write_helpers.remove_table_member(
            table_member=table_member, 
            removed_by=request.user
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class TableMemberListView(generics.ListAPIView):
    pagination_class = NumberOnlyPagination
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        my_table_member = table_member_fetchers.get_table_member_or_404(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_member:
            return responses.user_not_in_table()
        table_members = TableMember.objects.filter(
            table__id=table_pk
        ).exclude(
            is_deleted=True
        ).prefetch_related(
            'permissions', 
            'user', 
            'user__account',
        )
        page = self.paginate_queryset(table_members)
        serializer = TableMemberSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)