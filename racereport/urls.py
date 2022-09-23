from django.urls import path
from django_distill import distill_path
from . import views
from racereport.models import Race, RaceCat, RaceResult, Team, ScrapeReport
from django.db.models import Count, Min, Q
from django.utils.html import conditional_escape


def get_index():
    return None

def get_team_reports():
    for category in ["all", "A", "B", "C", "D", "E"]:
        yield {'category':category}

def get_last_7_days_races():
    for category in ["all", "A", "B", "C", "D", "E"]:
        yield {'category':category}


'''
def get_team_pages():
    for team in Team.objects.all().annotate(raceresult_count=Count('raceresult')).order_by('-raceresult_count')[:100]:
        team_url_name = team.url_name
        yield {'team_url_name':team_url_name}
'''

def get_team_pages_category():
    teams = Team.objects.get_teams_with_wins_today()
    for team in teams:
        for category in ["all","A", "B", "C", "D", "E"]:
            yield {'team_url_name':team.url_name, 'category':category}

#    distill_path('race/<int:event_id>/<str:category>', views.display_race_single, name='display_race_single'),
#    distill_path('submit_video', views.submit_video, name='submit_video'),
#    distill_path('process_video', views.process_video, name='process_video'),

urlpatterns = [
    distill_path('', views.top_teams, name='top_teams', distill_file='index.html'),
    distill_path('about', views.about, name='about'),
    distill_path('logs', views.last_100_scrapes, name='last_scrapes'),
    distill_path('top_teams/<str:category>', views.top_teams, name='top_teams', distill_func=get_team_reports),
    distill_path('races/week/<str:category>', views.last_7_days_races, name='last_7_days_races', distill_func=get_last_7_days_races),
    distill_path('races/day/<str:category>', views.last_24hrs_races, name='last_24hr_races', distill_func=get_last_7_days_races),
    distill_path('team/<str:team_url_name>/<str:category>', views.this_week_team_results, name='team_results'),
    
    # switching team pages to live (no need to generate)
    # distill_path('team/<str:team_url_name>/<str:category>', views.this_week_team_results, name='team_results', distill_func=get_team_pages_category),
]