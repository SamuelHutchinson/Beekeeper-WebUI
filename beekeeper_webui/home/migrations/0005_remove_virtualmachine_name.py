# Generated by Django 3.0.1 on 2020-02-06 12:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0004_auto_20200203_1618'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='virtualmachine',
            name='name',
        ),
    ]