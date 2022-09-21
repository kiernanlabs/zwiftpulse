from datetime import datetime, timedelta
from nis import cat
from django.utils import timezone
from django.db import models
from django.db.models import Count, Min



class ScrapeReport(models.Model):
    scrape_start = models.DateTimeField()
    scrape_end = models.DateTimeField(default=None, blank=True, null=True)
    completed = models.BooleanField(default=False)
    count_successful = models.IntegerField(default=0, blank=True, null=True)
    
    def __str__(self):
        return f"=== {self.scrape_start} :: [{self.completed} - {self.count_successful} successful] completed: {self.scrape_end}"

class Race(models.Model):
    event_id = models.IntegerField()
    event_datetime = models.DateTimeField()
    event_name = models.CharField(max_length=200)
    # distance_km = models.FloatField()
    # course = models.CharField(max_length=200)

    def __str__(self):
        return self.event_name
    
    @property
    def hours_ago(self):
        return round((timezone.now() - self.event_datetime).seconds/60/60)

class RaceCatManager(models.Manager):
    def top_5_races(self, start_time):
        racecats = RaceCat.objects.annotate(race_time=Min('race__event_datetime'), racer_count=Count('raceresult')).filter(race_time__gte=start_time, include=True).order_by('racer_count')
        return racecats[0:5]
    
    def top_5_races_cat(self, start_time, category):
        racecats = RaceCat.objects.annotate(race_time=Min('race__event_datetime'), racer_count=Count('raceresult')).filter(race_time__gte=start_time, category=category, include=True).order_by('racer_count')
        return racecats[0:5]
    
    def racecats_since(self, start_time):
        return RaceCat.objects.annotate(race_time=Min('race__event_datetime')).filter(race_time__gte=start_time, include=True)
    
    def racecats_this_week(self, category=None):
        today = timezone.now()
        beginning_of_week = today - timedelta(days=today.weekday(),hours=today.hour, minutes=today.minute, seconds=today.second, microseconds=today.microsecond)
        if category:
            return RaceCat.objects.annotate(race_time=Min('race__event_datetime')).filter(
                race_time__gte=beginning_of_week, category=category, include=True)
        else:
            return RaceCat.objects.annotate(race_time=Min('race__event_datetime')).filter(
                race_time__gte=beginning_of_week, include=True)
    
    def racecats_prev_week(self, category=None):
        today = timezone.now()
        end_of_last_week = today - timedelta(days=today.weekday(),hours=today.hour, minutes=today.minute, seconds=today.second, microseconds=today.microsecond)
        beginning_of_last_week = end_of_last_week - timedelta(days=7)
        if category:
            return RaceCat.objects.annotate(race_time=Min('race__event_datetime')).filter(
                race_time__gte=beginning_of_last_week,
                race_time__lte=end_of_last_week,
                category=category, include=True)
        else:
            return RaceCat.objects.annotate(race_time=Min('race__event_datetime')).filter(
                race_time__gte=beginning_of_last_week,
                race_time__lte=end_of_last_week, include=True)

    def racecats_last24hrs(self, category=None):
        twenty_four_hours_ago = timezone.now() - timedelta(days = 1)
        if category:
            return RaceCat.objects.annotate(race_time=Min('race__event_datetime')).filter(
                race_time__gte=twenty_four_hours_ago, category=category, include=True)
        else:
            return RaceCat.objects.annotate(race_time=Min('race__event_datetime')).filter(
                race_time__gte=twenty_four_hours_ago, include=True)

    def racecats_prev24hrs(self, category=None):
        twenty_four_hours_ago = timezone.now() - timedelta(days = 1)
        forty_eight_hours_ago = timezone.now() - timedelta(days = 2)
        if category:
            return RaceCat.objects.annotate(race_time=Min('race__event_datetime')).filter(
                race_time__gte=forty_eight_hours_ago,
                race_time__lte=twenty_four_hours_ago,
                category=category, include=True)
        else:
            return RaceCat.objects.annotate(race_time=Min('race__event_datetime')).filter(
                race_time__gte=forty_eight_hours_ago,
                race_time__lte=twenty_four_hours_ago, include=True)
    
    def largest_races_last_7_days(self, category=None):
        seven_days_ago = timezone.now() - timedelta(days = 7)
        if category:
            race_cats = RaceCat.objects.annotate(race_time=Min('race__event_datetime'), racer_count=Count('raceresult')).filter(
                race_time__gte=seven_days_ago, category=category, include=True).order_by('-racer_count')
        else:
            race_cats = RaceCat.objects.annotate(race_time=Min('race__event_datetime'), racer_count=Count('raceresult')).filter(
                race_time__gte=seven_days_ago, include=True).order_by('-racer_count')
        
        return race_cats[:10]
    
    def most_competitive_races_last_7_days(self, category=None):
        seven_days_ago = timezone.now() - timedelta(days = 7)
        if category:
            race_cats = RaceCat.objects.annotate(race_time=Min('race__event_datetime'), racer_count=Count('raceresult')).filter(
                race_time__gte=seven_days_ago, category=category, include=True).order_by('-racer_count')
        else:
            race_cats = RaceCat.objects.annotate(race_time=Min('race__event_datetime'), racer_count=Count('raceresult')).filter(
                race_time__gte=seven_days_ago, include=True).order_by('-racer_count')
        
        return sorted(race_cats, key=lambda x: x.race_quality)[:10]
        

