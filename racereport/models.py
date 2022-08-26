from django.db import models
from django.db.models import Count, Min


class Race(models.Model):
    event_id = models.IntegerField()
    event_datetime = models.DateTimeField()
    event_name = models.CharField(max_length=200)
    # distance_km = models.FloatField()
    # course = models.CharField(max_length=200)

    def __str__(self):
        return self.event_name

class RaceCatManager(models.Manager):
    def top5races(self, start_time):
        racecats = RaceCat.objects.annotate(race_time=Min('race__event_datetime'), racer_count=Count('raceresult')).filter(race_time__gte=start_time).order_by('racer_count')
        return racecats[0:5]
    
    def top5races_cat(self, start_time, category):
        racecats = RaceCat.objects.annotate(race_time=Min('race__event_datetime'), racer_count=Count('raceresult')).filter(race_time__gte=start_time, category=category).order_by('racer_count')
        return racecats[0:5]


class RaceCat(models.Model):
    objects = RaceCatManager()
    race = models.ForeignKey(Race, on_delete=models.CASCADE)
    category = models.CharField(max_length=1)

    @property
    def podium(self):
        return RaceResult.objects.filter(race_cat=self, position__lte=3)

    @property
    def event_id(self):
        return self.race.event_id
    
    def __str__(self):
        return f'[{self.category}] {self.race}'




class RaceResult(models.Model):
    race_cat = models.ForeignKey(RaceCat, on_delete=models.CASCADE)
    racer_name = models.CharField(max_length=200)
    team = models.CharField(max_length=200)
    position = models.IntegerField()
    time_ms = models.IntegerField()
    zp_rank_before = models.FloatField()
    zp_rank_event = models.FloatField()

    def __str__(self):
        return f'[{self.position}][{self.race_cat.category}] {self.racer_name}'
