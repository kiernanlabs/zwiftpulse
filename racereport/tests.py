from django.core.management import call_command
from django.test import TestCase

from racereport.models import Race,RaceCat,RaceResult

class ImportRaceTestCase(TestCase):
    def setup(self):  
        pass
        
        # expected rows:
        # 3054484,1661015400,Matthew Ladd,COALITION,A,2087000,172.34,,1
        # 3054484,1661015400,Knox Whipple,,B,2129000,425.18,403.26,1
    
    def test_load_race(self):
        call_command('load_racereports', '/home/joey32/AntHill/zwiftpulse/racereport/sample_result')
        race = Race.objects.get(event_id=3054484)
        race_cat = RaceCat.objects.get(race=race, category='A')
        race_result = RaceResult.objects.filter(race_cat=race_cat)

        self.assertTrue(race)
        self.assertTrue(race_cat)
        self.assertTrue(race_result[0])
    
    def test_load_race_consistent_races(self):
        call_command('load_racereports', '/home/joey32/AntHill/zwiftpulse/racereport/sample_result')
        race = Race.objects.get(event_id=3054484)
        race_cat_A = RaceCat.objects.get(race=race, category='A')
        race_cat_B = RaceCat.objects.get(race=race, category='B')
        race_result_A = RaceResult.objects.filter(race_cat=race_cat_A)
        race_result_B = RaceResult.objects.filter(race_cat=race_cat_B)

        race_A = race_result_A[0].race_cat.race
        race_B = race_result_B[0].race_cat.race

        self.assertEqual(race_A.event_id, race_B.event_id)
    
    def test_race_cat_podium_full(self):
        call_command('load_racereports', '/home/joey32/AntHill/zwiftpulse/racereport/sample_result')
        race = Race.objects.get(event_id=3054484)
        race_cat_B = RaceCat.objects.get(race=race, category='B')
        self.assertIsNotNone(race_cat_B.podium)
    
    def test_race_cat_podium_only_one(self):
        call_command('load_racereports', '/home/joey32/AntHill/zwiftpulse/racereport/sample_result')
        race = Race.objects.get(event_id=3054484)
        race_cat_A = RaceCat.objects.get(race=race, category='A')
        self.assertIsNotNone(race_cat_A.podium)

