from datetime import datetime, timedelta
from django.utils import timezone
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
    def top_5_races(self, start_time):
        racecats = RaceCat.objects.annotate(race_time=Min('race__event_datetime'), racer_count=Count('raceresult')).filter(race_time__gte=start_time).order_by('racer_count')
        return racecats[0:5]
    
    def top_5_races_cat(self, start_time, category):
        racecats = RaceCat.objects.annotate(race_time=Min('race__event_datetime'), racer_count=Count('raceresult')).filter(race_time__gte=start_time, category=category).order_by('racer_count')
        return racecats[0:5]
    
    def racecats_since(self, start_time):
        return RaceCat.objects.annotate(race_time=Min('race__event_datetime')).filter(race_time__gte=start_time)
    
    def racecats_last24hrs(self, category=None):
        twenty_four_hours_ago = timezone.now() - timedelta(days = 1)
        if category:
            return RaceCat.objects.annotate(race_time=Min('race__event_datetime')).filter(
                race_time__gte=twenty_four_hours_ago, category=category)
        else:
            return RaceCat.objects.annotate(race_time=Min('race__event_datetime')).filter(
                race_time__gte=twenty_four_hours_ago)

    def racecats_prev24hrs(self, category=None):
        twenty_four_hours_ago = timezone.now() - timedelta(days = 1)
        forty_eight_hours_ago = timezone.now() - timedelta(days = 2)
        if category:
            return RaceCat.objects.annotate(race_time=Min('race__event_datetime')).filter(
                race_time__gte=forty_eight_hours_ago,
                race_time__lte=twenty_four_hours_ago,
                category=category)
        else:
            return RaceCat.objects.annotate(race_time=Min('race__event_datetime')).filter(
                race_time__gte=forty_eight_hours_ago,
                race_time__lte=twenty_four_hours_ago)

class RaceCat(models.Model):
    objects = RaceCatManager()
    race = models.ForeignKey(Race, on_delete=models.CASCADE)
    category = models.CharField(max_length=1)

    @property
    def first(self):
        query_set = RaceResult.objects.filter(race_cat=self, position=1)
        if len(query_set)>0: return query_set[0]
        
        return None 

    @property
    def second(self):
        query_set = RaceResult.objects.filter(race_cat=self, position=2)
        if len(query_set)>0: return query_set[0]
        
        return None 
    @property
    def third(self):
        query_set = RaceResult.objects.filter(race_cat=self, position=3)
        if len(query_set)>0: return query_set[0]
        
        return None 
    @property
    def podium(self):
        return RaceResult.objects.filter(race_cat=self, position__lte=3)

    @property
    def event_id(self):
        return self.race.event_id
    
    def __str__(self):
        return f'[{self.category}] {self.race}'


class RaceResultManager(models.Manager):
    def raceresults_since(self, start_time, category):
        racecats_since = RaceCat.objects.racecats_since(start_time, category)
        raceresults = super.filter(race__in=racecats_since)
        return raceresults

class TeamManager(models.Manager):
    def get_top_10_teams(self, category=None):
        teams = Team.objects.all()
        team_ranking = []
        for team in teams:
            team_last_24hr_results = team.get_podiums_last_24hrs(category)
            team_prev_24hr_results = team.get_podiums_prev_24hrs(category)
            team_all_results = team.get_all_podiums()
            team_ranking.append({
                "team": team,
                "24hr_wins": team_last_24hr_results['win_results'],
                "24hr_wins_count": len(team_last_24hr_results['win_results']),
                "wins_change": (len(team_last_24hr_results['win_results']) - len(team_prev_24hr_results['win_results'])),
                "24hr_podiums": team_last_24hr_results['podium_results'],
                "24hr_podiums_count": len(team_last_24hr_results['podium_results']),
                "podiums_change": (len(team_last_24hr_results['podium_results']) - len(team_prev_24hr_results['podium_results'])),
                "all_time_wins": len(team_all_results['win_results']),
            })
        return sorted(team_ranking,key=lambda d: d['24hr_wins_count'], reverse=True)[:10]
        

class Team(models.Model):
    objects = TeamManager()
    name = models.CharField(max_length=200)
    
    def get_all_podiums(self):
        win_results = RaceResult.objects.filter(position=1, team=self)
        podium_results = RaceResult.objects.filter(position__lte=3, team=self)
        return {'win_results': win_results, 'podium_results': podium_results}


    def get_podiums_last_24hrs(self, category=None):
        racecats_since = None
        racecats_since = RaceCat.objects.racecats_last24hrs(category)    
        win_results = RaceResult.objects.filter(race_cat__in=racecats_since, position=1, team=self)
        podium_results = RaceResult.objects.filter(race_cat__in=racecats_since, position__lte=3, team=self)
        return {'win_results': win_results, 'podium_results': podium_results}

    def get_podiums_prev_24hrs(self, category=None):
        racecats_since = RaceCat.objects.racecats_prev24hrs(category)
        win_results = RaceResult.objects.filter(race_cat__in=racecats_since, position=1, team=self)
        podium_results = RaceResult.objects.filter(race_cat__in=racecats_since, position__lte=3, team=self)
        return {'win_results': win_results, 'podium_results': podium_results}

    
    def get_wins_since(self, start_time):
        racecats_since = RaceCat.objects.racecats_since(start_time)
        win_results = RaceResult.objects.filter(race_cat__in=racecats_since, position=1, team=self)
        return win_results
    
    def get_podiums_since(self, start_time):
        racecats_since = RaceCat.objects.racecats_since(start_time)
        win_results = RaceResult.objects.filter(race_cat__in=racecats_since, position__lte=3, team=self)
        return win_results

    def __str__(self):
        return self.name


class RaceResult(models.Model):
    race_cat = models.ForeignKey(RaceCat, on_delete=models.CASCADE)
    racer_name = models.CharField(max_length=200)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    position = models.IntegerField()
    time_ms = models.IntegerField()
    zp_rank_before = models.FloatField()
    zp_rank_event = models.FloatField()

    def __str__(self):
        return f'[{self.position}][{self.race_cat.category}] {self.racer_name}'
