from django.core.management.base import BaseCommand, CommandError
from racereport.models import Race, RaceCat, RaceResult
from datetime import datetime
import csv
import os.path
import pytz


class Command(BaseCommand):
    help = 'imports scraped files into the database'
    
    # Expected file format:
    # EventID,EventTimestamp,Name,Team,Category,Time (ms),RankBefore,RankEvent,Position
    # 3054484,1661015400,Matthew Ladd,COALITION,A,2087000,172.34,,1

    def add_arguments(self, parser):
        parser.add_argument('paths', nargs='+')

    def handle(self, *args, **options):
        for path in options['paths']:
            self.import_finish_file(path)
            
    def import_finish_file(self, path):
        with open(path) as file:
            reader = csv.reader(file)
            next(reader) # header
            first_row = next(reader)
            event_datetime = datetime.fromtimestamp(int(first_row[1]), pytz.timezone("US/Eastern"))
            race = Race.objects.get_or_create(
                event_id=first_row[0],
                defaults={'event_datetime': event_datetime, 'event_name': self.extract_race_name(path)}
            )[0]
            
            file.seek(0) # back to top
            next(reader) # skip header
            for row in reader:
                print(f'--parsing row:{row}')
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

        race_result = RaceResult.objects.get_or_create(
            race_cat = race_cat_row,
            racer_name = row[2],
            defaults={'team': row[4], 'position': row[8], 'time_ms': row[5], 'zp_rank_before': zp_rank_before, 'zp_rank_event': zp_rank_event}
        )