from django.shortcuts import render
from .models import *
from .serializers import *
from .pagination import NumberOnlyPagination
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from . import table_member_write_helpers
from . import table_member_fetchers, game_views
from . import responses
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView

class TableRetrieveView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        table = get_object_or_404(
            Table,
            members__user__id=request.user.id,
            members__is_deleted=False,
            pk=pk,
        )
        serializer = TableSerializer(table, context={'request': request})
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        table_pk = self.kwargs.get('pk')
        table = get_object_or_404(
            Table,
            pk=table_pk
        )
        my_table_member = table_member_fetchers.get_table_member(
            user_id=request.user.id, 
            table_id=table.id,
        )
        if not my_table_member.permissions.can_edit_settings:
            return responses.forbidden("User cannot edit settings")
        serializer = TableSerializer(
            table, 
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class TableListView(generics.ListCreateAPIView):
    pagination_class = NumberOnlyPagination
    permission_classes = [IsAuthenticated]

    def list(self, request):
        tables = Table.objects.filter(
            members__user__id=request.user.id,
            members__is_deleted=False
        )
        page = self.paginate_queryset(tables)
        serializer = TableSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        class Serializer(serializers.Serializer):
            name = serializers.CharField(max_length=25)
        serializer = Serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        name = serializer.data['name']
        
        table = Table.objects.create(
            name=name,
            created_by=request.user,
        )

        TableSettings.objects.create(
            table=table
        )

        admin_permissions = TablePermissions.objects.create(
            can_edit_permissions = True,
            can_edit_settings = True,
            can_send_invite = True,
            can_remove_member = True,
            can_sit_player_out = True,
            can_force_move = True,
            can_play = True,
            can_chat = True,
            can_adjust_chips=True,
            can_deal=True,
        )

        table_member_write_helpers.join_table(
            user=request.user, 
            table_id=table.id,
            permissions=admin_permissions,
        )

        game_views.create_game(
            table_id=table.id, 
            game_type=GameType.NO_LIMIT_HOLD_EM
        )

        chat_room = ChatRoom.objects.create()
        TableChatRoom.objects.create(
            room=chat_room,
            table=table,
        )

        serializer = TableSerializer(table, context={'request': request})
        return Response(serializer.data)

class StaticBackgroundsView(APIView):
    def get(self, request):
        data = [
            {
                "id": "alps",
                "title": "Bavarian Alps",
                "image_url": "https://res.cloudinary.com/eggler/image/upload/v1744984762/alps_uhv26s.jpg"
            },
            {
                "id": "campout",
                "title": "Campout",
                "image_url": "https://res.cloudinary.com/eggler/image/upload/v1744984759/campout_e33o3r.jpg"
            },
            {
                "id": "classroom",
                "title": "Classroom",
                "image_url": "https://res.cloudinary.com/eggler/image/upload/v1744984760/classroom_za0fqt.jpg"
            },
            {
                "id": "dojo",
                "title": "Dojo",
                "image_url": "https://res.cloudinary.com/eggler/image/upload/v1744984758/dojo_qymwqh.jpg"
            },
            {
                "id": "garden",
                "title": "Garden",
                "image_url": "https://res.cloudinary.com/eggler/image/upload/v1744984763/garden_kynbap.jpg"
            },
            {
                "id": "gym",
                "title": "Gym",
                "image_url": "https://res.cloudinary.com/eggler/image/upload/v1744984764/basketball_gym_ypirkr.jpg"
            },
            {
                "id": "coffeeShop",
                "title": "Coffee Shop",
                "image_url": "https://res.cloudinary.com/eggler/image/upload/v1744984755/coffee_shop_y2pecz.jpg"
            },
            {
                "id": "beach",
                "title": "Kailua-Kona",
                "image_url": "https://res.cloudinary.com/eggler/image/upload/v1744984757/beach_eoiyat.jpg"
            },
            {
                "id": "garage",
                "title": "Garage",
                "image_url": "https://res.cloudinary.com/eggler/image/upload/v1744984770/garage_gkjg7y.jpg"
            },
            {
                "id": "kitchen",
                "title": "Kitchen",
                "image_url": "https://res.cloudinary.com/eggler/image/upload/v1744984761/kitchen_zo8qnf.jpg"
            },
            {
                "id": "richHouse",
                "title": "Fancy House",
                "image_url": "https://res.cloudinary.com/eggler/image/upload/v1744984776/richGuysHouse_dpntvv.jpg"
            },
            {
                "id": "newYorkCity",
                "title": "New York City",
                "image_url": "https://res.cloudinary.com/eggler/image/upload/v1744984774/newYorkCity_p2mhqa.jpg"
            },
            {
                "id": "mexico",
                "title": "Mexico",
                "image_url": "https://res.cloudinary.com/eggler/image/upload/v1744984772/mexico_klmlly.jpg"
            },
            {
                "id": "singapore",
                "title": "Singapore",
                "image_url": "https://res.cloudinary.com/eggler/image/upload/v1744984778/singapore_ewbk07.jpg"
            },
            {
                "id": "dubai",
                "title": "Dubai",
                "image_url": "https://res.cloudinary.com/eggler/image/upload/v1744984768/dubai_io3hyf.jpg"
            },
            {
                "id": "paris",
                "title": "Paris",
                "image_url": "https://res.cloudinary.com/eggler/image/upload/v1744984775/paris_evseyh.jpg"
            },
            {
                "id": "london",
                "title": "London",
                "image_url": "https://res.cloudinary.com/eggler/image/upload/v1744984771/london_fpvez1.jpg"
            },
            {
                "id": "tokyo",
                "title": "Tokyo",
                "image_url": "https://res.cloudinary.com/eggler/image/upload/v1744984779/tokyo_szsv6c.jpg"
            },
            {
                "id": "vegas",
                "title": "Vegas",
                "image_url": "https://res.cloudinary.com/eggler/image/upload/v1744984780/vegas_mslhfk.jpg"
            },
            {
                "id": "basement",
                "title": "Scott's Basement",
                "image_url": "https://res.cloudinary.com/eggler/image/upload/v1744984755/basement_qfpyeg.jpg"
            }
        ]
        return Response(data)