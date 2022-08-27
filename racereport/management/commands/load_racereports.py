from django.core.management.base import BaseCommand, CommandError
from racereport.models import Race, RaceCat, RaceResult, Team
from datetime import datetime
import csv
import glob
import logging
import os.path
import pytz

logger = logging.getLogger('main')

class Command(BaseCommand):
    help = 'imports scraped files into the database'
    
    # Expected file format:
    # EventID,EventTimestamp,Name,Team,Category,Time (ms),RankBefore,RankEvent,Position
    # 3054484,1661015400,Matthew Ladd,COALITION,A,2087000,172.34,,1

    def add_arguments(self, parser):
        parser.add_argument('paths', nargs='+')

    def handle(self, *args, **options):
        for path in options['paths']:
            # find all finishes.csv files in directory
            finish_file_paths = glob.glob(f'{path}/*/finishes.csv')
            logger.info(f'{len(finish_file_paths)} files found for importing')
            
            for finish_file_path in finish_file_paths:
                self.import_finish_file(finish_file_path)
            
    def import_finish_file(self, path):
        with open(path) as file:
            reader = csv.reader(file)
            next(reader) # header
            first_row = next(reader)
            event_datetime = datetime.fromtimestamp(int(first_row[1]), pytz.timezone("US/Eastern"))
            event_name = self.extract_race_name(path)
            event_id = first_row[0]
            logger.info(f'--{event_name}: {event_id}')
            race = Race.objects.get_or_create(
                event_id=event_id,
                defaults={'event_datetime': event_datetime, 'event_name': event_name}
            )[0]
            
            file.seek(0) # back to top
            next(reader) # skip header
            for row in reader:
                logger.debug(f'--parsing row:{row}')
                self.import_race_result(race, row)

    def extract_race_name(self, path):
        full_name = os.path.basename(os.path.dirname(path))
        race_name = full_name[8:] # remove beginning event_id from folder name
        return race_name


    def import_race_result(self, race, row):
        race_cat_row = RaceCat.objects.get_or_create(
            race=race,
            category=row[4]
        )[0]

        zp_rank_before = row[6]
        zp_rank_event = row[7]
        if zp_rank_before == '': zp_rank_before=0
        if zp_rank_event == '': zp_rank_event=0
        
        team_name = row[3]
        if row[3] == '': team_name='None'
        team_obj = Team.objects.get_or_create(name=team_name)

        race_result = RaceResult.objects.get_or_create(
            race_cat = race_cat_row,
            racer_name = row[2],
            defaults={'team':team_obj[0], 'position': row[8], 'time_ms': row[5], 'zp_rank_before': zp_rank_before, 'zp_rank_event': zp_rank_event}
        )