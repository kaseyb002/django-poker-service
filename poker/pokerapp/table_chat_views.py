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

class TableChatMetadataRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        table = Table.objects.get(
            pk=table_pk
        )
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_member:
            return responses.unauthorized("User is not a member of this table.")
        table_chat_room = TableChatRoom.objects.get(
            table__id=table_pk
        )
        response = {
            "room": table_chat_room.room.id,
            "table": table.id,
            "table_name": table.name
        }
        return Response(response)

class TableChatMessageListView(generics.ListCreateAPIView):
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
        table_chat_room = TableChatRoom.objects.get(
            table__pk=table_pk
        )
        chat_messages = ChatMessage.objects.filter(
            room__pk=table_chat_room.room.id
        ).exclude(
            is_deleted=True
        ).prefetch_related('user', 'user__account')

        # Apply pagination
        page = self.paginate_queryset(chat_messages)
        if page is not None:
            serializer = ChatMessageSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        # If no pagination is applied, return all data
        serializer = ChatMessageSerializer(chat_messages, many=True, context={'request': request})
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        class Serializer(serializers.Serializer):
            text = serializers.CharField(max_length=1024)
        serializer = Serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        text = serializer.data['text']
        table_pk = self.kwargs.get('table_pk')

        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_member:
            return responses.user_not_in_table()
        if not my_table_member.permissions.can_chat:
            return responses.unauthorized("User is not permitted to chat.")
        table_chat_room = TableChatRoom.objects.get(
            table__pk=table_pk
        )
        chat_message = ChatMessage(
            text=text,
            user=request.user,
            room=table_chat_room.room
        )
        chat_message.save()
        serializer = ChatMessageSerializer(chat_message, context={'request': request})
        return Response(serializer.data)
