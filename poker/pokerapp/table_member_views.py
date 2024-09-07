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

class MyTableMemberRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        serializer = TableMemberSerializer(my_table_member, context={'request': request})
        return Response(serializer.data)

class TableMemberRetrieveView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        user_pk = self.kwargs.get('user_pk')
        table_member = table_member_fetchers.get_table_member(
            user_id=user_pk, 
            table_id=table_pk,
        )
        serializer = TableMemberSerializer(table_member, context={'request': request})
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        user_pk = self.kwargs.get('user_pk')
        table_member = table_member_fetchers.get_table_member(
            user_id=user_pk, 
            table_id=table_pk,
        )
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_member.permissions.can_remove_member:
            return responses.unauthorized("User cannot remove members")
        if not table_member_fetchers.get_table_has_another_admin(
            user_id=user_pk,
            table_id=table_pk,
        ):
            return responses.no_admins_remaining()
        table_member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class TableMemberListView(generics.ListAPIView):
    pagination_class = NumberOnlyPagination
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_member:
            return responses.user_not_in_table()
        table_members = TableMember.objects.filter(
            table__id=table_pk
        ).prefetch_related('permissions', 'user', 'user__account')

        # Apply pagination
        page = self.paginate_queryset(table_members)
        if page is not None:
            serializer = TableMemberSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        # If no pagination is applied, return all data
        serializer = TableMemberSerializer(tables, many=True, context={'request': request})
        return Response(serializer.data)

class SittingTableMemberListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_member:
            return responses.user_not_in_table()
        sitting_table_members = TableMember.objects.filter(
            table__id=table_pk
        ).filter(
            is_sitting=True
        ).prefetch_related('permissions', 'user', 'user__account')

        serializer = TableMemberSerializer(sitting_table_members, many=True, context={'request': request})
        return Response(serializer.data)
