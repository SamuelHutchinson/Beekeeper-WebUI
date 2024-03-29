# Generated by Django 3.0.1 on 2020-01-25 14:24

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DiskImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('devicetype', models.CharField(choices=[('router', 'ROUTER'), ('pc', 'PC'), ('switch', 'SWITCH'), ('mlswitch', 'MULTI-LAYER SWITCH')], default='pc', max_length=8)),
                ('disk_image', models.FileField(upload_to='disk_images/')),
            ],
        ),
    ]
