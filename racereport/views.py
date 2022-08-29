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

def index(request):
    race_cats = RaceCat.objects.racecats_last24hrs().annotate(racer_count=Count('raceresult')).order_by("-racer_count")
    top_teams = Team.objects.get_top_10_teams()
    context = {'racecats': race_cats, 'top_teams': top_teams}
    return render(request, 'racereport/racecat_list.html', context)