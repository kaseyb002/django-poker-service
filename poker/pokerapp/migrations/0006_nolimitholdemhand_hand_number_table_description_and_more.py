# Generated by Django 5.1 on 2024-12-23 02:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pokerapp', '0005_alter_tableinvite_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='nolimitholdemhand',
            name='hand_number',
            field=models.BigIntegerField(null=True, unique=True),
        ),
        migrations.AddField(
            model_name='table',
            name='description',
            field=models.CharField(blank=True, max_length=2000),
        ),
        migrations.AddField(
            model_name='table',
            name='tagline',
            field=models.CharField(blank=True, max_length=40),
        ),
    ]