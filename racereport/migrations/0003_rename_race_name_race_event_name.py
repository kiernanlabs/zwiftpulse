# Generated by Django 4.1 on 2022-08-21 13:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('racereport', '0002_race_event_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='race',
            old_name='race_name',
            new_name='event_name',
        ),
    ]
