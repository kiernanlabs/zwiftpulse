from nis import cat
import django_tables2 as tables
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import render
from django.db.models import Count, Min, Subquery, OuterRef
from django.http import HttpResponse
from django.views.generic import (
    ListView,
)

from .models import Race, RaceCat, RaceResult, ScrapeReport, Team, Narrative, Video
import logging

logger = logging.getLogger('main')

def about(request):
    context = {'category':None, 'report':'','timeframe':'week'}
    return render(request, 'racereport/about.html', context)

def display_race_single(request, event_id, category):
    race = Race.objects.get(event_id=event_id)
    race_cat = RaceCat.objects.filter(race=race,category=category).annotate(racer_count=Count('raceresult'))[0]
    videos = Video.objects.filter(race_cat=race_cat)
    context = {'category':None, 'report':'races','racecat':race_cat, 'timeframe':'week', 'videos':videos} 
    return render(request, 'racereport/race_page.html', context)


def submit_video(request):
    context = {'category':None, 'report':'','timeframe':'week'}
    return render(request, 'racereport/submit_video.html', context)

def process_video(request):
    logger.info(request.POST)
    commentary=False

    context = {'category':None, 'report':'','timeframe':'week'}

    if request.POST['commentary']=="yes": commentary=True
    video = Video.objects.create_video(request.POST['zp_url'], request.POST['category'], request.POST['stream_url'], request.POST['streamer_name'], commentary, request.POST['description'])
    if video:
        context = {'category':None, 'report':'video_submit', 'detail':video, 'timeframe':'week'}    
        return render(request, 'racereport/success.html', context)
    else:
        context = {'category':None, 'report':'video_submit', 'detail':"failed video creation", 'timeframe':'week'}    
        return render(request, 'racereport/error.html', context)

def last_100_scrapes(request):
    scrape_reports = ScrapeReport.objects.all().order_by('-scrape_start')[:100]
    context = {'scrape_reports': scrape_reports, 'category':None, 'report':'','timeframe':'week'}
    return render(request, 'racereport/scrape_list.html', context)

'''
def last_24hrs(request, category=None):
    race_cats = RaceCat.objects.racecats_last24hrs(category).annotate(racer_count=Count('raceresult')).order_by("-racer_count")[:5]
    top_teams = Team.objects.get_top_10_teams(category)
    
    last_race_imported = Race.objects.last()
    most_recent_race_imported = Race.objects.latest('event_datetime')
    
    context = {'racecats': race_cats, 'top_teams': top_teams, 'last_race_imported': last_race_imported, 'most_recent_race_imported': most_recent_race_imported, 'category':category}
    return render(request, 'racereport/report.html', context)
'''

def last_7_days_races(request, category=None):
    if category=="all": category=None
    race_cats_quality = RaceCat.objects.most_competitive_races_last_7_days(category)
    race_cats_size = RaceCat.objects.largest_races_last_7_days(category)

    context = {'racecats_quality': race_cats_quality, 'racecats_size': race_cats_size, 'category':category, 'report':'races','timeframe':'week'}
    return render(request, 'racereport/top_race_report.html', context)

def last_24hrs_races(request, category=None):
    if category=="all": category=None
    race_cats_quality = RaceCat.objects.most_competitive_races_last_24hrs(category)
    race_cats_size = RaceCat.objects.largest_races_last_24hrs(category)

    context = {'racecats_quality': race_cats_quality, 'racecats_size': race_cats_size, 'category':category, 'report':'races','timeframe':'day'}
    return render(request, 'racereport/top_race_report.html', context)


def top_teams(request, category=None):
    if category=="all": category=None
    top_teams = Team.objects.get_top_10_teams_this_week(category)

    narratives = Narrative.objects.get_top_10_narratives(category)[:5]
    
    context = {'narratives': narratives, 'top_teams': top_teams, 'category':category, 'report':'top_teams','timeframe':'week'}
    return render(request, 'racereport/top_team_report.html', context)

def this_week_team_results(request, team_url_name, category=None):
    team_name = team_url_name.replace('-slash-','/')
    team_name = team_name.replace('-space-',' ')
    team_name = team_name.replace('-pipe-','|')

    if category=="all": category=None
    try:
        team = Team.objects.get(name=team_name)
    except:
        context = {'error': "Error", 'category':category, 'report':'top_teams','timeframe':'week'}
        return render(request, 'racereport/error.html', context)

    results = team.get_podiums_this_week(category)
    racecat_wins = RaceCat.objects.filter(pk__in=results['win_results'].values('race_cat')).annotate(racer_count=Count('raceresult')).order_by('-race__event_datetime')
    '''
    racecat_wins = []
    for race_result in results['win_results']:
        race_cat = race_result.race_cat
    '''

    context = {'racecats': racecat_wins, 'team':team, 'category':category, 'report':'top_teams','timeframe':'week'}
    return render(request, 'racereport/team_report.html', context)

def scrape_reports(request):
    pass
