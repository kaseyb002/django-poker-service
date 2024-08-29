from rest_framework.pagination import PageNumberPagination
from rest_framework import generics
from .models import Table, TableSettings
from .serializers import TableSerializer, TableSettingsSerializer

class TablePagination(PageNumberPagination):
    page_size = 20

class TableListView(generics.ListAPIView):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    pagination_class = TablePagination

class TableSettingsView(generics.RetrieveAPIView):
    queryset = TableSettings.objects.all()
    serializer_class = TableSettingsSerializer
