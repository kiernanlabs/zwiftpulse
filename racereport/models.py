from statistics import mode
from unicodedata import category
from django.db import models

class Race(models.Model):
    event_time = models.DateTimeField()
    race_name = models.CharField(max_length=200)
    distance_km = models.FloatField()
    course = models.CharField(max_length=200)

class RaceCat(models.Model):
    race = models.ForeignKey(Race, on_delete=models.CASCADE)
    category = models.CharField(max_length=1)

class RaceResult(models.Model):
    race_cat = models.ForeignKey(RaceCat, on_delete=models.CASCADE)
    racer_name = models.CharField(max_length=200)
    team = models.CharField(max_length=200)
    position = models.IntegerField()
    time_ms = models.IntegerField()
    gap_to_first_ms = models.IntegerField()
    zp_rank_before = models.FloatField()
    zp_rank_event = models.FloatField()
