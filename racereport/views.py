import django_tables2 as tables
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import render
from django.db.models import Count, Min, Subquery, OuterRef
from django.http import HttpResponse
from django.views.generic import (
    ListView,
)

from .models import Race, RaceCat, RaceResult, ScrapeReport, Team
import logging

logger = logging.getLogger('main')

def last_100_scrapes(request):
    scrape_reports = ScrapeReport.objects.all().order_by('-scrape_start')[:100]
    context = {'scrape_reports': scrape_reports}
    return render(request, 'racereport/scrape_list.html', context)

def last_24hrs(request, category=None):
    race_cats = RaceCat.objects.racecats_last24hrs(category).annotate(racer_count=Count('raceresult')).order_by("-racer_count")[:5]
    top_teams = Team.objects.get_top_10_teams(category)
    
    last_race_imported = Race.objects.last()
    most_recent_race_imported = Race.objects.latest('event_datetime')
    
    context = {'racecats': race_cats, 'top_teams': top_teams, 'last_race_imported': last_race_imported, 'most_recent_race_imported': most_recent_race_imported, 'category':category}
    return render(request, 'racereport/report.html', context)

def this_week(request, category=None):
    race_cats = RaceCat.objects.racecats_last24hrs(category).annotate(racer_count=Count('raceresult')).order_by("-racer_count")[:5]
    race_cats_quality = sorted(race_cats, key=lambda x: x.race_quality)[:5]
    top_teams = Team.objects.get_top_10_teams_this_week(category)
    
    last_race_imported = Race.objects.last()
    most_recent_race_imported = Race.objects.latest('event_datetime')
    
    context = {'racecats': race_cats_quality, 'top_teams': top_teams, 'last_race_imported': last_race_imported, 'most_recent_race_imported': most_recent_race_imported, 'category':category}
    return render(request, 'racereport/report_week.html', context)

def this_week_team_results(request, team_name, category=None):
    try:
        team = Team.objects.get(name=team_name)
        print(f"Found team: {team_name}")
    except:
        print(f"Can't find team: {team_name}")        
        context = {'error': "Error"}
        return render(request, 'racereport/error.html', context)

    results = team.get_podiums_this_week(category)
    racecat_wins = RaceCat.objects.filter(pk__in=results['win_results'].values('race_cat')).annotate(racer_count=Count('raceresult')).order_by('-race__event_datetime')
    '''
    racecat_wins = []
    for race_result in results['win_results']:
        race_cat = race_result.race_cat
    '''

    context = {'racecats': racecat_wins, 'team':team}
    return render(request, 'racereport/team_report.html', context)

def scrape_reports(request):
    pass
