from django.core.management.base import BaseCommand
from django.utils import timezone
from racereport.models import Race, RaceCat, RaceResult, Team, ScrapeReport, Narrative
from datetime import datetime, timedelta
import logging

logger = logging.getLogger('main')

class Command(BaseCommand):
    help = 'generates narratives (tweets) for publication'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        
        # For each category, get top 10 teams
        # For each team, get and update the narrative
        # For each narrative, reevaluate scores for all narratives updated

        today = timezone.now()
        beginning_of_week = today - timedelta(days=today.weekday(),hours=today.hour, minutes=today.minute, seconds=today.second, microseconds=today.microsecond)
        
        categories = ["A","B","C","D"]
        for category in categories:
            top_teams = Team.objects.get_top_10_teams_this_week(category)
            for rank, team_rank in enumerate(top_teams):
                team = team_rank['team']
                if team.name == "None" : continue
                
                narratives = Narrative.objects.filter(created_at__gte=beginning_of_week, actor=team)
                if len(narratives)==0:
                   Narrative.objects.create_24hr_wins_narrative(team, category, rank)
                else:
                    narrative = narratives[0]
                    narrative.update(rank)

