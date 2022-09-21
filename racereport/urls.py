from django.urls import path
from django_distill import distill_path
from . import views
from racereport.models import Race, RaceCat, RaceResult, Team, ScrapeReport
from django.db.models import Count, Min
from django.utils.html import conditional_escape


def get_index():
    return None

def get_week_reports():
    for category in ["A", "B", "C", "D", "E"]:
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
    for team in Team.objects.all().annotate(raceresult_count=Count('raceresult')).order_by('-raceresult_count')[:500]:
        for category in ["all","A", "B", "C", "D", "E"]:
            yield {'team_url_name':team.url_name, 'category':category}


urlpatterns = [
    distill_path('', views.this_week, name='this_week', distill_file='index.html'),
    distill_path('about', views.about, name='about'),
    distill_path('logs', views.last_100_scrapes, name='last_scrapes'),
    distill_path('week/<str:category>', views.this_week, name='this_week', distill_func=get_week_reports),
    distill_path('races/<str:category>', views.last_7_days_races, name='last_7_days_races', distill_func=get_last_7_days_races),
    distill_path('team/<str:team_url_name>/<str:category>', views.this_week_team_results, name='team_results', distill_func=get_team_pages_category),
]