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

class TableMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'table_id', 'table_name')

    def table_id(self, obj):
        return obj.table.id

    def table_name(self, obj):
        return obj.table.name

    def username(self, obj):
        return obj.user.username

admin.site.register(TableMember, TableMemberAdmin)

class TablePermissionsAdmin(admin.ModelAdmin):
    list_display = ('id', 'can_edit_permissions')

admin.site.register(TablePermissions, TablePermissionsAdmin)

class TableInviteAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_by_username', 'table_id', 'table_name','used_by')

    def table_id(self, obj):
        return obj.table.id

    def table_name(self, obj):
        return obj.table.name

    def created_by_username(self, obj):
        return obj.created_by.username

admin.site.register(TableInvite, TableInviteAdmin)

class NoLimitHoldEmGameAdmin(admin.ModelAdmin):
    list_display = ('id', 'table_id', 'table_name','big_blind',)

    def table_id(self, obj):
        return obj.table.id

    def table_name(self, obj):
        return obj.table.name

admin.site.register(NoLimitHoldEmGame, NoLimitHoldEmGameAdmin)

class NoLimitHoldEmGamePlayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'game', 'user_id')

    def user_id(self, obj):
        return obj.user_id()

admin.site.register(NoLimitHoldEmGamePlayer, NoLimitHoldEmGamePlayerAdmin)

class NoLimitHoldEmHandAdmin(admin.ModelAdmin):
    list_display = ('id',)
    
admin.site.register(NoLimitHoldEmHand, NoLimitHoldEmHandAdmin)

class NoLimitHoldEmChipAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('id',)
    
admin.site.register(NoLimitHoldEmChipAdjustment, NoLimitHoldEmChipAdjustmentAdmin)

class Stage10GameAdmin(admin.ModelAdmin):
    list_display = ('id', 'table_id', 'table_name', 'created')

    def table_id(self, obj):
        return obj.table.id

    def table_name(self, obj):
        return obj.table.name

admin.site.register(Stage10Game, Stage10GameAdmin)

class Stage10GamePlayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'game', 'user_id')

    def user_id(self, obj):
        return obj.user_id()

admin.site.register(Stage10GamePlayer, Stage10GamePlayerAdmin)

class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id',)

admin.site.register(ChatRoom, ChatRoomAdmin)

class TableChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id',)

admin.site.register(TableChatRoom, TableChatRoomAdmin)

class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id','text')

admin.site.register(ChatMessage, ChatMessageAdmin)

class TableNotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ('id',)

admin.site.register(TableNotificationSettings, TableNotificationSettingsAdmin)

class PushNotificationRegistrationAdmin(admin.ModelAdmin):
    list_display = ('id',)

admin.site.register(PushNotificationRegistration, PushNotificationRegistrationAdmin)

class CurrentGameAdmin(admin.ModelAdmin):
    list_display = ('id',)

admin.site.register(CurrentGame, CurrentGameAdmin)