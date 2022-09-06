import django_tables2 as tables
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import render
from django.db.models import Count, Min, Subquery, OuterRef
from django.http import HttpResponse
from django.views.generic import (
    ListView,
)

from .models import Race, RaceCat, RaceResult, Team

def last_24hrs(request, category=None):
    race_cats = RaceCat.objects.racecats_last24hrs(category).annotate(racer_count=Count('raceresult')).order_by("-racer_count")[:5]
    top_teams = Team.objects.get_top_10_teams(category)
    
    last_race_imported = Race.objects.last()
    most_recent_race_imported = Race.objects.latest('event_datetime')
    
    context = {'racecats': race_cats, 'top_teams': top_teams, 'last_race_imported': last_race_imported, 'most_recent_race_imported': most_recent_race_imported, 'category':category}
    return render(request, 'racereport/report.html', context)

def this_week(request, category=None):
    race_cats = RaceCat.objects.racecats_last24hrs(category).annotate(racer_count=Count('raceresult')).order_by("-racer_count")[:5]
    top_teams = Team.objects.get_top_10_teams_this_week(category)
    
    last_race_imported = Race.objects.last()
    most_recent_race_imported = Race.objects.latest('event_datetime')
    
    context = {'racecats': race_cats, 'top_teams': top_teams, 'last_race_imported': last_race_imported, 'most_recent_race_imported': most_recent_race_imported, 'category':category}
    return render(request, 'racereport/report_week.html', context)