class RaceCat(models.Model):
    objects = RaceCatManager()
    race = models.ForeignKey(Race, on_delete=models.CASCADE)
    category = models.CharField(max_length=1)
    include = models.BooleanField(default=True)

    def set_include(self):
        if "Team Time Trial" in self.race.event_name: self.include = False
        if len(RaceResult.objects.filter(race_cat=self)) < 4: self.include = False
        self.save()

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
    def top_three_racers(self):
        query_set = RaceResult.objects.filter(race_cat=self, zp_rank_before__gte=1).order_by('zp_rank_before')
        if len(query_set)>0: return query_set[:3]

        return None

    @property
    def event_id(self):
        return self.race.event_id
    
    @property
    def race_quality(self):
        if self.first.zp_rank_event > 40: return self.first.zp_rank_event
        return 999
    
    @property
    def num_racers(self):
        return len(RaceResult.objects.filter(race_cat=self))

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
        return sorted(team_ranking,key=lambda d: d['24hr_wins_count'], reverse=True)[:11]
    
    def get_top_10_teams_this_week(self, category=None):
        racecats_this_week = RaceCat.objects.racecats_this_week(category)
        this_week_podiums = RaceResult.objects.filter(race_cat__in=racecats_this_week, position__lte=3)
        teams = Team.objects.filter(pk__in=this_week_podiums.values('team'))
        team_ranking = []
        for team in teams:
            team_this_week_results = team.get_podiums_this_week(category)
            team_prev_week_results = team.get_podiums_prev_week(category)
            team_last_24hr_results = team.get_podiums_last_24hrs(category)
            team_all_results = team.get_all_podiums(category)
            team_ranking.append({
                "team": team,
                "this_week_wins": team_this_week_results['win_results'],
                "this_week_wins_count": len(team_this_week_results['win_results']),
                "prev_week_wins_count": len(team_prev_week_results['win_results']),
                "last_24hrs_wins_count": (len(team_last_24hr_results['win_results'])),
                "this_week_podium_count": len(team_this_week_results['podium_results']),
                "all_time_wins": len(team_all_results['win_results']),
            })
        return sorted(team_ranking,key=lambda d: d['this_week_wins_count'], reverse=True)[:11]
        
class Team(models.Model):
    objects = TeamManager()
    name = models.CharField(max_length=200)

    @property
    def url_name(self):
        result = self.name.replace('/','-slash-')
        result = result.replace(' ','-space-')
        result = result.replace('|','-pipe-')
        return result

    def get_all_podiums(self, category=None):
        if category == None: 
            win_results = RaceResult.objects.filter(position=1, team=self, race_cat__include=True)
            podium_results = RaceResult.objects.filter(position__lte=3, team=self, race_cat__include=True)
        else:
            win_results = RaceResult.objects.filter(position=1, team=self, race_cat__category=category, race_cat__include=True)
            podium_results = RaceResult.objects.filter(position__lte=3, team=self, race_cat__category=category, race_cat__include=True)
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

    def get_podiums_this_week(self, category=None):
        racecats_since = None
        racecats_since = RaceCat.objects.racecats_this_week(category)    
        win_results = RaceResult.objects.filter(race_cat__in=racecats_since, position=1, team=self)
        podium_results = RaceResult.objects.filter(race_cat__in=racecats_since, position__lte=3, team=self)
        return {'win_results': win_results, 'podium_results': podium_results}

    def get_podiums_prev_week(self, category=None):
        racecats_since = RaceCat.objects.racecats_prev_week(category)
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

