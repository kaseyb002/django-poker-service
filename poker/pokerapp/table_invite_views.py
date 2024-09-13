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

@api_view(['POST'])
def join_table(request):
    """
    Joins table using an invite code
    """
    class Serializer(serializers.Serializer):
        code = serializers.CharField()
    serializer = Serializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    code = serializer.data['code']

    invite = TableInvite.objects.get(
        code=code
    )
    if invite.used_by:
        return responses.bad_request("Invite code has already been used.")

    # set permissions
    member_permissions = TablePermissions()
    member_permissions.save()

    # join table
    table_member = table_member_write_helpers.join_table(
        user=request.user, 
        table_id=invite.table.id,
        permissions=member_permissions,
    )

    if invite.is_one_time:
        invite.used_by = request.user
        invite.save()

    serializer = TableMemberSerializer(table_member, context={'request': request})
    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED,
    )

@api_view(['DELETE'])
def leave_table(request, *args, **kwargs):
    """
    Leaves the table
    """
    table_pk = kwargs.get('table_pk')
    table_member = table_member_fetchers.get_table_member(
        user_id=request.user.id, 
        table_id=table_pk,
    )
    if not table_member_fetchers.get_table_has_another_admin(
        user_id=request.user.id,
        table_id=table_pk,
    ):
        return responses.no_admins_remaining()
    table_member.delete()
    return Response(
        serializer.data,
        status=status.HTTP_204_NO_CONTENT,
    )

class TableInviteListView(generics.ListCreateAPIView):
    pagination_class = NumberOnlyPagination
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        invites = TableInvite.objects.filter(
            table__pk=table_pk
        ).filter(
            created_by__id=request.user.id
        )

        # Apply pagination
        page = self.paginate_queryset(invites)
        if page is not None:
            serializer = TableInviteSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        # If no pagination is applied, return all data
        serializer = TableInviteSerializer(tables, many=True, context={'request': request})
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')

        table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=table_pk,
        )

        if not table_member.permissions.can_send_invite:
            return responses.unauthorized("User does not have invite permissions.")

        #create invite
        invite = TableInvite(
            created_by=request.user,
            table=table_member.table,
        )
        invite.save()
            
        serializer = TableInviteSerializer(invite, context={'request': request})
        return Response(serializer.data)
