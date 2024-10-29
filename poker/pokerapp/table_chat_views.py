from .models import *
from .serializers import *
from .pagination import NumberOnlyPagination
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from . import table_member_fetchers
from . import responses
from . import push_notifications_fetchers, push_notifications, push_categories
from django.shortcuts import get_object_or_404

class TableChatMetadataRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('table_pk')
        table = get_object_or_404(
            Table, 
            pk=table_pk,
        )
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=table_pk,
        )
        if not my_table_member:
            return responses.unauthorized("User is not a member of this table.")
        table_chat_room = get_object_or_404(
            TableChatRoom,
            table__id=table_pk,
        )
        response = {
            "room": table_chat_room.room.id,
            "table": table.id,
            "table_name": table.name,
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
        table_chat_room = get_object_or_404(
            TableChatRoom,
            table__pk=table_pk,
        )
        chat_messages = ChatMessage.objects.filter(
            room__pk=table_chat_room.room.id
        ).exclude(
            is_deleted=True
        ).prefetch_related(
            'user', 
            'user__account',
        )
        page = self.paginate_queryset(chat_messages)
        serializer = ChatMessageSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

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
        table_chat_room = get_object_or_404(
            TableChatRoom,
            table__pk=table_pk,
        )
        chat_message = ChatMessage.objects.create(
            text=text,
            user=request.user,
            room=table_chat_room.room,
        )
        subscribed_users = push_notifications_fetchers.users_subscribed_to_chat_message(
            table_id=table_pk,
            author_user_id=my_table_member.user.id,
        )
        push_notifications.send_push_to_users(
            users=subscribed_users,
            text="Message from " + chat_message.text,
            title=my_table_member.user.username,
            subtitle=my_table_member.table.name,
            category=push_categories.NEW_CHAT_MESSAGE,
            extra_data={
                "table_id": table_pk,
                "message_id": str(chat_message.id),
            },
            thread_id=push_categories.chat_room_id(table_pk),
        )
        serializer = ChatMessageSerializer(chat_message, context={'request': request})
        return Response(serializer.data)