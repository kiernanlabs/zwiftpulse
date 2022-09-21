from django.core.management.base import BaseCommand
from django.utils import timezone
from racereport.models import Race, RaceCat, RaceResult, Team, ScrapeReport, Narrative
from datetime import datetime, timedelta
import logging

logger = logging.getLogger('main')

class Command(BaseCommand):
    help = 'updates include/exclude on all racecats from last 7 days'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        logger.info("Cleaning racecats...")
        
        seven_days_ago = timezone.now() - timedelta(days = 7)
        race_cats = RaceCat.objects.racecats_since(seven_days_ago)

        count_excluded = 0

        for race_cat in race_cats:
            race_cat.set_include()
            if race_cat.include == False: count_excluded += 1
        
        logger.info(f"{len(race_cats)} race_cats cleaned, {count_excluded} excluded")
        


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
            narrative.combined_score = (narrative.impact_score*2 + narrative.surprise_score)/3
            narrative.save()
            logger.debug(f"-- {narrative}: combined:{round(narrative.combined_score)} impact:{round(narrative.impact_score)}; surprise:{round(narrative.surprise_score)}")
            