class NarrativeManager(models.Manager):
    def create_24hr_wins_narrative(self, team, category, weekly_place):
        podiums = team.get_podiums_last_24hrs(category)
        last_week_podiums = team.get_podiums_prev_week(category)
        narrative = Narrative(
            type = "24hr wins",
            actor = team,
            arena = category,
            action = len(podiums['win_results']),
            outcome = weekly_place,
            context = len(last_week_podiums['win_results']),
        )
        narrative.save()

        narrative.why.clear()
        for race_result in podiums['win_results']:
            narrative.why.add(race_result)
    
    def get_this_week_narratives(self, category=None):
        today = timezone.now()
        beginning_of_week = today - timedelta(days=today.weekday(),hours=today.hour, minutes=today.minute, seconds=today.second, microseconds=today.microsecond)
        if category == None: return Narrative.objects.filter(created_at__gte=beginning_of_week)
        else: return Narrative.objects.filter(created_at__gte=beginning_of_week, arena=category)
    
    def get_top_10_narratives(self, category=None):
        today = timezone.now()
        beginning_of_week = today - timedelta(days=today.weekday(),hours=today.hour, minutes=today.minute, seconds=today.second, microseconds=today.microsecond)
        if category == None: return Narrative.objects.filter(created_at__gte=beginning_of_week).order_by('-combined_score')[:10]
        else: return Narrative.objects.filter(created_at__gte=beginning_of_week, arena=category).order_by('-combined_score')[:10]

class Narrative(models.Model):
    type = models.CharField(max_length=200) # team 24hr wins
    actor = models.ForeignKey(Team, on_delete=models.CASCADE) # team
    arena = models.CharField(max_length=200) # category
    action = models.IntegerField() # wins
    outcome = models.IntegerField() # weekly place
    context = models.IntegerField() # last week wins
    why = models.ManyToManyField(RaceResult) # list of raceresults
    impact_score = models.IntegerField(default=0) # number of wins
    surprise_score = models.IntegerField(default=0) # difference between wins and last week wins
    combined_score = models.IntegerField(default=0) # average of surprise and impact
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = NarrativeManager()
    
    def __str__(self):
        return f"{self.created_at}[{self.combined_score}]::{self.actor} wins {self.action} races in the last 24hrs in {self.arena} category::{self.impact_score}|{self.surprise_score}"

    @property
    def humanize_outcome(self):
        if self.outcome == 0: return "n/a"
        if self.outcome == 1: return "1st"
        if self.outcome == 2: return "2nd"
        if self.outcome == 3: return "3rd"
        if self.outcome <= 20: return f"{self.outcome}th"
        return f"{self.outcome}"

    @property
    def print_narrative(self):
        return f"{self.actor} wins {self.action} races in the last 24hrs in {self.arena} category, moving into {self.humanize_outcome} place this week.  Last week {self.actor} won {self.context} total races (~{round(self.context/7)} per day)."
    
    @property
    def print_narrative_no_team(self):
        return f" wins {self.action} races in the last 24hrs in {self.arena} category, moving into {self.humanize_outcome} place this week.  Last week {self.actor} won {self.context} total races (~{round(self.context/7)} per day)."
    

    def calc_impact(self):
        return self.action
    
    def calc_surprise(self):
        last_week_daily_wins = self.context / 7
        return max(self.action - last_week_daily_wins,0)

    @property
    def currently_active(self):
        today = timezone.now()
        if today.strftime("%V") == self.created_at.strftime("%V"): return True
        return False
    
    def update(self, weekly_place):
        podiums = self.actor.get_podiums_last_24hrs(self.arena)
        self.action = len(podiums['win_results'])
        self.outcome = weekly_place

        self.why.clear()
        for race_result in podiums['win_results']: self.why.add(race_result)

        self.save()



