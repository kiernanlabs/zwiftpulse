# Generated by Django 4.1 on 2022-09-20 16:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('racereport', '0009_alter_scrapereport_completed_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Narrative',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=200)),
                ('arena', models.CharField(max_length=200)),
                ('action', models.IntegerField()),
                ('outcome', models.IntegerField()),
                ('context', models.IntegerField()),
                ('impact_score', models.IntegerField(default=0)),
                ('surprise_score', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='racereport.team')),
                ('why', models.ManyToManyField(to='racereport.raceresult')),
            ],
        ),
    ]
