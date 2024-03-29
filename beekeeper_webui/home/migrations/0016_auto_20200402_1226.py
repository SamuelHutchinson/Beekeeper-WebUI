# Generated by Django 3.0.1 on 2020-04-02 12:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0015_ethernetports_port_no'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ethernetports',
            name='connected_to',
        ),
        migrations.RemoveField(
            model_name='ethernetports',
            name='port_no',
        ),
        migrations.AddField(
            model_name='ethernetports',
            name='mac_address',
            field=models.CharField(default='02:00:00:0a:01:02', max_length=48),
        ),
        migrations.CreateModel(
            name='EthernetCable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='bridge_name', max_length=100, unique=True)),
                ('cell_id', models.IntegerField(default='0')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='source', to='home.EthernetPorts')),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='target', to='home.EthernetPorts')),
            ],
        ),
    ]
