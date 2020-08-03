# Generated by Django 3.0.9 on 2020-08-03 15:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('test_storage', '0025_auto_20200803_1813'),
    ]

    operations = [
        migrations.AddField(
            model_name='test',
            name='state',
            field=models.CharField(choices=[('J', 'Running JMeter master'), ('C', 'Completed')], default='J', max_length=1),
        ),
        migrations.AlterField(
            model_name='jmeterrequest',
            name='source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='test_storage.JmeterRawLogsFile'),
        ),
    ]
