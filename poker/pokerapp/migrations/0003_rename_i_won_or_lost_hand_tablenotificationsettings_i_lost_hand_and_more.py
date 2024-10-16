# Generated by Django 5.1 on 2024-10-14 14:26

import shortuuid.main
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pokerapp', '0002_alter_tableinvite_code'),
    ]

    operations = [
        migrations.RenameField(
            model_name='tablenotificationsettings',
            old_name='i_won_or_lost_hand',
            new_name='i_lost_hand',
        ),
        migrations.AddField(
            model_name='tablenotificationsettings',
            name='i_won_hand',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='tableinvite',
            name='code',
            field=models.CharField(default=shortuuid.main.ShortUUID.uuid, editable=False, max_length=22, unique=True),
        ),
    ]
