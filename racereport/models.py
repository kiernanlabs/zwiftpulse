from django.db import models

class Race(models.Model):
    event_id = models.IntegerField()
    event_datetime = models.DateTimeField()
    event_name = models.CharField(max_length=200)
    # distance_km = models.FloatField()
    # course = models.CharField(max_length=200)

    def __str__(self):
        return self.event_name

class RaceCat(models.Model):
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

class RaceCatManager(models.Manager):
    def top5races(self):
        # Need to filter down to top races per category
        pass

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
