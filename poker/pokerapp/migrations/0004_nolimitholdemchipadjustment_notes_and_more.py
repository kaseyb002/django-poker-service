# Generated by Django 5.1 on 2024-12-14 02:33

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pokerapp', '0003_alter_tableinvite_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='nolimitholdemchipadjustment',
            name='notes',
            field=models.CharField(blank=True, max_length=1024),
        ),
        migrations.AddField(
            model_name='tableinvite',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]