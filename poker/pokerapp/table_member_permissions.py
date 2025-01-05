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
from django.shortcuts import get_object_or_404
from django.http import Http404

class TableMemberPermissionsUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        user_id = self.kwargs.get('user_pk')
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_member.permissions.can_edit_permissions:
            return responses.forbidden("User cannot edit permissions")

        table_member = table_member_fetchers.get_table_member(
            user_id=user_id, 
            table_id=table_pk,
        )
        if not table_member:
            return responses.not_found("Member not found in table")

        permissions_serializer = TablePermissionsSerializer(
            table_member.permissions,
            data=request.data, 
            partial=True,
            context={'request': request},
        )
        permissions_serializer.is_valid(raise_exception=True)
        # check for remaining admin
        if permissions_serializer.validated_data.get('can_edit_permissions') is not None:
            can_edit_permissions = permissions_serializer.validated_data['can_edit_permissions']
            if not can_edit_permissions:
                if not table_member_fetchers.get_table_has_another_admin(
                    user_id=user_id,
                    table_id=table_pk,
                ):
                    return responses.no_admins_remaining()
        permissions_serializer.save()
        serializer = TableMemberSerializer(table_member, context={'request': request})
        return Response(serializer.data)
