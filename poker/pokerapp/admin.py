from django.contrib import admin
from django.contrib.auth.models import User
from .models import *

class AccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'username',)

    def username(self, obj):
        return obj.user.username

admin.site.register(Account, AccountAdmin)

class TableAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created', 'image_url')

admin.site.register(Table, TableAdmin)

class TableSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'table_id', 'table_name')

    def table_id(self, obj):
        return obj.table.id

    def table_name(self, obj):
        return obj.table.name

admin.site.register(TableSettings, TableSettingsAdmin)

class TablePlayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'table_id', 'table_name')

    def table_id(self, obj):
        return obj.table.id

    def table_name(self, obj):
        return obj.table.name

    def username(self, obj):
        return obj.user.username

admin.site.register(TablePlayer, TablePlayerAdmin)

class TablePermissionsAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'table_id', 'table_name', 'can_edit_permissions')

    def table_id(self, obj):
        return obj.table_player.table.id

    def table_name(self, obj):
        return obj.table_player.table.name

    def username(self, obj):
        return obj.table_player.user.username

admin.site.register(TablePermissions, TablePermissionsAdmin)
