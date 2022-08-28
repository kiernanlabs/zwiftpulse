# Generated by Django 4.1 on 2022-08-27 00:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('racereport', '0006_remove_raceresult_gap_to_first_ms'),
    ]

    operations = [
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.AlterField(
            model_name='raceresult',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='racereport.team'),
        ),
    ]