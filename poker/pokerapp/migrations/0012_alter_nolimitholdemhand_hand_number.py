# Generated by Django 5.1 on 2025-01-05 01:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pokerapp', '0011_remove_stage10game_game_json_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nolimitholdemhand',
            name='hand_number',
            field=models.BigIntegerField(null=True),
        ),
    ]
