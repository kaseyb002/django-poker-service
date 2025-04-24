from .models import *
from .serializers import *
from .pagination import NumberOnlyPagination
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from . import table_member_fetchers 
from . import responses
from . import table_member_write_helpers
from . import table_default_permissions_helper
import shortuuid
from django.shortcuts import get_object_or_404

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

    member_permissions = table_default_permissions_helper.new_member_permissions(
        table_pk=invite.table.id,
    )

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
    table_member = table_member_fetchers.get_table_member_or_404(
        user_id=request.user.id, 
        table_id=table_pk,
    )
    if not table_member_fetchers.get_table_has_another_admin(
        user_id=request.user.id,
        table_id=table_pk,
    ) and not table_member_fetchers.table_member_count(table_pk) <= 1:
        return responses.no_admins_remaining()
    table_member_write_helpers.remove_table_member(
        table_member=table_member,
        removed_by=None,
    )
    return Response(
        {},
        status=status.HTTP_204_NO_CONTENT,
    )

class TableInviteListView(generics.ListCreateAPIView):
    pagination_class = NumberOnlyPagination
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        invites = TableInvite.objects.filter(
            table__pk=table_pk,
            created_by__id=request.user.id
        )
        page = self.paginate_queryset(invites)
        serializer = TableInviteSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        class Serializer(serializers.Serializer):
            is_one_time_code = serializers.BooleanField(required=False)
        serializer = Serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        is_one_time_code = serializer.data.get('is_one_time_code', True)
        table_pk = self.kwargs.get('table_pk')
        table_member = table_member_fetchers.get_table_member_or_404(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not table_member.permissions.can_send_invite:
            return responses.forbidden("User does not have invite permissions.")
        # if not is_one_time_code, and a non one_time_code code already exists, then just return that one_time_code
        existing_invite = TableInvite.objects.filter(
            table__pk=table_pk,
            created_by__id=request.user.id,
            is_one_time=False
        ).first()
        if existing_invite:
            serializer = TableInviteSerializer(existing_invite, context={'request': request})
            return Response(serializer.data)
        else:
            invite = TableInvite.objects.create(
                created_by=request.user,
                table=table_member.table,
                code=shortuuid.uuid(),
                is_one_time=is_one_time_code,
            )
            serializer = TableInviteSerializer(invite, context={'request': request})
            return Response(serializer.data)

class TableInviteRetrieveView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        invite_pk = self.kwargs.get('invite_pk')
        invite = get_object_or_404(
            TableInvite, 
            pk=invite_pk
        )
        my_table_member = table_member_fetchers.get_table_member_or_404(
            user_id=request.user.id, 
            table_id=invite.table.id,
        )
        if not my_table_member:
            return responses.forbidden("User is not a member of this table.")
        if my_table_member.user != invite.created_by:
            return responses.forbidden("User did not create this invite.")
        if invite.used_by:
            return responses.bad_request("Invite has already been used.")
        invite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)