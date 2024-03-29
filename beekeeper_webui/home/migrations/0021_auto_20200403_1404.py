# Generated by Django 3.0.1 on 2020-04-03 14:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0020_auto_20200403_0032'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ethernetcable',
            name='source',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='source', to='home.EthernetPorts'),
        ),
        migrations.AlterField(
            model_name='ethernetcable',
            name='target',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='target', to='home.EthernetPorts'),
        ),
    ]
