import uuid
from django.contrib.auth.models import User
from django.db import models

class Account(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image_url = models.URLField(null=True, blank=True)
    bio = models.CharField(max_length=1024, blank=True)

class Table(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('auth.User', related_name='created_tables', on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=25, blank=False)
    image_url = models.URLField(null=True, blank=True)

    class Meta:
        ordering = ['created']

class TableSettings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    table = models.OneToOneField(
        Table,
        on_delete=models.CASCADE,
    )
    turn_time_limit = models.DurationField(null=True, blank=True)

class TablePlayer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('auth.User', related_name='memberships', on_delete=models.CASCADE)
    table = models.ForeignKey(Table, related_name='players', on_delete=models.CASCADE)
    is_sitting = models.BooleanField(default=False)

    def username(self):
        return self.user.username

    def first_name(self):
        return self.user.first_name

    def last_name(self):
        return self.user.last_name

    def image_url(self):
        return self.user.account.image_url

class TablePermissions(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    table_player = models.OneToOneField(
        TablePlayer,
        on_delete=models.CASCADE,
    )
    can_edit_permissions = models.BooleanField(default=False)

class NoLimitHoldEmGameSettings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auto_deal = models.BooleanField(default=True)
    big_blind = models.DecimalField(max_digits=10, decimal_places=2, default=0.10)
    small_blind = models.DecimalField(max_digits=10, decimal_places=2, default=0.05)
