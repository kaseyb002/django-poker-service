# Generated by Django 5.1 on 2024-09-14 22:54

import django.db.models.deletion
import shortuuid.main
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NoLimitHoldEmGame',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('auto_deal', models.BooleanField(default=True)),
                ('big_blind', models.DecimalField(decimal_places=2, default=0.1, max_digits=10)),
                ('small_blind', models.DecimalField(decimal_places=2, default=0.05, max_digits=10)),
                ('starting_chip_count', models.DecimalField(decimal_places=2, default=10.0, max_digits=10)),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='TablePermissions',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('can_edit_permissions', models.BooleanField(default=False)),
                ('can_edit_settings', models.BooleanField(default=False)),
                ('can_send_invite', models.BooleanField(default=True)),
                ('can_remove_member', models.BooleanField(default=False)),
                ('can_force_move', models.BooleanField(default=False)),
                ('can_play', models.BooleanField(default=True)),
                ('can_sit_player_out', models.BooleanField(default=False)),
                ('can_chat', models.BooleanField(default=True)),
                ('can_adjust_chips', models.BooleanField(default=False)),
                ('can_deal', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('image_url', models.URLField(blank=True, null=True)),
                ('bio', models.CharField(blank=True, max_length=1024)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='NoLimitHoldEmGamePlayer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('chip_count', models.DecimalField(decimal_places=2, default=10.0, max_digits=10)),
                ('is_sitting', models.BooleanField(default=False)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='players', to='pokerapp.nolimitholdemgame')),
            ],
        ),
        migrations.CreateModel(
            name='NoLimitHoldEmHand',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('completed', models.DateTimeField(null=True)),
                ('hand_json', models.JSONField()),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hands', to='pokerapp.nolimitholdemgame')),
                ('players', models.ManyToManyField(to='pokerapp.nolimitholdemgameplayer')),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='Table',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=25)),
                ('image_url', models.URLField(blank=True, null=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tables', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['created'],
            },
        ),
        migrations.AddField(
            model_name='nolimitholdemgame',
            name='table',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='no_limit_hold_em_games', to='pokerapp.table'),
        ),
        migrations.CreateModel(
            name='CurrentGame',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('selected_game', models.CharField(choices=[('NO_LIMIT_HOLD_EM', 'No Limit Hold Em')], default='NO_LIMIT_HOLD_EM', max_length=20)),
                ('no_limit_hold_em_game', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='pokerapp.nolimitholdemgame')),
                ('table', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='current_game', to='pokerapp.table')),
            ],
        ),
        migrations.CreateModel(
            name='TableInvite',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(default=shortuuid.main.ShortUUID.uuid, editable=False, max_length=22, unique=True)),
                ('is_one_time', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_invites', to=settings.AUTH_USER_MODEL)),
                ('table', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invites', to='pokerapp.table')),
                ('used_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='used_invites', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TableMember',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('table', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='pokerapp.table')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to=settings.AUTH_USER_MODEL)),
                ('permissions', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='pokerapp.tablepermissions')),
            ],
            options={
                'ordering': ['created'],
            },
        ),
        migrations.AddField(
            model_name='nolimitholdemgameplayer',
            name='table_member',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='no_limit_hold_em_game_players', to='pokerapp.tablemember'),
        ),
        migrations.CreateModel(
            name='NoLimitHoldEmChipAdjusment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('amount', models.DecimalField(decimal_places=2, default=10.0, max_digits=10)),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chip_adjustments', to='pokerapp.nolimitholdemgameplayer')),
                ('adjusted_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chip_adjustments', to='pokerapp.tablemember')),
            ],
        ),
        migrations.CreateModel(
            name='TableSettings',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('turn_time_limit', models.DurationField(blank=True, null=True)),
                ('table', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='pokerapp.table')),
            ],
        ),
    ]
