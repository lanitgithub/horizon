# Generated by Django 2.2.13 on 2020-06-19 10:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('test_storage', '0014_auto_20200619_1450'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='test',
            name='errors_pct',
        ),
        migrations.RemoveField(
            model_name='test',
            name='response_time_avg',
        ),
        migrations.RemoveField(
            model_name='test',
            name='rps_avg',
        ),
        migrations.RemoveField(
            model_name='test',
            name='successful',
        ),
    ]
