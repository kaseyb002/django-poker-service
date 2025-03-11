from django.shortcuts import render
from .models import *
from .serializers import *
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404

def get_or_make_table_default_permissions(table_pk):
    table = get_object_or_404(Table, pk=table_pk)
    if not hasattr(table, 'default_permissions'):
        permissions = TablePermissions.objects.create()
        table.default_permissions = DefaultTablePermissions.objects.create(
            table=table,
            permissions=permissions,
        )
        table.save()
    return table.default_permissions

def new_member_permissions(table_pk):
    permissions = get_or_make_table_default_permissions(table_pk).permissions
    permissions.pk = None
    permissions.save()
    return permissions