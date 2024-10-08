# Generated by Django 5.1 on 2024-10-02 00:34

import shortuuid.main
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pokerapp', '0004_chatroom_alter_tableinvite_code_chatmessage_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='chatmessage',
            options={'ordering': ['-created']},
        ),
        migrations.AddField(
            model_name='nolimitholdemgameplayer',
            name='is_auto_move_on',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='tableinvite',
            name='code',
            field=models.CharField(default=shortuuid.main.ShortUUID.uuid, editable=False, max_length=22, unique=True),
        ),
    ]
