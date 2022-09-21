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
        logger.info("Generating Narratives...")
        # For each category, get top 10 teams
        # For each team, get and update the narrative
        # For each narrative, reevaluate scores for all narratives updated

        today = timezone.now()
        beginning_of_week = today - timedelta(days=today.weekday(),hours=today.hour, minutes=today.minute, seconds=today.second, microseconds=today.microsecond)
        
        categories = ["A","B","C","D"]
        for category in categories:
            logger.debug(f"-- {category}")
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
        
        narratives = Narrative.objects.get_this_week_narratives()
        logger.info(f"-- {len(narratives)} active narratives found this week")

        self.evaluate_narrative_scores(narratives)

    def evaluate_narrative_scores(self, narratives):
        # calculate max impact
        # calculate max surprise

        logger.debug(f"-- evaluating scores for {len(narratives)} narratives")

        max_impact = 0
        max_surprise = 0.0

        for narrative in narratives:
            if narrative.calc_impact() > max_impact: max_impact = narrative.calc_impact()
            if narrative.calc_surprise() > max_surprise: max_surprise = narrative.calc_surprise()

        logger.info(f"-- max impact: {max_impact}; max surprise: {max_surprise};")
        
        if max_impact == 0: 
            logger.debug(f"-- exiting, no narratives with impact found")
            return

        if max_surprise == 0: 
            logger.debug(f"-- exiting, no narratives with surprise found")
            return


        for narrative in narratives:
            narrative.impact_score = (narrative.calc_impact() / max_impact)*100
            narrative.surprise_score = (narrative.calc_surprise() / max_surprise)*100
            narrative.combined_score = (narrative.impact_score + narrative.surprise_score)/2
            narrative.save()
            logger.debug(f"-- {narrative}: combined:{round(narrative.combined_score)} impact:{round(narrative.impact_score)}; surprise:{round(narrative.surprise_score)}")
            
