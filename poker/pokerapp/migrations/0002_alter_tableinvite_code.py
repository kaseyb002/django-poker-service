# Generated by Django 5.1 on 2024-11-22 02:34

import shortuuid.main
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pokerapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tableinvite',
            name='code',
            field=models.CharField(default=shortuuid.main.ShortUUID.uuid, editable=False, max_length=22, unique=True),
        ),
    ]
