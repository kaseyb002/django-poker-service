from django.shortcuts import render
from .models import *
from .serializers import *
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from . import table_member_fetchers 
from . import table_default_permissions_helper
from . import responses
from django.shortcuts import get_object_or_404

class DefaultTablePermissionsRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_member.permissions.can_edit_permissions:
            return responses.forbidden("User cannot edit permissions")
        default_permissions = table_default_permissions_helper.get_or_make_table_default_permissions(
            table_pk=table_pk,
        )
        serializer = DefaultTablePermissionsSerializer(
            default_permissions,
            context={'request': request},
        )
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_member.permissions.can_edit_permissions:
            return responses.forbidden("User cannot edit permissions")
        default_permissions = table_default_permissions_helper.get_or_make_table_default_permissions(
            table_pk=table_pk,
        )
        serializer = TablePermissionsSerializer(
            default_permissions.permissions,
            data=request.data, 
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        default_permissions = table_default_permissions_helper.get_or_make_table_default_permissions(
            table_pk=table_pk,
        )
        serializer = DefaultTablePermissionsSerializer(
            default_permissions,
            context={'request': request},
        )
        return Response(serializer.data)