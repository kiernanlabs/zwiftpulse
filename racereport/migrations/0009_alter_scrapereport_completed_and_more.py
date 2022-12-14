# Generated by Django 4.1 on 2022-09-11 15:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('racereport', '0008_scrapereport'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scrapereport',
            name='completed',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='scrapereport',
            name='count_successful',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='scrapereport',
            name='scrape_end',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]
